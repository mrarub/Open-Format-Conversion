# -*- coding: utf-8 -*-
import os
# 指定为xcb
os.environ['QT_QPA_PLATFORM'] = 'xcb'
import subprocess
from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QFileDialog, QAbstractItemView, QHeaderView, QTableWidgetItem, QMessageBox
from PySide6.QtCore import QProcess, QObject, Signal
from page.home_ui import Ui_MainWindow
import sys
# 导入对应的 UI 类
from page.video import Ui_Form as VideoUiForm
from page.music import Ui_Form as MusicUiForm
from page.image import Ui_Form as ImageUiForm
from page.output_ui import Ui_Form as OutputUiForm
from page.koutu import PhotoIDTool  # 导入抠图窗口类
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator

class OutputWorker(QObject):
    log_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, input_file, output_file, page_index):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.handle_finished)
        self.cmd = None
        self.page_index = page_index  # 保存页面索引

    def start(self):
        # 使用自定义命令替代原固定模板
        if self.cmd:
            self.process.start("sh", ["-c", self.cmd])  # Linux/macOS
        else:
            # 保留原逻辑作为备用
            cmd = f'ffmpeg -y -i "{self.input_file}" "{self.output_file}"'
            self.process.start("sh", ["-c", cmd])

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.log_signal.emit(data)

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.log_signal.emit(data)

    def handle_finished(self):
        self.finished_signal.emit()

    def stop(self):
        self.process.terminate()
        if not self.process.waitForFinished(3000):
            self.process.kill()

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 检查并创建 ui_color.ini 文件
        config_dir = "config"
        ui_color_path = os.path.join(config_dir, "ui_color.ini")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        if not os.path.exists(ui_color_path):
            with open(ui_color_path, 'w', encoding='utf-8') as f:
                pass

        # 优化：通过通用方法应用颜色
        self.apply_ui_color(self)  # 主窗口自身应用颜色

        self.ui.action.triggered.connect(lambda: (self.update_ui_color("237, 255, 228"), QMessageBox.information(self, "提示", "皮肤已修改为护眼绿，需重启应用后生效.")))
        self.ui.action_1.triggered.connect(lambda: (self.update_ui_color("250, 248, 223"), QMessageBox.information(self, "提示", "皮肤已修改为杏仁黄，需重启应用后生效.")))
        self.ui.action_2.triggered.connect(lambda: (self.update_ui_color("212, 231, 246"), QMessageBox.information(self, "提示", "皮肤已修改为淡蓝梦幻，需重启应用后生效.")))
        self.ui.action_3.triggered.connect(lambda: (self.update_ui_color("112, 122, 111"), QMessageBox.information(self, "提示", "皮肤已修改为石青灰，需重启应用后生效.")))
        self.ui.action_4.triggered.connect(lambda: (self.update_ui_color("255, 255, 255"), QMessageBox.information(self, "提示", "皮肤已修改为珍珠白，需重启应用后生效.")))
        # 方法一：结合 QIntValidator 和输入检查
        if hasattr(self.ui, 'lineEdit'):
            int_validator = QIntValidator(0, 51)
            self.ui.lineEdit.setValidator(int_validator)
            self.ui.lineEdit.textChanged.connect(self.validate_line_edit)

        # 方法二：使用正则表达式验证器
        if hasattr(self.ui, 'lineEdit_1') and hasattr(self.ui, 'lineEdit_2'):
            regex = QRegularExpression(r'^\d+$')
            validator = QRegularExpressionValidator(regex)
            self.ui.lineEdit_1.setValidator(validator)
            self.ui.lineEdit_2.setValidator(validator)

        # 连接导航按钮点击事件
        self.ui.pushButton.clicked.connect(self.show_home_page)     # 首页按钮
        self.ui.pushButton_1.clicked.connect(self.show_video_page)  # 视频按钮
        self.ui.pushButton_2.clicked.connect(self.show_audio_page)  # 音频按钮
        self.ui.pushButton_3.clicked.connect(self.show_image_page)  # 图片按钮
        self.ui.pushButton_4.clicked.connect(self.show_compress_page) # 视频压缩按钮

        # 连接高级配置按钮点击事件
        self.ui.pushButton_5.clicked.connect(self.open_video_settings)  # page_1 高级配置
        self.ui.pushButton_10.clicked.connect(self.open_music_settings) # page_2 高级配置
        self.ui.pushButton_15.clicked.connect(self.open_image_settings) # page_3 高级配置

        # 初始化表格设置
        self.setup_table_widget(self.ui.tableWidget, self.ui.pushButton_6, self.ui.pushButton_7, self.ui.pushButton_8)
        self.setup_table_widget(self.ui.tableWidget_2, self.ui.pushButton_11, self.ui.pushButton_12, self.ui.pushButton_13)
        self.setup_table_widget(self.ui.tableWidget_3, self.ui.pushButton_16, self.ui.pushButton_17, self.ui.pushButton_18)
        self.setup_table_widget(self.ui.tableWidget_4, self.ui.pushButton_20, self.ui.pushButton_21, self.ui.pushButton_22)

        # 连接执行按钮点击事件
        self.ui.pushButton_9.clicked.connect(self.execute_ffmpeg)
        self.ui.pushButton_14.clicked.connect(self.execute_ffmpeg)
        self.ui.pushButton_19.clicked.connect(self.execute_ffmpeg)
        self.ui.pushButton_23.clicked.connect(self.execute_ffmpeg)

        # 一键抠图按钮事件
        self.ui.pushButton_24.clicked.connect(self.open_koutu_window)

        # 默认显示首页
        self.show_home_page()
        self.output_window = None
        self.output_worker = None

        # 允许的文件扩展名
        self.allowed_exts_video = [
            "3g2", "3gp", "amv", "asf", "avi", "divx", "dv", "f4v", "flv", "gif", "m2ts", "m4v",
            "mkv", "mov", "mp4", "mpeg", "mpg", "mts", "mxf", "nut", "ogv", "rm", "roq", "swf",
            "ts", "vob", "webm", "wmv", "yuv", "avs", "ivf", "mj2", "nsv", "r3d", "thp", "vmd", "xmv"
        ]
        self.allowed_exts_audio = [
            "aac", "ac3", "aiff", "alac", "amr", "ape", "au", "dts", "eac3", "flac", "m4a", "m4b", "mka", "mlp",
            "mp2", "mp3", "mpc", "oga", "ogg", "opus", "ra", "tak", "tta", "voc", "wav", "wma", "wv", "spx",
            "aif", "caf", "snd", "m3u", "pls", "midi", "mid", "rmi", "aacp"
        ]
        self.allowed_exts_image = [
            "jpg", "jpeg", "png", "bmp", "tiff", "tif", "webp", "gif", "ico", "jp2", "j2k", "pbm", "pgm", "ppm",
            "pam", "pcx", "tga", "sgi", "sun", "ras", "xbm", "xpm", "dds", "exr", "fits", "jpe", "svg", "heic",
            "heif", "avif"
        ]

    def show_home_page(self):
        self.ui.stackedWidget.setCurrentIndex(0)  # 显示page(首页)

    def show_video_page(self):
        self.ui.stackedWidget.setCurrentIndex(1)  # 显示page_1(视频)

    def show_audio_page(self):
        self.ui.stackedWidget.setCurrentIndex(2)  # 显示page_2(音频)

    def show_image_page(self):
        self.ui.stackedWidget.setCurrentIndex(3)  # 显示page_3(图片)

    def show_compress_page(self):
        self.ui.stackedWidget.setCurrentIndex(4)  # 显示page_4(视频压缩)

    def open_video_settings(self):
        self.video_window = QWidget()
        self.video_ui = VideoUiForm()
        self.video_ui.setupUi(self.video_window)
        self.apply_ui_color(self.video_window)  
        self.video_window.show()

    def open_music_settings(self):
        self.music_window = QWidget()
        self.music_ui = MusicUiForm()
        self.music_ui.setupUi(self.music_window)
        self.apply_ui_color(self.music_window)  
        self.music_window.show()

    def open_image_settings(self):
        self.image_window = QWidget()
        self.image_ui = ImageUiForm()
        self.image_ui.setupUi(self.image_window)
        self.apply_ui_color(self.image_window)  
        self.image_window.show()

    def setup_table_widget(self, table_widget, add_button, remove_button, clear_button):
        # 设置表格列数为 1
        table_widget.setColumnCount(1)
        # 设置表头
        table_widget.setHorizontalHeaderLabels(["文件详细信息"])
        # 获取水平表头
        horizontal_header = table_widget.horizontalHeader()
        # 设置列自动拉伸以填充表格
        horizontal_header.setSectionResizeMode(0, QHeaderView.Stretch)
        # 全局设置表格不可编辑
        table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # 绑定添加文件按钮点击事件
        if add_button.objectName() == "pushButton_6" or add_button.objectName() == "pushButton_20":
            add_button.clicked.connect(lambda: self.add_files_filter(table_widget, self.allowed_exts_video, "视频"))
        elif add_button.objectName() == "pushButton_11":
            add_button.clicked.connect(lambda: self.add_files_filter(table_widget, self.allowed_exts_audio, "音频"))
        elif add_button.objectName() == "pushButton_16":
            add_button.clicked.connect(lambda: self.add_files_filter(table_widget, self.allowed_exts_image, "图片"))
        else:
            add_button.clicked.connect(lambda: self.add_files(table_widget))
        # 绑定移除按钮点击事件
        remove_button.clicked.connect(lambda: self.remove_selected_row(table_widget))
        # 绑定移除全部按钮点击事件
        clear_button.clicked.connect(lambda: self.clear_table(table_widget))

    def add_files_filter(self, table_widget, allowed_exts, label):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        ext_str = " ".join([f"*.{ext}" for ext in allowed_exts])
        file_dialog.setNameFilters([
            f"支持的{label}文件 ({ext_str})",
            "所有文件 (*)"
        ])
        file_dialog.selectNameFilter(f"支持的{label}文件 ({ext_str})")
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            existing_paths = []
            for row in range(table_widget.rowCount()):
                item = table_widget.item(row, 0)
                if item:
                    existing_paths.append(item.text())
            for file_path in file_paths:
                if file_path not in existing_paths:
                    row_position = table_widget.rowCount()
                    table_widget.insertRow(row_position)
                    item = QTableWidgetItem(file_path)
                    table_widget.setItem(row_position, 0, item)

    def add_files(self, table_widget):
        # 打开文件选择框，允许多选
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_paths, _ = file_dialog.getOpenFileNames()
        if file_paths:
            existing_paths = []
            # 获取已存在的文件路径
            for row in range(table_widget.rowCount()):
                item = table_widget.item(row, 0)
                if item:
                    existing_paths.append(item.text())
            for file_path in file_paths:
                if file_path not in existing_paths:
                    row_position = table_widget.rowCount()
                    table_widget.insertRow(row_position)
                    # 设置文件详细信息
                    item = QTableWidgetItem(file_path)
                    table_widget.setItem(row_position, 0, item)

    def remove_selected_row(self, table_widget):
        # 获取选中的行
        selected_rows = table_widget.selectionModel().selectedRows()
        for row in sorted(selected_rows, reverse=True):
            table_widget.removeRow(row.row())

    def clear_table(self, table_widget):
        # 清空表格
        while table_widget.rowCount() > 0:
            table_widget.removeRow(0)

    def get_output_format(self):
        current_index = self.ui.stackedWidget.currentIndex()
        if current_index == 1:  # 视频页面
            return self.ui.comboBox.currentText()
        elif current_index == 2:  # 音频页面
            return self.ui.comboBox_2.currentText()
        elif current_index == 3:  # 图片页面
            return self.ui.comboBox_3.currentText()
        elif current_index == 4:  # 视频压缩页面
            return self.ui.comboBox_4.currentText()
        return None

    def get_input_files(self):
        current_index = self.ui.stackedWidget.currentIndex()
        if current_index == 1:
            table_widget = self.ui.tableWidget
        elif current_index == 2:
            table_widget = self.ui.tableWidget_2
        elif current_index == 3:
            table_widget = self.ui.tableWidget_3
        elif current_index == 4:
            table_widget = self.ui.tableWidget_4
        else:
            return []

        input_files = []
        for row in range(table_widget.rowCount()):
            item = table_widget.item(row, 0)
            if item:
                input_files.append(item.text())
        return input_files

    def read_config(self, config_path):
        """读取配置文件并解析有效参数"""
        params = {}
        if not os.path.exists(config_path):  # 文件不存在
            return params

        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if value:  # 只保留值非空的配置
                        params[key] = value
        return params

    def execute_ffmpeg(self):
        # 检查是否有正在运行的任务
        if self.output_worker is not None and self.output_worker.process.state() == QProcess.Running:
            QMessageBox.warning(self, "警告", "当前有任务正在运行，请等待完成后再尝试！")
            return

        output_format = self.get_output_format()
        input_files = self.get_input_files()

        if not output_format or not input_files:
            QMessageBox.warning(self, "警告", "请选择输出格式并添加输入文件！")
            return

        self.file_queue = input_files  # 填充文件队列
        self.current_file_index = 0  # 重置当前索引
        self.current_output_format = output_format  # 保存当前输出格式
        self.current_page_index = self.ui.stackedWidget.currentIndex()  # 保存当前页面索引
        self.process_next_file()  # 修改：不传递参数，使用实例变量

    def process_next_file(self):
        if self.current_file_index >= len(self.file_queue):
            # 所有文件处理完成
            QMessageBox.information(self, "提示", "所有文件执行已完成！")
            return

        input_file = self.file_queue[self.current_file_index]
        file_name = os.path.basename(input_file).rsplit('.', 1)[0]

        current_index = self.current_page_index  # 使用保存的页面索引
        output_format = self.current_output_format

        # 根据当前页面确定输出目录
        if current_index == 1:  # 视频页面（page_1）
            output_dir = "video"
        elif current_index == 2:  # 音频页面（page_2）
            output_dir = "music"
        elif current_index == 3:  # 图片页面（page_3）
            output_dir = "image"
        elif current_index == 4:  # 视频压缩页面（page_4）
            output_dir = "Video_compression"
        else:
            output_dir = ""

        # 创建 Open-Format-Conversion 目录下的输出目录（如果不存在）
        if output_dir:
            full_output_dir = os.path.join(os.getcwd(), "Open-Format-Conversion", output_dir)
            os.makedirs(full_output_dir, exist_ok=True)
            output_file = os.path.join(full_output_dir, f"{file_name}.{output_format.lower()}")
        else:
            output_file = input_file.rsplit('.', 1)[0] + '.' + output_format.lower()

        ffmpeg_args = []

        if current_index == 1:  # 视频页面（page_1）
            # 判断是否为GIF格式
            is_gif = output_format.lower() == "gif"
            config = self.read_config("config/video_settings.ini")

            if not is_gif:  # 非GIF格式时添加配置参数
                # 保留原有参数映射（crf/帧数/编码）
                param_map = {
                    "crf": "-crf",
                    "视频帧数(fps)": "-r",
                    "视频编码": "-c:v"
                }
                # 处理视频参数
                for key, ffmpeg_key in param_map.items():
                    if key in config and config[key]:
                        ffmpeg_args.extend([ffmpeg_key, config[key]])

                # 处理视频音量参数
                volume = config.get("音量", "").strip()
                if volume:
                    try:
                        float(volume)
                        ffmpeg_args.append(f"-filter:a volume={volume}")
                    except ValueError:
                        QMessageBox.warning(self, "警告", "音量值需为有效数字（如1.25）！")
                        return

                # 处理宽度/高度自适应
                width = config.get("宽度", "").strip()
                height = config.get("高度", "").strip()
                if width or height:
                    if width and height:
                        scale = f"scale={width}:{height}"
                    elif width:
                        scale = f"scale={width}:-1"
                    else:
                        scale = f"scale=-1:{height}"
                    ffmpeg_args.extend(["-vf", scale])

            # GIF格式时不添加任何视频参数（直接跳过）

        elif current_index == 2:
            config = self.read_config("config/music_settings.ini")
            param_map = {
                "采样率(Hz)": "-ar",
                "比特率(kbps)": "-b:a",
                "音量": "-filter:a volume="
            }
            # 处理音频参数
            for key, ffmpeg_key in param_map.items():
                if key in config:
                    if key == "音量":
                        ffmpeg_args.append(f"{ffmpeg_key}{config[key]}")
                    else:
                        ffmpeg_args.extend([ffmpeg_key, config[key]])

        elif current_index == 3:
            config = self.read_config("config/image_settings.ini")
            # 处理图片参数
            width = config.get("宽度", "")
            height = config.get("高度", "")
            if width and height:
                ffmpeg_args.extend(["-vf", f"scale={width}:{height}"])
            elif width:
                ffmpeg_args.extend(["-vf", f"scale={width}:-1"])  # 保持宽高比
            elif height:
                ffmpeg_args.extend(["-vf", f"scale=-1:{height}"])  # 保持宽高比

        elif current_index == 4:  # 视频压缩页面（page_4）
            # 1. 处理编码器
            encoder = self.ui.comboBox_5.currentText()
            if encoder and encoder != "默认":
                ffmpeg_args.extend(["-c:v", encoder])

            # 2. 处理CRF值
            crf = self.ui.lineEdit.text().strip()
            if crf:
                ffmpeg_args.extend(["-crf", crf])

            # 3. 处理宽度和高度
            width = self.ui.lineEdit_1.text().strip()
            height = self.ui.lineEdit_2.text().strip()
            if width or height:
                if width and height:
                    scale = f"scale={width}:{height}"
                elif width:
                    scale = f"scale={width}:-1"
                else:
                    scale = f"scale=-1:{height}"
                ffmpeg_args.extend(["-vf", scale])

        # 构造最终FFmpeg命令
        cmd_parts = ["ffmpeg", "-y", "-i", f'"{input_file}"']
        cmd_parts.extend(ffmpeg_args)
        cmd_parts.append(f'"{output_file}"')
        cmd = " ".join(cmd_parts)

        self.output_window = QWidget()
        self.output_ui = OutputUiForm()
        self.output_ui.setupUi(self.output_window)
        self.apply_ui_color(self.output_window)  
        self.output_window.show()

        self.output_worker = OutputWorker(input_file, output_file, current_index)  # 传递页面索引
        self.output_worker.cmd = cmd
        self.output_worker.log_signal.connect(self.update_log)
        self.output_worker.finished_signal.connect(self.output_finished)
        self.output_ui.pushButton.clicked.connect(self.stop_ffmpeg)
        self.output_window.closeEvent = self.close_output_window

        self.output_worker.start()

    def update_log(self, log):
        self.output_ui.textEdit.append(log)

    def stop_ffmpeg(self):
        if self.output_worker:
            self.output_worker.stop()
        if self.output_window:
            self.output_window.close()

    def output_finished(self):
        if self.output_window:
            self.output_window.close()
        self.current_file_index += 1
        if self.current_file_index >= len(self.file_queue):
            # 所有文件处理完成
            QMessageBox.information(self, "提示", "所有文件执行已完成！")
            # 使用 OutputWorker 中保存的页面索引
            current_index = self.output_worker.page_index
            if current_index == 1:  # 视频页面（page_1）
                output_dir = "video"
            elif current_index == 2:  # 音频页面（page_2）
                output_dir = "music"
            elif current_index == 3:  # 图片页面（page_3）
                output_dir = "image"
            elif current_index == 4:  # 视频压缩页面（page_4）
                output_dir = "Video_compression"
            else:
                output_dir = ""

            if output_dir:
                full_output_dir = os.path.join(os.getcwd(), "Open-Format-Conversion", output_dir)
                try:
                    # 使用 subprocess 模块打开目录
                    subprocess.run(['xdg-open', full_output_dir], check=True)
                except subprocess.CalledProcessError as e:
                    QMessageBox.warning(self, "警告", f"无法打开输出目录: {e}")
            return
        self.process_next_file()

    def close_output_window(self, event):
        self.stop_ffmpeg()
        event.accept()

    def validate_line_edit(self, text):
        if not text:  # 若输入为空，直接返回，允许清空
            self.ui.lineEdit.setProperty("prev_text", None)
            return
        try:
            value = int(text)
            if 0 <= value <= 51:
                # 记录有效输入
                self.ui.lineEdit.setProperty("prev_text", value)
            else:
                # 超出范围，恢复上一个有效输入
                prev_text = self.ui.lineEdit.property("prev_text")
                if prev_text is not None:
                    self.ui.lineEdit.setText(str(prev_text))
                else:
                    self.ui.lineEdit.clear()
        except ValueError:
            # 非整数输入，恢复上一个有效输入
            prev_text = self.ui.lineEdit.property("prev_text")
            if prev_text is not None:
                self.ui.lineEdit.setText(str(prev_text))
            else:
                self.ui.lineEdit.clear()

    def update_ui_color(self, color_value):
        # 使用相对路径构建配置文件路径
        config_path = os.path.join("config", "ui_color.ini")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(f"ui_color={color_value}\n")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"更新配置文件失败: {e}")

    def read_ui_color_config(self):
        """读取UI颜色配置（保持原有逻辑）"""
        config_path = os.path.join("config", "ui_color.ini")
        if not os.path.exists(config_path):
            return None
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                line = line.strip()
                if line.startswith("ui_color="):
                    color_value = line.split("=", 1)[1].strip()
                    return color_value if color_value else None
        return None

    def apply_ui_color(self, widget: QWidget):
        """通用方法：为指定部件应用颜色配置"""
        color = self.read_ui_color_config()
        if color:
            widget.setStyleSheet(f"background-color: rgb({color});")
    # 打开抠图窗口
    def open_koutu_window(self):
        self.koutu_window = PhotoIDTool()
        self.koutu_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
