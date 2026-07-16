# 开发会话记录 - 2026-07-16

## 会话目标

继续开发，接入真实数据源，构建 RAG 知识库，完善生产级功能。

---

## 1. 气象数据下载器

### 1.1 下载脚本

创建 `downloader/` 模块，从北京局 v2 接口下载数据：

| 脚本 | 数据类型 | 更新频率 |
|------|---------|---------|
| `fetcher.py` | 实况/逐时/逐天 | 10分钟/1小时/1天 |
| `alert.py` | 预警数据 | 实时 |
| `init_city.py` | 城市数据 | 一次性 |

### 1.2 数据库表

| 表名 | 说明 | 字段数 |
|------|------|--------|
| `city` | 城市表 | 城市编号、城市名 |
| `weather_cn` | 实况数据 | 温度、体感、湿度、风速风向、能见度、气压、降水 |
| `weather_hh` | 逐时预报 | 温度、风向风速、湿度、天气、降水概率、降雪、气压 |
| `weather_ff` | 逐天预报 | 最高低温、昼夜天气、风向风力、日出日落、湿度气压 |
| `alert_data` | 预警数据 | 预警类型、级别、标题、内容、生效时间 |

### 1.3 遇到的问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `predict_date` 字段太短 | datetime 格式 19 字符，字段定义 16 | 改为 VARCHAR(32) |
| `content` 字段太长 | 预警内容超过 1024 字符 | 改为 TEXT 类型 |
| zsh 方括号报错 | `pip install pymilvus[milvus_lite]` 方括号是特殊字符 | 加引号 `pip install 'pymilvus[milvus_lite]'` |

---

## 2. Skill 改造（Mock → 真实数据）

### 2.1 完成情况

| Skill | 文件 | 数据源 | 状态 |
|-------|------|--------|------|
| 实况查询 | `weather.py` | MySQL weather_cn | ✅ |
| 逐时预报 | `weather.py` | MySQL weather_hh | ✅ |
| 逐天预报 | `weather.py` | MySQL weather_ff | ✅ |
| 预警查询 | `alert.py` | MySQL alert_data | ✅ |
| 数据源检查 | `data_source.py` | 检查数据量/质量 | ✅ |
| 链路检查 | `pipeline.py` | 检查各表新鲜度 | ✅ |
| 体感计算 | `feels_like.py` | 真实公式 | ✅ |
| 知识检索 | `knowledge.py` | Milvus 向量 + 关键词 | ✅ |

### 2.2 数据库连接工具

创建 `app/skills/db.py`，提供同步数据库 session：

```python
from app.skills.db import get_session
session = get_session()
# 查询...
session.close()
```

---

## 3. RAG 知识库建设

### 3.1 数据准备

- 原始数据：`weather_feedback_enriched_v2.csv`（184 条）
- 清洗后：`weather_feedback_enriched_v3.csv`（194 条）

### 3.2 数据清洗

| 字段 | 问题 | 处理 |
|------|------|------|
| `severity` | 脏数据（跨部门、数据源等混入） | 只保留 high/medium/low |
| `tags` | 粒度不统一（"气象知识"太模糊） | 细化为体感温度/气象原理/天气系统等 |
| 新增 | 用户表达方式单一 | 增加 10 条示例反馈 |

### 3.3 向量检索方案

| 组件 | 选型 | 说明 |
|------|------|------|
| Embedding 模型 | BGE-large-zh-v1.5 | 智源研究院中文模型，1024 维 |
| 向量数据库 | Milvus Lite | 本地文件存储，开发用 |
| 检索策略 | 向量优先 + 关键词兜底 | 双层检索保证可用性 |

### 3.4 评估结果

```
测试用例: 15 个
Top-1 命中率: 93.3% (14/15)
Top-3 命中率: 93.3% (14/15)
Badcase: 1 个（"又淋雨了"匹配到"短临降水"而非"实况"，也合理）
```

### 3.5 遇到的问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `Numpy is not available` | numpy 2.x 和 torch 2.2 不兼容 | 降级 `pip install 'numpy<2'` |
| `dim 768, got 1024` | Embedding 维度设置错误 | 改为 1024 |
| `Collection is in released state` | Milvus 查询前需要 load | 加 `client.load_collection()` |
| `DataDirLockedError` | Milvus Lite 文件锁 | 删锁文件或重启进程 |
| `GOAWAY too_many_pings` | gRPC 连接过于频繁 | 重启服务 |

---

## 4. Agent 流程完善

### 4.1 分析流程

```
用户反馈 → 提取地点/时间 → 全部 Skill 查数据 → LLM 分析 → 返回结果
```

### 4.2 数据收集

1. 查实况 → weather_cn 表
2. 查逐时 → weather_hh 表（最近 6 小时给 LLM）
3. 查逐天 → weather_ff 表（最近 3 天给 LLM）
4. 查预警 → alert_data 表
5. 算体感 → feels_like.py（真实公式）
6. 搜知识 → knowledge.py（向量检索）
7. 调 LLM → 生成分析报告

### 4.3 信息分层设计

在 Prompt 中约束：
- **内部信息**（不告诉用户）：链路检查、数据源状态、技术细节
- **用户回复**（只包含）：实际数据、体感分析、气象解释、可操作建议

### 4.4 预警数据集成

- 查询预警：从 alert_data 表查当前生效预警
- 传给 LLM：拼入提示词的"## 预警信息"部分
- 返回结果：AnalysisResult.alert_data 字段
- 存入数据库：alert_type, alert_level, alert_time 字段

---

## 5. 生产级功能

### 5.1 分析结果持久化

创建 `analysis_result` 表，存储分析结果：

| 字段 | 说明 |
|------|------|
| analysis_id | 分析ID |
| feedback_id | 反馈ID |
| feedback_content | 反馈内容 |
| location | 位置 |
| feedback_type | 问题类型 |
| root_cause | 根因（内部） |
| reply_content | 回复内容（给用户） |
| actual_temp/humidity/wind_speed | 实况数据快照 |
| feels_like | 体感温度 |
| alert_type/level/time | 预警信息 |
| status | 状态（pending/approved/rejected/sent） |
| reviewer/review_time/review_comment | 审核信息 |

### 5.2 批量分析

- 异步处理：FastAPI BackgroundTasks
- 进度追踪：batch_id 查询进度
- 结果获取：批量结果详情
- 自动入库：每条分析完自动保存

### 5.3 审核流程

```
用户反馈 → Agent 分析 → 结果存库(status=pending)
                            ↓
                    运营人员审核
                     ↓           ↓
                  approved    rejected
                     ↓
                  发送给用户(status=sent)
```

### 5.4 问题预警

| 接口 | 说明 |
|------|------|
| `/api/v1/monitor/overview` | 监控概览（反馈量、类型分布、异常告警） |
| `/api/v1/monitor/trend` | 反馈趋势（按天统计） |
| `/api/v1/monitor/hot-issues` | 热点问题（高频类型/地区/问题） |

异常检测：
- 反馈量突增（>100 条/天）
- 某类问题占比过高（>50%）
- 某地区反馈集中（>20 条）
- 高严重度占比过高（>30%）

---

## 6. API 接口汇总

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/agent/analyze` | POST | 分析单条负反馈 |
| `/api/v1/agent/batch-analyze` | POST | 批量分析（异步） |
| `/api/v1/agent/batch/{batch_id}` | GET | 查询批量进度 |
| `/api/v1/agent/batch/{batch_id}/results` | GET | 获取批量结果 |
| `/api/v1/analysis/list` | GET | 查询历史列表 |
| `/api/v1/analysis/{id}` | GET | 查询详情 |
| `/api/v1/analysis/review` | POST | 审核（通过/驳回） |
| `/api/v1/analysis/{id}/send` | POST | 发送回复 |
| `/api/v1/analysis/stats/summary` | GET | 统计概览 |
| `/api/v1/monitor/overview` | GET | 监控概览 |
| `/api/v1/monitor/trend` | GET | 反馈趋势 |
| `/api/v1/monitor/hot-issues` | GET | 热点问题 |
| `/health` | GET | 健康检查 |

---

## 7. 测试脚本

| 脚本 | 测试内容 |
|------|---------|
| `tests/test_weather.py` | 气象数据查询 |
| `tests/test_knowledge.py` | 知识库检索 |
| `tests/test_pipeline.py` | 数据源 + 链路检查 |
| `tests/test_agent.py` | Agent 完整流程 |
| `tests/test_batch.py` | 批量分析 |
| `tests/test_monitor.py` | 监控报告 |
| `tests/eval_rag.py` | RAG 检索质量评估 |

---

## 8. 文档整理

| 文档 | 内容 |
|------|------|
| `docs/development-progress.md` | 开发进度总览 |
| `docs/interview-guide.md` | 面试指南（20 道题） |
| `docs/resume-project.md` | 简历项目描述（4 个版本） |
| `docs/session-log-2026-07-14.md` | 第一天会话记录 |
| `docs/session-log-2026-07-16.md` | 本文档 |

---

## 9. 面试文档

### 9.1 高含金量面试题

| # | 问题 | 考察点 |
|---|------|--------|
| 1 | 怎么测试 RAG 检索效果？ | 评估方法论、Badcase 分析 |
| 2 | 怎么防止 LLM 幻觉？ | Prompt 工程、数据校验 |
| 3 | 怎么保证实时性？ | 数据更新、缓存策略 |
| 4 | 检索知识和实时数据矛盾怎么办？ | 数据优先级、LLM 综合判断 |
| 5 | 核心技术难点是什么？ | 问题分析、解决方案 |
| 6 | 重新设计会怎么改进？ | 技术视野、优化思路 |
| 7 | 检索不到结果怎么办？ | 降级方案、兜底策略 |
| 8 | 系统延迟多少？怎么优化？ | 性能分析、优化方向 |
| 9 | 怎么评估 RAG 系统好坏？ | 评估指标体系 |
| 10 | 项目最大收获是什么？ | 思考深度、成长总结 |
| 11 | LLM 调用超时怎么办？ | 超时配置、重试、异步 |
| 12 | LLM 返回结果不稳定怎么办？ | 格式约束、校验、temperature |
| 13 | 怎么控制 LLM 调用成本？ | 精简 Prompt、缓存、模型分级 |
| 14 | 实际开发遇到哪些困难？ | 环境配置、数据质量、工程化 |
| 15 | 怎么监控 Token 使用量？ | 实时监控、统计分析 |
| 16 | 如何减少 Token 使用量？ | Prompt 精简、数据摘要 |
| 17 | 怎么处理 Token 超限？ | 截断策略、摘要策略 |
| 18 | 怎么评估 Prompt 的 Token 效率？ | 信息密度、A/B 测试 |
| 19 | 怎么处理 LLM 幻觉？ | 数据锚定、事实核查 |
| 20 | 向量数据库锁问题 + 并发性能？ | Milvus Lite vs Standalone |

---

## 10. Docker 部署（进行中）

### 10.1 文件

| 文件 | 说明 |
|------|------|
| `Dockerfile` | 应用镜像构建 |
| `docker-compose-app.yml` | 应用服务编排 |
| `.dockerignore` | 排除不需要的文件 |

### 10.2 遇到的问题

| 问题 | 原因 | 状态 |
|------|------|------|
| 镜像拉取超时 | Docker Hub 网络问题 | 待解决 |
| 阿里云镜像不存在 | 镜像地址错误 | 已回退 |
| 缓存损坏 | Docker 缓存问题 | 待清理 |

---

## 11. 简历优化

### 11.1 自我评价补充

新增 AI Agent 相关描述：
- RAG 系统从 0 到 1 建设经验
- 检索 Top-1 命中率 93.3%
- 单次分析成本优化 80%

### 11.2 工作经历补充

```
2021.8--至今  墨迹天气  高级Python工程师 / 数据中台负责人

职责：
1. 负责气象与环境数据中台架构设计与团队管理（5人）
2. 主导数据同步服务、数据质量监控、数据分析评估
3. 负责 AI Agent 系统从0到1建设，排查效率提升24倍
4. 推动向量知识库建设，检索命中率93.3%，成本优化80%
```

### 11.3 求职意向

```
求职意向: Python 高级开发工程师（AI Agent 方向）
```

---

## 12. 关键决策记录

| 决策 | 原因 |
|------|------|
| 用 Milvus Lite 而非 Docker | 194 条数据，本地文件够用 |
| 用 BGE-large-zh-v1.5 | 中文优化、开源免费、1024 维精度高 |
| 全部 Skill 查数据再给 LLM | 简单直接，不需要 Router |
| CSV tags 细化 | 原 "气象知识" 太模糊 |
| severity 清洗 | 原数据有脏数据 |
| 预警信息强制回复 | Prompt 约束 LLM 必须提预警 |
| .env.example 不提交 | 包含真实密码和 Key |
