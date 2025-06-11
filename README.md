# Open Format Conversion
![1](https://github.com/user-attachments/assets/82175739-0917-4062-a567-6f92f9da88c7)


**跨平台开源格式转换工具**

## 项目简介

Open 格式转换 是一款专为 **Linux 系统开发** 的 **图形化格式转换工具**，旨在为用户提供轻量、高效且开源的跨平台格式转换解决方案。项目灵感源自 Deepin 论坛网友需求——打造一个 **Linux 原生 GUI 交互** 的开源程序。现在，除了基本的格式转换功能，还新增了一系列强大的图像处理功能。

## 主要特性

- **系统兼容性**：原生支持 Linux（如 Deepin、Debian、Ubuntu）。
- **图形化交互**：基于 PySide6 开发的直观界面，操作简单便捷。
- **多格式支持**：依托 FFmpeg 技术，支持音视频、图片等常见格式的转换（如 MP4 ➔ MKV、JPG ➔ PNG 等）。
- **新增图像处理功能**：
  - **一键抠图**：智能分割主体与背景，支持多类型图像。利用 U-2-Net 和 onnxruntime 实现高效准确的图像分割。
  - **背景更换**：支持更换背景颜色，让您轻松为图像添加新的背景效果。
  - **图片清晰化**：深度学习增强细节，优化画质。借助 Real-ESRGAN 技术，提升图片的清晰度和质量。
- **开源免费**：遵循开源协议，代码完全公开，欢迎社区贡献与反馈。

## 访问地址

- **官方网站**：[https://mrarub.eu.org](https://mrarub.eu.org)
- **代码仓库**：
  - GitHub（国际）：[https://github.com/mrarub/Open-Format-Conversion](https://github.com/mrarub/Open-Format-Conversion)
  - Gitee（国内加速）：[https://gitee.com/mrarub/Open-Format-Conversion](https://gitee.com/mrarub/Open-Format-Conversion)

## 技术栈

项目使用了以下开源项目：

- PySide6：https://code.qt.io/cgit/pyside
- FFmpeg：https://github.com/FFmpeg/FFmpeg
- onnxruntime：https://github.com/microsoft/onnxruntime
- U-2-Net：https://github.com/xuebinqin/U-2-Net
- Real-ESRGAN：https://github.com/xinntao/Real-ESRGAN
- Pillow：https://github.com/python-pillow/Pillow
- PyInstaller：https://github.com/pyinstaller/pyinstaller

## 贡献与反馈

欢迎通过 GitHub/Gitee 提交 Issue 或 Pull Request 参与项目改进。  
如需帮助或反馈问题，可通过官方网站或仓库 Issues 联系开发者。

## 🌟 支持与鼓励

如果 Open Format Conversion 对您有所帮助，欢迎点击右上角的  **⭐ Star** 为项目点亮小星星～  
您的支持是我持续优化的最大动力！✨

（注：可在 GitHub/Gitee 仓库页面右上角找到星星图标哦～）
