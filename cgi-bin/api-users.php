<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('X-Content-Type-Options: nosniff');

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
$host = $_SERVER['HTTP_HOST'] ?? '';
if ($origin !== '' && $host !== '') {
    $originHost = parse_url($origin, PHP_URL_HOST);
    if ($originHost === $host) {
        header('Access-Control-Allow-Origin: ' . $origin);
        header('Access-Control-Allow-Credentials: true');
        header('Vary: Origin');
    }
}

if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') {
    http_response_code(204);
    exit;
}

function respond($obj, $status = 200) {
    http_response_code($status);
    echo json_encode($obj, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

function require_admin_auth() {
    if (getenv('WT_ADMIN_BYPASS') === '1') {
        return;
    }

    $token = trim((string)($_COOKIE['WT_ADMIN_SESSION'] ?? ''));
    if ($token === '') {
        respond(['success' => false, 'error' => 'unauthorized'], 401);
    }

    $sessionPath = '/tmp/.admin-sessions.json';
    $raw = @file_get_contents($sessionPath);
    $sessions = $raw !== false ? json_decode($raw, true) : null;
    if (!is_array($sessions)) {
        respond(['success' => false, 'error' => 'unauthorized'], 401);
    }

    $expiresAt = isset($sessions[$token]) ? intval($sessions[$token]) : 0;
    if ($expiresAt <= time()) {
        respond(['success' => false, 'error' => 'unauthorized'], 401);
    }
}

function get_possible_data_dirs() {
    return [
        '/var/www/users/',
        '/var/www/html/users/',
        __DIR__ . '/../users/',
        '../users/'
    ];
}

function get_data_dirs() {
    $possibleDirs = get_possible_data_dirs();
    $dirs = [];
    foreach ($possibleDirs as $dir) {
        if (is_dir($dir) && is_readable($dir)) {
            $real = realpath($dir);
            if ($real !== false) {
                $normalized = rtrim($real, '/') . '/';
                if (!in_array($normalized, $dirs, true)) {
                    $dirs[] = $normalized;
                }
            }
        }
    }
    $fallback = __DIR__ . '/../users/';
    if (!is_dir($fallback) && !@mkdir($fallback, 0755, true)) {
        respond(['success' => false, 'error' => '用户数据目录不可用'], 500);
    }
    $realFallback = realpath($fallback);
    if ($realFallback !== false && is_readable($realFallback)) {
        $normalized = rtrim($realFallback, '/') . '/';
        if (!in_array($normalized, $dirs, true)) {
            $dirs[] = $normalized;
        }
    }
    if (!$dirs) {
        respond(['success' => false, 'error' => '用户数据目录不可读'], 500);
    }
    return $dirs;
}

function list_users($dataDirs) {
    $users = [];
    foreach ($dataDirs as $dataDir) {
        $files = glob($dataDir . '*.json') ?: [];
        foreach ($files as $file) {
            $base = basename($file);
            if ($base === '.last_submits.json' || strpos($base, '.') === 0) {
                continue;
            }
            $content = @file_get_contents($file);
            if ($content === false) {
                continue;
            }
            $data = json_decode($content, true);
            if (!is_array($data)) {
                continue;
            }
            $email = trim((string)($data['email'] ?? ''));
            $name = trim((string)($data['name'] ?? ''));
            if ($email === '' || $email === 'noemail' || $email === '未填写' || $name === '') {
                continue;
            }
            $data['filename'] = $base;
            $users[] = $data;
        }
    }
    usort($users, function($a, $b) {
        return strtotime((string)($b['time'] ?? '')) <=> strtotime((string)($a['time'] ?? ''));
    });
    return $users;
}

function find_user_file($dataDirs, $filename) {
    foreach ($dataDirs as $dataDir) {
        $fullPath = $dataDir . $filename;
        if (is_file($fullPath)) {
            return $fullPath;
        }
    }
    return '';
}

function normalize_filename($name) {
    $name = trim((string)$name);
    if ($name === '') {
        return '';
    }
    $base = basename($name);
    if (!preg_match('/^[a-zA-Z0-9._@+\-]+\.json$/', $base)) {
        return '';
    }
    return $base;
}

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

require_admin_auth();

$dataDirs = get_data_dirs();

if ($method === 'GET') {
    respond(list_users($dataDirs));
}

if ($method !== 'POST') {
    respond(['success' => false, 'error' => 'method not allowed'], 405);
}

$action = trim((string)($_POST['action'] ?? ''));
if ($action !== 'delete') {
    respond(['success' => false, 'error' => 'unsupported action'], 400);
}

$targets = [];
$single = normalize_filename($_POST['filename'] ?? '');
if ($single !== '') {
    $targets[] = $single;
}
$manyRaw = trim((string)($_POST['filenames'] ?? ''));
if ($manyRaw !== '') {
    foreach (explode(',', $manyRaw) as $part) {
        $normalized = normalize_filename($part);
        if ($normalized !== '' && !in_array($normalized, $targets, true)) {
            $targets[] = $normalized;
        }
    }
}

if (!$targets) {
    respond(['success' => false, 'error' => '未指定要删除的记录'], 400);
}

$deleted = [];
$errors = [];
foreach ($targets as $filename) {
    $fullPath = find_user_file($dataDirs, $filename);
    if ($fullPath === '') {
        $errors[] = $filename . ' 不存在';
        continue;
    }
    if (!is_file($fullPath)) {
        $errors[] = $filename . ' 不是有效文件';
        continue;
    }
    if (!@unlink($fullPath)) {
        $errors[] = $filename . ' 删除失败';
        continue;
    }
    $deleted[] = $filename;
}

respond([
    'success' => count($deleted) > 0,
    'deleted' => $deleted,
    'errors' => $errors,
], count($deleted) > 0 ? 200 : 500);
