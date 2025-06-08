# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'video_settings.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

import os
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform, QIntValidator)  # 新增QIntValidator

from PySide6.QtWidgets import (QApplication, QHeaderView, QPushButton, QSizePolicy,
    QTableWidget, QTableWidgetItem, QWidget, QComboBox, QMessageBox, QLineEdit)  # 新增QLineEdit
import icon_rc  # 引入资源文件

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(515, 500)
        # 设置界面大小不可调节
        Form.setFixedSize(Form.size())

        self.tableWidget = QTableWidget(Form)
        self.tableWidget.setObjectName(u"tableWidget")
        self.tableWidget.setGeometry(QRect(10, 40, 491, 371))

        # 设置表格列数为2
        self.tableWidget.setColumnCount(2)
        # 设置表格行数为6
        self.tableWidget.setRowCount(6)
        # 隐藏行号和列号
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)
        # 设置列宽，两列各占一半
        self.tableWidget.setColumnWidth(0, self.tableWidget.width() // 2)
        self.tableWidget.setColumnWidth(1, self.tableWidget.width() // 2)

        # 定义表格内容
        self.table_data = [
            ("crf", ["", "23.5", "30", "40", "50"]),
            ("视频帧数(fps)", ["", "30", "60", "90", "120"]),
            ("视频编码", ["", "libx264", "libx265"]),
            ("音量", ["", "0", "1.25", "1.5", "1.75", "2.0", "2.5", "3.0", "4.0"]),  # 新增音量项
            ("宽度", [""]),  # 文本框，无选项列表
            ("高度", [""])   # 文本框，无选项列表
        ]

        # 创建配置目录
        self.config_dir = "config"
        self.config_file = os.path.join(self.config_dir, "video_settings.ini")
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 初始化配置字典
        self.config = {}
        self.load_settings()

        for row, (text, options) in enumerate(self.table_data):
            # 设置左列文本
            item = QTableWidgetItem(text)
            self.tableWidget.setItem(row, 0, item)
            
            # 根据类型创建组件：前4行用下拉框，后2行用文本框
            if row < 4:  # 前4行（含新增音量）使用下拉框
                combo_box = QComboBox()
                combo_box.addItems(options)
                # 从配置中加载保存的值
                saved_value = self.config.get(text, "")
                index = combo_box.findText(saved_value)
                if index >= 0:
                    combo_box.setCurrentIndex(index)
                else:
                    combo_box.setCurrentIndex(0)
                self.tableWidget.setCellWidget(row, 1, combo_box)
            else:  # 后2行（宽度/高度）用文本框
                line_edit = QLineEdit()
                validator = QIntValidator(0, 9999, line_edit)
                line_edit.setValidator(validator)
                saved_value = self.config.get(text, "")
                if saved_value.isdigit() and 0 <= int(saved_value) <= 9999:
                    line_edit.setText(saved_value)
                else:
                    line_edit.setText("")
                self.tableWidget.setCellWidget(row, 1, line_edit)

        self.pushButton = QPushButton(Form)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setGeometry(QRect(10, 450, 93, 26))
        icon = QIcon()
        icon.addFile(u":/icon/icon/移除_close.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton.setIcon(icon)
        
        # 连接取消按钮的点击事件
        self.pushButton.clicked.connect(Form.close)

        self.pushButton_1 = QPushButton(Form)
        self.pushButton_1.setObjectName(u"pushButton_1")
        self.pushButton_1.setGeometry(QRect(210, 450, 93, 26))
        icon1 = QIcon()
        icon1.addFile(u":/icon/icon/文档详情_doc-detail.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_1.setIcon(icon1)
        
        # 连接默认按钮的点击事件
        self.pushButton_1.clicked.connect(self.restore_defaults)

        self.pushButton_2 = QPushButton(Form)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setGeometry(QRect(410, 450, 93, 26))
        icon2 = QIcon()
        icon2.addFile(u":/icon/icon/确定_check.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_2.setIcon(icon2)
        
        # 连接确定按钮的点击事件
        self.pushButton_2.clicked.connect(self.save_settings)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    
    def load_settings(self):
        """从文件加载设置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line:
                        key, value = line.split('=', 1)
                        self.config[key.strip()] = value.strip()
    
    def save_settings_to_file(self):
        """保存设置到文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            for key, value in self.config.items():
                f.write(f"{key}={value}\n")
    
    def restore_defaults(self):
        """恢复默认设置"""
        for row in range(self.tableWidget.rowCount()):
            widget = self.tableWidget.cellWidget(row, 1)
            if isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)  # 下拉框恢复默认选项
            elif isinstance(widget, QLineEdit):
                widget.setText("")  # 文本框清空内容

    def save_settings(self):
        """保存设置"""
        for row in range(self.tableWidget.rowCount()):
            key = self.tableWidget.item(row, 0).text()
            widget = self.tableWidget.cellWidget(row, 1)
            
            # 根据组件类型获取值（下拉框/文本框）
            if isinstance(widget, QComboBox):
                value = widget.currentText()
            elif isinstance(widget, QLineEdit):
                value = widget.text().strip()  # 文本框需要去除前后空格
            self.config[key] = value
        
        # 保存到文件
        self.save_settings_to_file()
        
        # 显示保存成功的消息
        QMessageBox.information(None, "成功", "视频设置已保存!", QMessageBox.Ok)
        
        # 关闭窗口
        self.tableWidget.parent().close()

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"视频高级配置", None))
        self.pushButton.setText(QCoreApplication.translate("Form", u"取消修改", None))
        self.pushButton_1.setText(QCoreApplication.translate("Form", u"默认", None))
        self.pushButton_2.setText(QCoreApplication.translate("Form", u"确定修改", None))