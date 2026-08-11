# 公网二维码显示系统

## 📋 概述

这是一个动态的公网二维码产品信息显示系统，用于替换原有的硬编码版本。系统能够根据URL参数动态加载不同产品的JSON数据，并以移动端友好的界面展示产品信息。

## 🎯 主要特性

- **动态数据加载**：根据URL参数 `?id=产品ID` 动态获取对应的JSON文件
- **移动端优化**：响应式设计，适配各种屏幕尺寸
- **多语言支持**：中英文界面切换
- **错误处理**：完善的错误提示和重试机制
- **性能优化**：快速加载，流畅体验
- **安全性**：多层安全防护，输入验证，XSS防护，请求频率限制

## 📁 文件结构

```
qr_public_files/
├── qr_public.html          # 主HTML文件（替换服务器上的同名文件）
├── css/
│   └── mobile.css          # 移动端优化样式
├── js/
│   ├── main.js            # 主要逻辑
│   ├── i18n.js            # 国际化支持
│   ├── error-handler.js   # 错误处理模块
│   └── security-validator.js # 安全验证模块
├── test_qr_public.html    # 本地测试页面
├── docs/samples/web_tests/security_test.html     # 安全性测试页面（仓库内示例）
├── SECURITY.md            # 安全性文档
└── README.md              # 说明文档（本文件）
```

## 🚀 部署步骤

### 1. 备份现有文件
```bash
# 在服务器上备份现有的qr_public.html
cp /path/to/www.your-company-domain.com/data/qr/qr_public.html /path/to/backup/qr_public_old.html
```

### 2. 上传新文件
将以下文件上传到服务器对应位置：

```
服务器路径: http://www.your-company-domain.com/data/qr/

qr_public.html              → /data/qr/qr_public.html
css/mobile.css              → /data/qr/css/mobile.css
js/main.js                  → /data/qr/js/main.js
js/i18n.js                  → /data/qr/js/i18n.js
js/error-handler.js         → /data/qr/js/error-handler.js
js/security-validator.js    → /data/qr/js/security-validator.js
```

#### 快速部署方法
```bash
# 使用简化部署脚本
python simple_deploy.py

# 仅检查本地文件
python simple_deploy.py --check-only
```

### 3. 设置文件权限
```bash
# 确保文件可读
chmod 644 /path/to/www.your-company-domain.com/data/qr/qr_public.html
chmod 644 /path/to/www.your-company-domain.com/data/qr/css/mobile.css
chmod 644 /path/to/www.your-company-domain.com/data/qr/js/*.js
```

### 4. 验证部署
访问以下URL验证部署是否成功：
- `http://www.your-company-domain.com/data/qr/qr_public.html?id=A-DEMO-000008451`
- `http://www.your-company-domain.com/data/qr/qr_public.html?id=A-DEMO-000008452`

#### 自动化验证
```bash
# 运行完整的服务器验证
python server_verification.py

# 运行最终部署测试
python final_deployment_test.py

# 指定自定义服务器URL
python final_deployment_test.py http://your-server.com/data/qr
```

## 🔗 URL格式

新系统使用以下URL格式：

```
http://www.your-company-domain.com/data/qr/qr_public.html?id=产品ID&lang=语言代码
```

**参数说明：**
- `id`：产品ID（必需），对应JSON文件名（不含.json扩展名）
- `lang`：语言代码（可选），支持 `zh`（中文）和 `en`（英文）

**示例：**
- `http://www.your-company-domain.com/data/qr/qr_public.html?id=A-DEMO-000008451`
- `http://www.your-company-domain.com/data/qr/qr_public.html?id=A-DEMO-000008451&lang=en`

## 📱 支持的功能

### 基本功能
- [x] 动态加载产品JSON数据
- [x] 响应式移动端界面
- [x] 产品信息完整展示
- [x] 错误处理和重试机制

### 交互功能
- [x] 电话号码点击拨打
- [x] 官网链接点击跳转
- [x] 语言切换按钮
- [x] 重新加载按钮

### 用户体验
- [x] 加载动画和进度提示
- [x] 友好的错误提示信息
- [x] 流畅的触摸交互
- [x] 快速的页面加载

## 🧪 测试方法

### 本地测试
1. 打开 `test_qr_public.html` 文件
2. 点击测试链接验证各种场景
3. 使用浏览器开发者工具模拟移动设备

### 移动端测试
1. 生成包含新URL格式的二维码
2. 使用手机扫描二维码
3. 验证页面显示和交互功能

### 测试场景
- ✅ 正常产品数据加载
- ✅ 不存在的产品ID（404错误）
- ✅ 缺少ID参数（参数错误）
- ✅ 网络连接问题
- ✅ 中英文语言切换
- ✅ 不同屏幕尺寸适配

### 安全性测试
使用 `docs/samples/web_tests/security_test.html` 页面进行安全功能测试：
- 🔒 产品ID验证测试（有效/无效/恶意ID）
- 🌐 URL验证和域名白名单测试
- 📊 JSON数据验证和清理测试
- ⚡ 请求频率限制测试
- 🛡️ 安全事件监控测试

## 🔧 技术细节

### 数据获取
- 使用 `fetch()` API 获取JSON数据
- 支持超时和重试机制
- 缓存控制防止数据过期

### 错误处理
- 404错误：产品不存在
- 网络错误：连接失败或超时
- 数据错误：JSON格式错误
- 参数错误：缺少必需参数

### 性能优化
- 资源预加载（CSS、JS）
- 响应式图片处理
- 最小化DOM操作
- 合理的缓存策略

### 安全性
- 多层输入验证（产品ID、URL、JSON数据）
- XSS攻击防护和内容清理
- 请求频率限制和IP阻止
- CSP（内容安全策略）防护
- 恶意代码检测和阻止
- 安全事件监控和报告
- 安全的外部链接打开

详细安全信息请参考 [SECURITY.md](SECURITY.md) 文档。

## 🔄 与现有系统的兼容性

### JSON数据格式
新系统完全兼容现有的JSON数据格式，支持以下字段：

```json
{
  "company_name": "公司名称",
  "simplified_company_name": "简化公司名称",
  "product_type": "产品类型",
  "product_spec": "产品规格",
  "product_color": "产品颜色",
  "product_feature": "功能特性",
  "batch_number": "批次号",
  "production_date": "生产日期",
  "qr_sequence": "序列号",
  "standard": "执行标准",
  "distributor_name": "经销商",
  "issuer_name": "发行人",
  "plate_number": "物流车牌",
  "phone": "联系电话",
  "official_website": "官方网站"
}
```

### 自动同步
新系统与现有的JSON自动同步功能完全兼容，无需修改同步逻辑。

## 📞 技术支持

如果在部署或使用过程中遇到问题，请检查：

1. **文件路径**：确保所有文件都上传到正确位置
2. **文件权限**：确保Web服务器可以读取文件
3. **JSON数据**：确保对应的JSON文件存在且格式正确
4. **网络连接**：确保服务器网络连接正常

## 🔮 未来扩展

系统设计支持以下扩展功能：
- 更多语言支持
- 产品图片展示
- 二维码生成历史
- 访问统计分析
- 离线缓存支持