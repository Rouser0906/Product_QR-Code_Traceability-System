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

// 微信配置
$wechat_config = $api_config['wechat'] ?? [
    'app_id' => 'your_app_id',
    'app_secret' => 'your_app_secret'
];

// 短信配置（阿里云为例）
$sms_config = $api_config['sms_aliyun'] ?? [
    'access_key_id' => 'your_access_key_id',
    'access_key_secret' => 'your_access_key_secret',
    'sign_name' => '你的短信签名',
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
 * 验证微信登录
 */
function verify_wechat_login($auth_data, $wechat_config) {
    $code = $auth_data['code'] ?? '';
    
    if (empty($code)) {
        return [false, '微信授权码不能为空'];
    }
    
    // 通过code获取access_token和openid
    $url = "https://api.weixin.qq.com/sns/oauth2/access_token?" . http_build_query([
        'appid' => $wechat_config['app_id'],
        'secret' => $wechat_config['app_secret'],
        'code' => $code,
        'grant_type' => 'authorization_code'
    ]);
    
    $response = file_get_contents($url);
    $data = json_decode($response, true);
    
    if (isset($data['errcode'])) {
        return [false, '微信验证失败: ' . ($data['errmsg'] ?? '未知错误')];
    }
    
    $openid = $data['openid'] ?? '';
    $access_token = $data['access_token'] ?? '';
    
    if (empty($openid)) {
        return [false, '获取微信用户信息失败'];
    }
    
    // 获取用户信息
    $userinfo_url = "https://api.weixin.qq.com/sns/userinfo?" . http_build_query([
        'access_token' => $access_token,
        'openid' => $openid,
        'lang' => 'zh_CN'
    ]);
    
    $userinfo_response = file_get_contents($userinfo_url);
    $userinfo = json_decode($userinfo_response, true);
    
    return [true, [
        'openid' => $openid,
        'nickname' => $userinfo['nickname'] ?? '',
        'headimgurl' => $userinfo['headimgurl'] ?? '',
        'sex' => $userinfo['sex'] ?? 0,
        'province' => $userinfo['province'] ?? '',
        'city' => $userinfo['city'] ?? '',
        'country' => $userinfo['country'] ?? ''
    ]];
}

/**
 * 验证手机号登录
 */
function verify_phone_login($auth_data, $db) {
    $phone_number = $auth_data['phone_number'] ?? '';
    $verification_code = $auth_data['verification_code'] ?? '';
    
    if (empty($phone_number) || empty($verification_code)) {
        return [false, '手机号和验证码不能为空'];
    }
    
    // 验证手机号格式
    if (!preg_match('/^1[3-9]\d{9}$/', $phone_number)) {
        return [false, '手机号格式不正确'];
    }
    
    // 查询验证码
    $stmt = $db->prepare("
        SELECT id, verification_code, expires_at, used 
        FROM verification_codes 
        WHERE phone_number = ? 
        ORDER BY created_at DESC 
        LIMIT 1
    ");
    $stmt->execute([$phone_number]);
    $code_record = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$code_record) {
        return [false, '验证码不存在或已过期'];
    }
    
    if ($code_record['used']) {
        return [false, '验证码已使用'];
    }
    
    if (time() > strtotime($code_record['expires_at'])) {
        return [false, '验证码已过期'];
    }
    
    if ($code_record['verification_code'] !== $verification_code) {
        return [false, '验证码错误'];
    }
    
    // 标记验证码为已使用
    $stmt = $db->prepare("UPDATE verification_codes SET used = 1 WHERE id = ?");
    $stmt->execute([$code_record['id']]);
    
    return [true, [
        'phone_number' => $phone_number,
        'verified_at' => date('Y-m-d H:i:s')
    ]];
}

/**
 * 判断公司类型
 */
function get_company_type($sn) {
    if (strpos($sn, 'HS-') === 0) {
        return 'company_a';
    } elseif (strpos($sn, 'ZY-') === 0) {
        return 'company_b';
    }
    return 'unknown';
}

/**
 * 获取产品URL
 */
function get_product_url($sn, $company) {
    $base_urls = [
        'company_a' => 'https://your-company-domain.com/index.html?code=',
        'company_b' => 'https://your-company-domain.com/index.html?code='
    ];
    
    $base_url = $base_urls[$company] ?? $base_urls['company_a'];
    return $base_url . urlencode($sn);
}

/**
 * 记录扫码历史
 */
function record_scan_history($db, $sn, $auth_type, $verifier_info) {
    try {
        // 获取用户IP和设备信息
        $user_ip = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? '';
        $user_agent = $_SERVER['HTTP_USER_AGENT'] ?? '';
        
        // 基于IP获取地理位置信息（简化版本）
        $location_info = get_location_by_ip($user_ip);
        
        // 处理手机号
        $scanner_phone = '';
        if ($auth_type === 'phone') {
            $scanner_phone = $verifier_info['phone_number'] ?? '';
        }
        
        // 处理微信信息
        $scanner_wechat = '';
        $scanner_name = '';
        if ($auth_type === 'wechat') {
            $scanner_wechat = $verifier_info['openid'] ?? '';
            $scanner_name = $verifier_info['nickname'] ?? '';
        }
        
        $stmt = $db->prepare("
            INSERT INTO scan_history (
                qr_code, scanner_name, scanner_phone, scanner_wechat, 
                scan_time, country, province, city, district, 
                device_info, ip_address
            ) VALUES (?, ?, ?, ?, NOW(), ?, ?, ?, ?, ?, ?)
        ");
        
        $stmt->execute([
            $sn,
            $scanner_name,
            $scanner_phone,
            $scanner_wechat,
            $location_info['country'] ?? '中国',
            $location_info['province'] ?? '',
            $location_info['city'] ?? '',
            $location_info['district'] ?? '',
            $user_agent,
            $user_ip
        ]);
        
        return true;
    } catch (Exception $e) {
        error_log("记录扫码历史失败: " . $e->getMessage());
        return false;
    }
}

/**
 * 根据IP获取地理位置信息（简化版本）
 */
function get_location_by_ip($ip) {
    // 这里可以集成第三方IP地理位置服务
    // 如：淘宝IP、百度IP等
    // 简化实现，返回默认值
    return [
        'country' => '中国',
        'province' => '',
        'city' => '',
        'district' => ''
    ];
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
    $sn = $request_data['sn'] ?? '';
    $auth_type = $request_data['auth_type'] ?? '';
    $auth_data = $request_data['auth_data'] ?? [];
    
    // 验证必填参数
    if (empty($sn) || empty($auth_type)) {
        json_response(false, null, '缺少必填参数', 'MISSING_PARAMS');
    }
    
    // 验证二维码格式
    if (!preg_match('/^(HS|ZY)-Q\d{9}$/', $sn)) {
        json_response(false, null, '无效的二维码格式', 'INVALID_QR_FORMAT');
    }
    
    // 连接数据库
    $db = get_db_connection($db_config);
    
    // 查询二维码记录
    $stmt = $db->prepare("SELECT * FROM qr_codes WHERE sn = ?");
    $stmt->execute([$sn]);
    $qr_record = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$qr_record) {
        // 如果记录不存在，自动创建
        $company = get_company_type($sn);
        $product_url = get_product_url($sn, $company);
        
        $stmt = $db->prepare("
            INSERT INTO qr_codes (sn, product_url, company, status) 
            VALUES (?, ?, ?, 'unverified')
        ");
        $stmt->execute([$sn, $product_url, $company]);
        
        // 重新查询
        $stmt = $db->prepare("SELECT * FROM qr_codes WHERE sn = ?");
        $stmt->execute([$sn]);
        $qr_record = $stmt->fetch(PDO::FETCH_ASSOC);
    }
    
    // 根据认证类型进行验证
    $verification_result = null;
    $verifier_info = null;
    
    switch ($auth_type) {
        case 'wechat':
            list($success, $result) = verify_wechat_login($auth_data, $wechat_config);
            if (!$success) {
                json_response(false, null, $result, 'WECHAT_AUTH_FAILED');
            }
            $verifier_info = $result;
            break;
            
        case 'phone':
            list($success, $result) = verify_phone_login($auth_data, $db);
            if (!$success) {
                json_response(false, null, $result, 'PHONE_AUTH_FAILED');
            }
            $verifier_info = $result;
            break;
            
        default:
            json_response(false, null, '不支持的认证类型', 'UNSUPPORTED_AUTH_TYPE');
    }
    
    // 更新二维码记录状态
    $stmt = $db->prepare("
        UPDATE qr_codes 
        SET status = 'verified', 
            verifier_info = ?, 
            verified_at = NOW() 
        WHERE sn = ?
    ");
    $stmt->execute([json_encode($verifier_info, JSON_UNESCAPED_UNICODE), $sn]);
    
    // 记录扫码历史
    record_scan_history($db, $sn, $auth_type, $verifier_info);
    
    // 返回成功响应
    json_response(true, [
        'redirect_url' => $qr_record['product_url'],
        'sn' => $sn,
        'company' => $qr_record['company'],
        'auth_type' => $auth_type
    ], '验证成功');
    
} catch (Exception $e) {
    error_log("API错误: " . $e->getMessage());
    json_response(false, null, '服务器内部错误', 'INTERNAL_ERROR');
}
?>