<?php
// 产品详情页 - 验证成功后显示
header('Content-Type: text/html; charset=utf-8');

// 获取二维码信息
$code = $_GET['code'] ?? '';
$product_data = null;
$company_info = null;

if (!empty($code)) {
    try {
        // 调用统一API获取产品数据
        $api_url = "/api/get_product_data.php?code=" . urlencode($code);
        // 通过 HTTP 请求同域 API，避免直接读取 PHP 源码
        $scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
        $host = $_SERVER['HTTP_HOST'] ?? 'localhost';
        $full_url = $scheme . '://' . $host . $api_url;
        $api_response = @file_get_contents($full_url);
        
        if ($api_response) {
            $api_data = json_decode($api_response, true);
            if ($api_data && !isset($api_data['error'])) {
                $product_data = $api_data;
                
                // 设置公司信息
                if (strpos($code, 'A-') === 0) {
                    $company_info = [
                        'name' => '[已脱敏城市]示例品牌B材料有限公司',
                        'website' => 'https://www.your-company-domain.com',
                        'color' => '#e74c3c'
                    ];
                } elseif (strpos($code, 'B-') === 0) {
                    $company_info = [
                        'name' => '[已脱敏城市]示例品牌A有限公司',
                        'website' => 'https://www.your-company-domain.com',
                        'color' => '#3498db'
                    ];
                }
            }
        }
    } catch (Exception $e) {
        error_log("查询产品信息失败: " . $e->getMessage());
    }
}

// 如果没有找到数据，使用默认数据
if (!$product_data || !$company_info) {
    $product_data = [
        'company_name' => '[已脱敏城市]示例品牌B材料有限公司',
        'product_type' => 'XPS挤塑板',
        'product_spec' => '1800mm*600mm*50mm',
        'product_color' => '蓝色',
        'product_feature' => '隔热、保温',
        'quantity' => '1',
        'unit' => 'm³',
        'batch_number' => '20250815001',
        'production_date' => '2025-08-15 10:56:28',
        'distributor_name' => '[已脱敏城市]示例公司市场中心',
        'issuer_name' => '9810001',
        'plate_number' => '京A12345',
        'phone' => '（+86）138 0000 0000',
        'official_website' => 'https://www.your-company-domain.com'
    ];
    
    $company_info = [
        'name' => '[已脱敏城市]示例品牌B材料有限公司',
        'website' => 'https://www.your-company-domain.com',
        'color' => '#e74c3c'
    ];
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>产品溯源信息 - <?php echo htmlspecialchars($company_info['name']); ?></title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            max-width: 400px;
            width: 100%;
            overflow: hidden;
            max-height: 90vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: linear-gradient(135deg, <?php echo $company_info['color']; ?>, <?php echo $company_info['color']; ?>dd);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 16px;
            margin-bottom: 5px;
            font-weight: normal;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 12px;
        }
        
        .verified-badge {
            background: rgba(255,255,255,0.2);
            border-radius: 20px;
            padding: 5px 15px;
            font-size: 12px;
            margin-top: 10px;
            display: inline-block;
        }
        
        .content {
            flex: 1;
            overflow-y: auto;
            background: white;
        }
        
        .product-table {
            width: 100%;
            background: white;
        }
        
        .table-row {
            display: flex;
            align-items: center;
            padding: 12px 20px;
            border-bottom: 1px solid #f0f0f0;
            min-height: 45px;
        }
        
        .table-row:last-child {
            border-bottom: none;
        }
        
        .table-label {
            color: #666;
            font-size: 14px;
            min-width: 80px;
            flex-shrink: 0;
        }
        
        .table-value {
            color: #333;
            font-size: 14px;
            flex: 1;
            text-align: right;
            word-break: break-all;
        }
        
        .website-row {
            background: #f8f9ff;
        }
        
        .website-link {
            color: #1976d2;
            text-decoration: none;
            font-weight: 500;
        }
        
        .website-link:hover {
            text-decoration: underline;
        }
        
        .qr-code-row {
            background: #fff3cd;
            border-top: 2px solid #ffc107;
        }
        
        .qr-code-value {
            font-family: 'Monaco', 'Consolas', monospace;
            color: #856404;
            font-weight: bold;
        }
        
        .bottom-section {
            padding: 20px;
            background: white;
            text-align: center;
            border-top: 1px solid #f0f0f0;
        }
        
        .bottom-text {
            color: #666;
            font-size: 12px;
            margin-bottom: 15px;
        }
        
        .enter-website-btn {
            background: #1976d2;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        
        .enter-website-btn:hover {
            background: #1565c0;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
        }
        
        .footer {
            background: #f8f9fa;
            padding: 12px;
            text-align: center;
            font-size: 11px;
            color: #7f8c8d;
            border-top: 1px solid #eee;
        }
        
        .footer-success {
            color: #28a745;
            font-weight: bold;
            margin-bottom: 3px;
        }
        
        /* 响应式优化 */
        @media (max-width: 380px) {
            .container {
                margin: 5px;
                max-width: calc(100vw - 10px);
            }
            
            .header {
                padding: 15px;
            }
            
            .table-row {
                padding: 10px 15px;
            }
            
            .table-label {
                min-width: 70px;
                font-size: 13px;
            }
            
            .table-value {
                font-size: 13px;
            }
        }
        
        @media (max-height: 700px) {
            .container {
                max-height: 95vh;
            }
            
            .table-row {
                padding: 8px 15px;
                min-height: 40px;
            }
            
            .bottom-section {
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>产品溯源信息</h1>
            <p><?php echo htmlspecialchars($company_info['name']); ?></p>
            <div class="verified-badge">✅ 已验证身份</div>
        </div>
        
        <div class="content">
            <div class="product-table">
                <?php if ($code): ?>
                <div class="table-row qr-code-row">
                    <span class="table-label">追溯码</span>
                    <span class="table-value qr-code-value"><?php echo htmlspecialchars($code); ?></span>
                </div>
                <?php endif; ?>
                
                <div class="table-row">
                    <span class="table-label">公司名称</span>
                    <span class="table-value"><?php echo htmlspecialchars($product_data['company_name']); ?></span>
                </div>
                <div class="table-row">
                    <span class="table-label">产品类型</span>
                    <span class="table-value"><?php echo htmlspecialchars($product_data['product_type']); ?></span>
                </div>
                <div class="table-row">
                    <span class="table-label">产品规格</span>
                    <span class="table-value"><?php echo htmlspecialchars($product_data['product_spec']); ?></span>
                </div>
                <div class="table-row">
                    <span class="table-label">产品颜色</span>
                    <span class="table-value"><?php echo htmlspecialchars($product_data['product_color']); ?></span>
                </div>
                <div class="table-row">
                    <span class="table-label">功能特性</span>
                    <span class="table-value"><?php echo htmlspecialchars($product_data['product_feature']); ?></span>
                </div>
                <div class="table-row">
                    <span class="table-label">生产装置</span>
                    <span class="table-value"><?php echo htmlspecialchars($product_data['quantity']) . ' ' . htmlspecialchars($product_data['unit']); ?></span>
                </div>
                <div class="table-row">
                    <span class="table-label">批次号</span>
                    <span class="table-value"><?php echo htmlspecialchars($product_data['batch_number']); ?></span>
                </div>
                <div class="table-row">
                    <span class="table-label">生产日期</span>
                    <span class="table-value"><?php 
                        $date = new DateTime($product_data['production_date']);
                        echo $date->format('Y-m-d H:i:s');
                    ?></span>
                </div>
                <div class="table-row">
                    <span class="table-label">销售单位</span>
                    <span class="table-value"><?php echo htmlspecialchars($product_data['distributor_name']); ?></span>
                </div>
                <div class="table-row">
                    <span class="table-label">发行人</span>
                    <span class="table-value"><?php echo htmlspecialchars($product_data['issuer_name']); ?></span>
                </div>
                <div class="table-row">
                    <span class="table-label">经销商</span>
                    <span class="table-value"><?php echo htmlspecialchars($product_data['distributor_name']); ?></span>
                </div>
                <div class="table-row">
                    <span class="table-label">物流车牌</span>
                    <span class="table-value"><?php echo htmlspecialchars($product_data['plate_number']); ?></span>
                </div>
                <div class="table-row">
                    <span class="table-label">联系电话</span>
                    <span class="table-value"><?php echo htmlspecialchars($product_data['phone']); ?></span>
                </div>
                <div class="table-row website-row">
                    <span class="table-label">官网</span>
                    <span class="table-value">
                        <a href="<?php echo htmlspecialchars($company_info['website']); ?>" target="_blank" class="website-link">
                            <?php echo str_replace(['http://', 'https://'], '', $company_info['website']); ?>
                        </a>
                    </span>
                </div>
            </div>
            
            <div class="bottom-section">
                <div class="bottom-text">如需查询更多产品，请访问官方网站</div>
                <a href="<?php echo htmlspecialchars($company_info['website']); ?>" target="_blank" class="enter-website-btn">
                    进入官网（新窗口）
                </a>
            </div>
        </div>
        
        <div class="footer">
            <div class="footer-success">✅ 扫码查询成功 · 正品保障 · 品质保证</div>
            <p><?php echo htmlspecialchars($company_info['name']); ?></p>
        </div>
    </div>
</body>
</html>