# 显式导入打印支持（确保运行时和打包时都可用）
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPageSetupDialog
# 二维码依赖
import qrcode
from PIL import Image
# 兜底：显式引入二维码依赖，触发PyInstaller收集
import qrcode
from PIL import Image
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QLineEdit, QTextEdit, QDateTimeEdit, QRadioButton, QButtonGroup,
    QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QToolTip, QFileDialog, QDialog, QCalendarWidget, QSpacerItem, QSizePolicy, QSpinBox
)
from PyQt5.QtCore import Qt, QDateTime, QTimer, QBuffer, QSizeF
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QPen, QImage, QBrush
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog, QPrinterInfo
import qrcode
from io import BytesIO
from PIL import Image
import re
import sqlite3
import os
import socket
from datetime import datetime
import csv
import json
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'qr_system.db')
from PyQt5.QtCore import Qt as QtCoreQt
from modules.searchable_combobox import SearchableComboBox
import logging
from utils.permissions import has_permission

# 加载全局QSS样式
def load_global_qss():
    try:
        # 获取当前文件所在目录的上级目录（项目根目录）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        qss_file_path = os.path.join(project_root, "qr_print.qss")
        
        if os.path.exists(qss_file_path):
            with open(qss_file_path, "r", encoding="utf-8") as f:
                qss_content = f.read()
                # 获取QApplication实例并设置全局样式
                app = QApplication.instance()
                if app and hasattr(app, 'setStyleSheet'):
                    app.setStyleSheet(qss_content)
                    print(f"成功加载QSS样式文件: {qss_file_path}")
                else:
                    print("未找到QApplication实例或实例不支持setStyleSheet，无法设置全局样式")
        else:
            print(f"QSS文件不存在: {qss_file_path}")
    except Exception as e:
        print(f"加载QSS样式文件失败: {e}")

class QRPrintWidget(QWidget):
    
    
    def save_qr_json_enhanced(self, qr_data, qr_sequence, data_dir, domain):
        """
        增强版JSON保存函数 - 防止0字节文件生成
        """
        import json
        import os
        import tempfile
        import time
        import shutil
        from datetime import datetime
        
        qr_code = qr_sequence
        filepath = os.path.join(data_dir, f"{qr_code}.json")
        json_save_success = False
        max_retries = 3
        
        # 数据完整性检查
        if not qr_data or not isinstance(qr_data, dict):
            print(f"[ERROR] 数据无效: {qr_data}")
            return False
        
        if not qr_data.get('qr_sequence'):
            print(f"[ERROR] 缺少关键字段 qr_sequence")
            return False
        
        # 确保目录存在
        try:
            os.makedirs(data_dir, exist_ok=True)
            if not os.path.exists(data_dir):
                raise Exception(f"目录创建失败: {data_dir}")
        except Exception as e:
            print(f"[ERROR] 目录创建失败: {e}")
            return False
        
        # 多次重试保存
        for attempt in range(max_retries):
            try:
                print(f"[RETRY] 尝试保存 (第{attempt+1}次): {filepath}")
                
                # 先保存到临时文件
                temp_file = filepath + ".tmp"
                
                # 写入临时文件
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(qr_data, f, ensure_ascii=False, indent=2)
                    f.flush()  # 强制刷新缓冲区
                    os.fsync(f.fileno())  # 强制写入磁盘
                
                # 验证临时文件
                if not os.path.exists(temp_file):
                    raise Exception("临时文件不存在")
                
                temp_size = os.path.getsize(temp_file)
                if temp_size == 0:
                    raise Exception("临时文件为0字节")
                
                # 验证JSON格式
                with open(temp_file, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                    if test_data.get('qr_sequence') != qr_sequence:
                        raise Exception("JSON内容验证失败")
                
                # 原子性移动文件
                if os.path.exists(filepath):
                    backup_path = filepath + f".backup.{int(time.time())}"
                    shutil.move(filepath, backup_path)
                    print(f"[BACKUP] 备份原文件: {backup_path}")
                
                shutil.move(temp_file, filepath)
                
                # 最终验证
                final_size = os.path.getsize(filepath)
                if final_size > 0:
                    logging.getLogger(__name__).debug(f"[SUCCESS] JSON保存成功: {filepath} ({final_size} bytes)")
                    json_save_success = True
                    break
                else:
                    raise Exception("最终文件为0字节")
                    
            except Exception as e:
                print(f"[ERROR] 第{attempt+1}次保存失败: {e}")
                
                # 清理临时文件
                temp_file = filepath + ".tmp"
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                
                if attempt < max_retries - 1:
                    time.sleep(0.1)  # 短暂等待后重试
                else:
                    # 最后尝试：保存到系统临时目录
                    try:
                        temp_dir = tempfile.gettempdir()
                        emergency_path = os.path.join(temp_dir, f"emergency_{qr_code}.json")
                        
                        with open(emergency_path, 'w', encoding='utf-8') as f:
                            json.dump(qr_data, f, ensure_ascii=False, indent=2)
                            f.flush()
                            os.fsync(f.fileno())
                        
                        if os.path.getsize(emergency_path) > 0:
                            print(f"[EMERGENCY] 紧急保存成功: {emergency_path}")
                            print(f"[EMERGENCY] 请手动移动到: {filepath}")
                            return True
                            
                    except Exception as emergency_error:
                        print(f"[ERROR] 紧急保存也失败: {emergency_error}")
        
        return json_save_success
    

    def __init__(self, parent=None, current_user=None):
        super().__init__(parent)
        self.setWindowTitle("二维码打印")
        self.setMinimumSize(1550, 900)
        # 保存当前用户信息
        self.current_user = current_user or {'username': 'guest', 'user_id': 0, 'employee_id': ''}
        # 在初始化时加载全局QSS
        load_global_qss()
        self.initUI()
        
        # 已删除5秒自动刷新定时器功能（根据用户要求简化系统）

    def initUI(self):
        # ========== 主布局 ========== 
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)
        
        # 左侧面板
        left_panel = QFrame()
        left_panel.setFixedWidth(1000)
        left_panel.setStyleSheet("border:2px solid #7bb1e0; border-radius:8px;")
        main_layout.addWidget(left_panel, 0, 0) # 修改：不再跨行
        main_layout.setColumnStretch(0, 0)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(18, 10, 18, 18)
        left_layout.setSpacing(0)  # 极致收紧分区间距
        
        # 绿色大标题
        title_label = QLabel("二维码信息选择")
        title_label.setProperty('role', 'title')
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #228b22; border: none; background: transparent; padding: 2px 0 0 0;")
        left_layout.addWidget(title_label)

        # --- 表单分组 - 左右等宽布局优化 ---
        form_group = QFrame()
        form_group.setStyleSheet("")
        form_layout = QGridLayout(form_group)
        
        # 设置列宽比例：左栏和右栏等宽，添加适当间距
        form_layout.setColumnStretch(0, 1)  # 左栏：列0 - 拉伸系数1
        form_layout.setColumnStretch(1, 0)  # 分隔间距：列1 - 固定宽度
        form_layout.setColumnStretch(2, 1)  # 右栏：列2 - 拉伸系数1
        
        # 确保所有可能的列都有明确的拉伸设置
        for i in range(3, 10):  # 扩展到更多列，确保完整覆盖
            form_layout.setColumnStretch(i, 0)
            
        # 设置列的最小宽度，确保左右栏平衡
        form_layout.setColumnMinimumWidth(0, 200)  # 左栏最小宽度
        form_layout.setColumnMinimumWidth(1, 20)   # 间距列固定宽度
        form_layout.setColumnMinimumWidth(2, 200)  # 右栏最小宽度
        
        form_layout.setHorizontalSpacing(20)  # 设置列间距为20px
        form_layout.setVerticalSpacing(8)     # 设置行间距为8px
        # 一体化表单项样式
        item_frame_style = "border:1.5px solid #7bb1e0; border-radius:6px;"
        label_style = "color:#1976d2;font-weight:bold;padding-left:10px;border:none;background:transparent;"
        combo_style = "font-weight:bold;padding-left:8px;"  # 移除border:none，让下拉框显示默认边框和下拉按钮
        edit_style = "border:none;background:transparent;font-weight:bold;padding-left:8px;"
        date_style = "border:none;background:transparent;font-weight:bold;padding-left:8px;"
        # 第一列标签和下拉框
        labels_col1 = ["公司名称", "部门名称", "二维码发行人", "产品种类", "产品规格", "产品特性", "产品颜色", "经销商名称"]
        self.combos_col1 = []
        for i, text in enumerate(labels_col1):
            item_frame = QFrame()
            item_frame.setStyleSheet(item_frame_style)
            item_frame.setFixedHeight(51)
            item_layout = QHBoxLayout(item_frame)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(0)
            label = QLabel(text)
            label.setFixedWidth(150)
            label.setStyleSheet(label_style)
            # 为二维码发行人使用SearchableComboBox
            if text == "二维码发行人":
                combo = SearchableComboBox()
            else:
                combo = QComboBox()
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            combo.setFixedHeight(48)
            combo.setMinimumWidth(180)
            # 移除最大宽度限制，让下拉框完全填满可用空间，下拉按钮紧贴右边框
            combo.setStyleSheet(combo_style)  # 应用下拉框样式
            self.combos_col1.append(combo)
            item_layout.addWidget(label)
            item_layout.addWidget(combo, 1)
            
            # 为公司名称添加LOGO显示
            if i == 0:  # 公司名称
                self.company_logo_label = QLabel()
                self.company_logo_label.setFixedSize(40, 40)
                self.company_logo_label.setScaledContents(True)
                self.company_logo_label.setStyleSheet(
                    "border: 1px solid #ddd; border-radius: 5px; background: white;"
                )
                item_layout.addWidget(self.company_logo_label)
            
            form_layout.addWidget(item_frame, i, 0, 1, 1)  # 左栏：只占用列0
        # 业务员信息下拉框，单独插入到物流车牌号上方
        item_frame = QFrame()
        item_frame.setStyleSheet(item_frame_style)
        item_frame.setFixedHeight(51)
        item_layout = QHBoxLayout(item_frame)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(0)
        label = QLabel("业务员信息")
        label.setFixedWidth(150)
        label.setStyleSheet(label_style)
        combo = QComboBox()
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        combo.setFixedHeight(48)
        combo.setMinimumWidth(180)
        # 移除最大宽度限制，让业务员信息下拉框完全填满可用空间
        combo.setStyleSheet(combo_style)  # 应用下拉框样式
        self.combos_col1.append(combo)
        item_layout.addWidget(label)
        item_layout.addWidget(combo, 1)
        form_layout.addWidget(item_frame, 0, 2, 1, 1)  # 业务员信息：只占用列2
        # 第二列标签和输入框
        labels_col2 = ["物流车牌号", "售后&客服电话", "二维码序号", "生产日期时间", "产品批次号"]
        self.widgets_col2 = []
        for i, text in enumerate(labels_col2):
            item_frame = QFrame()
            item_frame.setStyleSheet(item_frame_style)
            item_frame.setFixedHeight(53)  # 原为56
            item_layout = QHBoxLayout(item_frame)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(0)
            label = QLabel(text)
            label.setFixedWidth(150)
            label.setStyleSheet(label_style)
            if text == "物流车牌号":
                widget = QComboBox()
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                widget.setFixedHeight(48)
                widget.setMinimumWidth(180)
            elif "日期时间" in text:
                widget = QDateTimeEdit(QDateTime.currentDateTime())
                widget.setCalendarPopup(True)
                widget.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                widget.setStyleSheet(date_style + "padding-right:32px;")
                widget.setFixedHeight(48)
                widget.setMinimumWidth(180)
            else:
                widget = QLineEdit()
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                widget.setStyleSheet(edit_style + "padding-right:32px;")
                widget.setFixedHeight(48)
                widget.setMinimumWidth(180)
            self.widgets_col2.append(widget)
            item_layout.addWidget(label)
            item_layout.addWidget(widget, 1)
            form_layout.addWidget(item_frame, i + 1, 2, 1, 1)  # 右栏：向下错位一行，避免与“业务员信息”重叠
        # ---------------- 执行标准 整行 ----------------
        qty_frame = QFrame()
        qty_frame.setStyleSheet(item_frame_style)
        qty_frame.setFixedHeight(53)
        qty_layout = QHBoxLayout(qty_frame)
        qty_layout.setContentsMargins(0, 0, 0, 0)
        qty_layout.setSpacing(0)
        qty_label = QLabel("执行标准")
        qty_label.setFixedWidth(150)
        qty_label.setStyleSheet(label_style)
        self.quantity_edit = QLineEdit()
        self.quantity_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.quantity_edit.setStyleSheet(edit_style + "padding-right:32px;")
        self.quantity_edit.setFixedHeight(48)
        self.quantity_edit.setMinimumWidth(180)
        self.quantity_edit.setPlaceholderText("GB/T10801.2-2018")
        self.quantity_edit.setText("GB/T10801.2-2018")
        qty_layout.addWidget(qty_label)
        qty_layout.addWidget(self.quantity_edit, 1)

        form_layout.addWidget(qty_frame, len(labels_col2) + 1, 2, 1, 1)  # 执行标准：置于“物流车牌号”等之后一行

        left_layout.addWidget(form_group)
        left_layout.addSpacing(6)

        # --- 备注分组（带圆角方框包裹） ---
        remark_outer = QFrame()
        remark_outer.setStyleSheet("border:2px solid #7bb1e0; border-radius:8px;")
        remark_outer_layout = QHBoxLayout(remark_outer)
        remark_outer_layout.setContentsMargins(8, 2, 8, 2)
        remark_outer_layout.setSpacing(0)
        remark_label = QLabel("备注:")
        remark_label.setFixedWidth(150)
        remark_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        remark_label.setStyleSheet("padding:0;margin:0;font-size:14px;font-weight:bold;color:#1976d2; border:none;background:transparent;")
        remark_label.setFixedHeight(32)
        self.remark_edit = QLineEdit()
        self.remark_edit.setObjectName('remark_edit')
        self.remark_edit.setFixedHeight(32)
        self.remark_edit.setStyleSheet("border:none;background:transparent;padding:0 4px;font-size:14px;")
        remark_outer_layout.addWidget(remark_label)
        remark_outer_layout.addWidget(self.remark_edit, 1)
        left_layout.addWidget(remark_outer)

        # 分割线3
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Sunken)
        line3.setStyleSheet("color:#b7b7e0;height:2px;margin:8px 0;")
        left_layout.addWidget(line3)

        # --- 按钮区，横向均匀分布 ---
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)
        
        # 为不同功能按钮定义不同颜色的样式，字号放大到18px（1.3倍）
        
        # 修改按钮样式 - 蓝色主题
        modify_style = """
            QPushButton {
                font-family: "Microsoft YaHei";
                font-size: 18px;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 92px;
                min-height: 40px;
                max-height: 40px;
                border: 2px solid #2196F3;
                border-radius: 8px;
                background-color: #e3f2fd;
                color: #1565C0;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #bbdefb;
                border-color: #1976D2;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #90caf9;
                transform: translateY(0px);
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #9e9e9e;
                border-color: #e0e0e0;
            }
        """
        
        # 重置按钮样式 - 橙色主题
        reset_style = """
            QPushButton {
                font-family: "Microsoft YaHei";
                font-size: 18px;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 92px;
                min-height: 40px;
                max-height: 40px;
                border: 2px solid #FF9800;
                border-radius: 8px;
                background-color: #fff3e0;
                color: #E65100;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #ffe0b2;
                border-color: #F57C00;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #ffcc80;
                transform: translateY(0px);
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #9e9e9e;
                border-color: #e0e0e0;
            }
        """
        
        # 确定按钮样式 - 绿色主题
        confirm_style = """
            QPushButton {
                font-family: "Microsoft YaHei";
                font-size: 18px;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 92px;
                min-height: 40px;
                max-height: 40px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                background-color: #e8f5e8;
                color: #2E7D32;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #c8e6c9;
                border-color: #45a049;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #a5d6a7;
                transform: translateY(0px);
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #9e9e9e;
                border-color: #e0e0e0;
            }
        """
        
        # 锁定按钮样式 - 紫色主题
        lock_style = """
            QPushButton {
                font-family: "Microsoft YaHei";
                font-size: 18px;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 92px;
                min-height: 40px;
                max-height: 40px;
                border: 2px solid #9C27B0;
                border-radius: 8px;
                background-color: #f3e5f5;
                color: #6A1B9A;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #e1bee7;
                border-color: #7B1FA2;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #ce93d8;
                transform: translateY(0px);
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #9e9e9e;
                border-color: #e0e0e0;
            }
        """
        
        # 预览按钮样式 - 青色主题
        preview_style = """
            QPushButton {
                font-family: "Microsoft YaHei";
                font-size: 18px;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 92px;
                min-height: 40px;
                max-height: 40px;
                border: 2px solid #00BCD4;
                border-radius: 8px;
                background-color: #e0f2f1;
                color: #00695C;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #b2dfdb;
                border-color: #0097A7;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #80cbc4;
                transform: translateY(0px);
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #9e9e9e;
                border-color: #e0e0e0;
            }
        """
        
        # 打印按钮样式 - 深绿色主题
        print_style = """
            QPushButton {
                font-family: "Microsoft YaHei";
                font-size: 18px;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 92px;
                min-height: 40px;
                max-height: 40px;
                border: 2px solid #388E3C;
                border-radius: 8px;
                background-color: #e8f5e8;
                color: #1B5E20;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #c8e6c9;
                border-color: #2E7D32;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #a5d6a7;
                transform: translateY(0px);
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #9e9e9e;
                border-color: #e0e0e0;
            }
        """
        
        # 批量打印按钮样式 - 红色主题
        batch_print_style = """
            QPushButton {
                font-family: "Microsoft YaHei";
                font-size: 18px;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 92px;
                min-height: 40px;
                max-height: 40px;
                border: 2px solid #F44336;
                border-radius: 8px;
                background-color: #ffebee;
                color: #C62828;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #ffcdd2;
                border-color: #D32F2F;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #ef9a9a;
                transform: translateY(0px);
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #9e9e9e;
                border-color: #e0e0e0;
            }
        """
        
        # 创建左上角按钮组，统一设置固定高度
        buttons_top = []
        
        self.modify_btn = QPushButton("修改")
        self.modify_btn.setObjectName('modify_btn')
        self.modify_btn.setFixedHeight(40)
        buttons_top.append(self.modify_btn)
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setObjectName('reset_btn')
        self.reset_btn.setFixedHeight(40)
        buttons_top.append(self.reset_btn)
        
        self.confirm_btn = QPushButton("确定")
        self.confirm_btn.setObjectName('confirm_btn')
        self.confirm_btn.setFixedHeight(40)
        buttons_top.append(self.confirm_btn)
        
        self.lock_btn = QPushButton("锁定")
        self.lock_btn.setObjectName('lock_btn')
        self.lock_btn.setFixedHeight(40)
        buttons_top.append(self.lock_btn)
        
        self.preview_btn_left = QPushButton("二维码预览")
        self.preview_btn_left.setObjectName('preview_btn_left')
        self.preview_btn_left.setFixedHeight(40)
        buttons_top.append(self.preview_btn_left)
        
        # 为每个按钮应用不同颜色的样式
        self.modify_btn.setStyleSheet(modify_style)
        self.reset_btn.setStyleSheet(reset_style)
        self.confirm_btn.setStyleSheet(confirm_style)
        self.lock_btn.setStyleSheet(lock_style)
        self.preview_btn_left.setStyleSheet(preview_style)
        
        self.print_btn_left = QPushButton("二维码打印")
        self.print_btn_left.setObjectName('print_btn_left')
        self.print_btn_left.setStyleSheet(print_style)
        
        self.batch_print_btn = QPushButton("批量打印")
        self.batch_print_btn.setObjectName('batch_print_btn')
        # 移除固定宽度限制，使用样式中的min-width来确保合适的宽度
        self.batch_print_btn.setStyleSheet(batch_print_style)
        
        btn_layout.addStretch(0)
        btn_layout.addWidget(self.modify_btn)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.confirm_btn)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.lock_btn)
        btn_layout.addWidget(self.preview_btn_left)
        btn_layout.addWidget(self.print_btn_left)
        btn_layout.addWidget(self.batch_print_btn)
        btn_layout.addStretch(0)
        left_layout.addLayout(btn_layout)
        left_layout.addStretch(1)

        # 右侧整体容器
        right_container = QFrame()
        right_container.setMinimumWidth(400)
        right_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        # 右上二维码区
        qr_panel_outer = QFrame()
        qr_panel_outer.setStyleSheet("border:2px solid #7bb1e0;border-radius:8px;")
        qr_panel_outer.setMinimumWidth(400)
        qr_panel_outer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # 使用网格布局来实现完美的居中
        outer_layout = QGridLayout(qr_panel_outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.qr_preview_label = QLabel()
        self.qr_preview_label.setFixedSize(500, 510)
        self.qr_preview_label.setAlignment(Qt.AlignCenter)
        self.qr_preview_label.setStyleSheet("background:transparent;border:none;padding:0;")
        
        outer_layout.addWidget(self.qr_preview_label, 0, 0, Qt.AlignCenter) # 添加并设置居中
        right_layout.addWidget(qr_panel_outer)
        
        # 右下内容区
        info_panel = QFrame()
        info_panel.setStyleSheet("border:2px solid #7bb1e0;border-radius:8px;")
        # info_panel.setFixedHeight(300) # 移除固定高度，使其可拉伸
        info_panel.setMinimumWidth(400)
        info_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # 设置为可拉伸
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(8, 8, 8, 8)
        info_layout.setSpacing(4)
        info_label = QLabel("二维码内容信息：")
        info_label.setProperty('role', 'section')
        info_label.setStyleSheet("font-family: 'Microsoft YaHei'; font-weight: bold; font-size: 14px; color: #333333; border: none; background: transparent; padding: 0; margin: 0;")
        info_layout.addWidget(info_label)
        self.qr_info_edit = QTextEdit()
        self.qr_info_edit.setStyleSheet("border:none;")
        self.qr_info_edit.setReadOnly(True)
        self.qr_info_edit.setWordWrapMode(True)  # 启用自动换行
        # self.qr_info_edit.setFixedHeight(240) # 移除固定高度
        
        # 🔧 修复：设置初始提示信息
        initial_content = """欢迎使用二维码打印系统！

操作步骤:
1. 选择公司名称
2. 填写产品信息
3. 生成二维码序号
4. 查看二维码内容
5. 打印二维码标签

提示: 生成二维码后，此处将显示完整的二维码内容信息"""
        self.qr_info_edit.setPlainText(initial_content)
        
        info_layout.addWidget(self.qr_info_edit)
        right_layout.addWidget(info_panel)
        # right_layout.addStretch(1) # 移除弹簧   因为现在是内容框自己拉伸

        main_layout.addWidget(right_container, 0, 1)
        main_layout.setColumnStretch(1, 1)
        main_layout.setRowStretch(0, 0)  # 确保第一行不拉伸，紧贴顶部

        # ========== 5. 下方表格区 ========== 
        table_panel = QFrame()
        table_panel.setStyleSheet("border:2px solid #7bb1e0;border-radius:8px;")
        table_panel.setFixedHeight(320)  # 恢复原高度，充分利用空间
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        # 新建一行：左侧标题+右侧按钮（极致紧凑）
        list_title_row = QHBoxLayout()
        list_title_row.setSpacing(0)
        list_title_row.setContentsMargins(0, 8, 0, 0)   # 整体下移 8 px ≈ 2 mm
        list_title = QLabel("二维码打印列表")
        list_title.setProperty('role', 'section')
        list_title.setFixedHeight(34)  # 调整为更紧凑的高度
        list_title.setStyleSheet("font-family: 'Microsoft YaHei'; font-size:16px; font-weight: bold; background-color: #f5f5dc; padding:0;margin:0;"
                                 "border: 2px solid #7bb1e0; border-radius: 6px;")
        # 以标题的推荐高度作为统一基准，减少约1mm（≈ 4px @96DPI）
        base_height = list_title.sizeHint().height()
        logical_dpi = self.logicalDpiY() if hasattr(self, 'logicalDpiY') else 96
        mm_reduce_px = int(round((1.0 / 25.4) * logical_dpi))
        target_height = max(20, base_height - mm_reduce_px)
        # 创建下方按钮组，统一高度和样式
        table_button_style = """
            QPushButton {
                font-family: "Microsoft YaHei";
                font-size: 13px;
                font-weight: bold;
                padding: 4px 12px;
                border: 2px solid #2196F3;
                border-radius: 8px;
                background-color: #f8fcff;
                color: #1565C0;
                min-width: 70px;
                /* 高度由代码控制为 target_height（标题 - 3mm） */
            }
            QPushButton:hover {
                background-color: #e3f2fd;
                border-color: #1976D2;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #bbdefb;
                transform: translateY(0px);
            }
        """
        
        # 新增刷新按钮
        self.refresh_list_btn = QPushButton("🔄 刷新")
        self.refresh_list_btn.setObjectName('refresh_list_btn')
        self.refresh_list_btn.setFixedHeight(target_height)
        self.refresh_list_btn.setStyleSheet(table_button_style.replace("#2196F3", "#FF9800").replace("#1565C0", "#E65100").replace("#f8fcff", "#fffaf8").replace("#e3f2fd", "#fff3e0").replace("#bbdefb", "#ffe0b2").replace("#1976D2", "#F57C00"))
        
        self.download_btn = QPushButton("📥 下载")
        self.download_btn.setObjectName('download_btn')
        self.download_btn.setFixedHeight(target_height)
        self.download_btn.setStyleSheet(table_button_style)
        
        self.preview_btn = QPushButton("👁️ 预览")
        self.preview_btn.setObjectName('preview_btn')
        self.preview_btn.setFixedHeight(target_height)
        self.preview_btn.setStyleSheet(table_button_style)
        
        self.print_btn = QPushButton("🖨️ 打印")
        self.print_btn.setObjectName('print_btn')
        self.print_btn.setFixedHeight(target_height)
        self.print_btn.setStyleSheet(table_button_style)
        list_title_row.addWidget(list_title)
        list_title_row.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        list_title_row.addWidget(self.refresh_list_btn)  # 新增刷新按钮
        list_title_row.addWidget(self.download_btn)
        list_title_row.addWidget(self.preview_btn)
        list_title_row.addWidget(self.print_btn)
        table_layout.addLayout(list_title_row)
        # 表格 - 删除工号列，调整列数为12
        self.table = QTableWidget(3, 12)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #7bb1e0;
                border-radius: 6px;
                gridline-color: #7bb1e0;
                show-decoration-selected: 1;
            }
            QTableWidget::item {
                padding: 6px;
                border-right: 1px solid #7bb1e0;
                border-bottom: 1px solid #7bb1e0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QHeaderView::section {
                background-color: #f0f8ff;
                padding: 8px;
                border: 1px solid #7bb1e0;
                font-weight: bold;
                color: #333;
            }
        """)
        self.table.setShowGrid(True)  # 显示网格线
        self.table.setHorizontalHeaderLabels(["序", "QRC No.", "发行时间", "打印人", "种类", "型号规格", "颜色", "功能特性", "生产时间", "业务员", "经销商", "物流车牌"])
        self.table.setFixedHeight(260)  # 增加表格高度，充分利用空间
        header = self.table.horizontalHeader()
        header.setFixedHeight(40)
        font = header.font()
        font.setPointSize(11)  # 从14减小到11，减小3个字号
        font.setBold(True)
        header.setFont(font)
        self.table.verticalHeader().setVisible(False)
        # 设置列宽自适应内容并支持用户手动调节
        header.setSectionResizeMode(QHeaderView.Interactive)  # 允许用户手动调节列宽
        
        # 设置各列的初始宽度 - 根据内容特点优化
        self.table.setColumnWidth(0, 50)    # 序号 - 较窄
        self.table.setColumnWidth(1, 140)   # QRC No. - 二维码序号较长
        self.table.setColumnWidth(2, 130)   # 发行时间 - 日期时间
        self.table.setColumnWidth(3, 80)    # 打印人 - 姓名
        self.table.setColumnWidth(4, 90)    # 种类 - 产品类型
        self.table.setColumnWidth(5, 150)   # 型号规格 - 较长
        self.table.setColumnWidth(6, 60)    # 颜色 - 较短
        self.table.setColumnWidth(7, 140)   # 功能特性 - 较长
        self.table.setColumnWidth(8, 130)   # 生产时间 - 日期时间
        self.table.setColumnWidth(9, 100)   # 业务员 - 姓名+工号
        self.table.setColumnWidth(10, 120)  # 经销商 - 公司名
        self.table.setColumnWidth(11, 100)  # 物流车牌 - 车牌号
        
        # 设置最后一列自动拉伸以填满剩余空间
        header.setStretchLastSection(True)
        
        # 启用内容自适应调整
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)   # 序号自适应内容
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)   # 打印人自适应内容
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)   # 颜色自适应内容
        # 移除setColumnWidth相关代码
        table_layout.addWidget(self.table)
        main_layout.addWidget(table_panel, 1, 0, 1, 3)

        # 初始化数据库连接（不创建表，只连接）
        self.init_database_connection()
        self.load_data_to_combos()
        
        # 初始化公司LOGO显示
        QTimer.singleShot(100, self._safe_update_company_logo)
        
        # 初始化二维码序号
        self.init_qr_sequence()

        # 验证状态
        self.validation_errors = {}
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self.perform_validation)

        # 连接信号
        self.connect_signals()
        self.preview_btn_left.clicked.connect(self.preview_qr)

        
        # 加载数据到下拉框
        self.load_data_to_combos()
        
        # 加载二维码记录
        self.load_qr_records()
        
        # 初始化状态变量
        self.is_locked = False
        self.is_confirmed = False
        
        # 初始化控件状态
        self.update_controls_state()
        
        # 初始化二维码
        self.generate_qr_code("初始二维码内容")
        
        # 自动刷新定时器已删除 - 根据用户要求简化系统
        # 权限应用：根据当前用户角色启用/禁用按钮
        try:
            if hasattr(self, 'current_user'):
                self.apply_permissions(self.current_user)
        except Exception:
            pass

    def _safe_update_company_logo(self):
        # 将诊断信息输出到日志文件，便于在无控制台时排查
        try:
            import sys, os, datetime
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(exe_dir, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            self._logo_diag_path = os.path.join(log_dir, 'ui_logo_diag.log')
        except Exception:
            self._logo_diag_path = None

        def _diag(msg):
            try:
                if self._logo_diag_path:
                    with open(self._logo_diag_path, 'a', encoding='utf-8') as f:
                        f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
            except Exception:
                pass
        """更新公司logo显示（安全统一入口）"""
        try:
            # 获取当前选择的公司名称
            if hasattr(self, 'combos_col1') and len(self.combos_col1) > 0:
                company_combo = self.combos_col1[0]  # 公司名称是第一个下拉框
                company_name = company_combo.currentText()
                
                # 根据公司名称加载对应的logo文件
                logo_path = None
                
                # 确定运行环境和资源路径
                import sys
                if getattr(sys, 'frozen', False):
                    # PyInstaller 打包环境
                    if hasattr(sys, '_MEIPASS') and sys._MEIPASS:
                        # onefile 解压目录
                        base_path = sys._MEIPASS
                        assets_candidates = [os.path.join(base_path, 'assets')]
                    else:
                        # onedir 布局：优先 exe/_internal/assets，其次 exe/assets
                        exe_dir = os.path.dirname(sys.executable)
                        base_path = exe_dir
                        assets_candidates = [
                            os.path.join(exe_dir, '_internal', 'assets'),
                            os.path.join(exe_dir, 'assets'),
                        ]
                else:
                    # 开发环境 - 使用项目根目录
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    base_path = base_dir
                    assets_candidates = [os.path.join(base_dir, 'assets')]
                
                # 根据公司名称匹配logo文件（支持中文名与英文别名）
                if '示例' in company_name or '示例品牌A' in company_name:
                    logo_names = ['示例品牌A 透明.png', 'demo_logo_b.png']
                elif '示例' in company_name or '示例品牌B' in company_name:
                    logo_names = ['示例品牌B 透明.png', 'demo_logo_a.png']
                else:
                    logo_names = []
                
                # 遍历候选路径与候选文件名
                logo_path = None
                for ap in assets_candidates:
                    try:
                        for name in logo_names:
                            cand = os.path.join(ap, name)
                            if os.path.exists(cand):
                                logo_path = cand
                                break
                        if logo_path:
                            break
                    except Exception:
                        continue
                
                # 调试信息 -> 写入日志文件
                _diag(f"env={'packed' if getattr(sys, 'frozen', False) else 'dev'} base={base_path}")
                for ap in assets_candidates:
                    try:
                        exists = os.path.exists(ap)
                        sample = []
                        if exists:
                            sample = os.listdir(ap)[:5]
                        _diag(f"candidate={ap} exists={exists} sample={sample}")
                    except Exception as ex:
                        _diag(f"candidate={ap} error={ex}")
                
                # 加载并显示logo
                if logo_path and os.path.exists(logo_path):
                    pixmap = QPixmap(logo_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.company_logo_label.setPixmap(scaled_pixmap)
                        self.company_logo_label.setToolTip(f"公司LOGO: {company_name}")
                        _diag(f"OK logo={logo_path}")
                    else:
                        _diag(f"FAIL pixmap.isNull logo={logo_path}")
                        self.company_logo_label.clear()
                        self.company_logo_label.setText("LOGO")
                        self.company_logo_label.setAlignment(Qt.AlignCenter)
                else:
                    self.company_logo_label.clear()
                    self.company_logo_label.setText("LOGO")
                    self.company_logo_label.setAlignment(Qt.AlignCenter)
                    _diag(f"MISS logo for company={company_name}")
        
        except Exception as e:
            print(f"❌ 更新公司logo时出错: {e}")
            # 出错时显示默认文本
            if hasattr(self, 'company_logo_label'):
                self.company_logo_label.clear()
                self.company_logo_label.setText("LOGO")

    def show_printer_selection_dialog(self, title="选择打印机"):
        """显示打印机选择对话框"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox, QGroupBox, QCheckBox
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont
        
        try:
            # 🔧 修复：多种方式检测可用打印机
            available_printers = QPrinterInfo.availablePrinters()
            
            # 调试信息：显示检测到的打印机数量
            print(f"QPrinterInfo.availablePrinters() 检测到 {len(available_printers)} 个打印机")
            
            # 如果QPrinterInfo检测不到，尝试其他方法
            if not available_printers:
                # 方法2：尝试获取默认打印机
                default_printer = QPrinterInfo.defaultPrinter()
                if default_printer and not default_printer.isNull():
                    available_printers = [default_printer]
                    print(f"通过默认打印机检测到: {default_printer.printerName()}")
                
                # 方法3：尝试使用系统命令检测打印机
                if not available_printers:
                    try:
                        import subprocess
                        import platform
                        
                        if platform.system() == "Windows":
                            # Windows系统使用wmic命令检测打印机
                            result = subprocess.run(['wmic', 'printer', 'get', 'name'], 
                                                   capture_output=True, text=True, timeout=5)
                            if result.returncode == 0:
                                printer_names = []
                                lines = result.stdout.strip().split('\n')
                                for line in lines[1:]:  # 跳过标题行
                                    line = line.strip()
                                    if line and line != "Name":
                                        printer_names.append(line)
                                print(f"通过wmic命令检测到 {len(printer_names)} 个打印机: {printer_names}")
                                
                                # 创建虚拟打印机信息对象
                                if printer_names:
                                    # 至少有一个打印机，创建一个可用的QPrinter对象
                                    test_printer = QPrinter()
                                    if test_printer:
                                        available_printers = [QPrinterInfo.defaultPrinter()]
                                        print("使用默认打印机作为可用选项")
                        
                    except Exception as cmd_error:
                        print(f"系统命令检测打印机失败: {cmd_error}")
            
            # 最终检查
            if not available_printers:
                # 尝试创建一个测试打印机对象
                try:
                    test_printer = QPrinter()
                    test_printer.setPrinterName("")  # 使用系统默认
                    if test_printer.printerName():
                        print(f"通过QPrinter检测到默认打印机: {test_printer.printerName()}")
                        available_printers = [QPrinterInfo.defaultPrinter()]
                except Exception as test_error:
                    print(f"QPrinter测试失败: {test_error}")
            
            # 🔧 BUGFIX: 增强打印机检测 - 解决"系统中没有找到可用的打印机"问题
            if not available_printers:
                print("⚠️ 尝试最后的检测方法...")
                
                # 方法4：强制创建一个基本打印机对象用于测试
                try:
                    # 创建基本打印机对象，让系统自动选择默认打印机
                    fallback_printer = QPrinter(QPrinter.HighResolution)
                    fallback_printer.setOutputFormat(QPrinter.NativeFormat)
                    
                    # 检查是否可以获取打印机名称
                    printer_name = fallback_printer.printerName()
                    print(f"回退方案检测到打印机: {printer_name}")
                    
                    if printer_name:
                        # 创建一个伪装的QPrinterInfo对象供界面使用
                        print("✅ 找到可用打印机，创建默认选项")
                        available_printers = [QPrinterInfo.defaultPrinter()]
                        
                        # 如果默认打印机信息为空，直接返回一个可用的打印机对象给调用者
                        if not available_printers[0] or available_printers[0].isNull():
                            print("⚡ 使用直接打印模式")
                            return fallback_printer  # 直接返回可用的打印机对象
                            
                except Exception as fallback_error:
                    print(f"回退方案失败: {fallback_error}")
            
            # 如果所有方法都失败了
            if not available_printers:
                # 🔧 修改错误信息，提供更友好的解决方案
                error_msg = """🖨️ 打印机连接检测异常

系统未能通过标准方法检测到打印机，但这可能是检测机制的问题，而非打印机故障。

快速解决方案：
✅ 1. 确认打印机电源已开启且连接正常
✅ 2. 在其他应用（如记事本）中测试打印功能
✅ 3. 如果其他应用可以正常打印，请点击"继续使用"

高级解决方案：
🔧 4. 重启"Print Spooler"服务：
   - 按 Win+R → 输入 services.msc
   - 找到"Print Spooler" → 右键重启
🔧 5. 检查设备管理器中的打印机状态
🔧 6. 重新安装打印机驱动程序

❓ 如果问题持续，请联系技术支持。"""
                
                # 创建自定义对话框，提供"继续使用"选项
                reply = QMessageBox.question(
                    self, 
                    "打印机检测问题", 
                    error_msg + "\n\n是否继续使用系统默认打印机？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # 用户选择继续，创建一个基础打印机对象
                    try:
                        basic_printer = QPrinter(QPrinter.HighResolution)
                        basic_printer.setOutputFormat(QPrinter.NativeFormat)
                        print("✅ 用户选择继续，使用系统默认打印机")
                        return basic_printer
                    except Exception as basic_error:
                        print(f"创建基础打印机失败: {basic_error}")
                        QMessageBox.critical(self, "打印机错误", f"无法创建打印机对象: {basic_error}")
                        return None
                else:
                    return None
            
            # 创建打印机选择对话框
            dialog = QDialog(self)
            dialog.setWindowTitle(title)
            dialog.setModal(True)
            dialog.setFixedSize(500, 400)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #f8f9fa;
                    border: 2px solid #007bff;
                    border-radius: 10px;
                }
                QLabel {
                    font-family: "Microsoft YaHei";
                    color: #333;
                }
                QComboBox {
                    font-family: "Microsoft YaHei";
                    font-size: 12px;
                    padding: 8px;
                    border: 2px solid #ddd;
                    border-radius: 5px;
                    background-color: white;
                }
                QComboBox:focus {
                    border-color: #007bff;
                }
                QPushButton {
                    font-family: "Microsoft YaHei";
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px 20px;
                    border: 2px solid #007bff;
                    border-radius: 8px;
                    background-color: #007bff;
                    color: white;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                    border-color: #0056b3;
                }
                QPushButton:pressed {
                    background-color: #004085;
                }
                QPushButton#cancelBtn {
                    background-color: #6c757d;
                    border-color: #6c757d;
                }
                QPushButton#cancelBtn:hover {
                    background-color: #545b62;
                    border-color: #545b62;
                }
                QGroupBox {
                    font-family: "Microsoft YaHei";
                    font-weight: bold;
                    font-size: 14px;
                    color: #007bff;
                    border: 2px solid #007bff;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 20px;
                    padding: 0 10px 0 10px;
                }
            """)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)
            
            # 标题
            title_label = QLabel("🖨️ 选择打印机")
            title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
            title_label.setStyleSheet("color: #007bff; padding: 10px 0; border: none;")
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            
            # 打印机选择组
            printer_group = QGroupBox("可用打印机列表")
            printer_layout = QVBoxLayout(printer_group)
            printer_layout.setContentsMargins(15, 20, 15, 15)
            printer_layout.setSpacing(10)
            
            # 打印机列表说明
            info_label = QLabel("请从下方列表中选择要使用的打印机：")
            info_label.setStyleSheet("color: #666; font-size: 12px; border: none;")
            printer_layout.addWidget(info_label)
            
            # 打印机下拉框
            printer_combo = QComboBox()
            printer_combo.setMinimumHeight(40)
            
            # 添加打印机到下拉框
            default_printer = QPrinterInfo.defaultPrinter()
            default_index = 0
            
            for i, printer_info in enumerate(available_printers):
                printer_name = printer_info.printerName()
                is_default = printer_info.isDefault()
                is_ready = printer_info.state() == QPrinterInfo.Idle
                
                # 构建显示文本
                display_text = printer_name
                if is_default:
                    display_text += " (默认)"
                    default_index = i
                if not is_ready:
                    display_text += " (离线)"
                
                printer_combo.addItem(display_text, printer_info)
            
            # 设置默认选择
            printer_combo.setCurrentIndex(default_index)
            printer_layout.addWidget(printer_combo)
            
            # 打印机状态信息
            status_label = QLabel()
            status_label.setStyleSheet("color: #28a745; font-size: 11px; border: none; padding: 5px;")
            status_label.setWordWrap(True)
            printer_layout.addWidget(status_label)
            
            def update_printer_status():
                current_data = printer_combo.currentData()
                if current_data:
                    status_text = f"打印机: {current_data.printerName()}\n"
                    status_text += f"状态: {'就绪' if current_data.state() == QPrinterInfo.Idle else '离线'}\n"
                    if current_data.description():
                        status_text += f"描述: {current_data.description()}"
                    status_label.setText(status_text)
            
            printer_combo.currentIndexChanged.connect(update_printer_status)
            update_printer_status()  # 初始更新
            
            layout.addWidget(printer_group)
            
            # 高级选项组
            options_group = QGroupBox("打印选项")
            options_layout = QVBoxLayout(options_group)
            options_layout.setContentsMargins(15, 20, 15, 15)
            options_layout.setSpacing(8)
            
            # 打印预览选项
            preview_check = QCheckBox("打印前显示预览")
            preview_check.setChecked(True)
            preview_check.setStyleSheet("QCheckBox { font-size: 12px; color: #333; }")
            options_layout.addWidget(preview_check)
            
            # 高质量打印选项
            quality_check = QCheckBox("高质量打印模式")
            quality_check.setChecked(True)
            quality_check.setStyleSheet("QCheckBox { font-size: 12px; color: #333; }")
            options_layout.addWidget(quality_check)
            
            layout.addWidget(options_group)
            
            # 按钮区域
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            # 取消按钮
            cancel_btn = QPushButton("取消")
            cancel_btn.setObjectName("cancelBtn")
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)
            
            # 确定按钮
            ok_btn = QPushButton("确定打印")
            ok_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(ok_btn)
            
            layout.addLayout(button_layout)
            
            # 显示对话框
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                selected_printer = printer_combo.currentData()
                return {
                    'printer_info': selected_printer,
                    'printer_name': selected_printer.printerName(),
                    'show_preview': preview_check.isChecked(),
                    'high_quality': quality_check.isChecked()
                }
            else:
                return None
                
        except Exception as e:
            print(f"打印机选择对话框错误: {e}")
            QMessageBox.critical(self, "错误", f"打印机选择对话框错误:\n{str(e)}")
            return None

    def connect_signals(self):
        """连接信号和槽函数"""
        # 连接公司名称下拉框的变化信号到logo更新
        if len(self.combos_col1) > 0:
            self.combos_col1[0].currentTextChanged.connect(self._safe_update_company_logo)
        # 表单数据变化时更新二维码内容
        for i, combo in enumerate(self.combos_col1):
            if combo is not None:
                combo.currentTextChanged.connect(self.update_qr_content)
                combo.currentTextChanged.connect(self.schedule_validation)
                # 公司名称变化时重新生成二维码序号
                if i == 0:  # 公司名称下拉框
                    combo.currentTextChanged.connect(self.generate_new_qr_sequence)
                    combo.currentTextChanged.connect(self.update_company_logo)
                    combo.currentTextChanged.connect(self.update_company_logo)
        for widget in self.widgets_col2 + [self.quantity_edit]:
            if widget is not None:
                if isinstance(widget, QLineEdit):
                    widget.textChanged.connect(self.update_qr_content)
                    widget.textChanged.connect(self.schedule_validation)
                elif isinstance(widget, QDateTimeEdit):
                    widget.dateTimeChanged.connect(self.update_qr_content)
                    widget.dateTimeChanged.connect(self.schedule_validation)
        # 备注变化时也更新二维码
        if self.remark_edit is not None:
            self.remark_edit.textChanged.connect(self.update_qr_content)
        # 按钮点击事件
        if self.modify_btn is not None:
            self.modify_btn.clicked.connect(self.modify_data)
        if self.reset_btn is not None:
            self.reset_btn.clicked.connect(self.reset_form)
        if self.confirm_btn is not None:
            self.confirm_btn.clicked.connect(self.confirm_data)
        if self.lock_btn is not None:
            self.lock_btn.clicked.connect(self.lock_form)
        if self.download_btn is not None:
            self.download_btn.clicked.connect(self.download_qr)
        if self.preview_btn is not None:
            self.preview_btn.clicked.connect(self.preview_qr_list)
        if self.print_btn_left is not None:
            self.print_btn_left.clicked.connect(self.print_qr)
        if self.batch_print_btn is not None:
            self.batch_print_btn.clicked.connect(self.batch_print_qr)
        # 连接刷新列表按钮
        if self.refresh_list_btn is not None:
            self.refresh_list_btn.clicked.connect(self.refresh_qr_list)
        # 物流车牌号为QComboBox时，切换选项也刷新内容区
        if self.widgets_col2 and hasattr(self.widgets_col2[0], 'currentTextChanged'):
            self.widgets_col2[0].currentTextChanged.connect(self.update_qr_content)
        
        # 🔧 修复：连接公司选择变化事件
        if len(self.combos_col1) > 0 and self.combos_col1[0]:
            self.combos_col1[0].currentTextChanged.connect(self.on_company_changed)
        
        # 🔧 修复：连接二维码序号变化事件
        if len(self.widgets_col2) > 2 and self.widgets_col2[2]:
            self.widgets_col2[2].textChanged.connect(self.on_qr_sequence_changed)
    
    def refresh_qr_list(self):
        """刷新二维码打印列表"""
        try:
            # 重新加载二维码记录
            self.load_qr_records()
            logging.getLogger(__name__).debug("[SUCCESS] 二维码打印列表已刷新")
        except Exception as e:
            print(f"[ERROR] 刷新二维码列表失败: {e}")
            QMessageBox.warning(self, "刷新失败", f"刷新二维码列表失败:\n{str(e)}")
    
    def preview_qr_list(self):
        """预览二维码打印列表"""
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTableWidget, QHeaderView
            from PyQt5.QtCore import Qt
            from PyQt5.QtGui import QFont
            
            # 创建预览对话框
            preview_dialog = QDialog(self)
            preview_dialog.setWindowTitle("二维码打印列表预览")
            preview_dialog.setModal(True)
            preview_dialog.resize(1200, 600)
            
            layout = QVBoxLayout(preview_dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)
            
            # 标题
            title_label = QLabel("二维码打印列表预览")
            title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
            title_label.setStyleSheet("color: #2E7D32; padding: 10px 0;")
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            
            # 创建预览表格
            preview_table = QTableWidget()
            preview_table.setColumnCount(self.table.columnCount())
            preview_table.setHorizontalHeaderLabels([
                self.table.horizontalHeaderItem(i).text() 
                for i in range(self.table.columnCount())
            ])
            
            # 复制原表格数据
            preview_table.setRowCount(self.table.rowCount())
            for row in range(self.table.rowCount()):
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        preview_table.setItem(row, col, QTableWidgetItem(item.text()))
            
            # 设置预览表格样式
            preview_table.setStyleSheet("""
                QTableWidget {
                    background-color: white;
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                    gridline-color: #4CAF50;
                    font-family: "Microsoft YaHei";
                    font-size: 12px;
                }
                QTableWidget::item {
                    padding: 8px;
                    border-right: 1px solid #4CAF50;
                    border-bottom: 1px solid #4CAF50;
                }
                QHeaderView::section {
                    background-color: #e8f5e8;
                    padding: 10px;
                    border: 1px solid #4CAF50;
                    font-weight: bold;
                    font-size: 11px;
                    color: #2E7D32;
                }
            """)
            
            # 设置表格属性
            preview_table.setAlternatingRowColors(True)
            preview_table.setSelectionBehavior(QTableWidget.SelectRows)
            preview_table.setSortingEnabled(True)
            preview_table.setEditTriggers(QTableWidget.NoEditTriggers)
            
            # 自适应列宽
            header = preview_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeToContents)
            header.setStretchLastSection(True)
            
            layout.addWidget(preview_table)
            
            # 按钮区域
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            close_btn = QPushButton("关闭")
            close_btn.setStyleSheet("""
                QPushButton {
                    font-family: "Microsoft YaHei";
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px 20px;
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                    background-color: #f8fff8;
                    color: #2E7D32;
                    min-width: 80px;
                    min-height: 36px;
                }
                QPushButton:hover {
                    background-color: #e8f5e8;
                    border-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #c8e6c9;
                }
            """)
            close_btn.clicked.connect(preview_dialog.close)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            # 显示对话框
            preview_dialog.exec_()
            
        except Exception as e:
            print(f"[ERROR] 预览二维码列表失败: {e}")
            QMessageBox.warning(self, "预览失败", f"预览二维码列表失败:\n{str(e)}")

    def schedule_validation(self):
        """延迟验证，避免频繁验证"""
        self.validation_timer.start(500)  # 500ms后执行验证

    def perform_validation(self):
        """执行表单验证"""
        self.validation_errors.clear()
        # 验证必填字段
        required_fields = [
            (self.combos_col1[0], "公司名称"),
            (self.combos_col1[1], "部门名称"),
            (self.combos_col1[2], "二维码发行人"),
            (self.combos_col1[3], "产品种类"),
            (self.combos_col1[4], "产品规格"),
            (self.quantity_edit, "执行标准"),
        ]
        for widget, field_name in required_fields:
            if widget is not None:
                if hasattr(widget, 'currentText'):
                    value = widget.currentText()
                else:
                    value = widget.text()
                if not value or value == f"{field_name}选项1":
                    self.validation_errors[field_name] = f"{field_name}为必填项"
        # 验证执行标准字段 - 适合文本输入的验证
        quantity_text = self.quantity_edit.text() if self.quantity_edit is not None else ''
        # 执行标准验证：允许任何文本输入，但检查长度和格式
        if quantity_text and len(quantity_text) > 100:
            self.validation_errors["执行标准"] = "执行标准长度不能超过100个字符"
        elif quantity_text and not re.match(r'^[\w\s\-\./:：,，()（）]*$', quantity_text):
            self.validation_errors["执行标准"] = "执行标准包含非法字符"
        # 验证车牌号格式
        plate_number = self.widgets_col2[0].currentText() if self.widgets_col2[0] is not None and hasattr(self.widgets_col2[0], 'currentText') else (self.widgets_col2[0].text() if self.widgets_col2[0] is not None else '')
        if plate_number and not re.match(r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-Z0-9]{5}$', plate_number):
            self.validation_errors["物流车牌号"] = "车牌号格式不正确"
        # 移除电话号码验证限制，允许任何格式
        phone_text = self.widgets_col2[1].text() if self.widgets_col2[1] is not None else ''
        # 不再验证电话号码格式，允许任何输入
        pass
        # 验证批次号格式（支持8位日期+3位流水号，共11位）
        batch_number = self.widgets_col2[4].text() if self.widgets_col2[4] is not None else ''
        if batch_number and not re.match(r'^[0-9]{11}$', batch_number):
            self.validation_errors["产品批次号"] = "批次号格式不正确（11位数字：YYYYMMDD+001-999）"
        # 更新UI显示验证结果
        self.update_validation_display()

    def update_validation_display(self):
        error_style = """
            QComboBox, QLineEdit, QDateTimeEdit {
                background-color: #fff5f5;
                border: 2px solid #ff6b6b;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                min-height: 28px;
                color: #2d4a6a;
            }
        """
        # 定义下拉框样式，显示边框和下拉按钮
        combo_style = "font-weight:bold;padding-left:8px;"  # 移除border:none，让下拉框显示默认边框和下拉按钮
        
        # 清空所有控件的局部样式，让全局QSS生效
        for combo in self.combos_col1:
            if combo is not None:
                combo.setStyleSheet(combo_style)  # 保持下拉框样式，确保下拉按钮紧贴右边框
        for widget in self.widgets_col2 + [self.quantity_edit]:
            if widget is not None:
                widget.setStyleSheet("")
        # 设置错误样式
        for field_name, error_msg in self.validation_errors.items():
            widget = self.get_widget_by_field_name(field_name)
            if widget is not None:
                widget.setStyleSheet(error_style)
                widget.setToolTip(error_msg)
        
        # 更新锁定按钮状态
        self.update_controls_state()

    def get_widget_by_field_name(self, field_name):
        """根据字段名获取对应的控件"""
        field_mapping = {
            "公司名称": self.combos_col1[0],
            "部门名称": self.combos_col1[1],
            "二维码发行人": self.combos_col1[2],
            "产品种类": self.combos_col1[3],
            "产品规格": self.combos_col1[4],
            "执行标准": self.quantity_edit,
        }
        return field_mapping.get(field_name)

    def get_simplified_company_name(self, full_company_name):
        """获取简化的公司名称"""
        if not full_company_name:
            return full_company_name
            
        # 根据需求简化公司名称
        if "[已脱敏城市]示例品牌B材料有限公司" in full_company_name:
            return "示例城市"
        elif "[已脱敏城市]示例品牌A有限公司" in full_company_name:
            return "示例城市"
        else:
            # 对于其他公司，保持原名或进行通用简化
            # 移除常见的公司后缀
            simplified = full_company_name
            suffixes = ["有限公司", "股份有限公司", "集团有限公司", "实业有限公司"]
            for suffix in suffixes:
                if simplified.endswith(suffix):
                    simplified = simplified[:-len(suffix)]
                    break
            return simplified

    def generate_qr_code(self, content):
        """生成二维码"""
        try:
            # 创建二维码实例
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.ERROR_CORRECT_H,  # 使用高容错率支持LOGO
                box_size=10,
                border=0,
            )
            qr.add_data(content)
            qr.make(fit=True)
            # 创建二维码图像
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 尝试添加公司LOGO到二维码
            try:
                company_name = self.combos_col1[0].currentText() if self.combos_col1 else ""
                if company_name:
                    img_with_logo = self.add_logo_to_qr_image(img, company_name)
                    if img_with_logo is not None:
                        img = img_with_logo
            except Exception as logo_e:
                print(f"添加LOGO失败，使用原始二维码: {logo_e}")
            # 转换为QImage并resize为320x320
            buffer = BytesIO()
            img.save(buffer)
            buffer.seek(0)
            qimg = QImage()
            qimg.loadFromData(buffer.getvalue())
            qimg = qimg.scaled(320, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pixmap = QPixmap.fromImage(qimg)
            # 设置到预览标签
            if self.qr_preview_label is not None:
                self.qr_preview_label.setPixmap(pixmap)
        except Exception as e:
            print(f"权限控制失败: {e}")

    def setup_permissions(self, user):
        """设置权限控制 - 兼容新的权限系统"""
        return self.apply_permissions(user)
    
    def apply_permissions(self, user):
        """应用权限控制"""
        try:
            self.current_user = user or {}
            
            # 校验用户权限并控制界面
            can_view = has_permission(user, "qr.view")
            if not can_view:
                # 如果没有查看权限，整个模块不可用
                self.setEnabled(False)
                return
                
            # 🚨 关键修复：检查生成权限，如果没有生成权限，整个模块应该禁用
            can_generate = has_permission(user, "qr.generate")
            if not can_generate:
                # 系统浏览者不应该能进入二维码打印模块
                print(f"🚨 安全控制: 用户 {user.get('username', 'unknown')} 没有qr.generate权限，禁用整个二维码打印模块")
                self.setEnabled(False)
                
                # 递归禁用所有子控件
                self._disable_all_widgets(self)
                
                # 设置模块级别的权限提示
                self.setToolTip("您没有使用二维码打印模块的权限 - 仅限系统浏览者查看")
                
                # 显示明显的权限不足提示
                try:
                    # 尝试在界面上显示权限提示
                    if hasattr(self, 'setStyleSheet'):
                        self.setStyleSheet("QWidget { background-color: #f8f9fa; color: #6c757d; }")
                except:
                    pass
                    
                print(f"✅ 二维码打印模块已完全禁用 - 用户: {user.get('username', 'unknown')}")
                return
            
            # 生成二维码权限
            can_generate = has_permission(user, "qr.generate")
            generate_controls = [self.confirm_btn, self.modify_btn, self.reset_btn, self.lock_btn]
            for control in generate_controls:
                if hasattr(self, control.__class__.__name__.replace('QPushButton', '').lower() + '_btn'):
                    control.setEnabled(can_generate)
                    if not can_generate:
                        control.setToolTip("您没有生成二维码的权限")
            
            # 下载权限检查
            can_download = has_permission(user, "qr.download")
            if hasattr(self, 'download_btn'):
                self.download_btn.setEnabled(can_download)
                if not can_download:
                    self.download_btn.setToolTip("您没有下载权限")
            
            # 打印权限检查  
            can_print = has_permission(user, "qr.print")
            print_controls = [self.print_btn_left, self.print_btn, self.batch_print_btn, self.preview_btn_left, self.preview_btn]
            for control in print_controls:
                if hasattr(self, control.__class__.__name__.replace('QPushButton', '').lower()):
                    control.setEnabled(can_print)
                    if not can_print:
                        control.setToolTip("您没有打印权限")
            
            # 删除权限检查（仅管理者可删除生产数据）
            can_delete = has_permission(user, "qr.delete")
            # 注意：删除按钮可能在表格右键菜单或其他地方
            # 这里先预留接口，具体的删除功能需要在相应位置添加权限检查
            
            print(f"权限应用完成 - 用户: {user.get('username', 'unknown')}, 权限: view={can_view}, generate={can_generate}, download={can_download}, print={can_print}, delete={can_delete}")
                    
        except Exception as e:
            print(f"权限控制失败: {e}")
            
    def _disable_all_widgets(self, parent_widget):
        """递归禁用所有子控件"""
        try:
            # 禁用父控件
            parent_widget.setEnabled(False)
            
            # 递归禁用所有子控件
            for child in parent_widget.findChildren(QWidget):
                child.setEnabled(False)
                child.setToolTip("您没有使用二维码打印模块的权限")
                
                # 特别处理按钮和输入框
                if hasattr(child, 'setText') and hasattr(child, 'setReadOnly'):
                    try:
                        child.setReadOnly(True)
                    except:
                        pass
                        
        except Exception as e:
            print(f"禁用控件时出错: {e}")
            # 如果生成失败，显示默认文本
            if self.qr_preview_label is not None:
                self.qr_preview_label.setText("二维码生成失败")
                self.qr_preview_label.setStyleSheet("""
                    QLabel {
                        background-color: white;
                        
                        border-radius: 8px;
                        padding: 10px;
                        color: #b3cde8;
                        font-size: 14px;
                    }
                """)

    def generate_minimal_qr_code(self, content):
        """生成极简二维码，减少黑点，提高扫描成功率"""
        try:
            # 使用最低版本和最高容错率的极简配置
            qr = qrcode.QRCode(
                version=1,  # 最低版本，最小尺寸
                error_correction=qrcode.ERROR_CORRECT_H,  # 最高容错率30%
                box_size=12,  # 稍大的模块尺寸，提高识别率
                border=0,     # 删除边框，让二维码直接显示
            )
            qr.add_data(content)
            qr.make(fit=True)
            
            # 创建二维码图像
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 尝试添加公司LOGO到二维码
            try:
                company_name = self.combos_col1[0].currentText() if self.combos_col1 else ""
                if company_name:
                    img_with_logo = self.add_logo_to_qr_image(img, company_name)
                    if img_with_logo is not None:
                        img = img_with_logo
            except Exception as logo_e:
                print(f"添加LOGO失败，使用原始二维码: {logo_e}")
            
            # 转换为QImage并优化尺寸
            buffer = BytesIO()
            img.save(buffer)
            buffer.seek(0)
            qimg = QImage()
            qimg.loadFromData(buffer.getvalue())
            
            # 保持清晰度的最优尺寸
            qimg = qimg.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pixmap = QPixmap.fromImage(qimg)
            
            # 设置到预览标签
            if self.qr_preview_label is not None:
                self.qr_preview_label.setPixmap(pixmap)
                
        except Exception as e:
            print(f"生成极简二维码时出错: {e}")
            # 如果生成失败，显示默认文本
            if self.qr_preview_label is not None:
                self.qr_preview_label.setText("二维码生成失败")
                self.qr_preview_label.setStyleSheet("""
                    QLabel {
                        background-color: white;
                        
                        border-radius: 8px;
                        padding: 10px;
                        color: #b3cde8;
                        font-size: 14px;
                    }
                """)

    def generate_high_quality_qr_code(self, content):
        """生成高容错率二维码，确保手机可识别"""
        try:
            # 高容错率配置
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.ERROR_CORRECT_H,  # 最高容错率30%
                box_size=10,
                border=0,
            )
            qr.add_data(content)
            qr.make(fit=True)
            # 创建二维码图像
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 尝试添加公司LOGO到二维码（如果失败不影响二维码显示）
            try:
                company_name = self.combos_col1[0].currentText() if self.combos_col1 else ""
                if company_name:
                    img_with_logo = self.add_logo_to_qr_image(img, company_name)
                    if img_with_logo is not None:
                        img = img_with_logo
            except Exception as logo_e:
                print(f"添加LOGO失败，使用原始二维码: {logo_e}")
            
            # 转换为QImage并resize为适合手机扫描的尺寸
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            qimg = QImage()
            qimg.loadFromData(buffer.getvalue())
            qimg = qimg.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pixmap = QPixmap.fromImage(qimg)
            # 设置到预览标签
            if self.qr_preview_label is not None:
                self.qr_preview_label.setPixmap(pixmap)
                self.qr_preview_label.setStyleSheet("")  # 清除错误样式
        except Exception as e:
            print(f"生成高容错率二维码时出错: {e}")
            import traceback
            traceback.print_exc()
            # 如果生成失败，尝试生成简单二维码
            try:
                self.generate_simple_fallback_qr(content)
            except:
                # 最后的备选方案：显示错误信息
                if self.qr_preview_label is not None:
                    self.qr_preview_label.setText("二维码生成失败")
                    self.qr_preview_label.setStyleSheet("""
                        QLabel {
                            background-color: white;
                            border-radius: 8px;
                            padding: 10px;
                            color: #b3cde8;
                            font-size: 14px;
                        }
                    """)

    def update_qr_content(self):
        """水平布局显示15项完整数据，动态生成二维码内容"""
        try:
            # 获取当前日期作为批次号基础
            current_date = QDateTime.currentDateTime().date()
            auto_prefix = current_date.toString('yyyyMMdd')
            
            # 获取当前批次号输入框的内容
            user_batch = self.widgets_col2[4].text().strip() if len(self.widgets_col2) > 4 and self.widgets_col2[4] is not None else ""
            
            # 如果用户输入的是3位数字，自动补全为完整批次号
            if len(user_batch) == 3 and user_batch.isdigit():
                batch_number = f"{auto_prefix}{user_batch}"
            elif len(user_batch) >= 8:  # 用户已输入完整批次号或部分批次号
                batch_number = user_batch
            else:
                # 默认显示完整批次号
                batch_number = f"{auto_prefix}001"
            
            # 不自动更新批次号输入框，让用户完全手动编辑
            # 仅在批次号为空时设置默认值
            current_batch = self.widgets_col2[4].text().strip()
            if not current_batch and len(self.widgets_col2) > 4 and self.widgets_col2[4] is not None:
                self.widgets_col2[4].setText(f"{auto_prefix}001")
            
            # 获取15项信息
            company_name = self.combos_col1[0].currentText() if self.combos_col1[0] is not None else "[已脱敏城市]示例品牌A有限公司"
            # 根据选择的公司名称动态获取公司网址
            company_website = self.get_company_website(company_name)
            product_type = self.combos_col1[3].currentText() if len(self.combos_col1) > 3 else "XPS-A1"
            product_spec = self.combos_col1[4].currentText() if len(self.combos_col1) > 4 else "30mm"
            product_feature = self.combos_col1[5].currentText() if len(self.combos_col1) > 5 else "保温隔热"
            product_color = self.combos_col1[6].currentText() if len(self.combos_col1) > 6 else "白色"
            plate_number = self.widgets_col2[0].currentText() if self.widgets_col2[0] is not None else "京A12345"
            service_phone = self.widgets_col2[1].text() if self.widgets_col2[1] is not None else "13800000002"
            production_time = self.widgets_col2[3].dateTime().toString('yyyy-MM-dd HH:mm:ss') if self.widgets_col2[3] is not None else "2025-07-20 14:30:00"
            inspection_result = "合格"  # 固定检验结果
            qr_sequence = self.widgets_col2[2].text() if self.widgets_col2[2] is not None else "QRC00000029"
            issuer_display = self.combos_col1[2].currentText() if len(self.combos_col1) > 2 else "[已脱敏]"
            # 从显示文本中提取工号
            if " (" in issuer_display and issuer_display.endswith(")"):
                issuer_name = issuer_display.split(" (")[1].rstrip(")")
            else:
                issuer_name = issuer_display
            shipment_quantity = self.quantity_edit.text() if self.quantity_edit is not None else "1"
            remark = self.remark_edit.text() if self.remark_edit is not None else "华南客户"
            distributor_name = self.combos_col1[7].currentText() if len(self.combos_col1) > 7 else ""
            
            # 获取数量单位
            unit = "m³"
            for radio in self.findChildren(QRadioButton):
                if isinstance(radio, QRadioButton) and radio.isChecked():
                    if "m²" in radio.text():
                        unit = "m²"
                    break
            
            # 获取执行标准文本（仅显示标准，不含单位）
            standard_text = self.quantity_edit.text() if self.quantity_edit is not None else "GB/T10801.2-2018"
            
            # 获取二维码序列号
            qr_sequence = self.widgets_col2[2].text() if len(self.widgets_col2) > 2 else "B-DEMO-000000001"
            
            # 构建指向云端展示页面的链接 - 根据公司动态生成URL
            company_website = self.get_company_website(company_name)
            company_prefix = self.get_company_prefix(company_name)
            
            # 使用新的二维码编号格式：公司简称-Q + 9位流水号
            if len(qr_sequence) > 3 and qr_sequence.startswith("QRC"):
                # 从旧的QRC格式中提取流水号
                try:
                    old_num = int(qr_sequence[3:])
                    qr_sequence = f"{company_prefix}-Q{old_num:09d}"
                except ValueError:
                    # 如果解析失败，生成新的9位流水号
                    qr_sequence = f"{company_prefix}-Q000000001"
            elif not qr_sequence.startswith(f"{company_prefix}-Q"):
                # 如果不是正确的格式，生成新的9位流水号
                qr_sequence = f"{company_prefix}-Q000000001"
            
            # 更新输入框显示新的二维码序号
            self.widgets_col2[2].setText(qr_sequence)
            
# 使用云端服务器域名，指向动态公开页面，无需登录验证，直接显示数据库数据
            # 统一由 generate_qr_url 生成扫码URL
            qr_content = self.generate_qr_url(qr_sequence)

            # 优化显示内容（隐藏题头，用分号分隔）
            display_content = f"{company_name}；{company_website}；{product_type}；{product_spec}；{product_feature}；{product_color}；{plate_number}；{service_phone}；{production_time}；{batch_number}；{inspection_result}；{qr_sequence}；{issuer_name}；{standard_text}；{distributor_name}；{remark}"

            # 准备保存到数据库的数据
            data_to_save = {
                'company_name': company_name,
                'product_type': product_type,
                'product_spec': product_spec,
                'product_color': product_color,
                'product_feature': product_feature,
                'quantity': shipment_quantity,
                'unit': unit,
                'batch_number': batch_number,
                'production_date': production_time,
                'qr_sequence': qr_sequence,
                'issuer_name': issuer_name,
                'distributor_name': distributor_name,
                'plate_number': plate_number,
                'phone': service_phone,
                'remark': remark,
                'official_website': company_website
            }
            
            # 注释掉自动保存数据到数据库的逻辑，只在实际打印时才保存
            # self.save_qr_data_to_db(data_to_save)

            # 更新批次号输入框提示
            if len(self.widgets_col2) > 4 and self.widgets_col2[4] is not None:
                current_suffix = self.widgets_col2[4].text().strip()
                if not current_suffix:
                    self.widgets_col2[4].setText(f"{auto_prefix}001")  # 默认完整11位批次号
                
            # 更新显示区域（水平布局）
            if self.qr_info_edit is not None:
                self.qr_info_edit.setPlainText(display_content)
            
            # 生成高容错率二维码，确保手机可识别
            self.generate_high_quality_qr_code(qr_content)
            self.current_qr_content = qr_content
            
        except Exception as e:
            print(f"更新二维码内容失败: {e}")
            qr_content = "示例品牌A QRC00000001"
            self.generate_minimal_qr_code(qr_content)
            self.current_qr_content = qr_content

    def get_company_website(self, company_name):
        """根据公司名称获取公司网址"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'qr_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 查询公司网址
            cursor.execute("SELECT website FROM companies WHERE name = ?", (company_name,))
            result = cursor.fetchone()
            
            conn.close()
            
            # 如果找到公司网址则返回，否则返回默认网址
            if result and result[0]:
                return result[0]
            else:
                return "https://www.your-company-domain.com"
        except Exception as e:
            print(f"获取公司网址失败: {e}")
            return "https://www.your-company-domain.com"

    def get_company_prefix(self, company_name):
        """根据公司名称获取公司简称前缀"""
        company_prefix_map = {
            "[已脱敏城市]示例品牌A有限公司": "B",
            "[已脱敏城市]示例品牌B材料有限公司": "A",
            "示例品牌A": "B",
            "示例品牌B": "A"
        }
        
        # 精确匹配
        if company_name in company_prefix_map:
            return company_prefix_map[company_name]
        
        # 模糊匹配
        for key, prefix in company_prefix_map.items():
            if key in company_name or company_name in key:
                return prefix
        
        # 默认使用B
        return "B"

    def save_qr_data_to_db(self, data):
        """保存二维码数据到数据库，供手机端查询"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'qr_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS qr_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT,
                    product_type TEXT,
                    product_spec TEXT,
                    product_color TEXT,
                    product_feature TEXT,
                    quantity TEXT,
                    unit TEXT,
                    batch_number TEXT,
                    production_date TEXT,
                    qr_sequence TEXT UNIQUE,
                    issuer_name TEXT,
                    distributor_name TEXT,
                    plate_number TEXT,
                    phone TEXT,
                    remark TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    official_website TEXT
                )
            ''')
            
            # 插入或更新数据
            cursor.execute('''
                INSERT OR REPLACE INTO qr_records (
                    company_name, product_type, product_spec, product_color,
                    product_feature, quantity, unit, batch_number, production_date,
                    qr_sequence, issuer_name, distributor_name, plate_number, phone, remark, official_website
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['company_name'], data['product_type'], data['product_spec'],
                data['product_color'], data['product_feature'], data['quantity'],
                data['unit'], data['batch_number'], data['production_date'],
                data['qr_sequence'], data['issuer_name'], data['distributor_name'],
                data['plate_number'], data['phone'], data['remark'], data['official_website']
            ))
            
            conn.commit()
            conn.close()
            print(f"二维码数据已保存: {data['qr_sequence']}")
            
        except Exception as e:
            print(f"保存二维码数据失败: {e}")

    def modify_data(self):
        """修改数据 - 解锁锁定状态"""
        try:
            if not self.is_locked and not self.is_confirmed:
                QMessageBox.information(self, "提示", "当前已经是可编辑状态，无需解锁")
                return
                
            self.is_locked = False
            self.is_confirmed = False
            self.update_controls_state()
            QMessageBox.information(self, "解锁成功", "已进入可编辑状态，可以进行数据选择和输入")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"修改数据失败: {str(e)}")

    def reset_form(self):
        """重置表单 - 恢复到默认状态"""
        try:
            reply = QMessageBox.question(
                self,
                "确认重置",
                "确定要将二维码打印页面重置为默认状态吗？\n\n这将清除所有已输入的数据。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
            # 重置所有下拉框
            for combo in self.combos_col1:
                combo.setCurrentIndex(0)
            
            # 重置所有输入框
            for widget in self.widgets_col2 + [self.quantity_edit]:
                if isinstance(widget, QLineEdit):
                    widget.clear()
                elif isinstance(widget, QDateTimeEdit):
                    widget.setDateTime(QDateTime.currentDateTime())
                elif hasattr(widget, 'setCurrentIndex'):
                    widget.setCurrentIndex(0)
            
            # 重置备注
            if self.remark_edit is not None:
                self.remark_edit.clear()
            
            # 重置单选按钮 - 默认选择立方米
            for radio in self.findChildren(QRadioButton):
                if isinstance(radio, QRadioButton) and "立方米" in radio.text():
                    radio.setChecked(True)
                    break
            
            # 重置状态变量
            self.is_locked = False
            self.is_confirmed = False
            
            # 清除验证错误
            self.validation_errors.clear()
            self.update_validation_display()
            
            # 更新控件状态
            self.update_controls_state()
            
            # 更新二维码内容为正确的URL
            self.update_qr_content()
            
            QMessageBox.information(self, "重置成功", "页面已重置为默认状态，可以进行任何操作")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"重置表单失败: {str(e)}")
            
    def update_controls_state(self):
        """更新控件状态"""
        enabled = not self.is_locked and not self.is_confirmed
        
        # 更新所有下拉框
        for combo in self.combos_col1:
            if combo is not None:
                combo.setEnabled(enabled)
                
        # 更新所有输入框
        for widget in self.widgets_col2 + [self.quantity_edit]:
            if widget is not None:
                if hasattr(widget, 'setEnabled'):
                    widget.setEnabled(enabled)
        
        # 更新备注输入框
        if self.remark_edit is not None:
            self.remark_edit.setEnabled(enabled)
        
        # 更新单选按钮
        for radio in self.findChildren(QRadioButton):
            if isinstance(radio, QRadioButton):
                radio.setEnabled(enabled)
        
        # 更新按钮状态
        self.modify_btn.setEnabled(True)  # 修改按钮始终可用
        self.reset_btn.setEnabled(True)   # 重置按钮始终可用
        self.confirm_btn.setEnabled(not self.is_locked and not self.is_confirmed)
        self.lock_btn.setEnabled(not self.is_locked and not self.is_confirmed and len(self.validation_errors) == 0)
        self.preview_btn_left.setEnabled(True)
        self.print_btn_left.setEnabled(True)
        self.batch_print_btn.setEnabled(True)

    def apply_permissions(self, user):
        """按角色权限控制二维码打印页按钮可用性"""
        try:
            # 视图权限（预览/查看）
            can_view = has_permission(user, "qr.view")
            if hasattr(self, "preview_btn"):
                self.preview_btn.setEnabled(bool(can_view))
            if hasattr(self, "preview_btn_left"):
                self.preview_btn_left.setEnabled(bool(can_view))

            # 下载权限
            can_download = has_permission(user, "qr.download")
            if hasattr(self, "download_btn"):
                self.download_btn.setEnabled(bool(can_download))

            # 打印权限（左上打印按钮与列表区打印按钮）
            can_print = has_permission(user, "qr.print")
            if hasattr(self, "print_btn_left"):
                self.print_btn_left.setEnabled(bool(can_print))
            if hasattr(self, "print_btn"):
                self.print_btn.setEnabled(bool(can_print))

            # 批量打印：若无独立配置，允许以 qr.print 作为后备
            can_batch = has_permission(user, "qr.batch_print") or can_print
            if hasattr(self, "batch_print_btn"):
                self.batch_print_btn.setEnabled(bool(can_batch))
        except Exception:
            # 安全兜底：不影响页面正常显示
            pass

    def confirm_data(self):
        """确认数据 - 带确认对话框"""
        try:
            if self.is_locked:
                QMessageBox.warning(self, "警告", "数据已被锁定，无法确认。请先解锁")
                return
                
            # 执行验证
            self.perform_validation()
            
            if self.validation_errors:
                error_msg = "请修正以下错误：\n\n"
                for field, error in self.validation_errors.items():
                    error_msg += f"• {field}: {error}\n"
                QMessageBox.warning(self, "数据验证失败", error_msg)
                return
            
            # 显示确认对话框
            reply = QMessageBox.question(
                self,
                "确认修改",
                "确实要修改当前的数据信息内容吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.is_confirmed = True
                self.update_controls_state()
                QMessageBox.information(self, "确认成功", "数据已确认，如需修改请点击'修改'按钮")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"确认数据失败: {str(e)}")

    def lock_form(self):
        """锁定表单 - 锁定所有数据字段"""
        try:
            if self.is_locked:
                QMessageBox.information(self, "提示", "数据已经是锁定状态")
                return
                
            # 执行验证
            self.perform_validation()
            
            if self.validation_errors:
                error_msg = "请先修正以下错误再锁定：\n\n"
                for field, error in self.validation_errors.items():
                    error_msg += f"• {field}: {error}\n"
                QMessageBox.warning(self, "验证失败", error_msg)
                return
            
            self.is_locked = True
            self.update_controls_state()
            QMessageBox.information(self, "锁定成功", "数据已锁定，无法进行选择和输入操作")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"锁定数据失败: {str(e)}")

    def download_qr(self):
        """下载二维码"""
        try:
            # 显示导出选项对话框
            export_dialog = QMessageBox()
            export_dialog.setWindowTitle("导出选项")
            export_dialog.setText("请选择导出格式：")
            export_dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            
            # 添加自定义按钮
            excel_btn = export_dialog.addButton("导出Excel", QMessageBox.ActionRole)
            csv_btn = export_dialog.addButton("导出CSV", QMessageBox.ActionRole)
            json_btn = export_dialog.addButton("导出JSON", QMessageBox.ActionRole)
            
            result = export_dialog.exec_()
            
            if export_dialog.clickedButton() == excel_btn:
                self.export_to_excel()
            elif export_dialog.clickedButton() == csv_btn:
                self.export_to_csv()
            elif export_dialog.clickedButton() == json_btn:
                self.export_to_json()
            elif result == QMessageBox.Ok:
                # 默认导出Excel
                self.export_to_excel()
                
        except Exception as e:
            QMessageBox.warning(self, "导出错误", f"导出失败: {e}")

    def export_to_excel(self):
        """导出到Excel格式"""
        try:
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存Excel文件", 
                f"二维码记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV文件 (*.csv);;所有文件 (*)"
            )
            
            if not file_path:
                return
            
            # 写入CSV文件（Excel可以打开）
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入表头
                headers = ["序", "发行日期时间", "姓名", "工号", "种类", "型号规格", "颜色", "功能特性", "生产日期时间", "数量", "业务员姓名", "经销商名称", "物流车牌号"]
                writer.writerow(headers)
                
                # 写入数据
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "导出成功", f"数据已导出到: {file_path}")
            
        except Exception as e:
            QMessageBox.warning(self, "导出错误", f"导出Excel失败: {e}")

    def export_to_csv(self):
        """导出到CSV格式"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存CSV文件", 
                f"二维码记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV文件 (*.csv);;所有文件 (*)"
            )
            
            if not file_path:
                return
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入表头
                headers = ["序", "发行日期时间", "姓名", "工号", "种类", "型号规格", "颜色", "功能特性", "生产日期时间", "数量", "业务员姓名", "经销商名称", "物流车牌号"]
                writer.writerow(headers)
                
                # 写入数据
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "导出成功", f"数据已导出到: {file_path}")
            
        except Exception as e:
            QMessageBox.warning(self, "导出错误", f"导出CSV失败: {e}")

    def export_to_json(self):
        """导出到JSON格式"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存JSON文件", 
                f"二维码记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON文件 (*.json);;所有文件 (*)"
            )
            
            if not file_path:
                return
            
            # 准备数据
            headers = ["序", "发行日期时间", "姓名", "工号", "种类", "型号规格", "颜色", "功能特性", "生产日期时间", "数量", "业务员姓名", "经销商名称", "物流车牌号"]
            
            data = {
                "export_time": datetime.now().isoformat(),
                "total_records": self.table.rowCount(),
                "headers": headers,
                "records": []
            }
            
            # 收集表格数据
            for row in range(self.table.rowCount()):
                record = {}
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    record[headers[col]] = item.text() if item else ""
                data["records"].append(record)
            
            # 写入JSON文件
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "导出成功", f"数据已导出到: {file_path}")
            
        except Exception as e:
            QMessageBox.warning(self, "导出错误", f"导出JSON失败: {e}")

    def export_qr_image(self):
        """导出二维码图片"""
        try:
            qr_pixmap = self.qr_preview_label.pixmap()
            if not qr_pixmap or qr_pixmap.isNull():
                QMessageBox.warning(self, "导出错误", "没有可导出的二维码图片")
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存二维码图片", 
                f"二维码_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                "PNG图片 (*.png);;JPEG图片 (*.jpg);;所有文件 (*)"
            )
            
            if not file_path:
                return
            
            # 保存图片
            qr_pixmap.save(file_path)
            QMessageBox.information(self, "导出成功", f"二维码图片已导出到: {file_path}")
            
        except Exception as e:
            QMessageBox.warning(self, "导出错误", f"导出二维码图片失败: {e}")

    def generate_unified_label_image(self, for_print=True, cached_logo=None):
        """统一的标签图像生成函数 - 打印功能为主，预览功能完全复制"""
        from PIL import Image, ImageDraw, ImageFont
        import qrcode
        import io
        from datetime import datetime
        import os
        
        # 终极修复：100%填充超级标签（1000×800像素）- 以打印功能为蓝本
        width, height = 1000, 800
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        try:
            font_title = ImageFont.truetype("msyh.ttc", 42)  # 最大字体
            font_en = ImageFont.truetype("arial.ttf", 28)    # 增大英文名称字号
            font_table = ImageFont.truetype("msyh.ttc", 28)  # 最大表格文字
            font_bold = ImageFont.truetype("msyhbd.ttc", 48)  # 放大1.5倍的粗体微软雅黑
            font_small = ImageFont.truetype("msyhbd.ttc", 36)  # 放大1.5倍的粗体微软雅黑小字
        except:
            font_title = font_en = font_table = font_bold = font_small = None
            
        company_cn = self.combos_col1[0].currentText() or "（未选择公司）"
        company_en = self.company_en_map.get(company_cn, "") if hasattr(self, 'company_en_map') else ""
        
        # 添加公司LOGO到左上角 - 放大1.2倍，向上移动3mm（12像素）
        logo_x = 20
        logo_y = 8  # 向上移动3mm = 12像素
        
        # 性能优化：优先使用缓存的LOGO
        if cached_logo:
            try:
                img.paste(cached_logo, (logo_x, logo_y))
            except Exception as e:
                print(f"粘贴缓存的LOGO失败: {e}")
        else:
            # 如果没有缓存的LOGO，则按原方式加载
            logo_path = None
            assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
            
            if "示例品牌A" in company_cn or "示例" in company_cn:
                logo_path = os.path.join(assets_dir, "示例品牌A 透明.png")
            elif "示例品牌B" in company_cn or "示例" in company_cn:
                logo_path = os.path.join(assets_dir, "示例品牌B 透明.png")
            
            if logo_path and os.path.exists(logo_path):
                try:
                    logo_img = Image.open(logo_path)
                    if logo_img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', logo_img.size, (255, 255, 255))
                        background.paste(logo_img, mask=logo_img.split()[-1] if logo_img.mode == 'RGBA' else None)
                        logo_img = background
                    
                    logo_size = 102
                    logo_img = logo_img.resize((logo_size, logo_size), Image.LANCZOS)
                    img.paste(logo_img, (logo_x, logo_y))
                except Exception as e:
                    print(f"加载公司LOGO失败: {e}")
        
        # 精准调整：中文52mm处，英文36mm处
        chinese_x = 208  # 52mm * 4像素/mm = 208像素
        draw.text((chinese_x, 10), company_cn, fill="black", font=font_title)
        
        # 英文名称36mm处
        english_x = 144  # 36mm * 4像素/mm = 144像素
        full_company_en = company_en or "Dongguan Example Brand A Co., Ltd."
        draw.text((english_x, 60), full_company_en, fill="black", font=font_en)
        
        # 终极100%填充布局 - 修复二维码与合格章居中对齐
        table_left = 20    # 从边缘开始
        table_right = 550  # 最大化表格
        table_top = 100    # 增大间距避免重叠
        table_bottom = 580  # 增大表格高度适应行距
        
        # 修复：合并第一行为一个单元格，用于显示"产品信息"
        product_info_height = 60
        
        # 绘制合并后的产品信息单元格
        draw.rectangle([table_left, table_top, table_right, table_top + product_info_height], outline="#3b6e99", width=4)
        
        # 产品信息居中显示在合并单元格内（水平和垂直居中）
        qr_sequence = self.widgets_col2[2].text() if len(self.widgets_col2) > 2 else "B-DEMO-000000001"
        product_info_text = f"QRC No.：{qr_sequence}"
        try:
            product_info_font = ImageFont.truetype("msyhbd.ttc", 36)
        except:
            product_info_font = None
        
        # 计算居中位置 - 根据实际文本长度调整
        try:
            text_bbox = draw.textbbox((0, 0), product_info_text, font=product_info_font)
            actual_text_width = text_bbox[2] - text_bbox[0]
            actual_text_height = text_bbox[3] - text_bbox[1]
        except:
            # 如果无法获取精确尺寸，使用估算值
            actual_text_width = len(product_info_text) * 36  # 每个字符约36像素
            actual_text_height = 36
        
        text_x = table_left + (table_right - table_left - actual_text_width) // 2
        text_y = table_top + (product_info_height - actual_text_height) // 2
        draw.text((text_x, text_y), product_info_text, fill="#3b6e99", font=product_info_font)
        
        # 调整表格布局：扩大第二列宽度以容纳28个中文字
        col1_width = 160  # 第一列宽度（标签列）
        col2_width = 320  # 第二列宽度（数值列，可容纳28个中文字）
        
        split_x = table_left + col1_width
        
        prod_date = ""
        if len(self.widgets_col2)>3 and hasattr(self.widgets_col2[3], 'dateTime'):
            dt = self.widgets_col2[3].dateTime()
            prod_date = dt.toString('yyyy年MM月dd日')
            
        standard_text = self.quantity_edit.text() if self.quantity_edit.text() else "GB/T10801.2-2018"
        
        # 修复：8行数据信息（删除冒号并扩大第二列宽度）
        fields = [
            ("产品名称", self.combos_col1[3].currentText() if len(self.combos_col1) > 3 else "XPS-A1"),
            ("产品规格", self.combos_col1[4].currentText() if len(self.combos_col1) > 4 else "30mm"),
            ("产品特性", self.combos_col1[5].currentText() if len(self.combos_col1) > 5 else "保温隔热"),
            ("产品颜色", self.combos_col1[6].currentText() if len(self.combos_col1) > 6 else "白色"),
            ("执行标准", standard_text),
            ("产品批次号", self.widgets_col2[4].text() if len(self.widgets_col2) > 4 else "20240720001"),
            ("生产日期", prod_date),
            ("生产地址", "[已脱敏地址]")
        ]
        
        # 重新计算表格布局：8行数据，每行高度均匀分布，调整为1.3倍行距
        data_start_y = table_top + product_info_height
        data_end_y = table_bottom
        available_height = data_end_y - data_start_y
        
        # 8行数据的行高，调整为1.3倍
        base_row_height = available_height / 8
        row_height = base_row_height * 1.3  # 增加1.3倍行距
        
        # 由于行距增加，需要重新计算表格底部位置
        new_table_bottom = data_start_y + 8 * row_height
        table_bottom = int(new_table_bottom)
        
        # 绘制7条水平分割线（形成8个完整区域）
        for i in range(1, 8):
            y = data_start_y + i * row_height
            draw.line([(table_left, int(y)), (table_right, int(y))], fill="#3b6e99", width=4)
        
        # 修复BUG：绘制完整的表格边框（左、右、下边框）
        # 左边框
        draw.line([(table_left, table_top), (table_left, table_bottom)], fill="#3b6e99", width=4)
        # 右边框  
        draw.line([(table_right, table_top), (table_right, table_bottom)], fill="#3b6e99", width=4)
        # 下边框
        draw.line([(table_left, table_bottom), (table_right, table_bottom)], fill="#3b6e99", width=4)
        
        # 修复BUG：垂直分割线（第一列与第二列之间），确保延伸到重新计算后的表格底部，覆盖第8、9行
        draw.line([(split_x, table_top + product_info_height), (split_x, table_bottom)], fill="#3b6e99", width=4)
        
        # 绘制数据内容 - 使用1.3倍行距
        for i, (label, value) in enumerate(fields):
            # 计算每行的精确Y坐标（使用1.3倍行距）
            cell_top = data_start_y + i * row_height
            cell_bottom = data_start_y + (i + 1) * row_height
            
            # 文字垂直居中的精确位置（28px字体高度）
            text_y = cell_top + (row_height - 28) // 2
            
            # 第一列文字：完全在单元格内，中部靠左对齐（已删除冒号）
            label_x = table_left + 15
            draw.text((label_x, int(text_y)), label, fill="black", font=font_table)
            
            # 第二列文字：完全在单元格内，中部靠左对齐
            value_x = split_x + 15
            value_text = str(value)
            draw.text((value_x, int(text_y)), value_text, fill="black", font=font_table)
            
        # [KEY] 关键修复：生成正确的产品信息URL（确保手机扫描能跳转）
        qr_sequence = self.widgets_col2[2].text() if len(self.widgets_col2) > 2 else ""
        company_name = self.combos_col1[0].currentText() if len(self.combos_col1) > 0 else ""
        
        # 根据公司确定正确的URL
        # 统一由 generate_qr_url 生成扫码URL
        qr_content = self.generate_qr_url(qr_sequence)
        print(f"[URL] 生成二维码URL: {qr_content}")
        
        # 更新当前二维码内容
        self.current_qr_content = qr_content
            
        # 终极二维码配置：超大尺寸+超高密度+超高容错
        qr = qrcode.QRCode(
            version=5,  # 最大版本15，使用5确保足够大
            error_correction=qrcode.ERROR_CORRECT_H,  # 最高容错率30%
            box_size=8,  # 每个模块8像素，超高密度
            border=0,    # 删除边框，让二维码直接显示
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # 添加公司LOGO到二维码
        qr_img = self.add_logo_to_qr_image(qr_img, company_cn)
        
        # 终极尺寸：350×350像素超大二维码
        qr_img = qr_img.resize((350, 350), Image.LANCZOS)  # 最高质量缩放
        
        # 终极100%填充布局 - 修复二维码与合格章居中对齐
        qr_size = 350
        qr_x = 625  # 右侧居中位置
        qr_y = 120  # 垂直居中起始位置
        img.paste(qr_img, (qr_x, qr_y))
        
        # 放大1.5倍的圆形章 - 垂直居中对齐，向上移动5mm（约15像素）
        circle_r = 120  # 80*1.5 = 120
        circle_x = qr_x + (qr_size - 2*circle_r) // 2  # 与二维码水平居中
        circle_y = qr_y + qr_size + 10  # 二维码下方10像素（从25像素再向上调整15像素）
        
        draw.ellipse([circle_x, circle_y, circle_x+2*circle_r, circle_y+2*circle_r], outline="#2ecc40", width=12)
        
        # 计算文字居中的位置 - 向上移动2mm（8像素） 和 向左移动2mm（8像素）
        text_y_center = circle_y + circle_r - 8  # 2mm = 8像素向上
        
        # "合格"文字向左移动总计4mm（16像素），向上移动2mm（8像素）
        draw.text((circle_x + circle_r - 46, text_y_center - 40), "合格", fill="#2ecc40", font=font_bold)
        # "检验员01"文字居中  
        draw.text((circle_x + circle_r - 70, text_y_center + 10), "检验员01", fill="#2ecc40", font=font_small)
        
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())
        return pixmap

    def preview_qr(self):
        """二维码预览功能 - 完全使用打印标签的样式"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtCore import Qt, QTimer
        
        # 弹窗显示
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle('二维码预览')
        preview_dialog.resize(1000, 800)
        layout = QVBoxLayout(preview_dialog)
        label = QLabel()
        
        # 使用统一的标签生成函数
        label.setPixmap(self.generate_unified_label_image(for_print=False))
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        btn_layout = QHBoxLayout()
        close_btn = QPushButton('关闭')
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        # 预览对话框中的5秒刷新定时器已删除 - 根据用户要求简化系统
        
        # 关闭按钮事件处理
        def on_close():
            """关闭弹窗"""
            preview_dialog.close()
        
        close_btn.clicked.connect(on_close)
        preview_dialog.exec_()

    def print_qr(self):
        """终极修复：绝对单次打印，零弹出，100%打印1张"""
        try:
            # 执行验证
            self.perform_validation()
            
            if self.validation_errors:
                error_msg = "请修正以下错误后再打印：\n\n"
                for field, error in self.validation_errors.items():
                    error_msg += f"{field}: {error}\n"
                QMessageBox.warning(self, "验证失败", error_msg)
                return
            
            # 终极静默打印：跳过所有对话框，直接打印
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSizeMM(QSizeF(100, 80))  # 100mm×80mm标签规格
            printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)
            
            # 终极静默打印：零用户交互
            painter = QPainter()
            if painter.begin(printer):
                label_pixmap = self.generate_label_image()
                page_rect = printer.pageRect()
                painter.drawPixmap(0, 0, page_rect.width(), page_rect.height(), label_pixmap)
                painter.end()
                
                # 先保存记录到数据库，确保数据一致性
                try:
                    self.save_qr_record()
                    print(f"单次打印数据保存成功，序号: {self.widgets_col2[2].text()}")
                    
                    # 数据保存成功后，生成新的二维码序号（为下次打印做准备）
                    self.generate_new_qr_sequence()
                    
                    print(f"单次打印完成，序号: {self.widgets_col2[2].text()}")
                except Exception as save_error:
                    print(f"单次打印数据保存失败: {save_error}")
                    QMessageBox.warning(self, "保存失败", f"数据保存失败，打印已取消：{str(save_error)}")
                    return
                
                # 静默成功提示（3秒后自动消失）
                msg = QMessageBox(self)
                msg.setWindowTitle("打印完成")
                msg.setText("[SUCCESS] 二维码标签已打印完成（1张）")
                msg.setStandardButtons(QMessageBox.Ok)
                QTimer.singleShot(3000, msg.close)  # 3秒后自动关闭
                msg.exec_()
            else:
                # 🎯 优化：显示打印机选择对话框
                printer_config = self.show_printer_selection_dialog("选择二维码打印机")
                if not printer_config:
                    QMessageBox.information(self, "取消", "用户取消了打印机选择")
                    return
                
                # 使用选中的打印机重新初始化
                try:
                    printer = QPrinter(QPrinter.HighResolution)
                    printer.setOutputFormat(QPrinter.NativeFormat)
                    printer.setPrinterName(printer_config['printer_name'])
                    
                    # 设置打印质量
                    if printer_config['high_quality']:
                        printer.setResolution(600)
                    else:
                        printer.setResolution(300)
                    
                    print(f"✅ 使用选定的打印机: {printer_config['printer_name']}")
                    
                except Exception as retry_error:
                    QMessageBox.critical(self, "打印失败", f"打印机 '{printer_config['printer_name']}' 初始化失败！\n\n错误: {str(retry_error)}\n\n请检查：\n1. 打印机连接状态\n2. 驱动程序\n3. 打印机就绪状态")
            
        except Exception as e:
            # 静默错误提示
            print(f"打印错误: {e}")

    def batch_print_qr(self):
        """批量打印二维码功能"""
        try:
            # 执行验证
            self.perform_validation()
            
            if self.validation_errors:
                error_msg = "请修正以下错误后再批量打印：\n\n"
                for field, error in self.validation_errors.items():
                    error_msg += f"- {field}: {error}\n"
                QMessageBox.warning(self, "验证失败", error_msg)
                return
            
            # 创建批量打印配置对话框
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QSpinBox, QPushButton, QHBoxLayout
            
            batch_dialog = QDialog(self)
            batch_dialog.setWindowTitle("批量打印配置")
            batch_dialog.setFixedSize(300, 200)
            
            layout = QVBoxLayout(batch_dialog)
            layout.setSpacing(15)
            
            # 打印数量设置
            label = QLabel("请输入打印份数（2-999张）：")
            label.setFont(QFont("Microsoft YaHei", 12))
            layout.addWidget(label)
            
            quantity_spinbox = QSpinBox()
            quantity_spinbox.setMinimum(2)  # 强制最小2张，区分单次打印
            quantity_spinbox.setMaximum(999)
            quantity_spinbox.setValue(2)
            quantity_spinbox.setFont(QFont("Microsoft YaHei", 12))
            layout.addWidget(quantity_spinbox)
            
            # 信息提示
            info_label = QLabel("系统将自动：\n- 每份递增生产时间5秒\n- 每份递增二维码序号1")
            info_label.setFont(QFont("Microsoft YaHei", 10))
            info_label.setStyleSheet("color: #666;")
            layout.addWidget(info_label)
            
            # 按钮区域
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            confirm_btn = QPushButton("开始批量打印")
            confirm_btn.setFont(QFont("Microsoft YaHei", 11))
            confirm_btn.setStyleSheet("""
                QPushButton {
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background: #45a049;
                }
            """)
            
            cancel_btn = QPushButton("取消")
            cancel_btn.setFont(QFont("Microsoft YaHei", 11))
            cancel_btn.setStyleSheet("""
                QPushButton {
                    background: #f44336;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background: #da190b;
                }
            """)
            
            button_layout.addWidget(cancel_btn)
            button_layout.addWidget(confirm_btn)
            layout.addLayout(button_layout)
            
            # 连接按钮事件
            confirm_btn.clicked.connect(batch_dialog.accept)
            cancel_btn.clicked.connect(batch_dialog.reject)
            
            result = batch_dialog.exec_()
            
            if result == QDialog.Accepted:
                print_count = quantity_spinbox.value()
                # 直接执行批量打印，无需二次确认
                self._execute_batch_print(print_count)
                
        except Exception as e:
            QMessageBox.warning(self, "批量打印错误", f"批量打印失败: {str(e)}")
            print(f"批量打印错误详情: {str(e)}")

    def _execute_batch_print(self, print_count, company_name=None):
        """执行批量打印的内部方法 - 优化为静默批量打印，并保证UI不阻塞"""
        from PIL import Image
        import os
        from PyQt5.QtWidgets import QApplication
        self._in_batch_print = True  # 标记进入批量打印，前台禁止同步FTP
        painter = None
        try:
            print(f"[BATCH] 开始批量打印, 份数={print_count}")
            # 获取基础数据
            base_production_date = self.widgets_col2[3].dateTime()
            
            if company_name is None:
                company_name = self.combos_col1[0].currentText() if self.combos_col1[0] is not None else "[已脱敏城市]示例品牌A有限公司"
            
            # 预加载和缓存公司LOGO
            cached_logo = None
            logo_path = None
            assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')

            if "示例品牌A" in company_name or "示例" in company_name:
                logo_path = os.path.join(assets_dir, "示例品牌A 透明.png")
            elif "示例品牌B" in company_name or "示例" in company_name:
                logo_path = os.path.join(assets_dir, "示例品牌B 透明.png")

            if logo_path and os.path.exists(logo_path):
                try:
                    logo_img = Image.open(logo_path)
                    if logo_img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', logo_img.size, (255, 255, 255))
                        background.paste(logo_img, mask=logo_img.split()[-1] if logo_img.mode == 'RGBA' else None)
                        logo_img = background
                    
                    logo_size = 102
                    cached_logo = logo_img.resize((logo_size, logo_size), Image.LANCZOS)
                except Exception as e:
                    print(f"预加载公司LOGO失败: {e}")

            company_prefix = self.get_company_prefix(company_name)
            
            base_num = self._get_max_sequence_number_atomic(company_name, company_prefix)
            print(f"批量打印开始，当前最大序号: {base_num}")
            
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSizeMM(QSizeF(100, 80))
            printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)
            
            painter = QPainter()
            if not painter.begin(printer):
                # 🎯 优化：显示打印机选择对话框
                printer_config = self.show_printer_selection_dialog("选择批量打印机")
                if not printer_config:
                    QMessageBox.information(self, "取消", "用户取消了批量打印")
                    return
                
                # 使用选中的打印机重新初始化
                try:
                    printer = QPrinter(QPrinter.HighResolution)
                    printer.setOutputFormat(QPrinter.NativeFormat)
                    printer.setPrinterName(printer_config['printer_name'])
                    
                    # 设置打印质量
                    if printer_config['high_quality']:
                        printer.setResolution(600)
                    else:
                        printer.setResolution(300)
                    
                    print(f"✅ 批量打印使用选定的打印机: {printer_config['printer_name']}")
                    
                except Exception as retry_error:
                    QMessageBox.critical(self, "批量打印失败", f"打印机 '{printer_config['printer_name']}' 初始化失败！\n\n错误: {str(retry_error)}\n\n请检查：\n1. 打印机连接状态\n2. 驱动程序\n3. 打印机就绪状态")
                return
            
            success_count = 0
            current_base_num = base_num
            
            app = QApplication.instance()
            for i in range(print_count):
                try:
                    # 保持界面响应，处理Qt事件队列
                    try:
                        app = QApplication.instance()
                        if app is not None:
                            app.processEvents()
                    except Exception:
                        pass
                    current_base_num += 1
                    current_qr_num = current_base_num
                    current_qr_sequence = f"{company_prefix}-Q{current_qr_num:09d}"
                    
                    print(f"批量打印第 {i+1} 份，使用序号: {current_qr_sequence}")
                    
                    current_date = base_production_date.addSecs(i * 5)
                    
                    self.widgets_col2[2].setText(current_qr_sequence)
                    self.widgets_col2[3].setDateTime(current_date)
                    
                    self.update_qr_content()
                    
                    try:
                        self.save_qr_record()
                        print(f"批量打印第 {i+1} 份数据保存成功，序号: {current_qr_sequence}")
                        
                        try:
                            label_pixmap = self.generate_label_image(cached_logo=cached_logo)
                            if not label_pixmap.isNull():
                                page_rect = printer.pageRect()
                                painter.drawPixmap(0, 0, page_rect.width(), page_rect.height(), label_pixmap)
                                
                                if i < print_count - 1:
                                    printer.newPage()
                                    
                                success_count += 1
                                print(f"批量打印成功第 {i+1} 份，序号: {current_qr_sequence}")
                            else:
                                print(f"批量打印第 {i+1} 份标签图像生成失败，但数据已保存")
                                success_count += 1
                        except Exception as print_error:
                            print(f"批量打印第 {i+1} 份打印失败: {print_error}，但数据已保存")
                            success_count += 1
                    except Exception as save_error:
                        print(f"批量打印第 {i+1} 份数据保存失败: {save_error}")
                        continue
                        
                except Exception as e:
                    print(f"批量打印第 {i+1} 份失败: {str(e)}")
                    continue
            
            final_max_num = self._get_max_sequence_number_atomic(company_name, company_prefix)
            next_qr_num = final_max_num + 1
            next_qr_sequence = f"{company_prefix}-Q{next_qr_num:09d}"
            
            while self._sequence_exists(next_qr_sequence):
                next_qr_num += 1
                next_qr_sequence = f"{company_prefix}-Q{next_qr_num:09d}"
            
            self.widgets_col2[2].setText(next_qr_sequence)
            print(f"批量打印完成，下次序号设置为: {next_qr_sequence}")
            
            painter.end()
            
            self.widgets_col2[3].setDateTime(base_production_date)
            self.update_qr_content()
            
            print(f"批量打印完成：共打印 {print_count} 份，成功 {success_count} 份")
                
        except Exception as e:
            QMessageBox.warning(self, "批量打印错误", f"批量打印执行失败: {str(e)}")
            print(f"批量打印执行错误: {str(e)}")
        finally:
            try:
                if painter is not None:
                    painter.end()
            except Exception:
                pass
            self._in_batch_print = False
            print("[BATCH] 批量打印结束，状态已清理")

    def print_qr_silent(self, printer):
        """静默打印二维码，无用户交互 - 使用与单次打印完全相同的样式"""
        try:
            # 直接执行打印，使用与单次打印相同的逻辑
            painter = QPainter()
            if not painter.begin(printer):
                return False
                
            # 使用统一的标签生成函数 - 与单次打印完全一致
            label_pixmap = self.generate_label_image()
            
            # 使用与单次打印完全相同的绘制方式
            page_rect = printer.pageRect()
            painter.drawPixmap(0, 0, page_rect.width(), page_rect.height(), label_pixmap)
            painter.end()
            return True
            
        except Exception as e:
            print(f"静默打印失败: {e}")
            return False

    def print_qr_correct(self, printer):
        """修正的打印方法 - 确保100%填充100×80mm标签纸"""
        try:
            # 设置标签尺寸为100mm×80mm规格
            printer.setPageSizeMM(QSizeF(100, 80))  # 100mm×80mm标签纸规格
            printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)  # 移除边距确保100%填充
            
            painter = QPainter()
            if not painter.begin(printer):
                print("无法启动打印机")
                return False
                
            # 获取标准标签图像
            label_pixmap = self.generate_label_image()
            if label_pixmap.isNull():
                print("标签图像生成失败")
                return False
            
            # 获取实际可用打印区域
            page_rect = printer.pageRect()
            
            # 100%填充整个标签纸，不留边距
            label_width = page_rect.width()
            label_height = page_rect.height()
            x_offset = 0
            y_offset = 0
            
            print(f"开始打印: 尺寸={label_width}x{label_height}, 100%填充标签纸")
            
            # 执行单次精确打印，确保100%填充
            painter.drawPixmap(int(x_offset), int(y_offset), label_width, label_height, label_pixmap)
            painter.end()
            print("打印完成 - 100%填充标签纸")
            return True
            
        except Exception as e:
            print(f"打印失败: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def print_qr_code_direct(self, printer):
        """直接打印二维码，跳过预览"""
        try:
            printer.setPageSize(QPrinter.A4)
            
            # 创建打印对话框
            dialog = QPrintDialog(printer, self)
            if dialog.exec_() == QPrintDialog.Accepted:
                # 直接执行打印
                painter = QPainter()
                if not painter.begin(printer):
                    print("Painter 初始化失败")
                    return False
                    
                label_pixmap = self.generate_label_image()
                label_width = 900
                label_height = 500
                page_rect = printer.pageRect()
                x_offset = (page_rect.width() - label_width) / 2
                y_offset = (page_rect.height() - label_height) / 2
                # 修正：使用完整页面尺寸确保填充整个标签纸
            page_rect = printer.pageRect()
            label_width = page_rect.width() - 4
            label_height = page_rect.height() - 4
            x_offset = 2
            y_offset = 2
            painter.drawPixmap(int(x_offset), int(y_offset), label_width, label_height, label_pixmap)
            painter.end()
            return True
        except Exception as e:
            print(f"打印二维码标签时出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_label_image(self, cached_logo=None):
        """生成适配100×80mm标签的标签图像 - 使用统一函数"""
        return self.generate_unified_label_image(for_print=True, cached_logo=cached_logo)

    def print_qr_code(self, printer):
        """打印二维码标签，样式与弹窗预览一致"""
        try:
            # 创建打印对话框
            dialog = QPrintDialog(printer, self)
            if dialog.exec_() != QPrintDialog.Accepted:
                return False
                
            painter = QPainter()
            if not painter.begin(printer):
                print("Painter 初始化失败")
                return False
                
            label_pixmap = self.generate_label_image()
            label_width = 750
            label_height = 380
            page_rect = printer.pageRect()
            x_offset = (page_rect.width() - label_width) / 2
            y_offset = (page_rect.height() - label_height) / 2
            # 修正：使用完整页面尺寸确保填充整个标签纸
            page_rect = printer.pageRect()
            label_width = page_rect.width() - 4
            label_height = page_rect.height() - 4
            x_offset = 2
            y_offset = 2
            painter.drawPixmap(int(x_offset), int(y_offset), label_width, label_height, label_pixmap)
            painter.end()
            return True
            
        except Exception as e:
            print(f"打印二维码标签时出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def print_table(self):
        """打印表格"""
        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPrinter.A4)
            printer.setOrientation(QPrinter.Landscape)  # 横向打印
            
            dialog = QPrintDialog(printer, self)
            if dialog.exec_() == QPrintDialog.Accepted:
                preview = QPrintPreviewDialog(printer, self)
                preview.paintRequested.connect(lambda p: self.print_table_content(p))
                preview.exec_()
        except Exception as e:
            QMessageBox.warning(self, "打印错误", f"打印表格失败: {e}")

    def print_table_content(self, printer):
        """打印表格内容"""
        try:
            painter = QPainter()
            painter.begin(printer)
            
            # 设置字体
            title_font = QFont("微软雅黑", 14, QFont.Bold)
            header_font = QFont("微软雅黑", 10, QFont.Bold)
            content_font = QFont("微软雅黑", 9)
            
            # 获取页面尺寸
            page_rect = printer.pageRect()
            x_margin = 30
            y_margin = 30
            content_width = page_rect.width() - 2 * x_margin
            content_height = page_rect.height() - 2 * y_margin
            
            # 绘制标题
            painter.setFont(title_font)
            title = "二维码打印记录表"
            title_rect = painter.boundingRect(x_margin, y_margin, content_width, 40, Qt.AlignCenter, title)
            painter.drawText(title_rect, title)
            
            # 绘制表头
            painter.setFont(header_font)
            headers = ["序", "发行日期时间", "姓名", "工号", "种类", "型号规格", "颜色", "功能特性", "生产日期时间", "数量", "业务员姓名", "经销商名称", "物流车牌号"]
            
            col_width = content_width // len(headers)
            row_height = 25
            header_y = y_margin + 60
            
            # 绘制表头背景
            painter.fillRect(x_margin, header_y, content_width, row_height, QColor(234, 246, 255))
            
            # 绘制表头文字
            for i, header in enumerate(headers):
                x = x_margin + i * col_width
                painter.drawRect(x, header_y, col_width, row_height)
                painter.drawText(x + 5, header_y, col_width - 10, row_height, Qt.AlignCenter, header)
            
            # 绘制表格数据
            painter.setFont(content_font)
            data_y = header_y + row_height
            
            for row in range(self.table.rowCount()):
                if data_y + row_height > page_rect.height() - y_margin:
                    # 需要新页面
                    printer.newPage()
                    data_y = y_margin + 60
                
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    text = item.text() if item else ""
                    x = x_margin + col * col_width
                    painter.drawRect(x, data_y, col_width, row_height)
                    painter.drawText(x + 5, data_y, col_width - 10, row_height, Qt.AlignCenter, text)
                
                data_y += row_height
            
            # 绘制打印信息
            painter.setFont(QFont("微软雅黑", 8))
            print_info = f"打印时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 共 {self.table.rowCount()} 条记录"
            painter.drawText(x_margin, page_rect.height() - y_margin - 20, content_width, 20, Qt.AlignRight, print_info)
            
            painter.end()
            
        except Exception as e:
            print(f"打印表格时出错: {e}")

    def init_database_connection(self):
        """初始化数据库连接并确保表结构完整"""
        try:
            # 连接数据库文件
            db_path = DB_PATH
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            
            # 检查并添加新字段（如果不存在）
            try:
                # 检查print_user_name字段是否存在
                self.cursor.execute("PRAGMA table_info(qr_records)")
                columns = [column[1] for column in self.cursor.fetchall()]
                
                if 'print_user_name' not in columns:
                    self.cursor.execute("ALTER TABLE qr_records ADD COLUMN print_user_name TEXT")
                    logging.getLogger(__name__).debug("[SUCCESS] 添加print_user_name字段")
                    
                if 'print_user_employee_id' not in columns:
                    self.cursor.execute("ALTER TABLE qr_records ADD COLUMN print_user_employee_id TEXT")
                    logging.getLogger(__name__).debug("[SUCCESS] 添加print_user_employee_id字段")
                    
                self.conn.commit()
            except Exception as alter_error:
                print(f"[WARNING] 数据库表结构更新警告: {alter_error}")
            
            logging.getLogger(__name__).debug("[SUCCESS] 数据库连接成功")
            
        except Exception as e:
            print(f"[ERROR] 数据库连接失败: {e}")
            QMessageBox.warning(self, "数据库错误", f"数据库连接失败: {e}")

    def create_tables(self):
        """创建数据表"""
        # 公司表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                english_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 部门表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        ''')
        
        # 员工表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                employee_id TEXT UNIQUE,
                department_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments (id)
            )
        ''')
        
        # 产品表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                spec TEXT NOT NULL,
                feature TEXT,
                color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 经销商表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS distributors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                contact_person TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 二维码记录表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS qr_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER,
                department_id INTEGER,
                issuer_id INTEGER,
                product_id INTEGER,
                distributor_id INTEGER,
                salesperson_id INTEGER,
                company_name TEXT,
                product_type TEXT,
                product_spec TEXT,
                product_color TEXT,
                product_feature TEXT,
                quantity INTEGER,
                unit TEXT,
                batch_number TEXT,
                plate_number TEXT,
                phone TEXT,
                qr_sequence TEXT,
                production_date TIMESTAMP,
                issuer_name TEXT,
                distributor_name TEXT,
                remark TEXT,
                standard TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id),
                FOREIGN KEY (department_id) REFERENCES departments (id),
                FOREIGN KEY (issuer_id) REFERENCES staff (id),
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (distributor_id) REFERENCES distributors (id),
                FOREIGN KEY (salesperson_id) REFERENCES staff (id)
            )
        ''')
        
        # 为现有表添加缺失的列（如果不存在）
        try:
            # 检查并添加缺失的列
            missing_columns = [
                ('company_name', 'TEXT'),
                ('product_type', 'TEXT'),
                ('product_spec', 'TEXT'),
                ('product_color', 'TEXT'),
                ('product_feature', 'TEXT'),
                ('issuer_name', 'TEXT'),
                ('distributor_name', 'TEXT'),
                ('standard', 'TEXT')
            ]
            
            for column_name, column_type in missing_columns:
                try:
                    self.cursor.execute(f'ALTER TABLE qr_records ADD COLUMN {column_name} {column_type}')
                    print(f"添加列: {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        pass  # 列已存在，忽略
                    else:
                        print(f"添加列 {column_name} 失败: {e}")
        except Exception as e:
            print(f"更新表结构失败: {e}")
        
        self.conn.commit()

    def insert_sample_data(self):
        """插入示例数据"""
        try:
            # 调试信息：开始插入数据
            print("开始插入示例数据")
            
            # 确保数据库连接正确
            print(f"数据库连接: {self.conn}")
            
            # 验证公司数据插入
            self.cursor.execute("SELECT COUNT(*) FROM companies")
            count = self.cursor.fetchone()[0]
            print(f"公司表当前数据量: {count}")
            
            # 检查所有表的数据量
            self.cursor.execute("SELECT COUNT(*) FROM companies")
            companies_count = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM departments")
            departments_count = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM staff")
            staff_count = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM products")
            products_count = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM distributors")
            distributors_count = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM qr_records")
            qr_records_count = self.cursor.fetchone()[0]
            
            if getattr(self, "_debug_mode", False):
                print(f"插入后各表数据量: 公司={companies_count}, 部门={departments_count}, 员工={staff_count}, 产品={products_count}, 经销商={distributors_count}, 二维码记录={qr_records_count}")
            
            print("示例数据插入成功")
            
        except Exception as e:
            print(f"插入示例数据失败: {e}")
            # 打印详细的错误信息
            import traceback
            traceback.print_exc()

    def load_data_to_combos(self):
        """加载数据到下拉框"""
        try:
            # 调试信息：检查控件列表长度
            if getattr(self, "_debug_mode", False):
                print("combos_col1 长度:", len(self.combos_col1))
            if getattr(self, "_debug_mode", False):
                print("widgets_col2 长度:", len(self.widgets_col2))
            if getattr(self, "_debug_mode", False):
                print("数据库连接状态: 正常")

            self.cursor.execute("SELECT COUNT(*) FROM companies")
            if getattr(self, "_debug_mode", False):
                if getattr(self, "_debug_mode", False): print(f"表数据量信息")

            self.cursor.execute("SELECT COUNT(*) FROM departments")
            if getattr(self, "_debug_mode", False):
                if getattr(self, "_debug_mode", False): print(f"表数据量信息")

            self.cursor.execute("SELECT COUNT(*) FROM staff")
            if getattr(self, "_debug_mode", False):
                if getattr(self, "_debug_mode", False): print(f"表数据量信息")

            self.cursor.execute("SELECT COUNT(*) FROM products")
            if getattr(self, "_debug_mode", False):
                if getattr(self, "_debug_mode", False): print(f"表数据量信息")

            self.cursor.execute("SELECT COUNT(*) FROM distributors")
            if getattr(self, "_debug_mode", False):
                if getattr(self, "_debug_mode", False): print(f"表数据量信息")

            # 设置生产日期时间为当前时间
            if len(self.widgets_col2) > 3 and self.widgets_col2[3] is not None and hasattr(self.widgets_col2[3], 'setDateTime'):
                self.widgets_col2[3].setDateTime(QDateTime.currentDateTime())

            # 加载公司数据
            self.cursor.execute("SELECT name, english_name FROM companies ORDER BY name")
            companies = [row[0] for row in self.cursor.fetchall()]
            # 构建公司名到英文名的映射
            self.cursor.execute("SELECT name, english_name FROM companies")
            self.company_en_map = {row[0]: row[1] for row in self.cursor.fetchall()}
            if len(self.combos_col1) > 0 and self.combos_col1[0] is not None:
                self.combos_col1[0].clear()
                self.combos_col1[0].addItems(companies)
                if companies:
                    self.combos_col1[0].setCurrentIndex(0)
                self.combos_col1[0].view().setMinimumWidth(220)
                from PyQt5.QtCore import Qt
                for i in range(self.combos_col1[0].count()):
                    self.combos_col1[0].setItemData(i, self.combos_col1[0].itemText(i), Qt.ToolTipRole)
                self.combos_col1[0].update(); self.combos_col1[0].repaint()
                if getattr(self, "_debug_mode", False):
                    if getattr(self, "_debug_mode", False): print(f"公司名称下拉框数据")
            # 加载部门数据
            self.cursor.execute("SELECT name FROM departments ORDER BY name")
            departments = [row[0] for row in self.cursor.fetchall()]
            if len(self.combos_col1) > 1 and self.combos_col1[1] is not None:
                self.combos_col1[1].clear()
                self.combos_col1[1].addItems(departments)
                if departments:
                    self.combos_col1[1].setCurrentIndex(0)
                self.combos_col1[1].update(); self.combos_col1[1].repaint()
                if getattr(self, "_debug_mode", False):
                    if getattr(self, "_debug_mode", False): print(f"部门名称下拉框数据")
            # 加载员工数据（二维码发行人）
            self.cursor.execute("SELECT name, employee_id FROM staff ORDER BY name")
            staff_data = [(row[0], row[1]) for row in self.cursor.fetchall()]
            staff_names = [f"{row[0]} ({row[1]})" for row in staff_data]
            # 二维码发行人（左栏）使用可搜索下拉框
            if len(self.combos_col1) > 2 and self.combos_col1[2] is not None:
                self.combos_col1[2].setItems(staff_names)
                if staff_names:
                    self.combos_col1[2].setCurrentIndex(0)
                self.combos_col1[2].update(); self.combos_col1[2].repaint()
                if getattr(self, "_debug_mode", False):
                    if getattr(self, "_debug_mode", False): print(f"二维码发行人下拉框数据")
            # 业务员信息（右栏靠上）下拉框：链接员工信息管理模块的数据
            # 该控件在界面构建时被追加到 combos_col1 列表的末尾
            if len(self.combos_col1) > 8 and self.combos_col1[8] is not None:
                # 普通 QComboBox 使用 addItems
                if hasattr(self.combos_col1[8], 'clear'):
                    self.combos_col1[8].clear()
                if hasattr(self.combos_col1[8], 'addItems'):
                    self.combos_col1[8].addItems(staff_names)
                # 默认选中员工列表第一行
                if staff_names and hasattr(self.combos_col1[8], 'setCurrentIndex'):
                    self.combos_col1[8].setCurrentIndex(0)
                # 刷新显示
                self.combos_col1[8].update(); self.combos_col1[8].repaint()
                if getattr(self, "_debug_mode", False):
                    print("业务员信息下拉框数据已加载（来源：员工信息管理模块）")
            # 加载产品种类数据
            self.cursor.execute("SELECT name FROM product_types ORDER BY id")
            product_types = [row[0] for row in self.cursor.fetchall()]
            if len(self.combos_col1) > 3 and self.combos_col1[3] is not None:
                self.combos_col1[3].clear()
                self.combos_col1[3].addItems(product_types)
                if product_types:
                    self.combos_col1[3].setCurrentIndex(0)
                self.combos_col1[3].update(); self.combos_col1[3].repaint()
                if getattr(self, "_debug_mode", False):
                    if getattr(self, "_debug_mode", False): print(f"产品种类下拉框数据")
            # 加载产品规格数据
            self.cursor.execute("SELECT name FROM product_specs ORDER BY id")
            specs = [row[0] for row in self.cursor.fetchall()]
            if len(self.combos_col1) > 4 and self.combos_col1[4] is not None:
                self.combos_col1[4].clear()
                self.combos_col1[4].addItems(specs)
                if specs:
                    self.combos_col1[4].setCurrentIndex(0)
                self.combos_col1[4].update(); self.combos_col1[4].repaint()
                if getattr(self, "_debug_mode", False):
                    if getattr(self, "_debug_mode", False): print(f"产品规格下拉框数据")
            # 加载物流车牌号数据
            self.cursor.execute("SELECT plate_number FROM logistics_vehicles ORDER BY id")
            plate_numbers = [row[0] for row in self.cursor.fetchall()]
            if len(self.widgets_col2) > 0 and self.widgets_col2[0] is not None and hasattr(self.widgets_col2[0], 'clear'):
                self.widgets_col2[0].clear()
                if hasattr(self.widgets_col2[0], 'addItems'):
                    self.widgets_col2[0].addItems(plate_numbers)
                    if plate_numbers:
                        self.widgets_col2[0].setCurrentIndex(0)
                    self.widgets_col2[0].update(); self.widgets_col2[0].repaint()
                    if getattr(self, "_debug_mode", False):
                        if getattr(self, "_debug_mode", False): print(f"物流车牌号下拉框数据")
                else:
                    if getattr(self, "_debug_mode", False):
                        print("物流车牌号下拉框: 不是有效的QComboBox控件")
            # 加载产品特性数据
            self.cursor.execute("SELECT name FROM product_features ORDER BY id")
            features = [row[0] for row in self.cursor.fetchall()]
            # print(f"产品特性表内容: {features}")  # 已优化
            if len(self.combos_col1) > 5 and self.combos_col1[5] is not None:
                self.combos_col1[5].clear()
                self.combos_col1[5].addItems(features)
                if features:
                    self.combos_col1[5].setCurrentIndex(0)
                self.combos_col1[5].update(); self.combos_col1[5].repaint()
                if getattr(self, "_debug_mode", False):
                    if getattr(self, "_debug_mode", False): print(f"产品特性下拉框数据")
            # 加载产品颜色数据
            self.cursor.execute("SELECT name FROM product_colors ORDER BY id")
            colors = [row[0] for row in self.cursor.fetchall()]
            # print(f"产品颜色表内容: {colors}")  # 已优化
            if len(self.combos_col1) > 6 and self.combos_col1[6] is not None:
                self.combos_col1[6].clear()
                self.combos_col1[6].addItems(colors)
                if colors:
                    self.combos_col1[6].setCurrentIndex(0)
                self.combos_col1[6].update(); self.combos_col1[6].repaint()
                if getattr(self, "_debug_mode", False):
                    if getattr(self, "_debug_mode", False): print(f"产品颜色下拉框数据")
            # 加载经销商名称数据
            self.cursor.execute("SELECT name FROM distributors ORDER BY id")
            distributors = [row[0] for row in self.cursor.fetchall()]
            # print(f"经销商表内容: {distributors}")  # 已优化
            if len(self.combos_col1) > 7 and self.combos_col1[7] is not None:
                self.combos_col1[7].clear()
                self.combos_col1[7].addItems(distributors)
                if distributors:
                    self.combos_col1[7].setCurrentIndex(0)
                self.combos_col1[7].update(); self.combos_col1[7].repaint()
                if getattr(self, "_debug_mode", False):
                    if getattr(self, "_debug_mode", False): print(f"经销商名称下拉框数据")
            # print("所有数据加载成功")  # 已优化
        except Exception as e:
            import traceback
            print(f"加载数据失败: {e}")
            print(traceback.format_exc())
            QMessageBox.warning(self, "数据加载错误", f"加载数据失败: {e}")

    def save_qr_record(self):
        """保存二维码记录到数据库和云端JSON文件"""
        try:
            # 获取电脑信息
            from utils.computer_info import get_print_source
            print_source_info = get_print_source()
            
            # 获取表单数据
            company_name = self.combos_col1[0].currentText()
            department_name = self.combos_col1[1].currentText()
            issuer_display = self.combos_col1[2].currentText()
            
            # 获取当前登录用户信息作为打印人
            print_user_name = self.current_user.get('username', 'guest') if self.current_user else 'guest'
            print_user_employee_id = self.current_user.get('employee_id', '') if self.current_user else ''
            
            # 解析显示文本获取二维码发行人员工工号
            if " (" in issuer_display and issuer_display.endswith(")"):
                issuer_name = issuer_display.split(" (")[1].rstrip(")")
            else:
                issuer_name = issuer_display
            product_type = self.combos_col1[3].currentText()
            product_spec = self.combos_col1[4].currentText()
            product_feature = self.combos_col1[5].currentText() if len(self.combos_col1) > 5 else "保温隔热"
            product_color = self.combos_col1[6].currentText() if len(self.combos_col1) > 6 else "白色"
            distributor_name = self.combos_col1[7].currentText() if len(self.combos_col1) > 7 else "官方直销"
            standard = self.quantity_edit.text() if self.quantity_edit.text() else "GB/T10801.2-2018"
            quantity = "1"
            batch_number = self.widgets_col2[4].text()
            plate_number = self.widgets_col2[0].currentText() if hasattr(self.widgets_col2[0], 'currentText') else self.widgets_col2[0].text()
            phone = self.widgets_col2[1].text()
            qr_sequence = self.widgets_col2[2].text()
            production_date = self.widgets_col2[3].dateTime().toString('yyyy-MM-dd hh:mm:ss') if hasattr(self.widgets_col2[3], 'dateTime') else ''
            remark = self.remark_edit.text() if self.remark_edit is not None else ''
            
            # 获取数量单位
            unit = "m³"
            for radio in self.findChildren(QRadioButton):
                if isinstance(radio, QRadioButton) and radio.isChecked():
                    if "m²" in radio.text():
                        unit = "m²"
                    break
            # 获取ID
            self.cursor.execute("SELECT id FROM companies WHERE name = ?", (company_name,))
            row = self.cursor.fetchone()
            company_id = row[0] if row else None
            self.cursor.execute("SELECT id FROM departments WHERE name = ?", (department_name,))
            row = self.cursor.fetchone()
            department_id = row[0] if row else None
            # 使用员工姓名查询ID
            self.cursor.execute("SELECT id FROM staff WHERE name = ?", (issuer_name,))
            row = self.cursor.fetchone()
            issuer_id = row[0] if row else None
            self.cursor.execute("SELECT id FROM products WHERE type = ? AND spec = ?", (product_type, product_spec))
            row = self.cursor.fetchone()
            product_id = row[0] if row else None
            # 插入记录（使用事务确保数据一致性）
            try:
                self.cursor.execute('''
                    INSERT INTO qr_records 
                    (company_name, product_type, product_spec, product_color, product_feature, quantity, unit, 
                     batch_number, production_date, plate_number, phone, qr_sequence, issuer_name, distributor_name, remark, standard,
                     print_user_name, print_user_employee_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (company_name, product_type, product_spec, product_color, product_feature, quantity, unit,
                      batch_number, production_date, plate_number, phone, qr_sequence, issuer_name, distributor_name, remark, standard,
                      print_user_name, print_user_employee_id))
                self.conn.commit()
                print(f"二维码记录保存成功: {qr_sequence}")
            except Exception as db_error:
                print(f"数据库保存失败: {db_error}")
                self.conn.rollback()
                # 数据库保存失败时，仍然尝试保存JSON文件，避免数据完全丢失
                print("⚠️ 数据库保存失败，但仍将尝试保存JSON文件")
            
            # 直接保存到正确目录并上传到FTP
            try:
                # 构造完整二维码数据 - 包含简化公司名称和打印人信息
                simplified_company_name = self.get_simplified_company_name(company_name)
                qr_data = {
                    'company_name': company_name,
                    'simplified_company_name': simplified_company_name,
                    'product_type': product_type,
                    'product_spec': product_spec,
                    'product_color': product_color,
                    'product_feature': product_feature,
                    'quantity': str(quantity),
                    'unit': unit,
                    'batch_number': batch_number,
                    'production_date': production_date,
                    'qr_sequence': qr_sequence,
                    'issuer_name': issuer_name,
                    'distributor_name': distributor_name,
                    'standard': standard,
                    'plate_number': plate_number,
                    'phone': phone,
                    'remark': remark,
                    'print_user_name': print_user_name,
                    'print_user_employee_id': print_user_employee_id,
                    'official_website': f"https://{'www.your-company-domain.com' if '示例品牌B' in company_name or '示例' in company_name else 'www.your-company-domain.com'}".replace('http://','https://')
                }
                
                # 根据公司确定保存目录（使用绝对路径确保正确）
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if "示例品牌B" in company_name or "示例" in company_name:
                    data_dir = os.path.join(base_path, "cloud", "demo_json_a")
                    domain = "your-company-domain.com"
                    prefix = "A-Q"
                elif "示例品牌A" in company_name or "示例" in company_name:
                    data_dir = os.path.join(base_path, "cloud", "demo_json_b")
                    domain = "your-company-domain.com"
                    prefix = "B-Q"
                else:
                    data_dir = os.path.join(base_path, "cloud", "demo_json_a")
                    domain = "your-company-domain.com"
                    prefix = "A-Q"
                
                # 确保目录存在
                os.makedirs(data_dir, exist_ok=True)
                
                # 保存文件
                qr_code = qr_sequence
                filepath = os.path.join(data_dir, f"{qr_code}.json")
                
                # 构造完整保存数据
                save_data = qr_data.copy()
                save_data.update({
                    "verification_url": f"https://scan.example.com/index.html?code={qr_code}",
                    "print_computer_id": print_source_info['print_computer_id'],
                    "print_computer_name": print_source_info['print_computer_name'],
                    "print_user": print_source_info['print_user'],
                    "print_ip": print_source_info['print_ip'],
                    "print_source": print_source_info['print_source'],
                    "print_timestamp": print_source_info['print_timestamp']
                })
                
                # 使用增强版JSON保存函数
                json_save_success = self.save_qr_json_enhanced(save_data, qr_sequence, data_dir, domain)
                
                if not json_save_success:
                    print(f"[EMERGENCY] 严重警告: JSON文件 {qr_code}.json 保存失败！")
                    print(f"[EMERGENCY] 序号 {qr_sequence} 的云端数据可能丢失！")
                else:
                    logging.getLogger(__name__).debug(f"[SUCCESS] JSON文件保存成功: {os.path.join(data_dir, f'{qr_code}.json')}")
                
                # 上传到FTP服务器（异步）
                try:
                    # 批量打印时，前台不做上传，交由后台自动同步服务处理，避免UI阻塞
                    if getattr(self, '_in_batch_print', False):
                        print("[INFO] 批量打印中：FTP上传交由后台自动同步服务完成，前台不阻塞")
                    else:
                        import threading
                        def _bg_upload():
                            # [DISABLED] Python FTP upload removed; handled by Windows Task Scheduler
                            return
                            # [DISABLED] Python FTP upload removed; handled by Windows Task Scheduler
                            return
                            try:
                                # [DISABLED] Internal FTP removed; background upload handled by Windows Task Scheduler
                                import json, os
                                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                config_candidates = [
                                    os.path.join(project_root, 'config', 'ftp_config.json'),
                                    os.path.join(project_root, 'ftp_config.json')
                                ]
                                cfg_path = next((p for p in config_candidates if os.path.exists(p)), None)
                                if not cfg_path:
                                    print(f"[WARNING] FTP配置文件不存在，跳过上传：{config_candidates}")
                                    return
                                with open(cfg_path, 'r', encoding='utf-8') as f:
                                    ftp_servers = json.load(f)
                                if "示例品牌B" in company_name or "示例" in company_name:
                                    server = ftp_servers.get('A', {})
                                    company_dir = 'demo_json_a'
                                elif "示例品牌A" in company_name or "示例" in company_name:
                                    server = ftp_servers.get('B', {})
                                    company_dir = 'demo_json_b'
                                else:
                                    server = ftp_servers.get('A', {})
                                    company_dir = 'demo_json_a'
                                host = server.get('host')
                                port = server.get('port', 21)
                                username = server.get('user') or server.get('username')
                                password = server.get('pass') or server.get('password')
                                use_tls = server.get('tls') or server.get('use_tls', False)
                                remote_dir = server.get('base_path') or ("/companies/demo_json_a/" if company_dir == 'demo_json_a' else "/companies/demo_json_b/")
                                if not host or not username or not password:
                                    print("[WARNING] FTP配置不完整（host/username/password缺失），跳过上传")
                                    return
                                ftp_manager = EnhancedFTPSyncManager(
                                    host=host,
                                    port=port,
                                    username=username,
                                    password=password,
                                    use_tls=use_tls
                                )
                                success = ftp_manager.upload_single_file(filepath, remote_dir)
                                if success:
                                    display_host = domain or host
                                    rd = remote_dir.rstrip('/')
                                    print(f"[UPLOAD] 已上传到FTP！全球访问: https://{display_host}{rd}/{qr_code}.json")
                                else:
                                    print("[WARNING] FTP上传失败，但文件已保存到本地")
                            except Exception as ftp_error:
                                print(f"[WARNING] FTP上传失败: {ftp_error}")
                                print("📱 文件已保存到本地，可手动上传到FTP")
                        print("[INFO] 已保存本地 JSON，上传将由 Windows 后台计划任务自动执行（随系统启动，独立于应用）")
                except Exception as ftp_error_outer:
                    print("[INFO] 已保存本地 JSON，上传将由 Windows 后台计划任务自动执行（随系统启动，独立于应用）")
                
            except Exception as e:
                print(f"保存二维码记录失败: {e}")
                # 静默处理错误，不显示任何弹窗
                print(f"静默保存失败: {e}")
            
            # 静默刷新表格，不显示弹窗
            try:
                self.load_qr_records()
            except Exception as e:
                print(f"静默刷新表格失败: {e}")
        except Exception as e:
            print(f"保存二维码记录失败: {e}")
            # 静默处理所有错误
            print(f"静默保存失败: {e}")

    def load_qr_records(self):
        """加载二维码记录到表格 - 优化列布局：删除工号列，QRC No.显示二维码序号"""
        try:
            # 查询最近的二维码记录，包含所有需要的字段
            self.cursor.execute('''
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY qr.created_at DESC) as seq_num,
                    qr.qr_sequence,
                    qr.created_at,
                    COALESCE(qr.print_user_name, qr.issuer_name, '') as print_user_name,
                    qr.product_type,
                    qr.product_spec,
                    qr.product_color,
                    qr.product_feature,
                    qr.production_date,
                    qr.issuer_name as salesperson_name,
                    qr.distributor_name,
                    qr.plate_number
                FROM qr_records qr
                ORDER BY qr.created_at DESC
                LIMIT 10
            ''')
            
            records = self.cursor.fetchall()
            
            # 清空表格并设置行数
            self.table.setRowCount(len(records))
            
            # 填充数据 - 新的12列布局：["序", "QRC No.", "发行时间", "打印人", "种类", "型号规格", "颜色", "功能特性", "生产时间", "业务员", "经销商", "物流车牌"]
            for row, record in enumerate(records):
                # 序号
                self.table.setItem(row, 0, QTableWidgetItem(str(record[0])))
                
                # QRC No.（二维码序号）
                qr_sequence = record[1] if record[1] else ""
                self.table.setItem(row, 1, QTableWidgetItem(str(qr_sequence)))
                
                # 发行时间
                created_at = record[2] if record[2] else ""
                # 格式化时间显示，只显示日期和时间，去掉秒
                if created_at:
                    try:
                        from datetime import datetime
                        dt = datetime.strptime(str(created_at)[:19], "%Y-%m-%d %H:%M:%S")
                        created_at = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                self.table.setItem(row, 2, QTableWidgetItem(str(created_at)))
                
                # 打印人姓名（登录人）
                print_user_name = record[3] if record[3] else ""
                self.table.setItem(row, 3, QTableWidgetItem(str(print_user_name)))
                
                # 种类
                product_type = record[4] if record[4] else ""
                self.table.setItem(row, 4, QTableWidgetItem(str(product_type)))
                
                # 型号规格
                product_spec = record[5] if record[5] else ""
                self.table.setItem(row, 5, QTableWidgetItem(str(product_spec)))
                
                # 颜色
                product_color = record[6] if record[6] else ""
                self.table.setItem(row, 6, QTableWidgetItem(str(product_color)))
                
                # 功能特性
                product_feature = record[7] if record[7] else ""
                self.table.setItem(row, 7, QTableWidgetItem(str(product_feature)))
                
                # 生产时间
                production_date = record[8] if record[8] else ""
                # 格式化生产时间显示
                if production_date:
                    try:
                        from datetime import datetime
                        dt = datetime.strptime(str(production_date)[:19], "%Y-%m-%d %H:%M:%S")
                        production_date = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                self.table.setItem(row, 8, QTableWidgetItem(str(production_date)))
                
                # 业务员姓名（二维码发行人）
                salesperson_name = record[9] if record[9] else ""
                self.table.setItem(row, 9, QTableWidgetItem(str(salesperson_name)))
                
                # 经销商名称
                distributor_name = record[10] if record[10] else ""
                self.table.setItem(row, 10, QTableWidgetItem(str(distributor_name)))
                
                # 物流车牌
                plate_number = record[11] if record[11] else ""
                self.table.setItem(row, 11, QTableWidgetItem(str(plate_number)))
                
                # 设置所有单元格居中对齐 - 调整为12列
                for col in range(12):
                    item = self.table.item(row, col)
                    if item:
                        item.setTextAlignment(Qt.AlignCenter)
            
            logging.getLogger(__name__).debug(f"[SUCCESS] 成功加载 {len(records)} 条二维码记录")
            
        except Exception as e:
            print(f"[ERROR] 加载二维码记录失败: {e}")
            # 显示错误信息但不中断程序
            import traceback
            traceback.print_exc()

    def init_qr_sequence(self):
        """初始化二维码序号，确保基于公司专属历史记录递增 - 修复版本"""
        try:
            # 获取当前公司名称
            company_name = self.combos_col1[0].currentText() if self.combos_col1[0] is not None else "[已脱敏城市]示例品牌A有限公司"
            company_prefix = self.get_company_prefix(company_name)
            
            # 使用原子性方法获取最大序号
            max_num = self._get_max_sequence_number_atomic(company_name, company_prefix)
            
            # 确定新的序号
            new_num = max_num + 1
            new_seq = f"{company_prefix}-Q{new_num:09d}"
            
            # 检查序号唯一性（防止重复）
            while self._sequence_exists(new_seq):
                new_num += 1
                new_seq = f"{company_prefix}-Q{new_num:09d}"
                print(f"初始化检测到序号重复，递增为: {new_seq}")
            
            # 更新输入框
            if len(self.widgets_col2) > 2 and self.widgets_col2[2] is not None:
                self.widgets_col2[2].setText(new_seq)
                print(f"初始化二维码序号为: {new_seq} (基于{company_name}历史记录)")
                # 更新二维码内容为正确的URL
                self.update_qr_content()
            else:
                print("警告: widgets_col2[2]不存在或为None，无法设置二维码序号")
        except Exception as e:
            print(f"初始化二维码序号失败: {e}")
            if len(self.widgets_col2) > 2 and self.widgets_col2[2] is not None:
                company_prefix = self.get_company_prefix(company_name)
                new_seq = f"{company_prefix}-Q000000001"
                self.widgets_col2[2].setText(new_seq)
                print(f"使用默认初始序号: {new_seq}")
                # 更新二维码内容为正确的URL
                self.update_qr_content()
            else:
                print("警告: widgets_col2[2]不存在或为None，无法设置二维码序号")
        
        # 设置批次号提示和默认值
        if len(self.widgets_col2) > 4 and self.widgets_col2[4] is not None:
            self.widgets_col2[4].setPlaceholderText("输入完整批次号或001-999")
            current_date = QDateTime.currentDateTime().date()
            auto_prefix = current_date.toString('yyyyMMdd')
            self.widgets_col2[4].setText(f"{auto_prefix}001")
    
    def generate_new_qr_sequence(self):
        """生成新的二维码序号，确保基于公司专属历史记录唯一递增 - 修复版本"""
        try:
            # 获取当前公司名称
            company_name = self.combos_col1[0].currentText() if self.combos_col1[0] is not None else "[已脱敏城市]示例品牌A有限公司"
            company_prefix = self.get_company_prefix(company_name)
            
            # 使用数据库事务确保原子性
            max_num = self._get_max_sequence_number_atomic(company_name, company_prefix)
            
            # 确定新的序号
            new_num = max_num + 1
            new_seq = f"{company_prefix}-Q{new_num:09d}"
            
            # 检查序号唯一性（防止重复）
            while self._sequence_exists(new_seq):
                new_num += 1
                new_seq = f"{company_prefix}-Q{new_num:09d}"
                print(f"检测到序号重复，递增为: {new_seq}")
            
            # 更新输入框
            self.widgets_col2[2].setText(new_seq)
            
            # 更新二维码内容
            self.update_qr_content()
            
            print(f"生成新二维码序号: {new_seq} (基于{company_name}历史记录)")
            
        except Exception as e:
            print(f"生成新二维码序号失败: {e}")
            # 出错时使用默认格式，从1开始
            company_prefix = self.get_company_prefix(company_name)
            new_seq = f"{company_prefix}-Q000000001"
            self.widgets_col2[2].setText(new_seq)
            self.update_qr_content()

    def _get_max_sequence_number_atomic(self, company_name, company_prefix):
        """原子性获取最大序号，确保线程安全 - 修复版本"""
        max_num = 0
        
        try:
            # 1. 检查云端JSON文件
            max_num = max(max_num, self._get_max_from_cloud(company_name, company_prefix))
            
            # 2. 检查本地数据库（确保读取最新数据）
            try:
                # 强制提交之前的事务，确保读取最新数据
                self.conn.commit()
                
                # 查询当前公司的所有序号（不使用事务锁定，避免读取延迟）
                self.cursor.execute("""
                    SELECT qr_sequence FROM qr_records 
                    WHERE qr_sequence LIKE ? AND qr_sequence IS NOT NULL 
                    ORDER BY id DESC LIMIT 100
                """, (f"{company_prefix}-Q%",))
                
                db_sequences = self.cursor.fetchall()
                
                for seq_tuple in db_sequences:
                    seq = seq_tuple[0]
                    if seq:
                        # 处理新格式：前缀-Q + 数字
                        import re
                        seq_match = re.search(r'(' + re.escape(company_prefix) + r')-Q(\d+)$', seq)
                        if seq_match:
                            try:
                                num = int(seq_match.group(2))
                                max_num = max(max_num, num)
                            except ValueError:
                                continue
                
                print(f"数据库中找到的最大序号: {max_num}")
                
            except Exception as e:
                print(f"数据库查询失败: {e}")
                
        except Exception as e:
            print(f"获取最大序号失败: {e}")
        
        return max_num

    def _get_max_from_cloud(self, company_name, company_prefix):
        """从云端文件获取最大序号"""
        max_num = 0
        
        try:
            import os
            import json
            import re
            
            # 根据公司确定云端数据目录
            if "示例品牌B" in company_name or "示例" in company_name:
                cloud_dir = os.path.join(os.path.dirname(__file__), '..', 'cloud', 'company_a', 'data')
            else:
                cloud_dir = os.path.join(os.path.dirname(__file__), '..', 'cloud', 'company_b', 'data')
            
            if os.path.exists(cloud_dir):
                json_files = [f for f in os.listdir(cloud_dir) if f.endswith('.json')]
                
                for filename in json_files:
                    # 从文件名提取序列号
                    seq_match = re.search(r'(' + re.escape(company_prefix) + r')-Q(\d+)\.json$', filename)
                    if seq_match:
                        num = int(seq_match.group(2))
                        max_num = max(max_num, num)
                    
                    # 从文件内容提取序列号
                    try:
                        file_path = os.path.join(cloud_dir, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            qr_seq = data.get('qr_sequence', '')
                            company_in_file = data.get('company_name', '')
                            
                            if company_in_file == company_name and qr_seq:
                                seq_match = re.search(r'(' + re.escape(company_prefix) + r')-Q(\d+)$', qr_seq)
                                if seq_match:
                                    num = int(seq_match.group(2))
                                    max_num = max(max_num, num)
                    except Exception:
                        continue
                        
        except Exception as e:
            print(f"读取云端数据失败: {e}")
        
        return max_num

    def _sequence_exists(self, sequence):
        """检查序号是否已存在 - 增强版本"""
        try:
            # 1. 检查数据库
            self.cursor.execute("SELECT COUNT(*) FROM qr_records WHERE qr_sequence = ?", (sequence,))
            db_count = self.cursor.fetchone()[0]
            
            if db_count > 0:
                print(f"序号 {sequence} 在数据库中已存在")
                return True
            
            # 2. 检查云端文件
            import os
            company_name = self.combos_col1[0].currentText() if self.combos_col1[0] is not None else "[已脱敏城市]示例品牌A有限公司"
            
            if "示例品牌B" in company_name or "示例" in company_name:
                cloud_dir = os.path.join(os.path.dirname(__file__), '..', 'cloud', 'company_a', 'data')
            else:
                cloud_dir = os.path.join(os.path.dirname(__file__), '..', 'cloud', 'company_b', 'data')
            
            cloud_file = os.path.join(cloud_dir, f"{sequence}.json")
            if os.path.exists(cloud_file):
                print(f"序号 {sequence} 在云端文件中已存在")
                return True
            
            # 3. 检查当前界面显示的序号（避免与当前正在使用的序号冲突）
            current_sequence = self.widgets_col2[2].text() if len(self.widgets_col2) > 2 else ""
            if current_sequence == sequence:
                print(f"序号 {sequence} 是当前正在使用的序号")
                return True
                
        except Exception as e:
            print(f"检查序号存在性失败: {e}")
        
        return False

    def _sequence_exists_for_batch(self, sequence):
        """批量打印专用的序号存在性检查（不检查当前界面序号）"""
        try:
            # 1. 检查数据库
            self.cursor.execute("SELECT COUNT(*) FROM qr_records WHERE qr_sequence = ?", (sequence,))
            db_count = self.cursor.fetchone()[0]
            
            if db_count > 0:
                print(f"序号 {sequence} 在数据库中已存在")
                return True
            
            # 2. 检查云端文件
            import os
            company_name = self.combos_col1[0].currentText() if self.combos_col1[0] is not None else "[已脱敏城市]示例品牌A有限公司"
            
            if "示例品牌B" in company_name or "示例" in company_name:
                cloud_dir = os.path.join(os.path.dirname(__file__), '..', 'cloud', 'company_a', 'data')
            else:
                cloud_dir = os.path.join(os.path.dirname(__file__), '..', 'cloud', 'company_b', 'data')
            
            cloud_file = os.path.join(cloud_dir, f"{sequence}.json")
            if os.path.exists(cloud_file):
                print(f"序号 {sequence} 在云端文件中已存在")
                return True
            
            # 注意：批量打印时不检查当前界面显示的序号
                
        except Exception as e:
            print(f"批量打印检查序号存在性失败: {e}")
        
        return False

    def get_local_ip(self):
        """获取本地IP地址，用于移动设备访问"""
        try:
            import socket
            # 创建一个UDP socket来获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # 连接到一个外部地址来获取本地IP
                s.connect(('8.8.8.8', 80))
                ip = s.getsockname()[0]
            except Exception:
                ip = 'localhost'
            finally:
                s.close()
            return ip
        except Exception:
            return 'localhost'
    
    def generate_qr_url(self, qr_sequence):
        """生成二维码URL - 使用正确的扫描页面显示产品信息"""
        try:
            company_name = self.combos_col1[0].currentText() if self.combos_col1[0] else ""
            
            # 所有公司都使用统一的正确URL（scan 子域）
            url = f"https://scan.example.com/index.html?code={qr_sequence}"
            logging.getLogger(__name__).debug(f"[SUCCESS] 生成二维码URL: {url}")
            return url
            
        except Exception as e:
            print(f"[ERROR] 生成二维码URL失败: {e}")
            return f"https://scan.example.com/index.html?code={qr_sequence}"
    
    def on_company_changed(self):
        """公司选择变化时的处理函数"""
        try:
            # print("[UPDATE] 公司选择已变化，更新二维码内容...")
            # 延迟更新，避免频繁调用
            QTimer.singleShot(100, self.update_qr_content)
        except Exception as e:
            print(f"[ERROR] 公司变化处理失败: {e}")
    
    def on_qr_sequence_changed(self):
        """二维码序号变化时的处理函数"""
        try:
            # print("[UPDATE] 二维码序号已变化，更新内容...")
            # 延迟更新，避免频繁调用
            QTimer.singleShot(200, self.update_qr_content)
        except Exception as e:
            print(f"[ERROR] 二维码序号变化处理失败: {e}")

    def update_qr_content(self):
        """更新二维码内容为正确的URL - 修复扫描跳转问题"""
        try:
            # 获取当前二维码序号
            qr_sequence = self.widgets_col2[2].text() if len(self.widgets_col2) > 2 else ""
            
            if qr_sequence and qr_sequence.strip():
                # 生成正确的URL
                self.current_qr_content = self.generate_qr_url(qr_sequence.strip())
                logging.getLogger(__name__).debug(f"[SUCCESS] 二维码内容已更新为URL: {self.current_qr_content}")
                
                # 🔧 修复：更新界面上的二维码内容信息框
                if hasattr(self, 'qr_info_edit') and self.qr_info_edit:
                    # 获取当前公司信息
                    company_name = self.combos_col1[0].currentText() if len(self.combos_col1) > 0 else ""
                    
                    # 获取所有15项数据信息，去掉题头标签，节省空间
                    company_website = self.get_company_website(company_name) if hasattr(self, 'get_company_website') else "https://www.your-company-domain.com"
                    product_type = self.combos_col1[3].currentText() if len(self.combos_col1) > 3 else "XPS-A1"
                    product_spec = self.combos_col1[4].currentText() if len(self.combos_col1) > 4 else "30mm"
                    product_feature = self.combos_col1[5].currentText() if len(self.combos_col1) > 5 else "保温隔热"
                    product_color = self.combos_col1[6].currentText() if len(self.combos_col1) > 6 else "白色"
                    plate_number = self.widgets_col2[0].currentText() if len(self.widgets_col2) > 0 and hasattr(self.widgets_col2[0], 'currentText') else "京A12345"
                    service_phone = self.widgets_col2[1].text() if len(self.widgets_col2) > 1 else "13800000002"
                    production_time = self.widgets_col2[3].dateTime().toString('yyyy-MM-dd HH:mm:ss') if len(self.widgets_col2) > 3 and hasattr(self.widgets_col2[3], 'dateTime') else "2025-07-20 14:30:00"
                    batch_number = self.widgets_col2[4].text() if len(self.widgets_col2) > 4 else "20240720001"
                    inspection_result = "合格"
                    issuer_display = self.combos_col1[2].currentText() if len(self.combos_col1) > 2 else "[已脱敏]"
                    if " (" in issuer_display and issuer_display.endswith(")"):
                        issuer_name = issuer_display.split(" (")[1].rstrip(")")
                    else:
                        issuer_name = issuer_display
                    standard_text = self.quantity_edit.text() if hasattr(self, 'quantity_edit') and self.quantity_edit.text() else "GB/T10801.2-2018"
                    distributor_name = self.combos_col1[7].currentText() if len(self.combos_col1) > 7 else ""
                    remark = self.remark_edit.text() if hasattr(self, 'remark_edit') and self.remark_edit else ""
                    
                    # 显示15项完整数据，无题头标签
                    display_content = f"{company_name}；{company_website}；{product_type}；{product_spec}；{product_feature}；{product_color}；{plate_number}；{service_phone}；{production_time}；{batch_number}；{inspection_result}；{qr_sequence.strip()}；{issuer_name}；{standard_text}；{distributor_name}；{remark}"
                    
                    self.qr_info_edit.setPlainText(display_content)
                    logging.getLogger(__name__).debug(f"[SUCCESS] 界面内容信息框已更新")
            else:
                # 如果没有序号，使用默认内容
                self.current_qr_content = "二维码内容"
                print(f"[WARNING] 二维码序号为空，使用默认内容")
                
                # 更新界面显示为空白或提示信息
                if hasattr(self, 'qr_info_edit') and self.qr_info_edit:
                    self.qr_info_edit.setPlainText("请先生成二维码序号，然后查看二维码内容信息")
                
            # 更新二维码预览（如果存在预览功能）
            if hasattr(self, 'qr_preview_label') and self.qr_preview_label:
                self.generate_simple_fallback_qr(self.current_qr_content)
                
        except Exception as e:
            print(f"[ERROR] 更新二维码内容失败: {e}")
            self.current_qr_content = "二维码内容"
            # 显示错误信息
            if hasattr(self, 'qr_info_edit') and self.qr_info_edit:
                self.qr_info_edit.setPlainText(f"二维码内容更新失败: {e}")
    
    # update_qr_by_time方法已删除 - 根据用户要求取消5秒自动刷新功能
        
    # 已删除start_auto_refresh_timer方法（根据用户要求简化系统）
        
    def closeEvent(self, event):
        """关闭事件，确保数据库连接正确关闭"""
        # 停止自动同步服务
        if hasattr(self, '_auto_sync_started'):
            try:
                from cloud.deploy_config import CloudDeployManager
                manager = CloudDeployManager(company_name=getattr(self, '_current_company', None))
                manager.stop_auto_sync()
                print("自动同步服务已停止")
            except Exception as e:
                print(f"停止自动同步服务失败: {e}")
        
        if hasattr(self, 'conn'):
            self.conn.close()
        if hasattr(self, 'auto_refresh_timer'):
            self.auto_refresh_timer.stop()
        event.accept()

    def get_conn(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            return conn
        except Exception as e:
            # ... existing code ...
            return None
    
    def get_company_logo_path(self, company_name):
        """根据公司名称获取LOGO文件路径"""
        try:
            if not company_name:
                return None
                
            # 根据公司名称选择对应的LOGO
            if "示例" in company_name:
                logo_path = "assets/示例品牌B 透明.png"
            elif "示例" in company_name:
                logo_path = "assets/示例品牌A 透明.png"
            else:
                return None
            
            # 检查文件是否存在
            if os.path.exists(logo_path):
                return logo_path
            else:
                print(f"LOGO文件不存在: {logo_path}")
                return None
                
        except Exception as e:
            print(f"获取LOGO路径失败: {e}")
            return None
    
    def update_company_logo(self):
        """更新公司LOGO显示"""
        try:
            if not hasattr(self, 'company_logo_label'):
                return
                
            company_name = self.combos_col1[0].currentText() if self.combos_col1 else ""
            logo_path = self.get_company_logo_path(company_name)
            
            if logo_path and os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                if pixmap.isNull():
                    print(f"LOGO图片加载失败: {logo_path}")
                else:
                    # 等比缩放到40x40，避免过大
                    pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.company_logo_label.setPixmap(pixmap)
                    self.company_logo_label.setToolTip(f"公司LOGO: {company_name}")
            else:
                # 如果没有LOGO文件，显示默认图标
                self.company_logo_label.clear()
                self.company_logo_label.setText("LOGO")
                self.company_logo_label.setAlignment(Qt.AlignCenter)
                self.company_logo_label.setStyleSheet(
                    "border: 1px solid #ddd; border-radius: 5px; "
                    "background: #f0f0f0; color: #666; font-size: 10px;"
                )
                
        except Exception as e:
            print(f"更新LOGO显示失败: {e}")
    
    def add_logo_to_qr_image(self, qr_img, company_name):
        """在二维码图片上添加公司LOGO"""
        try:
            logo_path = self.get_company_logo_path(company_name)
            if not logo_path or not os.path.exists(logo_path):
                print(f"LOGO路径无效或文件不存在: {logo_path}")
                return qr_img
            
            # 打开LOGO图片
            logo = Image.open(logo_path)
            
            # 确保LOGO有透明通道
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            # 计算LOGO大小（二维码的1/10，更小一些确保扫描成功）
            qr_width, qr_height = qr_img.size
            logo_size = min(qr_width, qr_height) // 10
            
            # 使用兼容的resize方法
            try:
                logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
            except AttributeError:
                # 如果LANCZOS不可用，使用ANTIALIAS
                logo = logo.resize((logo_size, logo_size), Image.ANTIALIAS)
            
            # 计算LOGO位置（左上角）
            logo_x = 8
            logo_y = 8
            
            # 确保二维码图片是RGB模式（避免RGBA模式的复杂性）
            if qr_img.mode == 'RGBA':
                # 创建白色背景
                background = Image.new('RGB', qr_img.size, (255, 255, 255))
                background.paste(qr_img, mask=qr_img.split()[-1] if qr_img.mode == 'RGBA' else None)
                qr_img = background
            
            # 将LOGO转换为RGB模式并粘贴
            if logo.mode == 'RGBA':
                # 创建白色背景的LOGO
                logo_bg = Image.new('RGB', logo.size, (255, 255, 255))
                logo_bg.paste(logo, mask=logo.split()[-1])
                logo = logo_bg
            
            # 将LOGO粘贴到二维码上
            qr_img.paste(logo, (logo_x, logo_y))
            
            return qr_img
            
        except Exception as e:
            print(f"添加LOGO到二维码失败: {e}")
            import traceback
            traceback.print_exc()
            return qr_img
    
    def create_qr_label_with_logo(self, qr_data, company_name, product_info):
        """创建带LOGO的二维码标签"""
        try:
            # [KEY] 确保qr_data是正确的URL格式
            if not qr_data.startswith('http'):
                # 如果传入的不是URL，重新生成正确的URL
                qr_sequence = self.widgets_col2[2].text() if len(self.widgets_col2) > 2 else ""
                # 使用统一的正确URL
                qr_data = self.generate_qr_url(qr_sequence)
                print(f"[URL] 重新生成二维码URL: {qr_data}")
            
            # 生成二维码
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # 高容错率支持LOGO
                box_size=10,
                border=0,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # 创建二维码图片
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # 添加公司LOGO到二维码
            qr_img = self.add_logo_to_qr_image(qr_img, company_name)
            
            # 创建完整的标签图片
            label_width = 800
            label_height = 600
            
            # 创建标签背景
            label_img = Image.new('RGB', (label_width, label_height), 'white')
            
            # 获取公司LOGO
            logo_path = self.get_company_logo_path(company_name)
            company_logo = None
            if logo_path and os.path.exists(logo_path):
                company_logo = Image.open(logo_path)
                if company_logo.mode != 'RGBA':
                    company_logo = company_logo.convert('RGBA')
                # 调整公司LOGO大小
                company_logo = company_logo.resize((80, 80), Image.Resampling.LANCZOS)
            
            # 调整二维码大小
            qr_size = 200
            qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
            
            # 粘贴公司LOGO到标签左上角
            if company_logo:
                label_img.paste(company_logo, (20, 20), company_logo)
            
            # 粘贴二维码到标签右侧
            qr_x = label_width - qr_size - 50
            qr_y = 50
            label_img.paste(qr_img, (qr_x, qr_y))
            
            return label_img
            
        except Exception as e:
            print(f"创建带LOGO的二维码标签失败: {e}")
            return None
    
    def generate_simple_fallback_qr(self, content):
        """生成简单的备选二维码（不包含LOGO）"""
        try:
            # [KEY] 确保content是正确的URL格式
            if not content.startswith('http'):
                # 如果传入的不是URL，重新生成正确的URL
                qr_sequence = self.widgets_col2[2].text() if len(self.widgets_col2) > 2 else ""
                company_name = self.combos_col1[0].currentText() if len(self.combos_col1) > 0 else ""
                
                # 使用统一的正确URL
                content = self.generate_qr_url(qr_sequence)
                print(f"[URL] 备选二维码URL: {content}")
            
            # 简单配置，确保能生成
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.ERROR_CORRECT_L,  # 低容错率，确保生成成功
                box_size=10,
                border=0,
            )
            qr.add_data(content)
            qr.make(fit=True)
            # 创建二维码图像
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 转换为QImage
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            qimg = QImage()
            qimg.loadFromData(buffer.getvalue())
            qimg = qimg.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pixmap = QPixmap.fromImage(qimg)
            # 设置到预览标签
            if self.qr_preview_label is not None:
                self.qr_preview_label.setPixmap(pixmap)
                self.qr_preview_label.setStyleSheet("")  # 清除错误样式
                if getattr(self, "_debug_mode", False):
                    print("使用简单备选二维码生成成功")
        except Exception as e:
            print(f"简单备选二维码生成也失败: {e}")
            raise
