<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') {
    http_response_code(204);
    exit;
}

function respond($obj, $status = 200) {
    http_response_code($status);
    echo json_encode($obj, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

function get_data_dir() {
    $possibleDirs = [
        '/var/www/users/',
        '/var/www/html/users/',
        __DIR__ . '/../users/',
        '../users/'
    ];
    foreach ($possibleDirs as $dir) {
        if (is_dir($dir)) {
            return rtrim($dir, '/') . '/';
        }
    }
    $fallback = __DIR__ . '/../users/';
    if (!is_dir($fallback) && !@mkdir($fallback, 0755, true)) {
        respond(['success' => false, 'error' => '用户数据目录不可用'], 500);
    }
    return rtrim($fallback, '/') . '/';
}

function list_users($dataDir) {
    $files = glob($dataDir . '*.json') ?: [];
    $users = [];
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
    usort($users, function($a, $b) {
        return strtotime((string)($b['time'] ?? '')) <=> strtotime((string)($a['time'] ?? ''));
    });
    return $users;
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

$dataDir = get_data_dir();
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

if ($method === 'GET') {
    respond(list_users($dataDir));
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
    $fullPath = $dataDir . $filename;
    if (!file_exists($fullPath)) {
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
