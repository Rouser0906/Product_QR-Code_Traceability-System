#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖检查脚本
在打包前检查所有必要的依赖是否已安装
"""

import sys
import importlib
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    print(f"   当前版本: Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor < 6:
        print("❌ 需要Python 3.6或更高版本")
        return False
    
    print("✅ Python版本满足要求")
    return True

def check_required_packages():
    """检查必需的Python包"""
    print("📦 检查Python包依赖...")
    
    required_packages = {
        'PyQt5': 'PyQt5',
        'qrcode': 'qrcode',
        'PIL': 'Pillow',
        'netifaces': 'netifaces',
        'watchdog': 'watchdog',
        'dotenv': 'python-dotenv',
        'PyInstaller': 'pyinstaller',
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            importlib.import_module(import_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            print(f"   ❌ {package_name} (缺失)")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有Python包依赖已满足")
    return True

def check_project_structure():
    """检查项目结构"""
    print("📁 检查项目结构...")
    
    required_files = [
        'main.py',
        'welcome.py', 
        'main_system.py',
        'requirements.txt',
        'modules/__init__.py',
        'utils/__init__.py',
        'assets/app_icon.ico',
    ]
    
    required_dirs = [
        'modules',
        'utils',
        'assets',
        'config',
        'cloud',
    ]
    
    project_root = Path(__file__).parent
    missing_items = []
    
    # 检查文件
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (缺失)")
            missing_items.append(file_path)
    
    # 检查目录
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"   ✅ {dir_path}/")
        else:
            print(f"   ❌ {dir_path}/ (缺失)")
            missing_items.append(f"{dir_path}/")
    
    if missing_items:
        print(f"\n❌ 缺少项目文件/目录: {', '.join(missing_items)}")
        return False
    
    print("✅ 项目结构完整")
    return True

def check_pyinstaller():
    """检查PyInstaller是否可用"""
    print("🔨 检查PyInstaller...")
    
    try:
        result = subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"   ✅ PyInstaller {version}")
            return True
        else:
            print("   ❌ PyInstaller不可用")
            return False
    except Exception as e:
        print(f"   ❌ PyInstaller检查失败: {e}")
        return False

def check_disk_space():
    """检查磁盘空间"""
    print("💾 检查磁盘空间...")
    
    try:
        import shutil
        total, used, free = shutil.disk_usage(Path(__file__).parent)
        
        free_gb = free // (1024**3)
        print(f"   可用空间: {free_gb} GB")
        
        if free_gb < 2:
            print("   ⚠️ 磁盘空间可能不足，建议至少2GB可用空间")
            return False
        
        print("   ✅ 磁盘空间充足")
        return True
        
    except Exception as e:
        print(f"   ⚠️ 无法检查磁盘空间: {e}")
        return True  # 不阻止打包

def main():
    """主检查函数"""
    print("=" * 60)
    print("🔍 示例集团多功能数智系统 - 打包依赖检查")
    print("=" * 60)
    
    checks = [
        ("Python版本", check_python_version),
        ("Python包依赖", check_required_packages),
        ("项目结构", check_project_structure),
        ("PyInstaller", check_pyinstaller),
        ("磁盘空间", check_disk_space),
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        print(f"\n{name}检查:")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有检查通过！可以开始打包了。")
        print("运行以下命令开始打包:")
        print("python build_ZY_PT-QRC.py")
    else:
        print("❌ 有检查项未通过，请先解决问题再打包。")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())