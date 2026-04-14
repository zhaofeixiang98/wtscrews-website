<?php
// WT Fasteners Contact Form Handler

// Get form data
$name = isset($_POST['name']) ? trim($_POST['name']) : '';
$email = isset($_POST['email']) ? trim($_POST['email']) : '';
$company = isset($_POST['company']) ? trim($_POST['company']) : '';
$phone = isset($_POST['phone']) ? trim($_POST['phone']) : '';
$subject = isset($_POST['subject']) ? trim($_POST['subject']) : '';
$message = isset($_POST['message']) ? trim($_POST['message']) : '';

// Get language from form or referer, default to en
$lang = isset($_POST['lang']) ? trim($_POST['lang']) : 'en';
// Validate language code
$allowed_langs = ['en', 'zh', 'ar', 'de', 'es', 'fr', 'id', 'ja', 'ko'];
if (!in_array($lang, $allowed_langs)) {
    $lang = 'en';
}

// Get client IP
$client_ip = $_SERVER['REMOTE_ADDR'] ?? '127.0.0.1';

// 尝试多个可能的目录
$possibleDirs = [
    '/var/www/users/',           // 云服务器
    '/var/www/html/users/',      // 备用云服务器路径
    __DIR__ . '/../users/',      // 本地开发 (相对于 cgi-bin)
];

$save_dir = null;
foreach ($possibleDirs as $dir) {
    if (is_dir($dir) || @mkdir($dir, 0755, true)) {
        $save_dir = $dir;
        break;
    }
}

// 如果所有目录都不存在，使用本地目录
if (!$save_dir) {
    $save_dir = __DIR__ . '/../users/';
    if (!is_dir($save_dir)) { 
        mkdir($save_dir, 0755, true);
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
    'lang' => $lang,
    'time' => date('c')
];

// Save to file
file_put_contents($filename, json_encode($record, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

// Redirect to language-specific success page
$success_url = '/pags/' . $lang . '/success.html';
header('Location: ' . $success_url);
exit;
