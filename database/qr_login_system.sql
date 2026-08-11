-- 扫码登录系统数据库结构
-- 创建 qr_codes 表用于管理二维码验证和产品信息跳转

CREATE TABLE IF NOT EXISTS qr_codes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sn VARCHAR(255) UNIQUE NOT NULL COMMENT '二维码序列号，格式: HS-DEMO-000000001 或 ZY-DEMO-000000001',
    product_url TEXT NOT NULL COMMENT '验证成功后跳转的产品信息页面URL',
    status VARCHAR(50) DEFAULT 'unverified' COMMENT '验证状态: unverified, verified',
    company VARCHAR(100) COMMENT '公司标识: company_a, company_b',
    verifier_info JSON COMMENT '验证者信息: 微信openid/昵称/头像 或 手机号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    verified_at TIMESTAMP NULL COMMENT '验证时间',
    INDEX idx_sn (sn),
    INDEX idx_status (status),
    INDEX idx_company (company)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='二维码验证管理表';

-- 创建手机验证码缓存表
CREATE TABLE IF NOT EXISTS verification_codes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    phone_number VARCHAR(20) NOT NULL COMMENT '手机号码',
    verification_code VARCHAR(10) NOT NULL COMMENT '验证码',
    expires_at TIMESTAMP NOT NULL COMMENT '过期时间',
    used BOOLEAN DEFAULT FALSE COMMENT '是否已使用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_phone (phone_number),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='手机验证码缓存表';

-- 插入示例数据
INSERT INTO qr_codes (sn, product_url, company) VALUES 
('HS-DEMO-000007616', 'http://www.your-company-domain.com/product/detail.php?id=HS-DEMO-000007616', 'company_a'),
('ZY-DEMO-000007616', 'http://www.your-company-domain.com/product/detail.php?id=ZY-DEMO-000007616', 'company_b'),
('HS-DEMO-000007617', 'http://www.your-company-domain.com/product/detail.php?id=HS-DEMO-000007617', 'company_a'),
('ZY-DEMO-000007617', 'http://www.your-company-domain.com/product/detail.php?id=ZY-DEMO-000007617', 'company_b');