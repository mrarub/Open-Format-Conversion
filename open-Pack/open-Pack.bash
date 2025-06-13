#!/bin/bash

# 输出开始创建目录和复制文件的提示信息
echo "开始创建必要的目录并复制文件..."

# 创建必要的目录
mkdir -p com.mrarub.open/DEBIAN
echo "已创建 com.mrarub.open/DEBIAN 目录"

mkdir -p com.mrarub.open/usr/bin
echo "已创建 com.mrarub.open/usr/bin 目录"

mkdir -p com.mrarub.open/usr/share/applications
echo "已创建 com.mrarub.open/usr/share/applications 目录"

mkdir -p com.mrarub.open/usr/share/icons/hicolor/512x512/apps
echo "已创建 com.mrarub.open/usr/share/icons/hicolor/512x512/apps 目录"

# 复制文件
cp "Open格式转换" com.mrarub.open/usr/bin/
echo "已将 'Open格式转换' 复制到 com.mrarub.open/usr/bin/ 目录"

cp open.png com.mrarub.open/usr/share/icons/hicolor/512x512/apps/com.mrarub.open.png
echo "已将 open.png 复制到 com.mrarub.open/usr/share/icons/hicolor/512x512/apps/ 目录，并命名为 com.mrarub.open.png"

# 开始计算并更新 Installed-Size
echo "开始计算并更新 Installed-Size..."

# 定义包目录
PACKAGE_DIR="com.mrarub.open"

# 计算包安装后的大小（单位：KB）
INSTALLED_SIZE=$(du -sk "$PACKAGE_DIR/usr" "$PACKAGE_DIR/var" "$PACKAGE_DIR/etc" 2>/dev/null | awk '{sum += $1} END {print sum}')
echo "计算得到包安装后的大小为 $INSTALLED_SIZE KB"

# 获取控制文件路径
CONTROL_FILE="$PACKAGE_DIR/DEBIAN/control"

# 检查 Installed-Size 字段是否存在，若存在则更新，不存在则添加
if grep -q "Installed-Size:" "$CONTROL_FILE"; then
    sed -i "s/Installed-Size: [0-9]*/Installed-Size: $INSTALLED_SIZE/" "$CONTROL_FILE"
    echo "已更新 $CONTROL_FILE 中的 Installed-Size 字段为 $INSTALLED_SIZE KB"
else
    echo "Installed-Size: $INSTALLED_SIZE" >> "$CONTROL_FILE"
    echo "已在 $CONTROL_FILE 中添加 Installed-Size 字段，值为 $INSTALLED_SIZE KB"
fi

# 开始打包
echo "开始打包..."
dpkg-deb --build com.mrarub.open
echo "已完成 com.mrarub.open 的打包操作"