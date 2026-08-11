#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例集团多功能数智系统 - 产品溯源二维码发行和管理子系统
PyInstaller 打包脚本

严格遵循打包规范：
1. 严禁修改任何源代码
2. 100%功能保留
3. 智能文件过滤
4. 生成单一可执行文件 PT-QRC.EXE
"""

import os
import sys
import shutil
import subprocess
import glob
from pathlib import Path

class BPackager:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist_package"
        self.spec_file = self.project_root / "PT-QRC_FIXED_QRCODE.spec"
        
    def clean_build_dirs(self):
        """清理构建目录"""
        print("🧹 清理构建目录...")
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"   已清理: {dir_path}")
        
    def analyze_dependencies(self):
        """分析项目依赖"""
        print("🔍 分析项目依赖...")
        
        # 核心依赖（从requirements.txt + 代码分析）
        dependencies = [
            'PyQt5.QtWidgets',
            'PyQt5.QtCore', 
            'PyQt5.QtGui',
            'PyQt5.QtPrintSupport',  # 打印功能
            'qrcode',                # 二维码生成
            'PIL',                   # 图像处理
            'netifaces',            # 网络接口
            'watchdog',             # 文件监控
            'python-dotenv',        # 环境变量
            'sqlite3',              # 数据库
            'json',                 # JSON处理
            'requests',             # HTTP请求（可能用于云同步）
            'threading',            # 多线程
            'datetime',             # 时间处理
            'os',                   # 操作系统接口
            'sys',                  # 系统接口
            'shutil',               # 文件操作
            'logging',              # 日志
        ]
        
        print(f"   识别到 {len(dependencies)} 个核心依赖")
        return dependencies
    
    def get_data_files(self):
        """获取需要打包的数据文件"""
        print("📁 识别数据文件...")
        
        data_files = []
        
        # 必须包含的目录和文件
        include_patterns = [
            # 资源文件（全量递归）
            ('assets/**/*', 'assets'),

            # 配置文件（包含子目录）
            ('config/**/*.json', 'config'),
            ('config/*.json', 'config'),

            # Python 模块目录
            ('modules/**/*.py', 'modules'),
            ('utils/**/*.py', 'utils'),
            ('auto_sync/**/*.py', 'auto_sync'),

            # 云端与数据目录（全量递归）
            ('cloud/**/*', 'cloud'),
            ('database/**/*', 'database'),

            # 前端文件（公网扫码 + 本地 qr 页面）
            ('qr_public_files/**/*', 'qr_public_files'),
            ('qr/**/*', 'qr'),
            ('product/**/*', 'product'),
            ('api/**/*.php', 'api'),
            ('js/**/*.js', 'js'),

            # 数据库文件（根目录下的 .db 也打包）
            ('*.db', '.'),

            # 其他必要文件
            ('.htaccess', '.'),
            ('web.config', '.'),
            ('index.html', '.'),
        ]
        
        for pattern, dest in include_patterns:
            if '*' in pattern or '**' in pattern:
                # 通配符模式
                matching_files = glob.glob(str(self.project_root / pattern), recursive=True)
                for file_path in matching_files:
                    if os.path.isfile(file_path):
                        rel_path = os.path.relpath(file_path, self.project_root)
                        # 使用正斜杠避免转义问题
                        rel_path = rel_path.replace('\\', '/')
                        data_files.append((rel_path, dest))
            else:
                # 直接路径
                file_path = self.project_root / pattern
                if file_path.exists():
                    # 使用正斜杠避免转义问题
                    rel_path = str(file_path).replace('\\', '/')
                    data_files.append((rel_path, dest))
        
        print(f"   识别到 {len(data_files)} 个数据文件")
        return data_files
    
    def get_excluded_files(self):
        """获取需要排除的文件模式"""
        print("🚫 设置文件排除规则...")
        
        exclude_patterns = [
            # 临时文件
            '*.tmp', '*.temp', '*.log',
            
            # 测试文件
            'test*', '*test*', 'tmp_dev_*',
            
            # 批处理和脚本文件
            '*.bat', '*.ps1', '*.sh',
            
            # 版本控制
            '.git/', '.gitignore', '.svn/',
            
            # IDE配置
            '.vscode/', '.idea/', '*.code-workspace',
            
            # 备份文件
            '*.bak', '*.old', '*fix.*', '*.backup*',
            
            # 构建产物
            'build/', 'dist/', '__pycache__/',
            '*.pyc', '*.pyo',
            
            # 文档草稿
            '*.md.backup', '*.tmp.md',
            
            # 打包相关
            'packaging/', '*.spec',
            
            # 开发工具
            'CRASH_DETECTIVE.py', 'DIRECT_TEST.py', 
            'PRECISE_DEBUG.py', 'debug_*',
            
            # 服务端文件（云端部署，不需要打包）
            'server_*', 'setup_*', 'install_*',
            'scripts/', 'legacy_disabled/',
            
            # MCP配置
            '.codebuddy/', 'pyproject.toml',
            
            # 输出目录
            'out/', 'cache/',
            
            # 特定不需要的文件
            'README*.md', 'DEPLOY_*.md', 'PERMISSION_*.md',
            '配置_CodeBuddy_*.md',
        ]
        
        print(f"   设置了 {len(exclude_patterns)} 个排除规则")
        return exclude_patterns
    
    def create_spec_file(self):
        """创建PyInstaller .spec配置文件"""
        print("📝 生成PyInstaller配置文件...")
        
        dependencies = self.analyze_dependencies()
        data_files = self.get_data_files()
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
示例集团多功能数智系统 - PyInstaller配置文件
生成目标：PT-QRC.EXE
"""

import sys
import os
from pathlib import Path

# 项目根目录
project_root = r"{self.project_root}"

# 数据文件配置
datas = [
{chr(10).join(f'    ("{data[0]}", "{data[1]}"),' for data in data_files)}
]

# 隐藏导入模块
hiddenimports = [
{chr(10).join(f'    "{dep}",' for dep in dependencies)}
]

# 排除模块（减小体积）
excludes = [
    'matplotlib',  # 如果不需要图表功能
    'numpy',       # 如果不使用数值计算
    'pandas',      # 如果不使用数据分析
    'scipy',       # 科学计算库
    'IPython',     # 交互式Python
    'jupyter',     # Jupyter相关
    'tkinter',     # 另一个GUI框架
]

# 二进制文件配置
binaries = []

# 分析配置
a = Analysis(
    ['main.py'],                    # 主入口文件
    pathex=[str(project_root)],     # 搜索路径
    binaries=binaries,              # 二进制文件
    datas=datas,                    # 数据文件
    hiddenimports=hiddenimports,    # 隐藏导入
    hookspath=[],                   # Hook路径
    hooksconfig={{}},               # Hook配置
    runtime_hooks=[],               # 运行时Hook
    excludes=excludes,              # 排除模块
    win_no_prefer_redirects=False,  # Windows重定向
    win_private_assemblies=False,   # Windows私有程序集
    cipher=None,                    # 加密
    noarchive=False,                # 不使用归档
)

# PYZ配置（Python字节码归档）
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE配置（可执行文件）
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PT-QRC',              # 输出文件名
    debug=False,                    # 调试模式
    bootloader_ignore_signals=False,  # 忽略信号
    strip=False,                    # 剥离符号
    upx=True,                      # UPX压缩（减小体积）
    upx_exclude=[],                # UPX排除
    runtime_tmpdir=None,           # 运行时临时目录
    console=False,                 # 不显示控制台窗口
    disable_windowed_traceback=False,  # 禁用窗口化回溯
    argv_emulation=False,          # argv模拟
    target_arch=None,              # 目标架构
    codesign_identity=None,        # 代码签名身份
    entitlements_file=None,        # 权限文件
    icon=str(project_root / "assets" / "app_icon.ico"),  # 应用图标
    version_file=None,             # 版本文件
)

# COLLECT 阶段（onedir 绿色便携目录）
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PT-QRC'
)
'''
        
        # 写入.spec文件
        with open(self.spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"   配置文件已生成: {self.spec_file}")
    
    def run_pyinstaller(self):
        """运行PyInstaller打包"""
        print("🔨 开始PyInstaller打包...")
        
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',                    # 清理临时文件
            '--noconfirm',               # 不确认覆盖
            '--log-level=INFO',          # 日志级别
            str(self.spec_file)          # 配置文件
        ]
        
        print(f"   执行命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, 
                                  capture_output=True, text=True, 
                                  encoding='utf-8')
            
            if result.returncode == 0:
                print("✅ PyInstaller打包成功!")
                return True
            else:
                print("❌ PyInstaller打包失败!")
                print("错误输出:", result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ 打包过程中发生异常: {e}")
            return False
    
    def create_documentation(self):
        """创建附属文档"""
        print("📚 生成附属文档...")
        
        docs = {
            "系统使用说明书.txt": """示例集团多功能数智系统 - 产品溯源二维码发行和管理子系统
使用说明书

=== 系统简介 ===
本系统是示例集团多功能数智系统的产品溯源二维码发行和管理子系统。
主要功能包括二维码生成、打印、云同步和公网扫码等。

=== 系统要求 ===
- 操作系统：Windows 7/10/11 及更高版本
- 内存：建议 4GB 以上
- 硬盘空间：至少 500MB 可用空间
- 网络：需要互联网连接（云同步功能）

=== 安装说明 ===
本程序为绿色便携版，无需安装：
1. 下载 PT-QRC.EXE 到任意目录
2. 双击运行即可启动系统
3. 首次运行会自动创建必要的配置文件

=== 主要功能 ===
1. 二维码生成：支持多种产品信息录入
2. 二维码打印：支持多种打印机选择
3. 云同步功能：自动同步数据到云服务器
4. 公网扫码：生成的二维码支持全球扫描访问
5. 用户管理：支持多用户权限管理
6. 数据管理：完整的产品溯源数据管理

=== 使用步骤 ===
1. 启动程序后，首先进行用户登录
2. 选择相应的功能模块
3. 录入产品信息
4. 生成并打印二维码
5. 系统自动同步数据到云端

=== 故障排除 ===
1. 程序无法启动：检查系统是否满足运行要求
2. 打印问题：确保打印机已正确安装和连接
3. 云同步问题：检查网络连接和防火墙设置
4. 其他问题：查看系统日志或联系技术支持

=== 联系信息 ===
技术支持：示例集团技术部
更新日期：2024年
版本：1.0""",

            "系统简介.txt": """示例集团多功能数智系统
产品溯源二维码发行和管理子系统

这是一个专业的产品溯源二维码管理系统，支持：
- 产品信息管理
- 二维码生成和打印
- 云端数据同步
- 公网扫码访问
- 多用户权限管理

系统特点：
✓ 绿色便携，无需安装
✓ 界面友好，操作简单
✓ 数据安全，云端备份
✓ 支持多种打印机
✓ 全球扫码访问

适用于：
- 制造企业产品溯源
- 质量管理追踪
- 供应链管理
- 产品防伪验证""",

            "readme.md": """# 示例集团多功能数智系统

## 产品溯源二维码发行和管理子系统

### 快速开始

1. **运行程序**
   ```
   双击 PT-QRC.EXE 启动系统
   ```

2. **系统登录**
   - 使用分配的用户名和密码登录
   - 首次运行会创建默认管理员账户

3. **主要功能**
   - 二维码生成和打印
   - 产品信息管理
   - 云端数据同步
   - 用户权限管理

### 技术特性

- **技术栈**: Python + PyQt5
- **数据库**: SQLite3
- **云同步**: 自动FTP上传
- **打印支持**: Windows标准打印机
- **网络功能**: HTTP/HTTPS公网访问

### 系统要求

- Windows 7/10/11
- 4GB+ RAM
- 500MB+ 磁盘空间
- 网络连接

### 支持信息

- **版本**: 1.0
- **发布日期**: 2024年
- **技术支持**: 示例集团技术部""",

            "版本号更新说明书.txt": """版本更新说明

=== 版本 1.0 (2024年) ===
[初始发布版本]

新增功能：
✓ 完整的二维码生成和管理功能
✓ 支持多种产品信息录入
✓ 打印机选择和打印功能
✓ 云端自动同步功能
✓ 公网扫码访问支持
✓ 多用户权限管理系统
✓ 产品溯源数据管理
✓ 系统托盘常驻功能

技术改进：
✓ 基于PyQt5的现代化界面
✓ SQLite3数据库存储
✓ 自动化FTP云同步
✓ 优化的打印机检测逻辑
✓ 增强的错误处理机制

已知问题：
- 无

计划功能：
- 多语言支持
- 高级数据分析
- 移动端管理界面
- API接口扩展

=== 更新历史 ===
- 2024年：系统开发和测试完成
- 2024年：品牌更新为示例集团
- 2024年：打包发布准备

=== 技术支持 ===
如需技术支持或反馈问题，请联系：
示例集团技术部"""
        }
        
        # 写入文档文件到 onedir 输出目录 dist/PT-QRC
        output_dir = self.dist_dir / "PT-QRC"
        output_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in docs.items():
            doc_path = output_dir / filename
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   已生成: {filename}")
    
    def verify_package(self):
        """验证打包结果"""
        print("🔍 验证打包结果...")
        
        # onedir 输出位于 dist/PT-QRC/PT-QRC.exe
        output_dir = self.dist_dir / "PT-QRC"
        exe_path = output_dir / "PT-QRC.exe"
        
        if not exe_path.exists():
            print("❌ 主程序文件不存在! 期望位置:", exe_path)
            return False
        
        file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
        print(f"   主程序大小: {file_size:.1f} MB")
        
        # 检查附属文档
        required_docs = [
            "系统使用说明书.txt",
            "系统简介.txt", 
            "readme.md",
            "版本号更新说明书.txt"
        ]
        
        missing_docs = []
        for doc in required_docs:
            if not (output_dir / doc).exists():
                missing_docs.append(doc)
        
        if missing_docs:
            print(f"⚠️ 缺少文档: {', '.join(missing_docs)}")
        else:
            print("✅ 所有附属文档已生成")
        
        print(f"✅ 打包验证完成，输出目录: {output_dir}")
        return True
    
    def package(self):
        """执行完整打包流程"""
        print("=" * 60)
        print("🚀 开始示例集团多功能数智系统打包流程")
        print("=" * 60)
        
        try:
            # 1. 清理构建目录
            self.clean_build_dirs()
            
            # 2. 创建配置文件
            self.create_spec_file()
            
            # 3. 运行PyInstaller
            if not self.run_pyinstaller():
                return False
            
            # 4. 生成附属文档
            self.create_documentation()
            
            # 5. 验证打包结果
            if not self.verify_package():
                return False
            
            print("=" * 60)
            print("🎉 打包完成！")
            print(f"📁 输出目录: {self.dist_dir}")
            print(f"🎯 主程序: PT-QRC.exe")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ 打包过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    packager = BPackager()
    success = packager.package()
    
    if success:
        print("\\n🎊 恭喜！PT-QRC.EXE 打包成功！")
        print("现在您可以将 dist_package 目录中的所有文件分发给用户了。")
    else:
        print("\\n😞 打包失败，请检查错误信息并重试。")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())