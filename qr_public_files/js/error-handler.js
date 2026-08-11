/**
 * 错误处理模块
 * 提供统一的错误处理、用户友好的错误提示和错误恢复机制
 */

class ErrorHandler {
    constructor() {
        this.errorHistory = [];
        this.maxHistorySize = 50;
        this.errorCounts = new Map();
        this.lastErrorTime = null;
        this.errorThreshold = 5; // 5分钟内同类错误超过3次则降级处理
        this.errorTimeWindow = 5 * 60 * 1000; // 5分钟
        
        this.init();
    }
    
    /**
     * 初始化错误处理器
     */
    init() {
        // 绑定全局错误处理
        this.bindGlobalErrorHandlers();
        
        // 定期清理错误历史
        setInterval(() => this.cleanupErrorHistory(), 60000); // 每分钟清理一次
    }
    
    /**
     * 绑定全局错误处理器
     */
    bindGlobalErrorHandlers() {
        // JavaScript运行时错误
        window.addEventListener('error', (event) => {
            this.handleGlobalError({
                type: 'javascript_error',
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error: event.error
            });
        });
        
        // Promise未捕获的拒绝
        window.addEventListener('unhandledrejection', (event) => {
            this.handleGlobalError({
                type: 'unhandled_promise_rejection',
                message: event.reason?.message || event.reason,
                error: event.reason
            });
        });
        
        // 资源加载错误
        window.addEventListener('error', (event) => {
            if (event.target !== window) {
                this.handleResourceError({
                    type: 'resource_error',
                    element: event.target.tagName,
                    source: event.target.src || event.target.href,
                    message: `Failed to load ${event.target.tagName.toLowerCase()}`
                });
            }
        }, true);
    }
    
    /**
     * 处理应用错误
     */
    handleError(errorType, error, context = {}) {
        const errorInfo = this.createErrorInfo(errorType, error, context);
        
        // 记录错误
        this.recordError(errorInfo);
        
        // 检查错误频率
        if (this.isErrorFrequent(errorType)) {
            return this.handleFrequentError(errorInfo);
        }
        
        // 根据错误类型处理
        switch (errorType) {
            case 'product-not-found':
                return this.handleProductNotFoundError(errorInfo);
            case 'network-error':
            case 'network-timeout':
                return this.handleNetworkError(errorInfo);
            case 'server-error':
                return this.handleServerError(errorInfo);
            case 'data-error':
                return this.handleDataError(errorInfo);
            case 'param-error':
                return this.handleParamError(errorInfo);
            case 'browser-not-supported':
                return this.handleBrowserError(errorInfo);
            case 'file-too-large':
                return this.handleFileSizeError(errorInfo);
            default:
                return this.handleGenericError(errorInfo);
        }
    }
    
    /**
     * 创建错误信息对象
     */
    createErrorInfo(errorType, error, context) {
        return {
            type: errorType,
            message: error?.message || error,
            stack: error?.stack,
            timestamp: new Date().toISOString(),
            context: context,
            userAgent: navigator.userAgent,
            url: window.location.href,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            connection: this.getConnectionInfo()
        };
    }
    
    /**
     * 获取网络连接信息
     */
    getConnectionInfo() {
        if ('connection' in navigator) {
            const conn = navigator.connection;
            return {
                effectiveType: conn.effectiveType,
                downlink: conn.downlink,
                rtt: conn.rtt,
                saveData: conn.saveData
            };
        }
        return null;
    }
    
    /**
     * 记录错误
     */
    recordError(errorInfo) {
        // 添加到历史记录
        this.errorHistory.push(errorInfo);
        
        // 限制历史记录大小
        if (this.errorHistory.length > this.maxHistorySize) {
            this.errorHistory.shift();
        }
        
        // 更新错误计数
        const errorKey = `${errorInfo.type}_${Date.now() - (Date.now() % this.errorTimeWindow)}`;
        const count = this.errorCounts.get(errorKey) || 0;
        this.errorCounts.set(errorKey, count + 1);
        
        // 记录到控制台
        console.error('🚨 Error recorded:', errorInfo);
        
        // 发送到错误监控服务（如果配置了）
        this.sendToErrorService(errorInfo);
    }
    
    /**
     * 检查错误是否频繁发生
     */
    isErrorFrequent(errorType) {
        const now = Date.now();
        const windowStart = now - this.errorTimeWindow;
        
        const recentErrors = this.errorHistory.filter(error => 
            error.type === errorType && 
            new Date(error.timestamp).getTime() > windowStart
        );
        
        return recentErrors.length >= 3;
    }
    
    /**
     * 处理频繁错误
     */
    handleFrequentError(errorInfo) {
        console.warn('⚠️ Frequent error detected, using fallback handling:', errorInfo.type);
        
        return {
            title: this.getText('error-title'),
            message: this.getText('frequent-error-message') || '系统遇到重复问题，请稍后重试或联系技术支持',
            actions: [
                {
                    text: this.getText('contact-support') || '联系技术支持',
                    action: () => this.showSupportInfo(),
                    primary: true
                },
                {
                    text: this.getText('try-later') || '稍后重试',
                    action: () => window.location.reload(),
                    primary: false
                }
            ],
            severity: 'high'
        };
    }
    
    /**
     * 处理产品未找到错误
     */
    handleProductNotFoundError(errorInfo) {
        return {
            title: this.getText('product-not-found'),
            message: this.getText('error-product-not-found-detail'),
            actions: [
                {
                    text: this.getText('retry'),
                    action: () => window.location.reload(),
                    primary: true
                },
                {
                    text: this.getText('contact-support'),
                    action: () => this.showSupportInfo(),
                    primary: false
                }
            ],
            solutions: [
                this.getText('solution-check-qr'),
                this.getText('solution-contact-support')
            ],
            severity: 'medium'
        };
    }
    
    /**
     * 处理网络错误
     */
    handleNetworkError(errorInfo) {
        const isOnline = navigator.onLine;
        const connectionInfo = this.getConnectionInfo();
        
        let message = this.getText('error-network-detail');
        let solutions = [
            this.getText('solution-check-network'),
            this.getText('solution-try-later')
        ];
        
        if (!isOnline) {
            message = '设备当前处于离线状态，请检查网络连接';
            solutions = ['请连接到互联网', '检查WiFi或移动数据连接'];
        } else if (connectionInfo?.effectiveType === 'slow-2g') {
            message = '网络连接较慢，可能影响加载速度';
            solutions = ['请等待加载完成', '尝试切换到更快的网络'];
        }
        
        return {
            title: this.getText('network-error'),
            message: message,
            actions: [
                {
                    text: this.getText('retry'),
                    action: () => this.retryWithDelay(2000),
                    primary: true
                },
                {
                    text: '检查网络',
                    action: () => this.showNetworkDiagnostics(),
                    primary: false
                }
            ],
            solutions: solutions,
            severity: 'medium'
        };
    }
    
    /**
     * 处理服务器错误
     */
    handleServerError(errorInfo) {
        return {
            title: this.getText('server-error'),
            message: '服务器暂时不可用，这通常是临时问题',
            actions: [
                {
                    text: this.getText('retry'),
                    action: () => this.retryWithDelay(5000),
                    primary: true
                },
                {
                    text: '查看状态',
                    action: () => this.checkServerStatus(),
                    primary: false
                }
            ],
            solutions: [
                this.getText('solution-try-later'),
                '服务器可能正在维护中'
            ],
            severity: 'high'
        };
    }
    
    /**
     * 处理数据错误
     */
    handleDataError(errorInfo) {
        return {
            title: this.getText('data-error'),
            message: this.getText('error-data-detail'),
            actions: [
                {
                    text: this.getText('retry'),
                    action: () => window.location.reload(),
                    primary: true
                },
                {
                    text: this.getText('contact-support'),
                    action: () => this.showSupportInfo(),
                    primary: false
                }
            ],
            solutions: [
                this.getText('solution-contact-support'),
                '数据文件可能已损坏'
            ],
            severity: 'high'
        };
    }
    
    /**
     * 处理参数错误
     */
    handleParamError(errorInfo) {
        return {
            title: this.getText('param-error'),
            message: this.getText('error-param-detail'),
            actions: [
                {
                    text: '重新扫码',
                    action: () => this.showQRInstructions(),
                    primary: true
                },
                {
                    text: this.getText('contact-support'),
                    action: () => this.showSupportInfo(),
                    primary: false
                }
            ],
            solutions: [
                this.getText('solution-check-qr'),
                '请使用正确的二维码扫描应用'
            ],
            severity: 'medium'
        };
    }
    
    /**
     * 处理浏览器不支持错误
     */
    handleBrowserError(errorInfo) {
        return {
            title: this.getText('browser-not-supported'),
            message: '当前浏览器版本过旧，可能无法正常显示页面',
            actions: [
                {
                    text: '了解更多',
                    action: () => this.showBrowserUpgradeInfo(),
                    primary: true
                }
            ],
            solutions: [
                this.getText('solution-use-modern-browser'),
                '建议升级到最新版本浏览器'
            ],
            severity: 'high'
        };
    }
    
    /**
     * 处理文件过大错误
     */
    handleFileSizeError(errorInfo) {
        return {
            title: this.getText('file-too-large'),
            message: '产品数据文件过大，无法在当前网络条件下加载',
            actions: [
                {
                    text: '稍后重试',
                    action: () => this.retryWithDelay(3000),
                    primary: true
                },
                {
                    text: this.getText('contact-support'),
                    action: () => this.showSupportInfo(),
                    primary: false
                }
            ],
            solutions: [
                '请在网络条件较好时重试',
                '联系技术支持优化数据文件'
            ],
            severity: 'medium'
        };
    }
    
    /**
     * 处理通用错误
     */
    handleGenericError(errorInfo) {
        return {
            title: '发生未知错误',
            message: '系统遇到了未预期的问题',
            actions: [
                {
                    text: this.getText('retry'),
                    action: () => window.location.reload(),
                    primary: true
                },
                {
                    text: this.getText('contact-support'),
                    action: () => this.showSupportInfo(),
                    primary: false
                }
            ],
            solutions: [
                '请尝试刷新页面',
                '如问题持续，请联系技术支持'
            ],
            severity: 'medium'
        };
    }
    
    /**
     * 处理全局错误
     */
    handleGlobalError(errorInfo) {
        console.error('💥 Global error:', errorInfo);
        this.recordError(errorInfo);
        
        // 对于全局错误，通常不显示用户界面，只记录
        // 除非是严重错误影响页面功能
        if (this.isCriticalError(errorInfo)) {
            this.showCriticalErrorMessage();
        }
    }
    
    /**
     * 处理资源加载错误
     */
    handleResourceError(errorInfo) {
        console.warn('📦 Resource loading error:', errorInfo);
        this.recordError(errorInfo);
        
        // 尝试重新加载关键资源
        if (this.isCriticalResource(errorInfo.source)) {
            this.reloadCriticalResource(errorInfo);
        }
    }
    
    /**
     * 判断是否为关键错误
     */
    isCriticalError(errorInfo) {
        const criticalPatterns = [
            /Cannot read property/,
            /is not a function/,
            /ReferenceError/,
            /TypeError.*undefined/
        ];
        
        return criticalPatterns.some(pattern => 
            pattern.test(errorInfo.message)
        );
    }
    
    /**
     * 判断是否为关键资源
     */
    isCriticalResource(source) {
        if (!source) return false;
        
        const criticalResources = [
            'main.js',
            'i18n.js',
            'mobile.css'
        ];
        
        return criticalResources.some(resource => 
            source.includes(resource)
        );
    }
    
    /**
     * 重新加载关键资源
     */
    reloadCriticalResource(errorInfo) {
        // 这里可以实现资源重新加载逻辑
        console.log('🔄 Attempting to reload critical resource:', errorInfo.source);
    }
    
    /**
     * 显示严重错误消息
     */
    showCriticalErrorMessage() {
        // 创建简单的错误提示，不依赖其他模块
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            font-family: Arial, sans-serif;
        `;
        
        errorDiv.innerHTML = `
            <div style="text-align: center; padding: 20px;">
                <h2>系统错误</h2>
                <p>页面遇到严重错误，请刷新页面重试</p>
                <button onclick="window.location.reload()" style="
                    margin-top: 20px;
                    padding: 10px 20px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                ">刷新页面</button>
            </div>
        `;
        
        document.body.appendChild(errorDiv);
    }
    
    /**
     * 延迟重试
     */
    retryWithDelay(delay) {
        setTimeout(() => {
            if (window.qrApp && typeof window.qrApp.loadProductData === 'function') {
                window.qrApp.loadProductData();
            } else {
                window.location.reload();
            }
        }, delay);
    }
    
    /**
     * 显示支持信息
     */
    showSupportInfo() {
        const supportInfo = `
技术支持信息：
${this.getText('support-phone')}
${this.getText('support-email')}
${this.getText('support-website')}

错误ID: ${this.generateErrorId()}
时间: ${new Date().toLocaleString()}
        `.trim();
        
        if (navigator.share) {
            navigator.share({
                title: '技术支持信息',
                text: supportInfo
            });
        } else {
            // 复制到剪贴板
            this.copyToClipboard(supportInfo);
            alert('支持信息已复制到剪贴板');
        }
    }
    
    /**
     * 显示网络诊断信息
     */
    showNetworkDiagnostics() {
        const diagnostics = {
            online: navigator.onLine,
            connection: this.getConnectionInfo(),
            timestamp: new Date().toISOString()
        };
        
        console.log('🌐 Network diagnostics:', diagnostics);
        alert(`网络状态: ${diagnostics.online ? '在线' : '离线'}`);
    }
    
    /**
     * 检查服务器状态
     */
    checkServerStatus() {
        // 这里可以实现服务器状态检查
        console.log('🔍 Checking server status...');
        alert('正在检查服务器状态...');
    }
    
    /**
     * 显示二维码使用说明
     */
    showQRInstructions() {
        const instructions = `
二维码使用说明：
1. 确保二维码清晰完整
2. 使用手机相机或专用扫码应用
3. 确保网络连接正常
4. 如仍有问题，请联系技术支持
        `.trim();
        
        alert(instructions);
    }
    
    /**
     * 显示浏览器升级信息
     */
    showBrowserUpgradeInfo() {
        const upgradeInfo = `
建议使用以下现代浏览器：
• Chrome (推荐)
• Safari
• Firefox
• Edge

请访问浏览器官网下载最新版本
        `.trim();
        
        alert(upgradeInfo);
    }
    
    /**
     * 生成错误ID
     */
    generateErrorId() {
        return 'ERR-' + Date.now().toString(36).toUpperCase();
    }
    
    /**
     * 复制到剪贴板
     */
    async copyToClipboard(text) {
        try {
            if (navigator.clipboard) {
                await navigator.clipboard.writeText(text);
            } else {
                // 降级方案
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
            }
        } catch (error) {
            console.error('Failed to copy to clipboard:', error);
        }
    }
    
    /**
     * 获取国际化文本
     */
    getText(key) {
        if (window.i18n && typeof window.i18n.getText === 'function') {
            return window.i18n.getText(key);
        }
        return key;
    }
    
    /**
     * 发送错误到监控服务
     */
    sendToErrorService(errorInfo) {
        // 这里可以集成第三方错误监控服务
        // 例如：Sentry, LogRocket, Bugsnag等
        
        try {
            // 示例：发送到自定义错误收集端点
            if (window.location.hostname !== 'localhost') {
                fetch('/api/errors', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(errorInfo)
                }).catch(() => {
                    // 静默处理发送失败
                });
            }
        } catch (error) {
            // 静默处理错误发送失败
        }
    }
    
    /**
     * 清理错误历史
     */
    cleanupErrorHistory() {
        const now = Date.now();
        const cutoff = now - (24 * 60 * 60 * 1000); // 24小时前
        
        // 清理旧的错误记录
        this.errorHistory = this.errorHistory.filter(error => 
            new Date(error.timestamp).getTime() > cutoff
        );
        
        // 清理旧的错误计数
        for (const [key, value] of this.errorCounts.entries()) {
            const timestamp = parseInt(key.split('_')[1]);
            if (timestamp < cutoff) {
                this.errorCounts.delete(key);
            }
        }
    }
    
    /**
     * 获取错误统计
     */
    getErrorStats() {
        const stats = {
            totalErrors: this.errorHistory.length,
            errorsByType: {},
            recentErrors: 0
        };
        
        const now = Date.now();
        const recentCutoff = now - (60 * 60 * 1000); // 1小时前
        
        this.errorHistory.forEach(error => {
            // 按类型统计
            stats.errorsByType[error.type] = (stats.errorsByType[error.type] || 0) + 1;
            
            // 统计最近错误
            if (new Date(error.timestamp).getTime() > recentCutoff) {
                stats.recentErrors++;
            }
        });
        
        return stats;
    }
}

// 创建全局错误处理器实例
window.errorHandler = new ErrorHandler();

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorHandler;
}