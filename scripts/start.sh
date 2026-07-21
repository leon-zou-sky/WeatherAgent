#!/bin/bash
# =============================================
# 启动服务脚本
# 用法: bash scripts/start.sh
# =============================================

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="/Users/skyfei/opt/miniconda3/envs/py311/bin/python"

cd "$PROJECT_DIR"

echo "========================================"
echo "启动气象负反馈分析系统"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

# 检查依赖
echo "📌 检查依赖..."
$PYTHON -c "import fastapi, uvicorn, sqlalchemy, httpx" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 缺少依赖，正在安装..."
    $PYTHON -m pip install -r requirements.txt -q
fi

# 启动服务
echo ""
echo "🚀 启动 FastAPI 服务..."
echo "   API 文档: http://localhost:8000/docs"
echo "   健康检查: http://localhost:8000/health"
echo ""

$PYTHON main.py
