#!/bin/bash
# WeatherAgent 启动脚本
# 同时启动 FastAPI (HTTP) + MCP (SSE)

PYTHON="/Users/zouxuefei/miniconda3/envs/py311/bin/python"
PROJECT_DIR="/Users/zouxuefei/agent_code/WeatherAgent"

cd "$PROJECT_DIR"

echo "🚀 启动 WeatherAgent..."

# 启动 FastAPI (端口 8000)
echo "📡 FastAPI 启动中... http://0.0.0.0:8000"
$PYTHON -m app.main &
FASTAPI_PID=$!

# 启动 MCP SSE Server (端口 9000)
echo "🔧 MCP Server 启动中... http://0.0.0.0:9000/sse"
$PYTHON -c "
from app.mcp.server import mcp
mcp.run(transport='sse', host='0.0.0.0', port=9000)
" &
MCP_PID=$!

echo "✅ 启动完成"
echo "   HTTP API: http://localhost:8000/docs"
echo "   MCP SSE:  http://localhost:9000/sse"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待退出
trap "kill $FASTAPI_PID $MCP_PID 2>/dev/null; exit" INT TERM
wait
