import sys
from PIL import Image
import numpy as np
import onnxruntime as ort
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QFileDialog, QColorDialog, QSizePolicy, 
                              QMessageBox, QProgressDialog, QFrame)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, Signal, QThread, QObject
import os
# 指定为xcb
os.environ['QT_QPA_PLATFORM'] = 'xcb'
import subprocess


class PhotoProcessor(QObject):
    finished = Signal(QImage)
    batch_finished = Signal()
    error = Signal(str)
    progress = Signal(int)

    ort_session = None

    def __init__(self, image_path, operation, **kwargs):
        super().__init__()
        self.image_path = image_path 
        self.operation = operation
        self.kwargs = kwargs
        self.batch_mode = kwargs.get('batch_mode', False)
        self.output_dir = kwargs.get('output_dir', None)
        if PhotoProcessor.ort_session is None:
            model_path = os.path.join(os.path.dirname(__file__), "u2netp.onnx")
            PhotoProcessor.ort_session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.ort_session = PhotoProcessor.ort_session

    def process(self):
        try:
            if isinstance(self.image_path, list):  # 批量处理模式
                self._process_batch()
            else:  # 单张图片处理模式
                if isinstance(self.image_path, Image.Image):
                    img = self.image_path
                else:
                    img = Image.open(self.image_path)
                if self.operation == "remove_bg":
                    result = self._remove_background(img)
                elif self.operation == "change_bg_color":
                    result = self._change_background_color(img)
                elif self.operation == "enhance_image":
                    result = self._enhance_image(self.image_path)
                else:
                    raise ValueError("Unknown operation")
                self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    def _process_batch(self):
        """批量处理图片"""
        errors = []  # 用于存储错误信息
        try:
            total = len(self.image_path)
            for i, path in enumerate(self.image_path, 1):
                try:
                    img = Image.open(path)
                    if self.operation == "remove_bg":
                        output = self.remove_bg_onnx(img)
                    elif self.operation == "change_bg_color":
                        no_bg = self.remove_bg_onnx(img)
                        color = self.kwargs.get('color', (255, 255, 255))
                        output = Image.new('RGB', no_bg.size, color)
                        output.paste(no_bg, (0, 0), no_bg)
                    elif self.operation == "enhance_image":
                        import tempfile
                        import shutil
                        exe_path = os.path.join(os.path.dirname(__file__), "realesrgan-ncnn-vulkan")
                        temp_dir = tempfile.mkdtemp()
                        output_path = os.path.join(temp_dir, "enhanced.png")
                        cmd = [
                            exe_path,
                            "-i", path,
                            "-o", output_path,
                        ]
                        try:
                            subprocess.run(cmd, check=True)
                            enhanced_img = Image.open(output_path)
                            output = enhanced_img.convert("RGBA")
                        finally:
                            try:
                                shutil.rmtree(temp_dir)
                            except Exception:
                                pass
                    else:
                        continue
                    if self.output_dir:
                        filename = os.path.basename(path)
                        save_path = os.path.join(self.output_dir, filename)
                        if self.operation == "enhance_image":
                            save_path = os.path.splitext(save_path)[0] + ".png"
                        output.save(save_path)
                    self.progress.emit(int(i * 100 / total))
                except Exception as e:
                    errors.append(f"{path}: {str(e)}")
            self.batch_finished.emit()
            if errors:
                self.error.emit('\n'.join(errors))
        except Exception as e:
            self.error.emit(str(e))

    def _remove_background(self, img):
        output = self.remove_bg_onnx(img)
        return self._pil_to_qimage(output)

    def _change_background_color(self, img):
        color = self.kwargs.get('color', (255, 255, 255))
        no_bg = self.remove_bg_onnx(img)
        background = Image.new('RGB', no_bg.size, color)
        background.paste(no_bg, (0, 0), no_bg)
        return self._pil_to_qimage(background)

    def remove_bg_onnx(self, img):
        # 预处理
        img = img.convert('RGB')
        im = img.resize((320, 320), Image.BILINEAR)
        arr = np.array(im).astype(np.float32) / 255.0
        arr = arr.transpose((2, 0, 1))[np.newaxis, ...]
        # 推理
        ort_inputs = {self.ort_session.get_inputs()[0].name: arr}
        ort_outs = self.ort_session.run(None, ort_inputs)
        pred = ort_outs[0][0][0]
        # 后处理
        pred = (pred - pred.min()) / (pred.max() - pred.min() + 1e-8)
        mask = (pred * 255).astype(np.uint8)
        mask = Image.fromarray(mask).resize(img.size, Image.BILINEAR)
        # 合成透明背景
        img_rgba = img.convert("RGBA")
        mask_np = np.array(mask)
        img_np = np.array(img_rgba)
        img_np[..., 3] = mask_np
        return Image.fromarray(img_np)

    def _pil_to_qimage(self, pil_img):
        try:
            if pil_img.mode == 'RGBA':
                data = pil_img.convert('RGBA').tobytes('raw', 'RGBA')
                return QImage(data, pil_img.width, pil_img.height, pil_img.width * 4, QImage.Format_RGBA8888)
            else:
                data = pil_img.convert('RGB').tobytes('raw', 'RGB')
                return QImage(data, pil_img.width, pil_img.height, pil_img.width * 3, QImage.Format_RGB888)
        except Exception as e:
            self.error.emit(str(e))
            return None

    def _enhance_image(self, image_path):
        """调用realesrgan-ncnn-vulkan增强图片清晰度"""
        import tempfile
        import shutil

        exe_path = os.path.join(os.path.dirname(__file__), "realesrgan-ncnn-vulkan")
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "enhanced.png")
        cmd = [
            exe_path,
            "-i", image_path,
            "-o", output_path,
            "-n", "realesrgan-x4plus-anime"
        ]
        try:
            self.progress.emit(10)
            subprocess.run(cmd, check=True)
            self.progress.emit(80)
            enhanced_img = Image.open(output_path)
            qimg = self._pil_to_qimage(enhanced_img)
            self.progress.emit(100)
            return qimg
        except Exception as e:
            raise RuntimeError(f"图片增强失败: {e}")
        finally:
            # 优化3: 清理更健壮
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

class PhotoIDTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("一键抠图")
        self.setMinimumSize(800, 600)
        
        # 初始化变量
        self.current_image_path = None
        self.original_pixmap = None
        self.processed_pixmap = None
        self.bg_color = (255, 255, 255)  # 默认白色背景
        
        # 创建界面
        self._create_ui()

    def _create_ui(self):
        """创建主界面"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        main_layout = QHBoxLayout(main_widget)
        
        # 图像显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("QLabel { background-color: #333; }")
        main_layout.addWidget(self.image_label, 70)
        
        # 控制面板
        control_panel = QWidget()
        control_panel.setFixedWidth(250)
        control_layout = QVBoxLayout(control_panel)

        # 单张处理区域
        control_layout.addWidget(QLabel("单张处理"))
        
        # 打开按钮
        self.open_btn = QPushButton("打开图片")
        self.open_btn.clicked.connect(self.open_image)
        control_layout.addWidget(self.open_btn)
        
        # 恢复原图按钮
        self.restore_btn = QPushButton("恢复原图")
        self.restore_btn.setEnabled(False)
        self.restore_btn.clicked.connect(self.restore_original_image)
        control_layout.addWidget(self.restore_btn)

        # 单张背景处理功能
        self.remove_bg_btn = QPushButton("去除背景")
        self.remove_bg_btn.clicked.connect(lambda: self.process_image("remove_bg"))
        self.remove_bg_btn.setEnabled(False)
        control_layout.addWidget(self.remove_bg_btn)

        # 一键清晰按钮
        self.enhance_btn = QPushButton("一键清晰")
        self.enhance_btn.clicked.connect(lambda: self.process_image("enhance_image"))
        self.enhance_btn.setEnabled(False)
        control_layout.addWidget(self.enhance_btn)
        
        # 单张背景颜色设置
        bg_color_layout = QHBoxLayout()
        self.bg_color_btn = QPushButton("背景颜色")
        self.bg_color_btn.clicked.connect(self.choose_bg_color)
        bg_color_layout.addWidget(self.bg_color_btn)
        
        self.bg_color_display = QLabel()
        self.bg_color_display.setFixedSize(30, 30)
        self.bg_color_display.setStyleSheet("background-color: white; border: 1px solid black;")
        bg_color_layout.addWidget(self.bg_color_display)
        
        self.apply_bg_color_btn = QPushButton("更换背景")
        self.apply_bg_color_btn.clicked.connect(lambda: self.process_image("change_bg_color", color=self.bg_color))
        self.apply_bg_color_btn.setEnabled(False)
        bg_color_layout.addWidget(self.apply_bg_color_btn)
        
        control_layout.addLayout(bg_color_layout)

        # 保存结果按钮，移动到这里
        self.save_btn = QPushButton("保存结果")
        self.save_btn.clicked.connect(self.save_image)
        self.save_btn.setEnabled(False)
        control_layout.addWidget(self.save_btn)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        control_layout.addWidget(separator)
        
        # 批量处理区域
        control_layout.addWidget(QLabel("\n批量处理"))
        
        self.batch_open_btn = QPushButton("批量去除背景")
        self.batch_open_btn.clicked.connect(self.batch_open_images)
        control_layout.addWidget(self.batch_open_btn)
        
        self.batch_bg_btn = QPushButton("批量更换背景")
        self.batch_bg_btn.clicked.connect(self.batch_change_background)
        control_layout.addWidget(self.batch_bg_btn)

        # 新增：批量修复高清图片按钮
        self.batch_enhance_btn = QPushButton("批量修复高清图片")
        self.batch_enhance_btn.clicked.connect(self.batch_enhance_images)
        control_layout.addWidget(self.batch_enhance_btn)

        control_layout.addStretch()
        main_layout.addWidget(control_panel, 30)

    def open_image(self):
        """打开图片文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.webp *.ico)"
        )
        
        if file_path:
            self.current_image_path = file_path
            self.original_pixmap = QPixmap(file_path)
            self.display_image(self.original_pixmap)
            self.save_btn.setEnabled(True)
            self.remove_bg_btn.setEnabled(True)
            self.apply_bg_color_btn.setEnabled(True)
            self.enhance_btn.setEnabled(True)
            self.restore_btn.setEnabled(True)

    def restore_original_image(self):
        """恢复原图"""
        if self.original_pixmap:
            self.display_image(self.original_pixmap)
            self.processed_pixmap = None

    def start_batch_process(self, operation, file_paths, output_dir, dialog_title, dialog_text, **kwargs):
        """通用批量处理启动方法"""
        self.progress_dialog = QProgressDialog(dialog_text, "取消", 0, 100, self)
        self.progress_dialog.setWindowTitle(dialog_title)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.show()

        self.thread = QThread()
        self.processor = PhotoProcessor(
            file_paths,
            operation,
            batch_mode=True,
            output_dir=output_dir,
            **kwargs
        )
        self.processor.moveToThread(self.thread)
        self.thread.started.connect(self.processor.process)
        self.processor.progress.connect(self.update_progress)
        self.processor.batch_finished.connect(self.on_batch_finished)
        self.processor.error.connect(self.on_batch_error)
        self.processor.batch_finished.connect(self.thread.quit)
        self.processor.error.connect(self.thread.quit)
        self.processor.finished.connect(self.processor.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.set_buttons_enabled(False)
        self.thread.start()

    def batch_open_images(self):
        """批量去除背景文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择多张图片", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.webp *.ico)"
        )
        if file_paths:
            output_dir = QFileDialog.getExistingDirectory(self, "选择输出目录")
            if not output_dir:
                return
            self.start_batch_process(
                "remove_bg", file_paths, output_dir,
                "批量处理", "批量处理图片中..."
            )

    def batch_change_background(self):
        """批量更换背景颜色"""
        color = QColorDialog.getColor()
        if not color.isValid():
            return
        self.bg_color = (color.red(), color.green(), color.blue())
        self.bg_color_display.setStyleSheet(
            f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); "
            "border: 1px solid black;"
        )
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择多张图片", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.webp *.ico)"
        )
        if file_paths:
            output_dir = QFileDialog.getExistingDirectory(self, "选择输出目录")
            if not output_dir:
                return
            self.start_batch_process(
                "change_bg_color", file_paths, output_dir,
                "批量处理", "批量更换背景中...",
                color=self.bg_color
            )

    def batch_enhance_images(self):
        """批量修复高清图片"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择多张图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.webp *.ico)"
        )
        if file_paths:
            output_dir = QFileDialog.getExistingDirectory(self, "选择输出目录")
            if not output_dir:
                return
            self.start_batch_process(
                "enhance_image", file_paths, output_dir,
                "批量修复", "批量修复高清图片中..."
            )

    def update_progress(self, value):
        """更新进度条（在主线程中）"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setValue(value)

    def on_batch_finished(self):
        """批量处理完成（在主线程中）"""
        self.set_buttons_enabled(True)
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        QMessageBox.information(self, "完成", "批量处理完成!")

        if hasattr(self, 'processor') and self.processor.output_dir:
            try:
                if sys.platform == "darwin":
                    subprocess.run(["open", self.processor.output_dir], check=True)
                else:
                    subprocess.run(["xdg-open", self.processor.output_dir], check=True)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"无法打开输出目录: {str(e)}")

    def on_batch_error(self, error_msg):
        """批量处理错误（在主线程中）"""
        self.set_buttons_enabled(True)
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        QMessageBox.critical(self, "错误", f"批量处理出错:\n{error_msg}")

    def save_image(self):
        """保存处理后的图片"""
        if not self.processed_pixmap:
            QMessageBox.warning(self, "警告", "没有可保存的处理结果!")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存图片", "", "PNG 图片 (*.png);;JPEG 图片 (*.jpg *.jpeg);;BMP 图片 (*.bmp);;GIF 图片 (*.gif);;TIFF 图片 (*.tiff);;WebP 图片 (*.webp);;ICO 图片 (*.ico)"
        )
        if file_path:
            if not any(file_path.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp', '.ico']):
                file_path += '.png'
            self.processed_pixmap.save(file_path)
            QMessageBox.information(self, "成功", "图片已保存!")
            file_dir = os.path.dirname(os.path.abspath(file_path))
            try:
                if sys.platform == "darwin":
                    subprocess.run(["open", file_dir], check=True)
                else:
                    subprocess.run(["xdg-open", file_dir], check=True)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"无法打开目录: {str(e)}")

    def display_image(self, pixmap):
        """显示图片"""
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """窗口大小改变时调整图片"""
        super().resizeEvent(event)
        if hasattr(self, 'image_label') and self.image_label.pixmap():
            self.display_image(self.image_label.pixmap())

    def choose_bg_color(self):
        """选择背景颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.bg_color = (color.red(), color.green(), color.blue())
            self.bg_color_display.setStyleSheet(
                f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); "
                "border: 1px solid black;"
            )

    def process_image(self, operation, **kwargs):
        """处理图片"""
        if not self.image_label.pixmap():
            QMessageBox.warning(self, "警告", "请先打开一张图片!")
            return

        # 一键清晰也处理label上的图片，先保存为临时文件再传递路径
        if operation == "enhance_image":
            import tempfile
            qimg = self.image_label.pixmap().toImage().convertToFormat(QImage.Format_RGBA8888)
            width = qimg.width()
            height = qimg.height()
            arr = qimg.bits().tobytes()
            img = Image.frombytes("RGBA", (width, height), arr)
            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            img.save(temp_file.name)
            image_input = temp_file.name
        else:
            # QPixmap -> QImage -> PIL.Image
            qimg = self.image_label.pixmap().toImage().convertToFormat(QImage.Format_RGBA8888)
            width = qimg.width()
            height = qimg.height()
            arr = qimg.bits().tobytes()
            img = Image.frombytes("RGBA", (width, height), arr)
            image_input = img

        self.thread = QThread()
        self.processor = PhotoProcessor(image_input, operation, **kwargs)
        self.processor.moveToThread(self.thread)
        self.thread.started.connect(self.processor.process)
        self.processor.finished.connect(self.on_processing_finished)
        self.processor.error.connect(self.on_processing_error)
        self.processor.finished.connect(self.thread.quit)
        self.processor.error.connect(self.thread.quit)
        self.processor.finished.connect(self.processor.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.set_buttons_enabled(False)
        self.statusBar().showMessage("正在处理图片...")

        if operation == "enhance_image":
            self.progress_dialog = QProgressDialog("图片处理中...", "取消", 0, 100, self)
            self.progress_dialog.setWindowTitle("图片修复")
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setAutoClose(True)
            self.progress_dialog.show()
            self.processor.progress.connect(self.update_enhance_progress)
        else:
            self.progress_dialog = None

        self.thread.start()

    def update_enhance_progress(self, value):
        """更新增强进度条"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setValue(value)

    def on_processing_finished(self, qimage):
        """处理完成"""
        self.processed_pixmap = QPixmap.fromImage(qimage)
        self.display_image(self.processed_pixmap)
        self.set_buttons_enabled(True)
        self.statusBar().showMessage("处理完成!", 3000)
        # 关闭进度条
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    def on_processing_error(self, error_msg):
        """处理出错"""
        QMessageBox.critical(self, "错误", f"图片处理失败:\n{error_msg}")
        self.set_buttons_enabled(True)
        self.statusBar().showMessage("处理失败!", 3000)
        # 关闭进度条
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    def set_buttons_enabled(self, enabled):
        """设置按钮启用状态"""
        self.open_btn.setEnabled(enabled)
        self.batch_open_btn.setEnabled(enabled)
        self.batch_bg_btn.setEnabled(enabled)
        self.remove_bg_btn.setEnabled(enabled)
        self.apply_bg_color_btn.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.enhance_btn.setEnabled(enabled)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = PhotoIDTool()
    window.show()
    sys.exit(app.exec())