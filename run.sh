#!/bin/bash
# 股票相关性分析 Web 应用启动脚本

echo "========================================"
echo "📈 股票相关性分析 Web 应用"
echo "========================================"

# 切换到 web 目录
cd "$(dirname "$0")"

# 检查并安装依赖
echo "检查 Python 依赖..."
pip install -r requirements.txt -q

# 启动服务
echo ""
echo "启动 Flask 服务..."
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo "========================================"
echo ""

python app.py
