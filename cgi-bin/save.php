<?php
// WT Fasteners Contact Form Handler

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
$record = [
    'name' => $name,
    'email' => $email,
    'company' => $company,
    'phone' => $phone,
    'subject' => $subject,
    'message' => $message,
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
