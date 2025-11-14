#!/bin/bash

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 切换到脚本目录
cd "$SCRIPT_DIR"

echo "======================================"
echo "Office 365 订阅监控系统"
echo "======================================"
echo ""
echo "工作目录: $SCRIPT_DIR"
echo ""
echo "正在启动..."
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    echo "请先安装 Python 3.7 或更高版本"
    exit 1
fi

# 检查依赖是否安装
if ! python3 -c "import flask" &> /dev/null; then
    echo "📦 正在安装依赖..."
    pip3 install -r requirements.txt
fi

echo "✅ 依赖检查完成"
echo ""
echo "🚀 启动服务..."
echo ""
echo "访问地址: http://localhost:5000"
echo "默认密码: xiaokun567"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动应用
python3 app.py
