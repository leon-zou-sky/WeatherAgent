#!/usr/bin/env python3
"""
WeatherAgent 服务启动入口
同时启动 FastAPI (HTTP API) + MCP (SSE)
"""

import multiprocessing
import uvicorn


def run_fastapi():
    """启动 FastAPI 服务 (端口 8000)"""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


def run_mcp_sse():
    """启动 MCP SSE 服务 (端口 9000)"""
    from mcp.server.fastmcp import FastMCP
    from app.mcp.server import mcp

    # 覆盖 host/port 配置
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 9000
    mcp.run(transport="sse")


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 WeatherAgent 服务启动")
    print("=" * 50)
    print("📡 FastAPI (HTTP API): http://0.0.0.0:8000")
    print("🔧 MCP Server (SSE):   http://0.0.0.0:9000/sse")
    print("=" * 50)

    # 启动两个进程
    p1 = multiprocessing.Process(target=run_fastapi, daemon=True)
    p2 = multiprocessing.Process(target=run_mcp_sse, daemon=True)

    p1.start()
    p2.start()

    try:
        p1.join()
        p2.join()
    except KeyboardInterrupt:
        print("\n🛑 服务停止")
        p1.terminate()
        p2.terminate()
