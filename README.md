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
| Agent 框架 | LangChain |
| LLM | 豆包大模型 (火山引擎) |
| 向量数据库 | Milvus |
| 数据库 | MySQL + Redis |

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

## 开发计划

- [x] 项目骨架搭建
- [ ] 接入豆包大模型 API
- [ ] 接入真实气象数据源
- [ ] 实现 Milvus RAG 检索
- [ ] 接入 MySQL 持久化
- [ ] 批量异步处理
- [ ] 监控告警
