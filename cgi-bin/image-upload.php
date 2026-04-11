<?php
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    exit(json_encode(['success' => false, 'error' => 'Method not allowed']));
}

if (empty($_FILES['file']) || $_FILES['file']['error'] === UPLOAD_ERR_NO_FILE) {
    exit(json_encode(['success' => false, 'error' => '未选择文件']));
}

$file = $_FILES['file'];
if ($file['error'] !== UPLOAD_ERR_OK) {
    exit(json_encode(['success' => false, 'error' => '上传出错，错误码: ' . $file['error']]));
}

// Validate extension
$original = basename($file['name']);
$ext      = strtolower(pathinfo($original, PATHINFO_EXTENSION));
if (!in_array($ext, ['jpg','jpeg','png','gif','webp','svg'], true)) {
    exit(json_encode(['success' => false, 'error' => '仅支持 jpg/png/gif/webp/svg 格式']));
}

// Determine final filename
$rename_raw = trim($_POST['rename'] ?? '');
if ($rename_raw !== '') {
    $safe_base  = trim(preg_replace('/[^a-zA-Z0-9_\-]/', '-', pathinfo($rename_raw, PATHINFO_FILENAME)), '-') ?: 'image';
    $final_name = $safe_base . '.' . $ext;
} else {
    $final_name = trim(preg_replace('/-{2,}/', '-', preg_replace('/[^a-zA-Z0-9_\-.]/', '-', $original)), '-');
    if (!$final_name) { $final_name = 'image.' . $ext; }
}

// Save to images/news/
$base_dir   = realpath(__DIR__ . '/..');
$upload_dir = $base_dir . '/images/news';
if (!is_dir($upload_dir)) {
    mkdir($upload_dir, 0755, true);
}

// Avoid duplicate filenames: file.jpg → file-1.jpg → file-2.jpg
$base_name = pathinfo($final_name, PATHINFO_FILENAME);
$candidate = $final_name;
$counter   = 1;
while (file_exists($upload_dir . '/' . $candidate)) {
    $candidate = $base_name . '-' . $counter . '.' . $ext;
    $counter++;
}
$final_name = $candidate;

if (!move_uploaded_file($file['tmp_name'], $upload_dir . '/' . $final_name)) {
    exit(json_encode(['success' => false, 'error' => '保存失败，请检查目录写入权限']));
}

exit(json_encode(['success' => true, 'filename' => $final_name, 'path' => 'news/' . $final_name]));
