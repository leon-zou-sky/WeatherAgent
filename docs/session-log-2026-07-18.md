# 开发日志 - 2026-07-18

> MCP 服务实现 + RAG 知识库扩充 + Docker 部署

---

## 一、今日完成

### 1.1 MCP Server 实现

**目标**：将 Skills 层能力通过 MCP 协议暴露，客服/运营可通过 Trae/Cursor 直接调用。

**实现内容**：
- 创建 `app/mcp/server.py`，注册 7 个 MCP Tools
- 创建 `mcp_main.py`，stdio 模式启动入口
- 更新 `requirements.txt`，添加 `mcp>=1.0.0`
- 更新 `README.md`，添加 MCP 配置说明

**7 个 MCP Tools**：

| Tool | 角色 | 说明 |
|------|------|------|
| `query_weather` | 客服 | 查询城市实况气象数据 |
| `query_alert` | 客服 | 查询当前生效的气象预警 |
| `get_life_index` | 客服 | 查询生活指数（穿衣/紫外线/中暑等） |
| `search_knowledge` | 客服 | 检索知识库相似案例 |
| `analyze_feedback` | 客服 | 分析负反馈生成报告 |
| `check_pipeline` | 运营 | 检查数据链路健康状态 |
| `get_monitor_overview` | 运营 | 获取反馈监控概览 |

**遇到的问题**：
- FastMCP API 变更：`description` 改为 `instructions`
- MCP 版本兼容：`mcp>=1.0.0` 安装后 API 不同，需适配
- 环境变量传递：Docker 容器需通过 `env_file` 加载 `.env.example`

### 1.2 Docker 部署

**实现内容**：
- 创建 `start_services.py`，同时启动 FastAPI + MCP SSE
- 更新 `Dockerfile`，添加 MCP 依赖和模型
- 更新 `docker-compose-app.yml`，暴露 8000（FastAPI）+ 9000（MCP SSE）端口

**部署架构**：
```
┌─────────────────────────────────────────────────┐
│  服务器（Docker）                                 │
│  ┌──────────────┐    ┌──────────────┐           │
│  │ FastAPI :8000│    │ MCP SSE :9000│           │
│  └──────┬───────┘    └──────┬───────┘           │
│         └───────┬───────────┘                   │
│                 ▼                               │
│         ┌──────────────┐                        │
│         │ Skills 层    │                        │
│         │ MySQL/Milvus │                        │
│         └──────────────┘                        │
└─────────────────────────────────────────────────┘
```

**遇到的问题**：
- Docker I/O 错误：重启 Docker Desktop 解决
- MySQL 镜像拉取慢：配置国内镜像源
- milvus-lite 缺失：Docker 容器需安装 `milvus-lite`
- LLM API Key 未传递：使用 `env_file` 加载 `.env.example`

### 1.3 RAG 知识库扩充

**目标**：从 194 条扩充到 800+ 条，提升检索命中率。

**数据构建方法**：
1. **模板变体生成**：基础模板 + 变量替换（温度/湿度/风速等）
2. **模块均衡扩充**：识别盲区（逐天预报/逐小时预报）定向补充
3. **产品设计问题挖掘**：城市级数据精度、功能缺失等
4. **Badcase 闭环优化**：分析匹配错误 → 补充精确条目
5. **语义聚类**：14 个模块 × 6 种问题模式 = 84 个维度

**扩充结果**：
```
扩充前：194 条
扩充后：840 条（+646 条）

各模块分布：
  实况: 210 条 (25%)
  天气预警: 111 条 (13%)
  逐天预报: 85 条 (10%)
  格点可视化: 79 条 (9%)
  空气质量: 78 条 (9%)
  生活指数: 72 条 (9%)
  逐小时预报: 49 条 (6%)
  App体验: 41 条 (5%)
  其他: 115 条 (14%)
```

**命中率提升**：
| 指标 | 扩充前（194条） | 扩充后（840条） | 提升 |
|------|----------------|----------------|------|
| Top-1 | 62.0% | **90.0%** | +28% |
| Top-3 | 76.0% | **100.0%** | +24% |

### 1.4 文档更新

**更新内容**：
- 设计文档：第六章 RAG 知识库设计（大幅扩充，新增数据构建方法论）
- 面试文档：RAG 技术亮点、项目成果、面试追问
- README.md：技术栈、开发进度、MCP 配置说明

---

## 二、技术要点

### 2.1 RAG 效果决定因素

```
RAG 效果 = 数据质量 × 40%
         + 标签/分类 × 25%
         + Embedding 模型 × 20%
         + 检索策略 × 15%
```

**核心结论**：RAG 的核心不是算法，是数据工程。

### 2.2 数据构建五种方法

| 方法 | 说明 | 效果 |
|------|------|------|
| 模板变体生成 | 基础模板 + 变量替换 | 覆盖不同表述方式 |
| 模块均衡扩充 | 识别盲区定向补充 | 消除检索偏差 |
| 产品设计问题挖掘 | 用户痛点 + 竞品对比 | 覆盖真实场景 |
| Badcase 闭环优化 | 分析错误 → 补充条目 | 修复边界 case |
| 语义聚类 | 模块×模式×标签 | 结构化管理 |

### 2.3 MCP vs HTTP API

| 维度 | HTTP API | MCP |
|------|---------|-----|
| 调用方 | 程序代码 | LLM（Trae/Cursor） |
| 发现机制 | 文档/Swagger | `tools/list` 动态发现 |
| 调用方式 | 手写 HTTP 请求 | LLM 自动选择工具+填参数 |
| 适用场景 | 批量处理、定时任务 | 对话式交互、Agent 协作 |
| 前端开发 | 需要 | **零前端开发** |

---

## 三、待办事项

### P2 优先

| 功能 | 说明 | 状态 |
|------|------|------|
| 混合检索 | 向量 + BM25 双路召回 | ❌ 待实现 |
| Reranker 精排 | 交叉编码器重排序 | ❌ 待实现 |
| 自动派单 | 分析结果自动派给对应团队 | ❌ 待实现 |

### P3 后续

| 功能 | 说明 | 状态 |
|------|------|------|
| Query 改写 | 用户查询优化 | ❌ 待实现 |
| 知识库微调 | 领域数据微调 Embedding | ❌ 待实现 |
| 多轮对话 | 支持上下文对话 | ❌ 待实现 |

---

## 四、文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/mcp/__init__.py` | 新建 | MCP 模块初始化 |
| `app/mcp/server.py` | 新建 | MCP Server 定义，7 个 Tools |
| `mcp_main.py` | 新建 | stdio 模式启动入口 |
| `start_services.py` | 新建 | FastAPI + MCP SSE 双服务启动 |
| `scripts/expand_knowledge_base.py` | 新建 | 知识库扩充脚本 |
| `scripts/import_weather_icon.py` | 新建 | 天气现象数据导入脚本 |
| `tests/test_mcp.py` | 新建 | MCP 功能测试脚本 |
| `requirements.txt` | 修改 | 添加 mcp、milvus-lite 依赖 |
| `Dockerfile` | 修改 | 添加 MCP 依赖和模型 |
| `docker-compose-app.yml` | 修改 | 暴露 9000 端口，env_file 配置 |
| `README.md` | 修改 | 添加 MCP 配置和部署说明 |
| `feedback-analysis-agent-design.md` | 修改 | 第六章 RAG 设计大幅扩充 |
| `docs/resume-project.md` | 修改 | RAG 技术亮点和项目成果更新 |
| `weather_feedback_enriched_v3.csv` | 修改 | 从 194 条扩充到 840 条 |

---

## 五、环境配置

### 数据库

```
MySQL Docker 容器：mysql-crm
端口：3307
密码：123456
```

### MCP 客户端配置

**Trae / Cursor**：
```json
{
  "mcpServers": {
    "weather-agent": {
      "url": "http://localhost:9000/sse"
    }
  }
}
```

**Claude Code**：
```json
{
  "mcpServers": {
    "weather-agent": {
      "command": "/Users/zouxuefei/miniconda3/envs/py311/bin/python",
      "args": ["mcp_main.py"]
    }
  }
}
```

---

## 六、关键决策

| 决策 | 原因 |
|------|------|
| MCP 用 SSE 模式 | 支持远程访问，多客户端共享 |
| 知识库扩充到 840 条 | 覆盖 14 个模块，消除检索盲区 |
| Top-3 命中率 100% | 50 个测试用例全部命中 |
| Docker 双服务 | FastAPI（HTTP）+ MCP SSE 并行 |
| 使用 conda py311 | 统一 Python 环境 |
