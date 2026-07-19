#!/usr/bin/env python3
"""
WeatherAgent MCP Server 启动入口

使用方式：
  # stdio 模式（Claude Code / Cursor / Claude Desktop 使用）
  python mcp_main.py

  # 配置到 Claude Code（.claude/settings.json）:
  # {
  #   "mcpServers": {
  #     "weather-agent": {
  #       "command": "python",
  #       "args": ["mcp_main.py"],
  #       "env": { "DB_HOST": "localhost", "DB_PORT": "3307", ... }
  #     }
  #   }
  # }
"""

from app.mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
