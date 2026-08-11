/**
 * 国际化支持模块
 * 提供中英文语言切换功能
 */

// 语言资源定义
const i18nResources = {
    zh: {
        // 页面标题和基础文本
        'page-title': '产品溯源信息 - [已脱敏城市]示例品牌B材料有限公司',
        'loading': '正在加载产品信息...',
        'product-info': '产品溯源信息',
        
        // 错误信息
        'error-title': '加载失败',
        'retry': '重新加载',
        'product-not-found': '产品信息未找到，请检查二维码是否正确',
        'network-error': '网络连接失败，请检查网络连接后重试',
        'data-error': '数据格式错误，请联系技术支持',
        'param-error': '参数错误，请使用正确的二维码扫描',
        'server-error': '服务器暂时不可用，请稍后重试',
        'network-timeout': '网络请求超时，请检查网络连接',
        'file-too-large': '文件过大，无法加载',
        'browser-not-supported': '浏览器不支持，请使用现代浏览器',
        'connection-lost': '网络连接已断开',
        'connection-restored': '网络连接已恢复',
        'loading-timeout': '加载超时，正在重试...',
        'max-retries-reached': '已达到最大重试次数，请检查网络连接',
        'cache-error': '缓存错误，正在清理...',
        'render-error': '页面渲染错误，请刷新页面',
        'validation-error': '数据验证失败，请联系技术支持',
        
        // 错误详情和支持
        'show-details': '显示详情',
        'hide-details': '隐藏详情',
        'suggested-solutions': '建议解决方案',
        'technical-support': '技术支持',
        'contact-support': '联系支持',
        
        // 详细错误说明
        'error-product-not-found-detail': '可能原因：\n• 二维码损坏或模糊\n• 产品信息尚未上传\n• 二维码格式不正确',
        'error-network-detail': '可能原因：\n• 网络连接不稳定\n• 服务器维护中\n• 防火墙阻止访问',
        'error-data-detail': '可能原因：\n• 数据文件损坏\n• 服务器配置错误\n• 文件格式不正确',
        'error-param-detail': '可能原因：\n• 二维码链接不完整\n• URL参数缺失\n• 扫码应用异常',
        
        // 解决方案提示
        'solution-check-qr': '请确认二维码清晰完整',
        'solution-check-network': '请检查网络连接',
        'solution-try-later': '请稍后重试',
        'solution-contact-support': '如问题持续，请联系技术支持',
        'solution-use-modern-browser': '请使用Chrome、Safari或Firefox等现代浏览器',
        
        // 联系信息
        'support-phone': '技术支持：(+86) 138 0000 0000',
        'support-email': '邮箱支持：support@your-company-domain.com',
        'support-website': '官方网站：www.your-company-domain.com',
        
        // 信息卡片标题
        'basic-info': '基本信息',
        'production-info': '生产信息',
        'sales-info': '销售信息',
        'contact-info': '联系信息',
        
        // 字段标签
        'company-name': '公司名称',
        'product-type': '产品类型',
        'product-spec': '产品规格',
        'product-color': '产品颜色',
        'product-feature': '功能特性',
        'batch-number': '批次号',
        'production-date': '生产日期',
        'qr-sequence': '序列号',
        'standard': '执行标准',
        'distributor': '经销商',
        'issuer': '发行人',
        'plate-number': '物流车牌',
        'phone': '联系电话',
        'website': '官网',
        
        // 操作按钮和文本
        'more-products': '如需查询更多产品，请访问官方网站',
        'visit-website': '进入官网',
        'verified': '扫码验证成功 · 正品保证 · 品质保证'
    },
    
    en: {
        // 页面标题和基础文本
        'page-title': 'Product Traceability - Dongguan Example Brand B Materials Co., Ltd.',
        'loading': 'Loading product information...',
        'product-info': 'Product Traceability',
        
        // 错误信息
        'error-title': 'Loading Failed',
        'retry': 'Retry',
        'product-not-found': 'Product not found, please check if the QR code is correct',
        'network-error': 'Network connection failed, please check your connection and try again',
        'data-error': 'Data format error, please contact technical support',
        'param-error': 'Parameter error, please use the correct QR code',
        'server-error': 'Server temporarily unavailable, please try again later',
        'network-timeout': 'Network request timeout, please check your connection',
        'file-too-large': 'File too large to load',
        'browser-not-supported': 'Browser not supported, please use a modern browser',
        'connection-lost': 'Network connection lost',
        'connection-restored': 'Network connection restored',
        'loading-timeout': 'Loading timeout, retrying...',
        'max-retries-reached': 'Maximum retries reached, please check your connection',
        'cache-error': 'Cache error, cleaning up...',
        'render-error': 'Page rendering error, please refresh the page',
        'validation-error': 'Data validation failed, please contact technical support',
        
        // 错误详情和支持
        'show-details': 'Show Details',
        'hide-details': 'Hide Details',
        'suggested-solutions': 'Suggested Solutions',
        'technical-support': 'Technical Support',
        'contact-support': 'Contact Support',
        
        // 详细错误说明
        'error-product-not-found-detail': 'Possible causes:\n• QR code damaged or blurry\n• Product information not uploaded yet\n• Incorrect QR code format',
        'error-network-detail': 'Possible causes:\n• Unstable network connection\n• Server under maintenance\n• Firewall blocking access',
        'error-data-detail': 'Possible causes:\n• Data file corrupted\n• Server configuration error\n• Incorrect file format',
        'error-param-detail': 'Possible causes:\n• Incomplete QR code link\n• Missing URL parameters\n• QR scanner app error',
        
        // 解决方案提示
        'solution-check-qr': 'Please ensure QR code is clear and complete',
        'solution-check-network': 'Please check your network connection',
        'solution-try-later': 'Please try again later',
        'solution-contact-support': 'If the problem persists, please contact technical support',
        'solution-use-modern-browser': 'Please use modern browsers like Chrome, Safari, or Firefox',
        
        // 联系信息
        'support-phone': 'Technical Support: (+86) 138 0000 0000',
        'support-email': 'Email Support: support@your-company-domain.com',
        'support-website': 'Official Website: www.your-company-domain.com',
        
        // 信息卡片标题
        'basic-info': 'Basic Information',
        'production-info': 'Production Information',
        'sales-info': 'Sales Information',
        'contact-info': 'Contact Information',
        
        // 字段标签
        'company-name': 'Company Name',
        'product-type': 'Product Type',
        'product-spec': 'Specifications',
        'product-color': 'Color',
        'product-feature': 'Features',
        'batch-number': 'Batch Number',
        'production-date': 'Production Date',
        'qr-sequence': 'Serial Number',
        'standard': 'Standard',
        'distributor': 'Distributor',
        'issuer': 'Issuer',
        'plate-number': 'License Plate',
        'phone': 'Phone',
        'website': 'Website',
        
        // 操作按钮和文本
        'more-products': 'For more products, please visit our official website',
        'visit-website': 'Visit Website',
        'verified': 'QR Code Verified · Authentic Product · Quality Guaranteed'
    }
};

// 国际化管理类
class I18nManager {
    constructor() {
        this.currentLanguage = 'zh'; // 默认中文
        this.resources = i18nResources;
        this.init();
    }
    
    /**
     * 初始化国际化系统
     */
    init() {
        // 检测语言优先级：URL参数 > 本地存储 > 浏览器语言 > 默认中文
        this.currentLanguage = this.detectLanguage();
        
        // 绑定语言切换按钮事件
        this.bindLanguageSwitcher();
        
        // 应用当前语言
        this.applyLanguage(this.currentLanguage);
        
        // 监听语言变化事件
        this.bindLanguageChangeEvents();
        
        console.log(`🌍 I18n initialized with language: ${this.currentLanguage}`);
    }
    
    /**
     * 检测用户语言偏好
     */
    detectLanguage() {
        // 1. 检查URL参数（最高优先级）
        const urlParams = new URLSearchParams(window.location.search);
        const langParam = urlParams.get('lang');
        if (langParam && this.resources[langParam]) {
            this.saveLanguagePreference(langParam);
            return langParam;
        }
        
        // 2. 检查本地存储的用户偏好
        const savedLang = this.getSavedLanguagePreference();
        if (savedLang && this.resources[savedLang]) {
            return savedLang;
        }
        
        // 3. 检查浏览器语言
        const browserLang = navigator.language || navigator.userLanguage;
        if (browserLang) {
            // 简化语言代码 (zh-CN -> zh, en-US -> en)
            const simpleLang = browserLang.split('-')[0].toLowerCase();
            if (this.resources[simpleLang]) {
                return simpleLang;
            }
        }
        
        // 4. 默认中文
        return 'zh';
    }
    
    /**
     * 绑定语言切换按钮事件
     */
    bindLanguageSwitcher() {
        const langButtons = document.querySelectorAll('.lang-btn');
        langButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetLang = e.target.getAttribute('data-lang');
                if (targetLang && this.resources[targetLang]) {
                    this.switchLanguage(targetLang);
                }
            });
        });
    }
    
    /**
     * 切换语言
     */
    switchLanguage(language) {
        if (this.resources[language]) {
            const oldLanguage = this.currentLanguage;
            this.currentLanguage = language;
            
            // 保存用户偏好
            this.saveLanguagePreference(language);
            
            // 应用新语言
            this.applyLanguage(language);
            this.updateLanguageSwitcher();
            
            // 更新URL参数（不刷新页面）
            const url = new URL(window.location);
            url.searchParams.set('lang', language);
            window.history.replaceState({}, '', url);
            
            // 触发语言变化事件
            this.dispatchLanguageChangeEvent(oldLanguage, language);
            
            console.log(`🌍 Language switched from ${oldLanguage} to ${language}`);
        }
    }
    
    /**
     * 应用语言到页面
     */
    applyLanguage(language) {
        const elements = document.querySelectorAll('[data-i18n]');
        elements.forEach(element => {
            const key = element.getAttribute('data-i18n');
            const text = this.getText(key, language);
            if (text) {
                // 根据元素类型设置文本
                if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                    element.placeholder = text;
                } else if (element.tagName === 'IMG') {
                    element.alt = text;
                } else {
                    element.textContent = text;
                }
            }
        });
        
        // 更新页面标题
        const titleText = this.getText('page-title', language);
        if (titleText) {
            document.title = titleText;
        }
        
        // 更新HTML lang属性
        document.documentElement.lang = language === 'zh' ? 'zh-CN' : 'en';
        
        this.updateLanguageSwitcher();
    }
    
    /**
     * 更新语言切换按钮状态
     */
    updateLanguageSwitcher() {
        const langButtons = document.querySelectorAll('.lang-btn');
        langButtons.forEach(btn => {
            const btnLang = btn.getAttribute('data-lang');
            if (btnLang === this.currentLanguage) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }
    
    /**
     * 获取指定语言的文本
     */
    getText(key, language = null) {
        const lang = language || this.currentLanguage;
        return this.resources[lang] && this.resources[lang][key] || key;
    }
    
    /**
     * 获取当前语言
     */
    getCurrentLanguage() {
        return this.currentLanguage;
    }
    
    /**
     * 格式化日期
     */
    formatDate(dateString, language = null) {
        const lang = language || this.currentLanguage;
        
        if (!dateString) return '-';
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return dateString;
            
            const options = {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            };
            
            if (lang === 'zh') {
                return date.toLocaleString('zh-CN', options);
            } else {
                return date.toLocaleString('en-US', options);
            }
        } catch (error) {
            console.warn('Date formatting error:', error);
            return dateString;
        }
    }
    
    /**
     * 格式化电话号码
     */
    formatPhone(phone, language = null) {
        if (!phone) return '-';
        
        // 如果已经是格式化的电话号码，直接返回
        if (phone.includes('(') || phone.includes('+')) {
            return phone;
        }
        
        // 简单的电话号码格式化
        const cleanPhone = phone.replace(/\D/g, '');
        if (cleanPhone.length === 11 && cleanPhone.startsWith('1')) {
            // 中国手机号格式化
            return `${cleanPhone.slice(0, 3)} ${cleanPhone.slice(3, 7)} ${cleanPhone.slice(7)}`;
        }
        
        return phone;
    }
    
    /**
     * 保存语言偏好到本地存储
     */
    saveLanguagePreference(language) {
        try {
            localStorage.setItem('qr_display_language', language);
        } catch (error) {
            console.warn('Failed to save language preference:', error);
        }
    }
    
    /**
     * 获取保存的语言偏好
     */
    getSavedLanguagePreference() {
        try {
            return localStorage.getItem('qr_display_language');
        } catch (error) {
            console.warn('Failed to get saved language preference:', error);
            return null;
        }
    }
    
    /**
     * 绑定语言变化事件监听
     */
    bindLanguageChangeEvents() {
        // 监听存储变化（多标签页同步）
        window.addEventListener('storage', (e) => {
            if (e.key === 'qr_display_language' && e.newValue !== this.currentLanguage) {
                this.switchLanguage(e.newValue);
            }
        });
        
        // 监听页面可见性变化，重新检测语言
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                const savedLang = this.getSavedLanguagePreference();
                if (savedLang && savedLang !== this.currentLanguage && this.resources[savedLang]) {
                    this.switchLanguage(savedLang);
                }
            }
        });
    }
    
    /**
     * 触发语言变化事件
     */
    dispatchLanguageChangeEvent(oldLanguage, newLanguage) {
        const event = new CustomEvent('languagechange', {
            detail: {
                oldLanguage: oldLanguage,
                newLanguage: newLanguage,
                timestamp: new Date().toISOString()
            }
        });
        
        window.dispatchEvent(event);
    }
    
    /**
     * 获取支持的语言列表
     */
    getSupportedLanguages() {
        return Object.keys(this.resources);
    }
    
    /**
     * 检查是否支持指定语言
     */
    isLanguageSupported(language) {
        return !!this.resources[language];
    }
    
    /**
     * 获取语言的本地化名称
     */
    getLanguageDisplayName(language) {
        const displayNames = {
            'zh': '中文',
            'en': 'English'
        };
        
        return displayNames[language] || language;
    }
    
    /**
     * 批量获取文本
     */
    getTexts(keys, language = null) {
        const lang = language || this.currentLanguage;
        const result = {};
        
        keys.forEach(key => {
            result[key] = this.getText(key, lang);
        });
        
        return result;
    }
    
    /**
     * 动态添加翻译文本
     */
    addTranslations(language, translations) {
        if (!this.resources[language]) {
            this.resources[language] = {};
        }
        
        Object.assign(this.resources[language], translations);
        
        // 如果是当前语言，重新应用
        if (language === this.currentLanguage) {
            this.applyLanguage(language);
        }
    }
    
    /**
     * 获取浏览器首选语言
     */
    getBrowserPreferredLanguage() {
        const languages = navigator.languages || [navigator.language || navigator.userLanguage];
        
        for (const lang of languages) {
            const simpleLang = lang.split('-')[0].toLowerCase();
            if (this.resources[simpleLang]) {
                return simpleLang;
            }
        }
        
        return 'zh'; // 默认中文
    }
    
    /**
     * 重新初始化（用于动态加载新的翻译资源后）
     */
    reinitialize() {
        this.applyLanguage(this.currentLanguage);
        this.updateLanguageSwitcher();
    }
}

// 创建全局国际化实例
window.i18n = new I18nManager();

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = I18nManager;
}