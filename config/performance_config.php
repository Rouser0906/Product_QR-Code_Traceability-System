<?php
/**
 * 性能优化配置文件
 * 用于缓存和加速二维码扫描系统的数据访问
 */

// 缓存配置
define('CACHE_ENABLED', true);
define('CACHE_DURATION', 300); // 5分钟缓存（秒）
define('CACHE_DIR', __DIR__ . '/../cache/product_data/');

// 远端 JSON 基础 URL（生产规范）
define('FTP_SERVERS', [
    'HS' => [
        'base_url'    => 'https://scan.example.com/companies/demo_json_a/',
        'company'     => '[已脱敏城市]示例品牌B材料有限公司',
        'timeout'     => 15,
        'max_retries' => 3
    ],
    'ZY' => [
        'base_url'    => 'https://scan.example.com/companies/demo_json_b/',
        'company'     => '[已脱敏城市]示例品牌A有限公司',
        'timeout'     => 15,
        'max_retries' => 3
    ]
]);

// 性能与错误日志
define('PERFORMANCE_LOG_ENABLED', true);
define('PERFORMANCE_LOG_FILE', __DIR__ . '/../logs/performance.log');

define('ERROR_LOG_ENABLED', true);
define('ERROR_LOG_FILE', __DIR__ . '/../logs/api_errors.log');

// 可选：预加载常用产品代码（按需）
define('PRELOAD_PRODUCTS', [
    'HS-DEMO-000008704', 'HS-DEMO-000008705', 'HS-DEMO-0001',
    'ZY-DEMO-000000001', 'ZY-DEMO-000000005', 'ZY-DEMO-000000006'
]);

/**
 * 根据产品代码获取远端配置（HS-Q..., ZY-Q...）
 */
function get_ftp_config($product_code) {
    if (strpos($product_code, 'HS-Q') === 0) {
        return FTP_SERVERS['HS'];
    } elseif (strpos($product_code, 'ZY-Q') === 0) {
        return FTP_SERVERS['ZY'];
    }
    return null;
}

/** 获取缓存文件路径 */
function get_cache_file_path($product_code) {
    if (!CACHE_ENABLED) return null;
    $cache_dir = CACHE_DIR;
    if (!is_dir($cache_dir)) {
        @mkdir($cache_dir, 0755, true);
    }
    return $cache_dir . md5($product_code) . '.json';
}

/** 判断缓存是否有效 */
function is_cache_valid($cache_file) {
    if (!CACHE_ENABLED || !$cache_file || !file_exists($cache_file)) {
        return false;
    }
    return (time() - filemtime($cache_file)) < CACHE_DURATION;
}

/** 记录性能日志 */
function log_performance($message, $duration = null) {
    if (!PERFORMANCE_LOG_ENABLED) return;
    $log_dir = dirname(PERFORMANCE_LOG_FILE);
    if (!is_dir($log_dir)) {
        @mkdir($log_dir, 0755, true);
    }
    $timestamp = date('Y-m-d H:i:s');
    $duration_str = $duration !== null ? sprintf(' (%.3fs)', $duration) : '';
    $line = "[$timestamp] $message$duration_str\n";
    @file_put_contents(PERFORMANCE_LOG_FILE, $line, FILE_APPEND | LOCK_EX);
}

/** 记录错误日志 */
function log_error($message, $context = []) {
    if (!ERROR_LOG_ENABLED) return;
    $log_dir = dirname(ERROR_LOG_FILE);
    if (!is_dir($log_dir)) {
        @mkdir($log_dir, 0755, true);
    }
    $timestamp = date('Y-m-d H:i:s');
    $ctx = $context ? (' ' . json_encode($context, JSON_UNESCAPED_UNICODE)) : '';
    $line = "[$timestamp] ERROR: $message$ctx\n";
    @file_put_contents(ERROR_LOG_FILE, $line, FILE_APPEND | LOCK_EX);
}
?>
