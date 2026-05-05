<?php
// WT Fasteners Contact Form Handler

const MAX_ATTACHMENT_BYTES = 10485760; // 10MB per file
const MAX_ATTACHMENT_COUNT = 5;
const MAX_ATTACHMENT_TOTAL_BYTES = 31457280; // 30MB total per submission
const BLOCKED_ATTACHMENT_EXTENSIONS = [
    'php', 'phtml', 'phar', 'cgi', 'pl', 'py', 'sh', 'bash', 'zsh', 'exe', 'dll', 'bat', 'cmd', 'com', 'scr', 'js', 'mjs', 'html', 'htm', 'shtml', 'svg'
];

function normalize_uploaded_files($field) {
    if (!isset($_FILES[$field])) {
        return [];
    }
    $files = $_FILES[$field];
    $normalized = [];
    if (is_array($files['name'])) {
        $count = count($files['name']);
        for ($i = 0; $i < $count; $i++) {
            $normalized[] = [
                'name' => $files['name'][$i] ?? '',
                'type' => $files['type'][$i] ?? '',
                'tmp_name' => $files['tmp_name'][$i] ?? '',
                'error' => $files['error'][$i] ?? UPLOAD_ERR_NO_FILE,
                'size' => $files['size'][$i] ?? 0,
            ];
        }
    } else {
        $normalized[] = $files;
    }
    return $normalized;
}

function fail_upload($message, $status = 400) {
    http_response_code($status);
    header('Content-Type: text/plain; charset=utf-8');
    echo $message;
    exit;
}

function save_uploaded_attachments($save_dir, $safe_time, $safe_email) {
    $uploads = normalize_uploaded_files('attachments');
    $uploads = array_values(array_filter($uploads, function ($file) {
        return isset($file['error']) && intval($file['error']) !== UPLOAD_ERR_NO_FILE;
    }));

    if (count($uploads) > MAX_ATTACHMENT_COUNT) {
        fail_upload('You can upload up to ' . MAX_ATTACHMENT_COUNT . ' files per submission.', 413);
    }

    $total = 0;
    $saved = [];
    if (!$uploads) {
        return $saved;
    }

    $attachment_dir = rtrim($save_dir, "/\\") . '/attachments';
    if (!is_dir($attachment_dir) && !@mkdir($attachment_dir, 0755, true)) {
        fail_upload('Attachment folder could not be created. Please contact us by WhatsApp or email.', 500);
    }
    if (!is_writable($attachment_dir)) {
        fail_upload('Attachment folder is not writable. Please contact us by WhatsApp or email.', 500);
    }

    foreach ($uploads as $idx => $file) {
        $error = intval($file['error'] ?? UPLOAD_ERR_NO_FILE);
        if ($error !== UPLOAD_ERR_OK) {
            fail_upload('File upload failed. Error code: ' . $error, 400);
        }
        $size = intval($file['size'] ?? 0);
        if ($size <= 0) {
            fail_upload('Uploaded file is empty.', 400);
        }
        if ($size > MAX_ATTACHMENT_BYTES) {
            fail_upload('Each uploaded file must be 10MB or smaller.', 413);
        }
        $total += $size;
        if ($total > MAX_ATTACHMENT_TOTAL_BYTES) {
            fail_upload('Total uploaded files must be 30MB or smaller.', 413);
        }

        $original = basename((string)($file['name'] ?? 'attachment'));
        $ext = strtolower(pathinfo($original, PATHINFO_EXTENSION));
        if ($ext === '' || in_array($ext, BLOCKED_ATTACHMENT_EXTENSIONS, true)) {
            fail_upload('This file type is not allowed. Please upload drawings, documents, images, ZIP/RAR, or CAD files.', 400);
        }

        $base = pathinfo($original, PATHINFO_FILENAME);
        $base = preg_replace('/[^a-zA-Z0-9._-]+/', '-', $base);
        $base = trim($base, '.-_');
        if ($base === '') {
            $base = 'attachment';
        }
        $stored = $safe_time . '_' . $safe_email . '_' . ($idx + 1) . '_' . $base . '.' . $ext;
        $stored = preg_replace('/[^a-zA-Z0-9._+-]/', '_', $stored);
        $target = $attachment_dir . '/' . $stored;
        if (!move_uploaded_file($file['tmp_name'], $target)) {
            fail_upload('Uploaded file could not be saved. Please contact us by WhatsApp or email.', 500);
        }
        @chmod($target, 0644);
        $saved[] = [
            'original_name' => $original,
            'stored_name' => $stored,
            'size' => $size,
            'mime_type' => (string)($file['type'] ?? ''),
            'path' => $target,
        ];
    }
    return $saved;
}

function get_client_ip_details() {
    $candidates = [
        'HTTP_CF_CONNECTING_IP' => 'cf-connecting-ip',
        'HTTP_X_REAL_IP' => 'x-real-ip',
        'HTTP_X_FORWARDED_FOR' => 'x-forwarded-for',
        'REMOTE_ADDR' => 'remote-addr',
    ];

    foreach ($candidates as $serverKey => $label) {
        $raw = isset($_SERVER[$serverKey]) ? trim((string)$_SERVER[$serverKey]) : '';
        if ($raw === '') {
            continue;
        }
        $parts = ($serverKey === 'HTTP_X_FORWARDED_FOR')
            ? preg_split('/\s*,\s*/', $raw)
            : [$raw];
        foreach ($parts as $part) {
            $ip = trim((string)$part);
            if ($ip !== '' && filter_var($ip, FILTER_VALIDATE_IP)) {
                return [
                    'ip' => $ip,
                    'ip_source' => $label,
                    'ip_raw' => $raw,
                    'ip_raw_remote_addr' => (string)($_SERVER['REMOTE_ADDR'] ?? ''),
                ];
            }
        }
    }

    return [
        'ip' => '127.0.0.1',
        'ip_source' => 'fallback',
        'ip_raw' => '',
        'ip_raw_remote_addr' => (string)($_SERVER['REMOTE_ADDR'] ?? ''),
    ];
}

// Get form data
$name = isset($_POST['name']) ? trim($_POST['name']) : '';
$email = isset($_POST['email']) ? trim($_POST['email']) : '';
$company = isset($_POST['company']) ? trim($_POST['company']) : '';
$phone = isset($_POST['phone']) ? trim($_POST['phone']) : '';
$subject = isset($_POST['subject']) ? trim($_POST['subject']) : '';
$message = isset($_POST['message']) ? trim($_POST['message']) : '';

// Honeypot field - if filled, it's a bot
$honeypot = isset($_POST['website']) ? trim($_POST['website']) : '';

// Time check - form must be loaded at least 3 seconds before submission
$form_loaded = isset($_POST['form_time']) ? intval($_POST['form_time']) : 0;
$time_diff = time() - $form_loaded;

// Get language from form or referer, default to en
$lang = isset($_POST['lang']) ? trim($_POST['lang']) : 'en';
$allowed_langs = ['en', 'zh', 'ar', 'de', 'es', 'fr', 'id', 'ja', 'ko'];
if (!in_array($lang, $allowed_langs)) {
    $lang = 'en';
}

// Get client IP
$ipInfo = get_client_ip_details();
$client_ip = $ipInfo['ip'];

// Preserve landing page / ad tracking fields submitted by generated pages.
$tracking_keys = [
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'utm_id',
    'gclid', 'gbraid', 'wbraid', 'fbclid',
    'landing_page', 'page_path', 'page_title', 'referrer',
];
$tracking = [];
foreach ($tracking_keys as $key) {
    $tracking[$key] = isset($_POST[$key]) ? trim((string)$_POST[$key]) : '';
}

// Honeypot bots get a silent success so they do not learn the filter.
if (!empty($honeypot)) {
    $success_url = '/pags/' . $lang . '/success.html';
    header('Location: ' . $success_url);
    exit;
}

// Do not show a success page for a real submission that was not saved.
if ($form_loaded > 0 && $time_diff < 3) {
    http_response_code(429);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'Please wait a moment before submitting the form again.';
    exit;
}

// Validate required fields
if (empty($name) || empty($email) || empty($message)) {
    // Missing required fields - redirect back with error
    header('Location: /pags/' . $lang . '/contact.html?error=1');
    exit;
}

// Validate email format
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    header('Location: /pags/' . $lang . '/contact.html?error=2');
    exit;
}

// Try multiple possible directories
$possibleDirs = [
    '/var/www/users/',
    '/var/www/html/users/',
    __DIR__ . '/../users/',
];

$save_dir = null;
foreach ($possibleDirs as $dir) {
    if ((is_dir($dir) || @mkdir($dir, 0755, true)) && is_writable($dir)) {
        $save_dir = $dir;
        break;
    }
}

if (!$save_dir) {
    $save_dir = __DIR__ . '/../users/';
    if (!is_dir($save_dir)) {
        @mkdir($save_dir, 0755, true);
    }
    if (!is_writable($save_dir)) {
        http_response_code(500);
        header('Content-Type: text/plain; charset=utf-8');
        echo 'Submission could not be saved. Please contact us by WhatsApp or email.';
        exit;
    }
}

// Save data to JSON file
$safe_email = !empty($email) ? preg_replace('/[^a-zA-Z0-9@._-]/', '_', $email) : 'noemail';
$safe_email = str_replace('@', '_at_', $safe_email);
$safe_email = str_replace('.', '_', $safe_email);
$safe_time = date('Y-m-d\TH-i-s') . '.' . substr(microtime(true), 11, 6) . '+00:00';
$filename = $save_dir . '/' . str_replace(':', '-', $safe_time) . '_' . $safe_email . '.json';

// Create record
$attachments = save_uploaded_attachments($save_dir, $safe_time, $safe_email);

$record = [
    'name' => $name,
    'email' => $email,
    'company' => $company,
    'phone' => $phone,
    'subject' => $subject,
    'message' => $message,
    'attachments' => $attachments,
    'ip' => $client_ip,
    'ip_source' => $ipInfo['ip_source'],
    'ip_raw' => $ipInfo['ip_raw'],
    'ip_raw_remote_addr' => $ipInfo['ip_raw_remote_addr'],
    'tracking' => $tracking,
    'lang' => $lang,
    'time' => date('c')
];

// Save to file
$saved = file_put_contents($filename, json_encode($record, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE), LOCK_EX);
if ($saved === false) {
    http_response_code(500);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'Submission could not be saved. Please contact us by WhatsApp or email.';
    exit;
}

// Redirect to language-specific success page
$success_url = '/pags/' . $lang . '/success.html';
header('Location: ' . $success_url);
exit;
