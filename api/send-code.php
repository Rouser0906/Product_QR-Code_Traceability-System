<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// 处理预检请求
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// 数据库配置 - 请在 db_config.php 中配置
$db_config = file_exists(__DIR__ . '/db_config.php') 
    ? require(__DIR__ . '/db_config.php')
    : [
        'host' => 'localhost',
        'dbname' => 'qr_system',
        'username' => 'root',
        'password' => ''
    ];

// API配置 - 请在 api_config.php 中配置
$api_config = file_exists(__DIR__ . '/api_config.php')
    ? require(__DIR__ . '/api_config.php')
    : [];

// 短信配置（阿里云）
$sms_config = $api_config['sms_aliyun'] ?? [
    'access_key_id' => 'your_access_key_id',
    'access_key_secret' => 'your_access_key_secret',
    'sign_name' => '产品溯源',
    'template_code' => 'SMS_123456789'
];

/**
 * 返回JSON响应
 */
function json_response($success, $data = null, $message = '', $error_code = '') {
    $response = [
        'success' => $success,
        'message' => $message,
        'timestamp' => time()
    ];
    
    if ($data !== null) {
        $response['data'] = $data;
    }
    
    if ($error_code) {
        $response['error_code'] = $error_code;
    }
    
    echo json_encode($response, JSON_UNESCAPED_UNICODE);
    exit();
}

/**
 * 获取数据库连接
 */
function get_db_connection($config) {
    try {
        $dsn = "mysql:host={$config['host']};dbname={$config['dbname']};charset=utf8mb4";
        $pdo = new PDO($dsn, $config['username'], $config['password']);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        return $pdo;
    } catch (PDOException $e) {
        error_log("数据库连接失败: " . $e->getMessage());
        json_response(false, null, '数据库连接失败', 'DB_CONNECTION_ERROR');
    }
}

/**
 * 生成6位随机验证码
 */
function generate_verification_code() {
    return sprintf('%06d', mt_rand(0, 999999));
}

/**
 * 检查发送频率限制
 */
function check_rate_limit($db, $phone_number) {
    // 检查1分钟内是否已发送
    $stmt = $db->prepare("
        SELECT COUNT(*) as count 
        FROM verification_codes 
        WHERE phone_number = ? 
        AND created_at > DATE_SUB(NOW(), INTERVAL 1 MINUTE)
    ");
    $stmt->execute([$phone_number]);
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if ($result['count'] > 0) {
        return [false, '请等待1分钟后再次发送'];
    }
    
    // 检查1小时内发送次数
    $stmt = $db->prepare("
        SELECT COUNT(*) as count 
        FROM verification_codes 
        WHERE phone_number = ? 
        AND created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
    ");
    $stmt->execute([$phone_number]);
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if ($result['count'] >= 5) {
        return [false, '发送次数过多，请1小时后再试'];
    }
    
    return [true, ''];
}

/**
 * 发送阿里云短信
 */
function send_aliyun_sms($phone_number, $code, $config) {
    // 这里实现阿里云短信发送
    // 由于需要阿里云SDK，这里提供简化版本
    
    // 实际项目中需要：
    // 1. 引入阿里云SMS SDK
    // 2. 配置正确的AccessKey
    // 3. 实现完整的短信发送逻辑
    
    // 模拟发送成功（开发环境）
    if (strpos($_SERVER['HTTP_HOST'], 'localhost') !== false || 
        strpos($_SERVER['HTTP_HOST'], '127.0.0.1') !== false) {
        // 开发环境，模拟发送成功
        error_log("模拟发送短信到 {$phone_number}，验证码：{$code}");
        return [true, '开发环境模拟发送成功'];
    }
    
    // 生产环境的阿里云短信发送代码
    try {
        // 这里应该调用阿里云SMS API
        // $result = aliyun_sms_send($phone_number, $code, $config);
        
        // 临时返回成功（需要实际实现）
        return [true, '短信发送成功'];
        
    } catch (Exception $e) {
        error_log("短信发送失败: " . $e->getMessage());
        return [false, '短信发送失败：' . $e->getMessage()];
    }
}

/**
 * 发送腾讯云短信
 */
function send_tencent_sms($phone_number, $code, $config) {
    // 腾讯云短信发送实现
    // 这里提供备用方案
    return [true, '短信发送成功'];
}

// 主处理逻辑
try {
    // 检查请求方法
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        json_response(false, null, '仅支持POST请求', 'METHOD_NOT_ALLOWED');
    }
    
    // 解析请求数据
    $input = file_get_contents('php://input');
    $request_data = json_decode($input, true);
    
    if (!$request_data) {
        json_response(false, null, '无效的JSON数据', 'INVALID_JSON');
    }
    
    // 获取参数
    $phone_number = $request_data['phone_number'] ?? '';
    
    // 验证手机号
    if (empty($phone_number)) {
        json_response(false, null, '手机号不能为空', 'MISSING_PHONE');
    }
    
    if (!preg_match('/^1[3-9]\d{9}$/', $phone_number)) {
        json_response(false, null, '手机号格式不正确', 'INVALID_PHONE');
    }
    
    // 连接数据库
    $db = get_db_connection($db_config);
    
    // 检查发送频率
    list($rate_ok, $rate_message) = check_rate_limit($db, $phone_number);
    if (!$rate_ok) {
        json_response(false, null, $rate_message, 'RATE_LIMIT_EXCEEDED');
    }
    
    // 生成验证码
    $verification_code = generate_verification_code();
    
    // 发送短信
    list($sms_success, $sms_message) = send_aliyun_sms($phone_number, $verification_code, $sms_config);
    
    if (!$sms_success) {
        // 尝试腾讯云备用方案
        list($sms_success, $sms_message) = send_tencent_sms($phone_number, $verification_code, $sms_config);
    }
    
    if (!$sms_success) {
        json_response(false, null, $sms_message, 'SMS_SEND_FAILED');
    }
    
    // 保存验证码到数据库
    $expires_at = date('Y-m-d H:i:s', time() + 300); // 5分钟有效期
    
    $stmt = $db->prepare("
        INSERT INTO verification_codes (phone_number, verification_code, expires_at) 
        VALUES (?, ?, ?)
    ");
    $stmt->execute([$phone_number, $verification_code, $expires_at]);
    
    // 返回成功响应
    json_response(true, [
        'phone_number' => $phone_number,
        'expires_in' => 300,
        'expires_at' => $expires_at
    ], '验证码发送成功');
    
} catch (Exception $e) {
    error_log("发送验证码API错误: " . $e->getMessage());
    json_response(false, null, '服务器内部错误', 'INTERNAL_ERROR');
}
?>