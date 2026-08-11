import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from PIL import Image, ImageDraw, ImageFont
import hashlib
import hmac
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import base64
from utils.security import security_manager
from utils.logger import log_info, log_error
from utils.config import config_manager

class QRSecurityManager:
    """二维码安全管理器"""
    
    def __init__(self):
        self.secret_key = secrets.token_urlsafe(32)
        self.config = config_manager.get_qr_config()
    
    def generate_secure_qr_data(self, data: Dict[str, Any], 
                              expiry_hours: int = 8760) -> str:
        """生成安全的二维码数据"""
        try:
            # 添加时间戳和过期时间
            secure_data = {
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=expiry_hours)).isoformat(),
                'version': '2.0',
                'nonce': secrets.token_urlsafe(16)
            }
            
            # 生成签名
            data_str = json.dumps(secure_data, sort_keys=True)
            signature = hmac.new(
                self.secret_key.encode(),
                data_str.encode(),
                hashlib.sha256
            ).hexdigest()
            
            secure_data['signature'] = signature
            
            # 编码为base64字符串
            encoded_data = base64.urlsafe_b64encode(
                json.dumps(secure_data).encode()
            ).decode()
            
            return encoded_data
            
        except Exception as e:
            log_error(f"生成安全二维码数据失败: {str(e)}")
            raise
    
    def verify_qr_data(self, encoded_data: str) -> Dict[str, Any]:
        """验证二维码数据"""
        try:
            # 解码数据
            decoded_data = json.loads(
                base64.urlsafe_b64decode(encoded_data.encode()).decode()
            )
            
            # 检查过期时间
            expires_at = datetime.fromisoformat(decoded_data['expires_at'])
            if datetime.now() > expires_at:
                return {'valid': False, 'error': '二维码已过期'}
            
            # 验证签名
            signature = decoded_data.pop('signature')
            data_str = json.dumps(decoded_data, sort_keys=True)
            expected_signature = hmac.new(
                self.secret_key.encode(),
                data_str.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return {'valid': False, 'error': '数据签名无效'}
            
            return {
                'valid': True,
                'data': decoded_data['data'],
                'timestamp': decoded_data['timestamp'],
                'expires_at': decoded_data['expires_at']
            }
            
        except Exception as e:
            log_error(f"验证二维码数据失败: {str(e)}")
            return {'valid': False, 'error': str(e)}
    
    def generate_qr_with_watermark(self, data: str, 
                                 watermark_text: str = "防伪水印",
                                 options: Dict[str, Any] = None) -> Image.Image:
        """生成带水印的二维码"""
        try:
            if options is None:
                options = {}
            
            # 配置参数
            qr = qrcode.QRCode(
                version=options.get('version', 1),
                error_correction=self._get_error_correction(options.get('error_correction', 'M')),
                box_size=options.get('box_size', 10),
                border=options.get('border', self.config.get('border', 4))
            )
            
            qr.add_data(data)
            qr.make(fit=True)
            
            # 生成二维码图像
            img = qr.make_image(fill_color=options.get('fill_color', 'black'),
                              back_color=options.get('back_color', 'white'))
            
            # 添加水印
            if watermark_text:
                img = self._add_watermark(img, watermark_text, options)
            
            return img
            
        except Exception as e:
            log_error(f"生成带水印二维码失败: {str(e)}")
            raise
    
    def _get_error_correction(self, level: str) -> int:
        """获取错误纠正级别"""
        levels = {
            'L': ERROR_CORRECT_L,
            'M': ERROR_CORRECT_M,
            'Q': ERROR_CORRECT_Q,
            'H': ERROR_CORRECT_H
        }
        return levels.get(level.upper(), ERROR_CORRECT_M)
    
    def _add_watermark(self, img: Image.Image, text: str, 
                      options: Dict[str, Any]) -> Image.Image:
        """添加水印"""
        try:
            # 创建透明层
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # 设置字体
            font_size = options.get('watermark_font_size', 20)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # 计算文本位置
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (img.width - text_width) // 2
            y = (img.height - text_height) // 2
            
            # 添加半透明文本
            text_color = options.get('watermark_color', (128, 128, 128, 128))
            draw.text((x, y), text, font=font, fill=text_color)
            
            # 合并图像
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            result = Image.alpha_composite(img, overlay)
            return result.convert('RGB')
            
        except Exception as e:
            log_error(f"添加水印失败: {str(e)}")
            return img
    
    def generate_batch_qr_codes(self, data_list: List[Dict[str, Any]], 
                              options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """批量生成二维码"""
        try:
            results = []
            
            for i, data in enumerate(data_list):
                try:
                    # 生成安全数据
                    secure_data = self.generate_secure_qr_data(data)
                    
                    # 生成二维码
                    img = self.generate_qr_with_watermark(secure_data, f"批次 {i+1}", options)
                    
                    # 保存二维码
                    filename = f"qr_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    filepath = os.path.join(options.get('output_dir', './output'), filename)
                    
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    img.save(filepath, quality=self.config.get('quality', 95))
                    
                    results.append({
                        'index': i + 1,
                        'filename': filename,
                        'filepath': filepath,
                        'data': data,
                        'qr_data': secure_data,
                        'success': True
                    })
                    
                except Exception as e:
                    results.append({
                        'index': i + 1,
                        'error': str(e),
                        'success': False
                    })
            
            log_info(f"批量生成二维码完成: 成功 {sum(1 for r in results if r['success'])} 个")
            return results
            
        except Exception as e:
            log_error(f"批量生成二维码失败: {str(e)}")
            raise
    
    def generate_product_qr(self, product_data: Dict[str, Any], 
                          options: Dict[str, Any] = None) -> Dict[str, Any]:
        """生成产品二维码"""
        try:
            if options is None:
                options = {}
            
            # 产品数据
            qr_data = {
                'type': 'product',
                'product_id': product_data.get('id'),
                'product_name': product_data.get('name'),
                'company': product_data.get('company'),
                'batch_number': product_data.get('batch_number'),
                'production_date': product_data.get('production_date'),
                'expiry_date': product_data.get('expiry_date'),
                'qr_code': product_data.get('qr_sequence')
            }
            
            # 生成安全二维码数据
            secure_data = self.generate_secure_qr_data(
                qr_data, 
                options.get('expiry_hours', 8760)
            )
            
            # 生成二维码
            img = self.generate_qr_with_watermark(
                secure_data,
                options.get('watermark', '产品溯源'),
                options
            )
            
            return {
                'qr_data': secure_data,
                'qr_image': img,
                'product_data': qr_data,
                'expires_at': (datetime.now() + timedelta(hours=options.get('expiry_hours', 8760))).isoformat()
            }
            
        except Exception as e:
            log_error(f"生成产品二维码失败: {str(e)}")
            raise
    
    def verify_product_qr(self, qr_code_data: str) -> Dict[str, Any]:
        """验证产品二维码"""
        try:
            result = self.verify_qr_data(qr_code_data)
            
            if result['valid']:
                product_data = result['data']
                
                # 验证产品类型
                if product_data.get('type') != 'product':
                    return {'valid': False, 'error': '无效的二维码类型'}
                
                return {
                    'valid': True,
                    'product_info': product_data,
                    'verified_at': datetime.now().isoformat(),
                    'expires_at': result['expires_at']
                }
            else:
                return result
                
        except Exception as e:
            log_error(f"验证产品二维码失败: {str(e)}")
            return {'valid': False, 'error': str(e)}
    
    def generate_tracking_qr(self, tracking_data: Dict[str, Any], 
                           options: Dict[str, Any] = None) -> Dict[str, Any]:
        """生成物流追踪二维码"""
        try:
            if options is None:
                options = {}
            
            # 物流数据
            qr_data = {
                'type': 'tracking',
                'tracking_id': tracking_data.get('tracking_id'),
                'order_number': tracking_data.get('order_number'),
                'logistics_company': tracking_data.get('logistics_company'),
                'vehicle_plate': tracking_data.get('vehicle_plate'),
                'driver_name': tracking_data.get('driver_name'),
                'current_location': tracking_data.get('current_location'),
                'status': tracking_data.get('status'),
                'estimated_arrival': tracking_data.get('estimated_arrival')
            }
            
            # 生成安全二维码数据
            secure_data = self.generate_secure_qr_data(
                qr_data,
                options.get('expiry_hours', 168)  # 物流二维码有效期较短
            )
            
            # 生成二维码
            img = self.generate_qr_with_watermark(
                secure_data,
                options.get('watermark', '物流追踪'),
                options
            )
            
            return {
                'qr_data': secure_data,
                'qr_image': img,
                'tracking_data': qr_data,
                'expires_at': (datetime.now() + timedelta(hours=options.get('expiry_hours', 168))).isoformat()
            }
            
        except Exception as e:
            log_error(f"生成物流追踪二维码失败: {str(e)}")
            raise
    
    def get_qr_info(self, qr_image: Image.Image) -> Dict[str, Any]:
        """获取二维码信息"""
        try:
            import pyzbar.pyzbar as pyzbar
            
            decoded_objects = pyzbar.decode(qr_image)
            
            if not decoded_objects:
                return {'success': False, 'error': '无法识别二维码'}
            
            qr_data = decoded_objects[0].data.decode('utf-8')
            
            # 尝试验证数据
            verification_result = self.verify_qr_data(qr_data)
            
            return {
                'success': True,
                'raw_data': qr_data,
                'verification': verification_result,
                'data_type': 'secure' if verification_result['valid'] else 'plain',
                'decoded_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            log_error(f"获取二维码信息失败: {str(e)}")
            return {'success': False, 'error': str(e)}

# 全局二维码安全管理器
qr_security_manager = QRSecurityManager()