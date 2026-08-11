<?php
/**
 * 简化版产品数据获取API
 * 直接读取服务器上的JSON文件
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET');
header('Access-Control-Allow-Headers: Content-Type');

$code = isset($_GET['code']) ? trim($_GET['code']) : '';

if (empty($code)) {
    http_response_code(400);
    echo json_encode(['error' => '缺少 code 参数']);
    exit;
}

if (!preg_match('/^(HS-Q|ZY-Q)\d+$/', $code)) {
    http_response_code(400);
    echo json_encode(['error' => '无效的 code 参数格式']);
    exit;
}

// 确定文件路径
$company_type = (strpos($code, 'HS-Q') === 0) ? 'demo_json_a' : 'demo_json_b';
$file_path = __DIR__ . "/../companies/{$company_type}/{$code}.json";

// 检查文件是否存在
if (!file_exists($file_path)) {
    http_response_code(404);
    echo json_encode([
        'error' => '产品信息未找到',
        'code' => $code,
        'file_path' => $file_path,
        'file_exists' => false
    ]);
    exit;
}

// 读取文件内容
$json_content = file_get_contents($file_path);
if ($json_content === false) {
    http_response_code(500);
    echo json_encode([
        'error' => '无法读取产品数据文件',
        'code' => $code,
        'file_path' => $file_path
    ]);
    exit;
}

// 解析JSON
$data = json_decode($json_content, true);
if ($data === null) {
    http_response_code(500);
    echo json_encode([
        'error' => 'JSON数据格式错误',
        'code' => $code,
        'json_error' => json_last_error_msg()
    ]);
    exit;
}

// 返回数据
echo json_encode($data);
?>