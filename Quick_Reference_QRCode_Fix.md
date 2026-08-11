# 二维码模块修复快速参考手册

## 🚨 问题识别
**错误信息**: `No module named 'qrcode'`  
**场景**: PyInstaller打包后的EXE文件中qrcode模块无法导入

## ⚡ 快速解决方案

### 1. 检查环境
```bash
python -c "import qrcode; print('✓ qrcode可用')"
pip list | findstr qrcode
```

### 2. 使用修复版spec文件
复制以下配置到你的`.spec`文件：

```python
hiddenimports=[
    # PyQt5核心
    'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtPrintSupport',
    
    # QRCode必需模块
    'qrcode', 'qrcode.main', 'qrcode.image', 'qrcode.image.pil',
    'qrcode.util', 'qrcode.constants',
    
    # PIL图像处理
    'PIL', 'PIL.Image', 'PIL.ImageDraw',
    
    # 你的项目模块
    'modules.qr_print_widget', # 根据实际情况调整
],

excludes=[
    'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 
    'PySide2', 'PySide6', 'tkinter'
],
```

### 3. 重新打包
```bash
pyinstaller --clean --noconfirm your_app.spec
```

## 🔧 常见变体问题

| 错误信息 | 解决方案 |
|---------|---------|
| `No module named 'PIL'` | 添加`'PIL', 'PIL.Image'`到hiddenimports |
| `No module named 'qrcode.image.pil'` | 添加`'qrcode.image.pil'`到hiddenimports |
| Qt版本冲突 | 在excludes中排除不用的Qt版本 |

## ✅ 验证方法
1. 生成的EXE文件应该能正常启动
2. 二维码模块能够正常加载
3. 可以生成和显示二维码图像

## 📁 备用文件
- `PT-QRC_SIMPLE_FIX.spec` - 验证成功的完整配置
- `QRCode_Module_Fix_Technical_Documentation.md` - 详细技术文档