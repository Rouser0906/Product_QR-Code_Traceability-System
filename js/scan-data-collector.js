/**
 * 扫码数据收集器
 * 用于收集用户扫码时的设备信息和位置数据
 */
class ScanDataCollector {
    constructor(qrCode, options = {}) {
        this.qrCode = qrCode;
        this.options = {
            apiUrl: options.apiUrl || '/api/scan_tracker.php',
            locationTimeout: options.locationTimeout || 10000, // 10秒超时
            enableLocation: options.enableLocation !== false, // 默认启用位置收集
            retryAttempts: options.retryAttempts || 3,
            retryDelay: options.retryDelay || 1000,
            debug: options.debug || false
        };

        this.scanData = {
            qr_code: this.qrCode,
            scan_time: new Date().toISOString().slice(0, 19).replace('T', ' '),
            device_info: '',
            screen_resolution: '',
            location: null
        };

        this.log('ScanDataCollector initialized for QR code:', this.qrCode);
    }

    /**
     * 开始收集扫码数据
     */
    async collect() {
        try {
            this.log('Starting data collection...');

            // 收集设备信息
            this.collectDeviceInfo();

            // 收集位置信息（异步，不阻塞）
            if (this.options.enableLocation) {
                this.collectLocationData();
            }

            // 延迟发送数据，给位置收集一些时间
            setTimeout(() => {
                this.sendData();
            }, 2000);

        } catch (error) {
            this.handleError('Data collection failed', error);
        }
    }

    /**
     * 收集设备信息
     */
    collectDeviceInfo() {
        try {
            // 基本设备信息
            this.scanData.device_info = navigator.userAgent || 'Unknown';

            // 屏幕分辨率
            if (screen.width && screen.height) {
                this.scanData.screen_resolution = `${screen.width}x${screen.height}`;
            }

            // 额外的设备信息
            const deviceDetails = {
                platform: navigator.platform || 'Unknown',
                language: navigator.language || 'Unknown',
                cookieEnabled: navigator.cookieEnabled,
                onLine: navigator.onLine,
                viewport: {
                    width: window.innerWidth || document.documentElement.clientWidth,
                    height: window.innerHeight || document.documentElement.clientHeight
                },
                colorDepth: screen.colorDepth || 'Unknown',
                pixelDepth: screen.pixelDepth || 'Unknown'
            };

            this.scanData.device_details = deviceDetails;
            this.log('Device info collected:', deviceDetails);

        } catch (error) {
            this.handleError('Failed to collect device info', error);
        }
    }

    /**
     * 收集位置数据
     */
    collectLocationData() {
        if (!navigator.geolocation) {
            this.log('Geolocation not supported');
            return;
        }

        this.log('Requesting location data...');

        const options = {
            enableHighAccuracy: true,
            timeout: this.options.locationTimeout,
            maximumAge: 300000 // 5分钟缓存
        };

        navigator.geolocation.getCurrentPosition(
            (position) => {
                this.scanData.location = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    altitude: position.coords.altitude,
                    altitudeAccuracy: position.coords.altitudeAccuracy,
                    heading: position.coords.heading,
                    speed: position.coords.speed,
                    timestamp: position.timestamp
                };

                this.log('Location data collected:', this.scanData.location);

                // 如果还没发送数据，现在发送
                if (!this.dataSent) {
                    this.sendData();
                }
            },
            (error) => {
                this.handleLocationError(error);
            },
            options
        );
    }

    /**
     * 处理位置错误
     */
    handleLocationError(error) {
        let errorMessage = 'Location error: ';

        switch (error.code) {
            case error.PERMISSION_DENIED:
                errorMessage += 'User denied the request for Geolocation.';
                break;
            case error.POSITION_UNAVAILABLE:
                errorMessage += 'Location information is unavailable.';
                break;
            case error.TIMEOUT:
                errorMessage += 'The request to get user location timed out.';
                break;
            default:
                errorMessage += 'An unknown error occurred.';
                break;
        }

        this.log(errorMessage);

        // 即使位置获取失败，也要发送其他数据
        if (!this.dataSent) {
            this.sendData();
        }
    }

    /**
     * 发送数据到后端API
     */
    async sendData(attempt = 1) {
        if (this.dataSent) {
            return; // 避免重复发送
        }

        try {
            this.log('Sending scan data (attempt ' + attempt + '):', this.scanData);

            const response = await fetch(this.options.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.scanData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.dataSent = true;
                this.log('Scan data sent successfully:', result);
                this.onSuccess(result);
            } else {
                throw new Error(result.error || 'Unknown API error');
            }

        } catch (error) {
            this.handleError('Failed to send scan data', error);

            // 重试机制
            if (attempt < this.options.retryAttempts) {
                this.log(`Retrying in ${this.options.retryDelay}ms...`);
                setTimeout(() => {
                    this.sendData(attempt + 1);
                }, this.options.retryDelay * attempt); // 指数退避
            } else {
                this.log('Max retry attempts reached. Giving up.');
                this.onError(error);
            }
        }
    }

    /**
     * 成功回调
     */
    onSuccess(result) {
        // 可以被子类重写或通过选项传入回调
        if (this.options.onSuccess) {
            this.options.onSuccess(result);
        }
    }

    /**
     * 错误回调
     */
    onError(error) {
        // 可以被子类重写或通过选项传入回调
        if (this.options.onError) {
            this.options.onError(error);
        }
    }

    /**
     * 错误处理
     */
    handleError(message, error) {
        const errorInfo = {
            message: message,
            error: error.message || error,
            timestamp: new Date().toISOString(),
            qrCode: this.qrCode
        };

        this.log('Error:', errorInfo);

        // 不让错误影响页面正常显示
        try {
            if (window.console && console.warn) {
                console.warn('ScanDataCollector:', errorInfo);
            }
        } catch (e) {
            // 忽略console错误
        }
    }

    /**
     * 日志输出
     */
    log(...args) {
        if (this.options.debug && window.console && console.log) {
            console.log('[ScanDataCollector]', ...args);
        }
    }

    /**
     * 静态方法：快速收集数据
     */
    static quickCollect(qrCode, options = {}) {
        const collector = new ScanDataCollector(qrCode, options);
        collector.collect();
        return collector;
    }
}

// 兼容性检查和polyfill
(function () {
    // 检查fetch支持
    if (!window.fetch) {
        console.warn('ScanDataCollector: fetch API not supported, data collection disabled');
        return;
    }

    // 检查Promise支持
    if (!window.Promise) {
        console.warn('ScanDataCollector: Promise not supported, data collection disabled');
        return;
    }

    // 导出到全局
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = ScanDataCollector;
    } else {
        window.ScanDataCollector = ScanDataCollector;
    }
})();

/**
 * 使用示例：
 * 
 * // 基本使用
 * const collector = new ScanDataCollector('A-DEMO-000000123');
 * collector.collect();
 * 
 * // 高级配置
 * const collector = new ScanDataCollector('A-DEMO-000000123', {
 *     apiUrl: '/api/scan_tracker.php',
 *     enableLocation: true,
 *     locationTimeout: 5000,
 *     debug: true,
 *     onSuccess: (result) => console.log('Success:', result),
 *     onError: (error) => console.error('Error:', error)
 * });
 * collector.collect();
 * 
 * // 快速使用
 * ScanDataCollector.quickCollect('A-DEMO-000000123', { debug: true });
 */