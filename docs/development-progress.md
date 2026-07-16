# 气象负反馈分析 Agent - 开发进度

> 更新时间：2026-07-15

---

## 一、项目概述

**目标**：构建智能 Agent 系统，自动分析气象数据负反馈，定位问题原因，生成回复。

**核心价值**：
- 排查时间：2 小时 → 5 分钟
- 人力成本：降低 90%
- 响应速度：提升 100 倍

---

## 二、技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| Python | 3.11 | /Users/skyfei/opt/miniconda3/envs/py311 |
| Web 框架 | FastAPI | 异步支持、自动生成 API 文档 |
| LLM | 豆包大模型 | 火山引擎 Ark 平台，OpenAI 兼容接口 |
| 向量数据库 | Milvus Lite | 本地文件存储，不需要 Docker |
| Embedding | BGE-large-zh-v1.5 | 智源研究院中文向量模型，1024 维 |
| 关系数据库 | MySQL 8.0 | Docker 容器，端口 3307 |
| ORM | SQLAlchemy | 同步/异步双模式 |

---

## 三、已完成功能

### 3.1 气象数据下载器 (`downloader/`)

从北京局 v2 接口下载三种数据：

| 数据类型 | 表名 | 更新频率 | 字段数 |
|---------|------|---------|--------|
| 实况 | `weather_cn` | 每10分钟 | 温度、体感、湿度、风速风向、能见度、气压、降水 |
| 逐时预报 | `weather_hh` | 每小时 | 温度、风向风速、湿度、天气、降水概率、降雪、气压 |
| 逐天预报 | `weather_ff` | 每天3次 | 最高低温、昼夜天气、风向风力、日出日落、湿度气压 |
| 城市表 | `city` | - | 城市编号、城市名 |

**使用方式**：
```bash
# 建表
python -m downloader.main --init-db

# 下载全部
python -m downloader.main

# 只下载某类
python -m downloader.main --type condition
python -m downloader.main --type hourly
python -m downloader.main --type forecast

# 初始化城市数据
python -m downloader.init_city
```

### 3.2 Skill 层 (`app/skills/`)

| Skill | 文件 | 状态 | 说明 |
|-------|------|------|------|
| 实况查询 | `weather.py` | ✅ 真实数据 | 从 `weather_cn` 表查询 |
| 逐时预报 | `weather.py` | ✅ 真实数据 | 从 `weather_hh` 表查询 |
| 逐天预报 | `weather.py` | ✅ 真实数据 | 从 `weather_ff` 表查询 |
| 预警查询 | `alert.py` | ⚠️ Mock | 需对接真实预警接口 |
| 数据源检查 | `data_source.py` | ⚠️ Mock | 需检查 DB 最新数据时间 |
| 链路检查 | `pipeline.py` | ⚠️ Mock | 需检查数据更新延迟 |
| 体感计算 | `feels_like.py` | ✅ 真实公式 | 风寒指数 + 热指数 |
| 知识检索 | `knowledge.py` | ✅ 向量+关键词 | Milvus 向量检索 + 关键词兜底 |
| 通知 | `notification.py` | ⚠️ Mock | 需确认推送渠道 |

### 3.3 知识库

**数据来源**：`weather_feedback_enriched_v3.csv`（194 条）

**字段设计**：
| 字段 | 说明 | 用途 |
|------|------|------|
| `module` | 产品模块（14类） | 结构化过滤 |
| `problem_pattern` | 问题模式（5类） | 分类匹配 |
| `problem_desc` | 问题描述 | 向量检索 + 展示 |
| `root_cause` | 根因分析 | 向量检索 + LLM 参考 |
| `solution` | 解决方案 | 返回给 LLM |
| `tags` | 语义标签 | 向量检索增强 |
| `severity` | 严重程度 | 排序加权 |

**检索方式**：
1. **向量检索**（优先）：BGE-large-zh Embedding + Milvus 余弦相似度
2. **关键词匹配**（兜底）：滑动窗口 + 多字段加权打分

**入库命令**：
```bash
python -m app.skills.milvus_loader
```

### 3.4 Agent 核心 (`app/agent/`)

**分析流程**：
```
用户反馈 → 提取地点/时间 → 全部 Skill 查数据 → LLM 分析 → 返回结果
```

**数据收集**：
1. 查实况 → `weather_cn` 表
2. 查逐时 → `weather_hh` 表（最近6小时给LLM）
3. 查逐天 → `weather_ff` 表（最近3天给LLM）
4. 查预警 → alert（目前Mock）
5. 算体感 → `feels_like.py`（真实公式）
6. 搜知识 → `knowledge.py`（向量检索）
7. 调LLM → 生成分析报告

**返回结果**（精简版）：
```json
{
    "analysis_id": "A20260715...",
    "feedback_type": "问题类型",
    "root_cause": "根因分析",
    "actual_data": { 实况数据 },
    "feels_like": { 体感温度 },
    "meteorological_explanation": "气象解释",
    "suggestion": "改进建议",
    "reply_content": "回复用户内容"
}
```

### 3.5 API 接口 (`app/api/`)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/agent/analyze` | POST | 分析单条负反馈 |
| `/api/v1/agent/batch-analyze` | POST | 批量分析（待实现） |
| `/api/v1/agent/analysis/{id}` | GET | 查询分析结果（待实现） |
| `/health` | GET | 健康检查 |

---

## 四、配置说明

### 4.1 环境变量（`.env.example`）

```bash
# 数据库
DB_HOST=localhost
DB_PORT=3307
DB_USER=root
DB_PASSWORD=123456
DB_NAME=weather

# 北京局数据源
BJ_API_KEY=your_key

# 豆包大模型 (Ark)
ARK_API_KEY=your_key
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL_ENDPOINT=doubao-seed-character-260628
```

### 4.2 数据库

- MySQL 8.0 Docker 容器（`crm-mysql`，端口 3307）
- 4 张表：`city`、`weather_cn`、`weather_hh`、`weather_ff`

### 4.3 Milvus

- Milvus Lite（本地文件存储，不需要 Docker）
- 数据文件：`milvus_weather.db`
- Collection：`weather_feedback`
- Embedding 模型：`models/bge-large-zh-v1.5/`

---

## 五、测试脚本

```bash
# 测试气象数据查询
python tests/test_weather.py

# 测试知识库检索
python tests/test_knowledge.py

# 测试 Agent 完整分析流程
python tests/test_agent.py
```

---

## 六、待开发功能

### P1 优先

| 功能 | 说明 |
|------|------|
| 预警查询 | 对接真实预警接口 |
| 数据源检查 | 检查 DB 最新数据时间，判断是否正常更新 |
| 链路检查 | 检查各环节数据延迟 |
| 分析结果持久化 | 结果存 MySQL，支持查询历史 |
| 批量分析 | 异步队列处理大量反馈 |

### P2 后续

| 功能 | 说明 |
|------|------|
| 自动派单 | 按问题类型派给对应团队 |
| 问题预警 | 监控负反馈趋势，提前预警 |
| 通知推送 | 对接推送服务 |
| 部署 | Docker 打包上线 |

---

## 七、项目结构

```
WeatherAgent/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── api/v1/
│   │   ├── router.py        # 路由汇总
│   │   └── endpoints/
│   │       └── analyze.py   # 分析接口
│   ├── agent/
│   │   ├── core.py          # Agent 主逻辑
│   │   ├── prompts.py       # Prompt 模板
│   │   └── tools.py         # Function Calling 定义
│   ├── skills/
│   │   ├── weather.py       # 气象数据查询
│   │   ├── alert.py         # 预警查询
│   │   ├── data_source.py   # 数据源检查
│   │   ├── pipeline.py      # 链路检查
│   │   ├── feels_like.py    # 体感计算
│   │   ├── knowledge.py     # 知识检索
│   │   ├── notification.py  # 通知
│   │   ├── db.py            # 数据库连接
│   │   └── milvus_loader.py # Milvus 入库脚本
│   ├── models/
│   │   ├── schemas.py       # Pydantic 模型
│   │   └── database.py      # SQLAlchemy 模型
│   └── services/
│       └── llm.py           # LLM 调用封装
├── downloader/
│   ├── main.py              # 数据下载入口
│   ├── models.py            # 数据库模型
│   ├── fetcher.py           # API 抓取 + 解析
│   └── init_city.py         # 城市数据初始化
├── tests/
│   ├── test_weather.py      # 气象数据测试
│   ├── test_knowledge.py    # 知识库测试
│   └── test_agent.py        # Agent 测试
├── models/
│   └── bge-large-zh-v1.5/   # Embedding 模型
├── docs/
│   ├── development-progress.md  # 本文档
│   └── session-log-2026-07-14.md
├── weather_feedback_enriched_v3.csv  # 知识库数据
├── milvus_weather.db        # Milvus 数据文件
├── docker-compose.yml       # Milvus Docker 配置（备用）
├── main.py                  # 启动脚本
├── requirements.txt
├── .env.example
└── README.md
```

---

## 八、启动方式

```bash
# 1. 激活环境
conda activate py311

# 2. 启动服务
python main.py

# 3. 访问 API 文档
http://localhost:8000/docs
```

---

## 九、关键决策记录

| 决策 | 原因 |
|------|------|
| 用 Milvus Lite 而非 Docker | 194 条数据，本地文件够用 |
| 用 BGE-large-zh-v1.5 | 中文语义向量效果好 |
| 全部 Skill 查数据再给 LLM | 简单直接，171 条规模不需要 Router |
| CSV tags 细化 | 原 "气象知识" 太模糊，拆成体感温度/气象原理/天气系统等 |
| severity 清洗 | 原数据有脏数据（跨部门、数据源等），只保留 high/medium/low |
