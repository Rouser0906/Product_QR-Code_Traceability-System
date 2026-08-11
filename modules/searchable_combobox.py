from PyQt5.QtWidgets import QComboBox, QCompleter
from PyQt5.QtCore import Qt, QStringListModel

class SearchableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        
        # 创建补全器
        self.completer = QCompleter(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(self.completer)
        
        # 连接信号
        self.lineEdit().textEdited.connect(self.on_text_edited)
        
    def setItems(self, items):
        """设置下拉项"""
        self.clear()
        self.addItems(items)
        # 更新补全器模型
        model = QStringListModel(items, self.completer)
        self.completer.setModel(model)
        
    def on_text_edited(self, text):
        """处理文本编辑事件"""
        # 如果文本为空，显示所有项
        if not text:
            self.completer.complete()
            return
            
        # 查找匹配项
        index = self.findText(text, Qt.MatchContains)
        if index >= 0:
            self.setCurrentIndex(index)
            # 显示补全列表
            self.completer.setCompletionPrefix(text)
            self.completer.complete()
        else:
            # 没有匹配项时也显示补全列表
            self.completer.setCompletionPrefix(text)
            self.completer.complete()