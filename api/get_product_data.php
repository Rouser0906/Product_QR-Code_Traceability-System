<?php
/**
 * 产品数据获取 API（生产规范版）
 * - 输入：GET ?code=A-Qxxxxxxxxx 或 B-Qxxxxxxxxx
 * - 优先读取本地 JSON（C:/inetpub/wwwroot/companies/{demo_json_a|demo_json_b}/code.json），找不到再拉取远端 URL
 * - 支持缓存、性能日志与错误日志
 */

require_once __DIR__ . '/../config/performance_config.php';

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET');
header('Access-Control-Allow-Headers: Content-Type');
header('Cache-Control: public, max-age=300');

$start_time = microtime(true);
$code = isset($_GET['code']) ? trim($_GET['code']) : '';

if ($code === '') {
    http_response_code(400);
    echo json_encode(['error' => '缺少 code 参数']);
    exit;
}
if (!preg_match('/^(A-Q|B-Q)\d+$/', $code)) {
    http_response_code(400);
    echo json_encode(['error' => '无效的 code 参数格式']);
    exit;
}

$cfg = get_ftp_config($code);
if (!$cfg) {
    http_response_code(400);
    echo json_encode(['error' => '不支持的 code 前缀']);
    exit;
}

$company = $cfg['company'];
$remote_url = rtrim($cfg['base_url'], '/') . '/' . $code . '.json';

// 本地优先 - 支持多种可能的路径
$possible_roots = [
    'C:/inetpub/qr-system',           // 原配置路径
    'C:/inetpub/wwwroot',        // 标准IIS路径
    realpath(__DIR__ . '/..')    // 开发环境相对路径
];

$local_hs = null;
$local_zy = null;

foreach ($possible_roots as $root) {
    if (is_dir($root . '/companies')) {
        $local_hs = $root . '/companies/demo_json_a/' . $code . '.json';
        $local_zy = $root . '/companies/demo_json_b/' . $code . '.json';
        break;
    }
}

// 如果都找不到，使用相对路径作为最后回退
if (!$local_hs) {
    $root = realpath(__DIR__ . '/..');
    $local_hs = $root . '/companies/demo_json_a/' . $code . '.json';
    $local_zy = $root . '/companies/demo_json_b/' . $code . '.json';
}
$local_path = (strpos($code, 'A-Q') === 0) ? $local_hs : $local_zy;

$cache_file = get_cache_file_path($code);
$use_cache = false;
$data_text = false;

if (is_cache_valid($cache_file)) {
    $data_text = @file_get_contents($cache_file);
    $use_cache = $data_text !== false;
}

// 本地读取
if (!$use_cache && file_exists($local_path)) {
    $data_text = @file_get_contents($local_path);
    if ($data_text !== false && CACHE_ENABLED) {
        @file_put_contents($cache_file, $data_text, LOCK_EX);
    }
}

// 远端回退
if ($data_text === false) {
    $context = stream_context_create([
        'http' => [
            'timeout' => $cfg['timeout'] ?? 15,
            'method' => 'GET',
            'header' => [
                'User-Agent: QR-Scanner/1.0',
                'Accept: application/json',
                'Cache-Control: no-cache'
            ],
            'ignore_errors' => true
        ]
    ]);

    $max = $cfg['max_retries'] ?? 1;
    for ($i = 0; $i < $max; $i++) {
        $data_text = @file_get_contents($remote_url, false, $context);
        if ($data_text !== false) {
            if (CACHE_ENABLED) {
                @file_put_contents($cache_file, $data_text, LOCK_EX);
            }
            break;
        }
        if ($i < $max - 1) { sleep(1); }
    }
}

if ($data_text === false) {
    http_response_code(404);
    echo json_encode([
        'error' => '产品信息未找到',
        'code' => $code,
        'company' => $company,
        'remote_url' => $remote_url
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

// 解析 JSON
$data = json_decode($data_text, true);
if (json_last_error() !== JSON_ERROR_NONE) {
    http_response_code(500);
    echo json_encode(['error' => 'JSON解析失败: ' . json_last_error_msg()], JSON_UNESCAPED_UNICODE);
    exit;
}

$total = microtime(true) - $start_time;

// 注入 API 元信息
$data['_api_info'] = [
    'source' => $use_cache ? 'cache' : (file_exists($local_path) ? 'local' : 'remote'),
    'url' => $remote_url,
    'timestamp' => date('Y-m-d H:i:s'),
    'code' => $code,
    'company' => $company,
    'response_time' => round($total * 1000, 2) . 'ms',
    'cached' => $use_cache
];

log_performance("GET /api/get_product_data.php?code=$code", $total);

// 输出
echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
