<?php
/**
 * 用户数据代理API
 * 读取用户数据目录中的JSON文件
 * 支持本地开发和云服务器环境
 */

// 设置响应头为 JSON
header('Content-Type: application/json; charset=utf-8');

// 允许跨域
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST');
header('Access-Control-Allow-Headers: Content-Type');

// 尝试多个可能的目录
$possibleDirs = [
    '/var/www/users/',           // 云服务器
    '/var/www/html/users/',      // 备用云服务器路径
    __DIR__ . '/../users/',      // 本地开发 (相对于 cgi-bin)
    '../users/'                  // 相对路径
];

$dataDir = null;
foreach ($possibleDirs as $dir) {
    if (is_dir($dir)) {
        $dataDir = $dir;
        break;
    }
}

// 如果所有目录都不存在，创建本地目录用于开发测试
if (!$dataDir) {
    $dataDir = __DIR__ . '/../users/';
    if (!is_dir($dataDir)) {
        mkdir($dataDir, 0755, true);
    }
}

// 获取所有 JSON 文件
$files = glob($dataDir . '*.json');

$users = [];

foreach ($files as $file) {
    // 跳过 .last_submits.json 等系统文件
    if (strpos(basename($file), '.') === 0) {
        continue;
    }
    
    $content = file_get_contents($file);
    $data = json_decode($content, true);
    
    if ($data) {
        $data['filename'] = basename($file);
        $users[] = $data;
    }
}

// 按时间排序（最新的在前）
usort($users, function($a, $b) {
    return strtotime($b['time']) - strtotime($a['time']);
});

echo json_encode($users, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);