<?php
/**
 * 扫码解析API - 兼容 /api/resolve?id=code 调用
 * 将请求转发到现有的 get_product_data.php 并转换数据格式
 */

require_once __DIR__ . '/../config/performance_config.php';

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET');
header('Access-Control-Allow-Headers: Content-Type');
header('Cache-Control: public, max-age=300');

$start_time = microtime(true);
$id = isset($_GET['id']) ? trim($_GET['id']) : '';

if ($id === '') {
    http_response_code(400);
    echo json_encode(['error' => '缺少 id 参数']);
    exit;
}

// 直接包含并调用现有的逻辑
$_GET['code'] = $id; // 设置 code 参数
ob_start(); // 开始输出缓冲
try {
    include __DIR__ . '/get_product_data.php';
    $response = ob_get_contents();
} catch (Exception $e) {
    ob_end_clean();
    http_response_code(500);
    echo json_encode(['error' => '内部服务器错误: ' . $e->getMessage()]);
    exit;
}
ob_end_clean();

if (empty($response)) {
    http_response_code(500);
    echo json_encode(['error' => '无法获取产品数据']);
    exit;
}

$data = json_decode($response, true);
if (json_last_error() !== JSON_ERROR_NONE) {
    http_response_code(500);
    echo json_encode(['error' => 'JSON解析失败: ' . json_last_error_msg()]);
    exit;
}

// 检查是否有错误
if (isset($data['error'])) {
    http_response_code(404);
    echo json_encode($data);
    exit;
}

// 转换数据格式以匹配前端期望的字段名
$resolved_data = [
    'qrcNo' => $data['qr_sequence'] ?? '',
    'qrSequence' => $data['qr_sequence'] ?? '',
    'companyName' => $data['company_name'] ?? '',
    'productType' => $data['product_type'] ?? '',
    'productSpec' => $data['product_spec'] ?? '',
    'productColor' => $data['product_color'] ?? '',
    'productFeature' => $data['product_feature'] ?? '',
    'batchNumber' => $data['batch_number'] ?? '',
    'productionDate' => $data['production_date'] ?? '',
    'distributorName' => $data['distributor_name'] ?? '',
    'phone' => $data['phone'] ?? '',
    'standard' => $data['standard'] ?? '',
    'remark' => $data['remark'] ?? '',
    'companyUrl' => $data['official_website'] ?? '',
    
    // 添加原始数据以供后续使用
    'original' => $data
];

$total = microtime(true) - $start_time;
log_performance("GET /api/resolve.php?id=$id", $total);

echo json_encode($resolved_data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);