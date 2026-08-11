# 🔒 安全性和输入验证文档

## 概述

本文档描述了公网二维码显示系统的安全性措施和输入验证机制。系统采用多层安全防护策略，确保在公网环境下的安全运行。

## 安全架构

### 1. 输入验证层
- **产品ID验证**: 严格的格式检查和白名单验证
- **URL验证**: 域名白名单和协议限制
- **数据验证**: JSON数据结构和内容验证
- **字符串清理**: XSS防护和恶意代码过滤

### 2. 请求控制层
- **频率限制**: 防止暴力攻击和资源滥用
- **客户端识别**: 基于浏览器特征的客户端标识
- **IP阻止**: 自动阻止恶意IP地址
- **请求监控**: 实时监控异常请求模式

### 3. 内容安全层
- **CSP策略**: 内容安全策略防护
- **DOM保护**: 防止恶意DOM操作
- **脚本监控**: 检测和阻止恶意脚本注入
- **事件监控**: 监控可疑的安全事件

## 安全配置

### 产品ID验证规则

```javascript
productId: {
    minLength: 3,                    // 最小长度
    maxLength: 50,                   // 最大长度
    pattern: /^[A-Z0-9\\-_]+$/i,     // 允许的字符模式
    allowedPrefixes: [               // 允许的前缀
        'HS-Q', 
        'ZY-Q', 
        'TEST-Q'
    ],
    blockedPatterns: [               // 阻止的恶意模式
        /script/i,
        /<.*>/,
        /javascript:/i,
        /data:/i,
        /vbscript:/i
    ]
}
```

### URL验证规则

```javascript
url: {
    allowedDomains: [                // 允许的域名
        'www.your-company-domain.com',
        'www.your-company-domain.com',
        'localhost',
        '127.0.0.1'
    ],
    allowedProtocols: [              // 允许的协议
        'http:', 
        'https:'
    ],
    maxLength: 2048                  // 最大URL长度
}
```

### 请求频率限制

```javascript
rateLimit: {
    maxRequestsPerMinute: 60,        // 每分钟最大请求数
    maxRequestsPerHour: 300,         // 每小时最大请求数
    blockDuration: 5 * 60 * 1000     // 阻止持续时间(5分钟)
}
```

### CSP策略

```javascript
csp: {
    'default-src': "'self'",
    'script-src': "'self' 'unsafe-inline'",
    'style-src': "'self' 'unsafe-inline'",
    'img-src': "'self' data: https:",
    'connect-src': "'self'",
    'font-src': "'self'",
    'object-src': "'none'",
    'media-src': "'self'",
    'frame-src': "'none'"
}
```

## 安全功能

### 1. SecurityValidator 类

主要的安全验证器类，提供以下功能：

#### 初始化和配置
- `init()`: 初始化安全验证器
- `setupCSP()`: 设置内容安全策略
- `bindSecurityEventListeners()`: 绑定安全事件监听器

#### 输入验证方法
- `validateProductId(productId)`: 验证产品ID
- `validateURL(url)`: 验证URL
- `validateJSONData(data)`: 验证JSON数据
- `validateRequest(request)`: 验证完整请求

#### 安全控制方法
- `checkRateLimit(identifier)`: 检查请求频率限制
- `sanitizeString(str)`: 清理字符串
- `sanitizeProductId(productId)`: 清理产品ID

#### 监控和报告
- `logSecurityEvent(eventType, data)`: 记录安全事件
- `getSecurityReport()`: 获取安全报告
- `cleanup()`: 清理过期数据

### 2. 集成到主系统

在 `main.js` 中的集成：

```javascript
// 初始化安全验证器
initializeSecurityValidator() {
    if (window.SecurityValidator) {
        this.securityValidator = new window.SecurityValidator();
    }
}

// 安全验证产品ID
validateProductIdSecurely(productId) {
    if (this.securityValidator) {
        return this.securityValidator.validateProductId(productId);
    } else {
        return this.fallbackValidateProductId(productId);
    }
}

// 安全设置文本内容
setElementTextSecurely(element, text) {
    let sanitizedText = text || '-';
    if (this.securityValidator) {
        sanitizedText = this.securityValidator.sanitizeString(sanitizedText);
    }
    element.textContent = sanitizedText;
}
```

## 安全事件类型

系统监控以下类型的安全事件：

### 1. 输入验证事件
- `blocked_malicious_product_id`: 阻止恶意产品ID
- `blocked_unauthorized_domain`: 阻止未授权域名
- `data_validation_failed`: 数据验证失败

### 2. 请求控制事件
- `rate_limit_exceeded`: 请求频率超限
- `ip_blocked`: IP地址被阻止
- `suspicious_request_pattern`: 可疑请求模式

### 3. 内容安全事件
- `suspicious_script_src`: 可疑脚本源
- `suspicious_script_content`: 可疑脚本内容
- `suspicious_iframe`: 可疑iframe
- `suspicious_link`: 可疑链接

### 4. 系统事件
- `devtools_opened`: 开发者工具打开
- `javascript_error`: JavaScript错误
- `client_security_check`: 客户端安全检查

## 安全测试

### 测试页面
访问 `docs/samples/web_tests/security_test.html` 进行安全功能测试：

1. **产品ID验证测试**
   - 有效ID测试
   - 无效ID测试
   - 恶意ID测试
   - 自定义ID测试

2. **URL验证测试**
   - URL格式验证
   - 域名白名单测试
   - 恶意URL检测

3. **数据验证测试**
   - JSON数据验证
   - 恶意数据检测
   - 数据清理测试

4. **请求频率测试**
   - 正常请求测试
   - 频率限制测试
   - 超限阻止测试

5. **安全监控测试**
   - 安全事件模拟
   - 安全报告生成
   - 日志清理测试

### 测试命令

```bash
# 在浏览器中打开测试页面
file:///path/to/docs/samples/web_tests/security_test.html

# 或者直接打开文件
file:///path/to/docs/samples/web_tests/security_test.html
```

## 安全最佳实践

### 1. 部署建议
- 使用HTTPS协议
- 配置适当的CSP头部
- 启用安全相关的HTTP头部
- 定期更新安全配置

### 2. 监控建议
- 定期检查安全报告
- 监控异常请求模式
- 及时处理安全事件
- 保持安全日志

### 3. 维护建议
- 定期更新安全规则
- 测试安全功能
- 备份安全配置
- 培训相关人员

## 故障排除

### 常见问题

1. **安全验证器未加载**
   - 检查 `security-validator.js` 文件是否存在
   - 确认脚本加载顺序正确
   - 查看浏览器控制台错误信息

2. **产品ID验证失败**
   - 检查产品ID格式是否符合规则
   - 确认前缀是否在白名单中
   - 查看验证错误详细信息

3. **请求被频率限制**
   - 检查请求频率是否过高
   - 确认客户端标识是否正确
   - 等待阻止时间结束

4. **CSP策略冲突**
   - 检查CSP配置是否正确
   - 确认资源URL是否在允许列表中
   - 调整CSP策略设置

### 调试方法

1. **启用详细日志**
   ```javascript
   // 在浏览器控制台中
   localStorage.setItem('debug', 'true');
   ```

2. **查看安全报告**
   ```javascript
   // 获取安全报告
   if (window.securityValidator) {
       console.log(window.securityValidator.getSecurityReport());
   }
   ```

3. **测试特定功能**
   ```javascript
   // 测试产品ID验证
   const result = securityValidator.validateProductId('TEST-Q123');
   console.log(result);
   ```

## 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 实现基础安全验证功能
- 添加请求频率限制
- 实现CSP策略
- 添加安全事件监控
- 创建安全测试页面

---

**注意**: 本文档会随着系统更新而持续更新，请定期查看最新版本。