# 气象负反馈分析 Agent

智能 Agent 系统，自动分析气象数据负反馈，定位数据链路问题。

## 核心能力

- **负反馈自动分析** - 自动解析用户反馈，判断问题类型
- **链路自动排查** - 检查数据源 → 采集 → 处理 → 存储 → 发布全链路
- **体感温度计算** - 基于风寒指数/热指数解释用户感受
- **知识检索 (RAG)** - 检索历史案例，参考解决方案
- **自动回复生成** - 生成专业回复内容

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| Agent 框架 | 自研编排（Skill + Agent 混合架构） |
| LLM | 豆包大模型 (火山引擎 Ark) |
| 向量数据库 | Milvus Lite + BGE-large-zh-v1.5 |
| 数据库 | MySQL 8.0 |
| MCP Server | MCP Python SDK（stdio / SSE） |
| 部署 | Docker Compose |

## 项目结构

```
WeatherAgent/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── api/v1/              # API 路由
│   │   └── endpoints/
│   │       └── analyze.py   # 分析接口
│   ├── agent/               # Agent 核心
│   │   ├── core.py          # Agent 主逻辑
│   │   ├── prompts.py       # Prompt 模板
│   │   └── tools.py         # Function Calling 定义
│   ├── skills/              # Skill 实现
│   │   ├── data_source.py   # 数据源检查
│   │   ├── pipeline.py      # 链路检查
│   │   ├── weather.py       # 气象数据查询
│   │   ├── alert.py         # 预警数据查询
│   │   ├── feels_like.py    # 体感温度计算
│   │   ├── knowledge.py     # 知识检索 RAG
│   │   └── notification.py  # 发送通知
│   ├── models/              # 数据模型
│   │   ├── schemas.py       # Pydantic Schema
│   │   └── database.py      # SQLAlchemy 模型
│   └── services/            # 外部服务
│       └── llm.py           # LLM 调用封装
├── tests/
├── main.py                  # 启动脚本
├── requirements.txt
├── .env.example
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入实际配置
```

### 3. 启动服务

```bash
python main.py
```

服务启动后访问:
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 4. 测试 API

```bash
curl -X POST http://localhost:8000/api/v1/agent/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "feedback_id": "FB20240115001",
    "content": "北京温度不准，显示25度，实际30度",
    "location": "北京",
    "time": "2024-01-15"
  }'
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/agent/analyze` | POST | 分析单条负反馈 |
| `/api/v1/agent/batch-analyze` | POST | 批量分析 |
| `/api/v1/agent/analysis/{id}` | GET | 查询分析结果 |
| `/health` | GET | 健康检查 |

## MCP Server

项目提供 MCP（Model Context Protocol）服务，可直接在 Claude Code / Cursor / Claude Desktop 中使用气象分析能力。

### 6 个工具

| 工具 | 角色 | 说明 |
|------|------|------|
| `query_weather` | 客服 | 查询城市实况气象数据 |
| `query_alert` | 客服 | 查询当前生效的气象预警 |
| `search_knowledge` | 客服 | 检索知识库相似案例和解决方案 |
| `analyze_feedback` | 客服 | 分析负反馈，生成分析报告和建议回复 |
| `check_pipeline` | 运营 | 检查数据链路健康状态 |
| `get_monitor_overview` | 运营 | 获取反馈监控概览和异常告警 |

### 启动方式

```bash
# stdio 模式（供 Claude Code / Cursor / Claude Desktop 调用）
python mcp_main.py
```

### Claude Code 配置

在项目根目录创建 `.claude/settings.json`：

```json
{
  "mcpServers": {
    "weather-agent": {
      "command": "python",
      "args": ["mcp_main.py"],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "3307",
        "DB_USER": "root",
        "DB_PASSWORD": "123456",
        "DB_NAME": "weather"
      }
    }
  }
}
```

配置完成后，在 Claude Code 对话中直接说：
- "帮我查一下北京天气"
- "有没有预警"
- "分析这条反馈：温度不准，显示25度实际30度"
- "检查一下北京数据链路"

Claude 会自动调用对应工具返回结果。

## 部署

### Docker 部署（推荐）

```bash
# 构建并启动
docker compose -f docker-compose-app.yml up -d

# 查看日志
docker compose -f docker-compose-app.yml logs -f
```

启动后：
- HTTP API：http://localhost:8000/docs
- MCP SSE：http://localhost:9000/sse

### 客户端配置

**Trae / Cursor**（连接远程 MCP）：

```json
{
  "mcpServers": {
    "weather-agent": {
      "url": "http://服务器IP:9000/sse"
    }
  }
}
```

**Claude Code**（本地 stdio 模式）：

```json
{
  "mcpServers": {
    "weather-agent": {
      "command": "python",
      "args": ["mcp_main.py"]
    }
  }
}
```

## 开发进度

- [x] 项目骨架搭建
- [x] 接入豆包大模型 API
- [x] 接入真实气象数据源（北京局接口）
- [x] 实现 Milvus RAG 检索（Top-1 命中率 93.3%）
- [x] 接入 MySQL 持久化
- [x] 批量异步处理
- [x] 监控告警
- [x] MCP Server（6 个工具，客服 + 运营）
- [x] Docker 部署（FastAPI + MCP SSE 双服务）
- [ ] 自动派单
- [ ] 混合检索（向量 + BM25）
- [ ] Reranker 精排
