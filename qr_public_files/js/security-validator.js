/**
 * 安全性和输入验证模块
 * 提供XSS防护、输入清理、参数验证等安全功能
 * 
 * @version 1.0.0
 * @author QR Display System
 */

class SecurityValidator {
    constructor() {
        this.config = {
            maxUrlLength: 2048,
            maxProductIdLength: 50,
            maxFileSize: 2 * 1024 * 1024, // 2MB
            allowedDomains: [
                'www.your-company-domain.com',
                'your-company-domain.com',
                'www.your-company-domain.com',
                'localhost',
                '127.0.0.1'
            ],
            blockedPatterns: [
                /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
                /javascript:/gi,
                /vbscript:/gi,
                /onload\s*=/gi,
                /onerror\s*=/gi,
                /onclick\s*=/gi,
                /onmouseover\s*=/gi,
                /<iframe\b[^>]*>/gi,
                /<object\b[^>]*>/gi,
                /<embed\b[^>]*>/gi,
                /<form\b[^>]*>/gi
            ],
            productIdPattern: /^[A-Z0-9\-_]{1,50}$/i,
            safeCharPattern: /^[a-zA-Z0-9\s\-_.,()（）\u4e00-\u9fff]*$/
        };
        
        this.securityLog = [];
        this.rateLimiter = new Map();
        
        this.init();
    }
    
    /**
     * 初始化安全验证器
     */
    init() {
        // 设置内容安全策略
        this.setupCSP();
        
        // 绑定全局安全事件监听
        this.bindSecurityEvents();
        
        // 初始化速率限制器
        this.initRateLimiter();
        
        console.log('🛡️ Security validator initialized');
    }
    
    /**
     * 设置内容安全策略
     */
    setupCSP() {
        try {
            // 检查是否已有CSP meta标签
            let cspMeta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
            
            if (!cspMeta) {
                cspMeta = document.createElement('meta');
                cspMeta.setAttribute('http-equiv', 'Content-Security-Policy');
                
                // 定义CSP策略
                const cspPolicy = [
                    "default-src 'self'",
                    "script-src 'self' 'unsafe-inline'", // 允许内联脚本（开发阶段）
                    "style-src 'self' 'unsafe-inline'",
                    "img-src 'self' data: https:",
                    "font-src 'self' data:",
                    "connect-src 'self' https:",
                    "frame-ancestors 'none'",
                    "base-uri 'self'",
                    "form-action 'self'"
                ].join('; ');
                
                cspMeta.setAttribute('content', cspPolicy);
                document.head.appendChild(cspMeta);
                
                console.log('🔒 CSP policy applied');
            }
        } catch (error) {
            console.warn('⚠️ Failed to set CSP:', error);
        }
    }
    
    /**
     * 绑定安全事件监听
     */
    bindSecurityEvents() {
        // 监听可疑的DOM操作
        if (typeof MutationObserver !== 'undefined') {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach((node) => {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                this.scanElementForThreats(node);
                            }
                        });
                    }
                });
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
        
        // 监听表单提交
        document.addEventListener('submit', (e) => {
            if (!this.validateForm(e.target)) {
                e.preventDefault();
                this.logSecurityEvent('form_validation_failed', {
                    form: e.target.id || 'unknown'
                });
            }
        });
        
        // 监听可疑的网络请求
        this.interceptFetch();
    }
    
    /**
     * 初始化速率限制器
     */
    initRateLimiter() {
        // 清理过期的速率限制记录
        setInterval(() => {
            const now = Date.now();
            const expireTime = 60 * 1000; // 1分钟
            
            for (const [key, data] of this.rateLimiter.entries()) {
                if (now - data.lastRequest > expireTime) {
                    this.rateLimiter.delete(key);
                }
            }
        }, 30 * 1000); // 每30秒清理一次
    }
    
    /**
     * 验证URL参数
     */
    validateUrlParameters() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const validationResults = {
                valid: true,
                errors: [],
                sanitized: {}
            };
            
            // 验证产品ID参数
            const productId = urlParams.get('id');
            if (productId) {
                const idValidation = this.validateProductId(productId);
                if (!idValidation.valid) {
                    validationResults.valid = false;
                    validationResults.errors.push(`Invalid product ID: ${idValidation.error}`);
                } else {
                    validationResults.sanitized.id = idValidation.sanitized;
                }
            }
            
            // 验证语言参数
            const lang = urlParams.get('lang');
            if (lang) {
                const langValidation = this.validateLanguageCode(lang);
                if (!langValidation.valid) {
                    validationResults.valid = false;
                    validationResults.errors.push(`Invalid language code: ${langValidation.error}`);
                } else {
                    validationResults.sanitized.lang = langValidation.sanitized;
                }
            }
            
            // 检查是否有未知参数
            const allowedParams = ['id', 'lang'];
            for (const [key, value] of urlParams.entries()) {
                if (!allowedParams.includes(key)) {
                    validationResults.errors.push(`Unknown parameter: ${key}`);
                    this.logSecurityEvent('unknown_parameter', { key, value });
                }
            }
            
            // 验证URL长度
            if (window.location.href.length > this.config.maxUrlLength) {
                validationResults.valid = false;
                validationResults.errors.push('URL too long');
            }
            
            return validationResults;
            
        } catch (error) {
            console.error('URL parameter validation error:', error);
            return {
                valid: false,
                errors: ['URL validation failed'],
                sanitized: {}
            };
        }
    }
    
    /**
     * 验证产品ID
     */
    validateProductId(productId) {
        try {
            // 基本格式检查
            if (!productId || typeof productId !== 'string') {
                return { valid: false, error: 'Product ID is required and must be a string' };
            }
            
            // 长度检查
            if (productId.length > this.config.maxProductIdLength) {
                return { valid: false, error: 'Product ID too long' };
            }
            
            // 格式检查
            if (!this.config.productIdPattern.test(productId)) {
                return { valid: false, error: 'Product ID contains invalid characters' };
            }
            
            // XSS检查
            const xssCheck = this.checkForXSS(productId);
            if (!xssCheck.safe) {
                return { valid: false, error: 'Product ID contains potentially malicious content' };
            }
            
            // 清理和标准化
            const sanitized = this.sanitizeInput(productId);
            
            return {
                valid: true,
                sanitized: sanitized,
                original: productId
            };
            
        } catch (error) {
            return { valid: false, error: 'Product ID validation failed' };
        }
    }
    
    /**
     * 验证语言代码
     */
    validateLanguageCode(lang) {
        try {
            const allowedLanguages = ['zh', 'en'];
            
            if (!lang || typeof lang !== 'string') {
                return { valid: false, error: 'Language code must be a string' };
            }
            
            const sanitized = lang.toLowerCase().trim();
            
            if (!allowedLanguages.includes(sanitized)) {
                return { valid: false, error: 'Unsupported language code' };
            }
            
            return {
                valid: true,
                sanitized: sanitized,
                original: lang
            };
            
        } catch (error) {
            return { valid: false, error: 'Language validation failed' };
        }
    }
    
    /**
     * XSS检查
     */
    checkForXSS(input) {
        try {
            if (!input || typeof input !== 'string') {
                return { safe: true, cleaned: input };
            }
            
            // 检查危险模式
            for (const pattern of this.config.blockedPatterns) {
                if (pattern.test(input)) {
                    this.logSecurityEvent('xss_attempt', {
                        input: input.substring(0, 100),
                        pattern: pattern.source
                    });
                    return { safe: false, reason: 'Blocked pattern detected' };
                }
            }
            
            // 检查HTML实体编码
            const decoded = this.decodeHtmlEntities(input);
            if (decoded !== input) {
                // 递归检查解码后的内容
                return this.checkForXSS(decoded);
            }
            
            return { safe: true, cleaned: input };
            
        } catch (error) {
            console.warn('XSS check error:', error);
            return { safe: false, reason: 'XSS check failed' };
        }
    }
    
    /**
     * 输入清理
     */
    sanitizeInput(input) {
        try {
            if (!input || typeof input !== 'string') {
                return input;
            }
            
            // 移除危险字符
            let sanitized = input
                .replace(/[<>\"']/g, '') // 移除HTML特殊字符
                .replace(/javascript:/gi, '') // 移除JavaScript协议
                .replace(/vbscript:/gi, '') // 移除VBScript协议
                .replace(/on\w+\s*=/gi, '') // 移除事件处理器
                .trim();
            
            // 限制长度
            if (sanitized.length > this.config.maxProductIdLength) {
                sanitized = sanitized.substring(0, this.config.maxProductIdLength);
            }
            
            return sanitized;
            
        } catch (error) {
            console.warn('Input sanitization error:', error);
            return '';
        }
    }
    
    /**
     * HTML实体解码
     */
    decodeHtmlEntities(input) {
        try {
            const textarea = document.createElement('textarea');
            textarea.innerHTML = input;
            return textarea.value;
        } catch (error) {
            return input;
        }
    }
    
    /**
     * 验证JSON数据
     */
    validateJsonData(data, maxSize = this.config.maxFileSize) {
        try {
            const validation = {
                valid: true,
                errors: [],
                sanitized: null
            };
            
            // 检查数据大小
            const dataString = JSON.stringify(data);
            if (dataString.length > maxSize) {
                validation.valid = false;
                validation.errors.push('Data too large');
                return validation;
            }
            
            // 递归清理对象
            const sanitized = this.sanitizeObject(data);
            validation.sanitized = sanitized;
            
            return validation;
            
        } catch (error) {
            return {
                valid: false,
                errors: ['JSON validation failed'],
                sanitized: null
            };
        }
    }
    
    /**
     * 清理对象数据
     */
    sanitizeObject(obj) {
        try {
            if (obj === null || obj === undefined) {
                return obj;
            }
            
            if (typeof obj === 'string') {
                const xssCheck = this.checkForXSS(obj);
                return xssCheck.safe ? obj : '';
            }
            
            if (typeof obj === 'number' || typeof obj === 'boolean') {
                return obj;
            }
            
            if (Array.isArray(obj)) {
                return obj.map(item => this.sanitizeObject(item));
            }
            
            if (typeof obj === 'object') {
                const sanitized = {};
                for (const [key, value] of Object.entries(obj)) {
                    // 清理键名
                    const cleanKey = this.sanitizeInput(key);
                    if (cleanKey && this.config.safeCharPattern.test(cleanKey)) {
                        sanitized[cleanKey] = this.sanitizeObject(value);
                    }
                }
                return sanitized;
            }
            
            return obj;
            
        } catch (error) {
            console.warn('Object sanitization error:', error);
            return {};
        }
    }
    
    /**
     * 速率限制检查
     */
    checkRateLimit(identifier, maxRequests = 10, timeWindow = 60000) {
        try {
            const now = Date.now();
            const key = `rate_${identifier}`;
            
            if (!this.rateLimiter.has(key)) {
                this.rateLimiter.set(key, {
                    count: 1,
                    firstRequest: now,
                    lastRequest: now
                });
                return { allowed: true, remaining: maxRequests - 1 };
            }
            
            const data = this.rateLimiter.get(key);
            
            // 检查时间窗口
            if (now - data.firstRequest > timeWindow) {
                // 重置计数器
                this.rateLimiter.set(key, {
                    count: 1,
                    firstRequest: now,
                    lastRequest: now
                });
                return { allowed: true, remaining: maxRequests - 1 };
            }
            
            // 检查请求数量
            if (data.count >= maxRequests) {
                this.logSecurityEvent('rate_limit_exceeded', {
                    identifier: identifier,
                    count: data.count,
                    timeWindow: timeWindow
                });
                return { allowed: false, remaining: 0 };
            }
            
            // 更新计数器
            data.count++;
            data.lastRequest = now;
            
            return { allowed: true, remaining: maxRequests - data.count };
            
        } catch (error) {
            console.warn('Rate limit check error:', error);
            return { allowed: true, remaining: 0 };
        }
    }
    
    /**
     * 扫描元素中的威胁
     */
    scanElementForThreats(element) {
        try {
            // 检查脚本标签
            if (element.tagName === 'SCRIPT') {
                this.logSecurityEvent('script_injection_attempt', {
                    content: element.textContent?.substring(0, 100)
                });
                element.remove();
                return;
            }
            
            // 检查危险属性
            const dangerousAttrs = ['onclick', 'onload', 'onerror', 'onmouseover'];
            for (const attr of dangerousAttrs) {
                if (element.hasAttribute(attr)) {
                    this.logSecurityEvent('dangerous_attribute', {
                        element: element.tagName,
                        attribute: attr
                    });
                    element.removeAttribute(attr);
                }
            }
            
            // 检查href属性
            if (element.hasAttribute('href')) {
                const href = element.getAttribute('href');
                if (href.startsWith('javascript:') || href.startsWith('vbscript:')) {
                    this.logSecurityEvent('malicious_link', { href });
                    element.removeAttribute('href');
                }
            }
            
        } catch (error) {
            console.warn('Element threat scan error:', error);
        }
    }
    
    /**
     * 验证表单
     */
    validateForm(form) {
        try {
            const formData = new FormData(form);
            
            for (const [key, value] of formData.entries()) {
                const xssCheck = this.checkForXSS(value);
                if (!xssCheck.safe) {
                    this.logSecurityEvent('form_xss_attempt', {
                        field: key,
                        value: value.substring(0, 100)
                    });
                    return false;
                }
            }
            
            return true;
            
        } catch (error) {
            console.warn('Form validation error:', error);
            return false;
        }
    }
    
    /**
     * 拦截Fetch请求
     */
    interceptFetch() {
        try {
            const originalFetch = window.fetch;
            
            window.fetch = async (url, options = {}) => {
                // 验证URL
                if (typeof url === 'string') {
                    const urlValidation = this.validateRequestUrl(url);
                    if (!urlValidation.valid) {
                        this.logSecurityEvent('blocked_request', {
                            url: url,
                            reason: urlValidation.error
                        });
                        throw new Error('Request blocked by security policy');
                    }
                }
                
                // 检查速率限制
                const rateLimit = this.checkRateLimit('fetch_requests', 20, 60000);
                if (!rateLimit.allowed) {
                    throw new Error('Rate limit exceeded');
                }
                
                return originalFetch(url, options);
            };
            
        } catch (error) {
            console.warn('Fetch interception setup failed:', error);
        }
    }
    
    /**
     * 验证请求URL
     */
    validateRequestUrl(url) {
        try {
            const parsedUrl = new URL(url, window.location.origin);
            
            // 检查协议
            if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
                return { valid: false, error: 'Invalid protocol' };
            }
            
            // 检查域名（如果是绝对URL）
            if (parsedUrl.origin !== window.location.origin) {
                const hostname = parsedUrl.hostname;
                if (!this.config.allowedDomains.includes(hostname)) {
                    return { valid: false, error: 'Domain not allowed' };
                }
            }
            
            return { valid: true };
            
        } catch (error) {
            return { valid: false, error: 'URL parsing failed' };
        }
    }
    
    /**
     * 记录安全事件
     */
    logSecurityEvent(type, details = {}) {
        const event = {
            type: type,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            details: details
        };
        
        this.securityLog.push(event);
        
        // 限制日志大小
        if (this.securityLog.length > 100) {
            this.securityLog = this.securityLog.slice(-50);
        }
        
        console.warn('🚨 Security event:', event);
        
        // 可以在这里添加向服务器报告的逻辑
        // this.reportSecurityEvent(event);
    }
    
    /**
     * 获取安全统计
     */
    getSecurityStats() {
        const stats = {
            totalEvents: this.securityLog.length,
            eventTypes: {},
            recentEvents: this.securityLog.slice(-10),
            rateLimitStatus: {
                activeKeys: this.rateLimiter.size,
                keys: Array.from(this.rateLimiter.keys())
            }
        };
        
        // 统计事件类型
        this.securityLog.forEach(event => {
            stats.eventTypes[event.type] = (stats.eventTypes[event.type] || 0) + 1;
        });
        
        return stats;
    }
    
    /**
     * 清理安全日志
     */
    clearSecurityLog() {
        this.securityLog = [];
        console.log('🧹 Security log cleared');
    }
}

// 创建全局安全验证器实例
window.securityValidator = new SecurityValidator();

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SecurityValidator;
}