/**
 * 隐私合规的位置处理器
 */
class PrivacyCompliantLocationHandler {
    constructor(options = {}) {
        this.options = {
            timeout: options.timeout || 10000,
            showPrivacyNotice: options.showPrivacyNotice !== false,
            onSuccess: options.onSuccess || null,
            onError: options.onError || null,
            onDenied: options.onDenied || null,
            onTimeout: options.onTimeout || null
        };
        this.requestInProgress = false;
    }
    
    async requestLocation() {
        if (this.requestInProgress) return;
        this.requestInProgress = true;
        
        try {
            if (!navigator.geolocation) {
                throw new Error('Geolocation not supported');
            }
            
            if (this.options.showPrivacyNotice) {
                const consent = await this.showPrivacyNotice();
                if (!consent) {
                    this.handleDenied('User declined privacy notice');
                    return;
                }
            }
            
            await this.getCurrentPosition();
        } catch (error) {
            this.handleError(error);
        } finally {
            this.requestInProgress = false;
        }
    }
    
    async showPrivacyNotice() {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 10000; display: flex; align-items: center; justify-content: center; padding: 20px;';
            
            const content = document.createElement('div');
            content.style.cssText = 'background: white; border-radius: 15px; max-width: 500px; width: 100%; padding: 30px; text-align: center;';
            
            content.innerHTML = `
                <h3 style="margin: 0 0 20px 0;">🔒 位置信息使用说明</h3>
                <div style="text-align: left; margin: 20px 0;">
                    <p><strong>我们想要获取您的位置信息用于：</strong></p>
                    <ul>
                        <li>📍 为您推荐附近的服务商和门店</li>
                        <li>🚚 提供更准确的配送服务</li>
                        <li>📊 改善产品和服务质量</li>
                    </ul>
                    <p><strong>隐私保护承诺：</strong></p>
                    <ul>
                        <li>✅ 位置信息仅用于上述目的</li>
                        <li>✅ 不会与第三方分享您的精确位置</li>
                        <li>✅ 您可以随时拒绝或撤销授权</li>
                        <li>✅ 拒绝位置授权不影响产品查询功能</li>
                    </ul>
                </div>
                <div style="margin-top: 25px;">
                    <button id="decline-btn" style="padding: 12px 24px; margin: 0 10px; border: 2px solid #ddd; border-radius: 8px; background: #f8f9fa; color: #666; cursor: pointer;">暂不授权</button>
                    <button id="accept-btn" style="padding: 12px 24px; margin: 0 10px; border: none; border-radius: 8px; background: #4CAF50; color: white; cursor: pointer;">同意并继续</button>
                </div>
            `;
            
            modal.appendChild(content);
            document.body.appendChild(modal);
            
            content.querySelector('#accept-btn').onclick = () => {
                document.body.removeChild(modal);
                resolve(true);
            };
            
            content.querySelector('#decline-btn').onclick = () => {
                document.body.removeChild(modal);
                resolve(false);
            };
            
            setTimeout(() => {
                if (document.body.contains(modal)) {
                    document.body.removeChild(modal);
                    resolve(false);
                }
            }, 30000);
        });
    }
    
    async getCurrentPosition() {
        return new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const locationData = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        timestamp: position.timestamp
                    };
                    this.handleSuccess(locationData);
                    resolve(locationData);
                },
                (error) => {
                    this.handleGeolocationError(error);
                    reject(error);
                },
                {
                    enableHighAccuracy: false,
                    timeout: this.options.timeout,
                    maximumAge: 300000
                }
            );
        });
    }
    
    handleGeolocationError(error) {
        switch (error.code) {
            case error.PERMISSION_DENIED:
                this.handleDenied('User denied location access');
                break;
            case error.POSITION_UNAVAILABLE:
                this.handleError(new Error('Location unavailable'));
                break;
            case error.TIMEOUT:
                this.handleTimeout('Location request timed out');
                break;
            default:
                this.handleError(new Error('Unknown location error'));
                break;
        }
    }
    
    handleSuccess(locationData) {
        if (this.options.onSuccess) {
            this.options.onSuccess(locationData);
        }
    }
    
    handleDenied(reason) {
        if (this.options.onDenied) {
            this.options.onDenied(reason);
        }
    }
    
    handleTimeout(reason) {
        if (this.options.onTimeout) {
            this.options.onTimeout(reason);
        }
    }
    
    handleError(error) {
        if (this.options.onError) {
            this.options.onError(error);
        }
    }
}

if (typeof window !== 'undefined') {
    window.PrivacyCompliantLocationHandler = PrivacyCompliantLocationHandler;
}