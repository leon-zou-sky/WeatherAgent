# 气象负反馈分析 Agent 设计文档

> 版本：v1.0  
> 作者：XXX  
> 日期：2024-01-15  
> 状态：设计中

---

## 一、项目背景

### 1.1 业务背景

气象数据服务面向亿级用户提供天气预报、预警、空气质量等数据产品。每周收到大量用户负反馈，包括"天气不准"、"没有预警"、"空气质量不准"等问题。

### 1.2 现状痛点

| 痛点 | 描述 | 影响 |
|------|------|------|
| 人工排查耗时 | 每个反馈需要 1-2 小时排查 | 人力成本高 |
| 响应慢 | 用户等待 2-3 天才有回复 | 用户体验差 |
| 链路复杂 | 数据源→采集→处理→存储→发布→用户 | 定位困难 |
| 产品多样 | 温度、风速、降水、预警、AQI 等 | 排查工作量大 |
| 知识流失 | 经验在人脑中，人员离职就丢失 | 培训成本高 |

### 1.3 项目目标

构建智能 Agent 系统，实现负反馈自动分析和链路排查，提升排查效率和用户体验。

**核心价值**：
- 排查时间：2 小时 → 5 分钟
- 人力成本：降低 90%
- 响应速度：提升 100 倍

---

## 二、需求分析

### 2.1 功能需求

| 需求 | 描述 | 优先级 |
|------|------|--------|
| 负反馈自动分析 | 自动分析用户反馈，定位问题原因 | P0 |
| 链路自动排查 | 自动检查整个数据链路，定位问题环节 | P0 |
| 自动回复用户 | 自动生成回复，发送给用户 | P1 |
| 自动派单 | 根据问题类型，自动派单给对应团队 | P1 |
| 问题预警 | 监控负反馈趋势，提前预警 | P2 |
| 知识沉淀 | 自动积累问题库和解决方案 | P2 |

### 2.2 非功能需求

| 需求 | 描述 |
|------|------|
| 性能 | 单次分析 < 5 分钟 |
| 可用性 | 99.9% |
| 扩展性 | 支持新增数据产品 |
| 安全性 | 数据脱敏、权限控制 |

### 2.3 负反馈类型

| 类型 | 描述 | 可能原因 |
|------|------|----------|
| 天气不准 | 温度、风速、降水等数据偏差 | 数据源问题、位置不匹配、体感差异 |
| 没有预警 | 用户未收到预警信息 | 推送失败、用户关闭推送、范围不覆盖 |
| 预警不准 | 预警和实际天气不符 | 预报偏差、天气突变 |
| 空气质量不准 | AQI 数据偏差 | 数据源问题、数据延迟 |

---

## 三、系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              接入层                                      │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │
│   │ 负反馈系统  │    │ 客服系统    │    │ 运营后台    │                │
│   └─────────────┘    └─────────────┘    └─────────────┘                │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                              服务层                                      │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                       Agent 服务                                 │  │
│   │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │  │
│   │   │ 负反馈分析  │    │ 链路排查    │    │ 自动回复    │        │  │
│   │   │   Agent     │    │   Agent     │    │   Agent     │        │  │
│   │   └─────────────┘    └─────────────┘    └─────────────┘        │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                              能力层                                      │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │
│   │ LLM 服务    │    │ RAG 服务    │    │ Skill 服务  │                │
│   │ (豆包大模型)│    │ (向量检索)  │    │ (工具调用)  │                │
│   └─────────────┘    └─────────────┘    └─────────────┘                │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                              数据层                                      │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │
│   │ 气象数据    │    │ 预警数据    │    │ AQI 数据    │                │
│   │ (HBase)     │    │ (MySQL)     │    │ (ClickHouse)│                │
│   └─────────────┘    └─────────────┘    └─────────────┘                │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Agent 架构

```
输入：负反馈数据
   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       规划模块 (Planning)                                │
│   • 解析反馈内容                                                         │
│   • 识别问题类型                                                         │
│   • 决定排查策略                                                         │
└─────────────────────────────────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       Function Calling（调用机制）                       │
│   • LLM 决定调用哪个 Skill                                              │
│   • LLM 生成 Skill 参数                                                 │
└─────────────────────────────────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       Skill 层（工具调用）                               │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│   │ 数据源   │  │ 链路     │  │ 计算     │  │ 知识检索 │              │
│   │ 检查Skill│  │ 检查Skill│  │ 工具Skill│  │ RAG Skill│              │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       生成模块 (Generation)                              │
│   • 汇总检查结果                                                         │
│   • 定位问题环节                                                         │
│   • 生成分析报告                                                         │
│   • 生成回复内容                                                         │
└─────────────────────────────────────────────────────────────────────────┘
   ↓
输出：分析报告 + 回复内容 + 派单建议
```

### 3.3 Skill + Agent 混合架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Agent 层（智能决策）                             │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    LLM（大脑）                                  │  │
│   │   • 理解用户反馈（自然语言理解）                                 │  │
│   │   • 判断问题类型                                                 │  │
│   │   • 决定调用哪些 Skill                                           │  │
│   │   • 组合结果，生成回复                                           │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         Skill 层（固定功能）                             │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│   │ 数据查询 │  │ 链路检查 │  │ 计算工具 │  │ 通知工具 │              │
│   │  Skill   │  │  Skill   │  │  Skill   │  │  Skill   │              │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 四、技术方案

### 4.1 技术选型

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| Agent 框架 | LangChain | 生态成熟、文档完善 |
| LLM | 豆包大模型 | 国内访问快、成本低 |
| RAG | Milvus + Embedding | 向量检索 |
| 后端框架 | FastAPI | 异步支持、性能好 |
| 数据库 | MySQL + Redis | 元数据 + 缓存 |

### 4.2 Skill 设计

#### Skill 1：数据源检查

```python
def check_data_source(location: str, time: str, data_type: str) -> dict:
    """
    检查数据源状态
    
    Args:
        location: 位置（城市/经纬度）
        time: 时间
        data_type: 数据类型（温度/风速/降水等）
    
    Returns:
        {
            "status": "正常/异常",
            "station_id": "气象站ID",
            "data_quality": "数据质量",
            "coverage": "是否覆盖"
        }
    """
    # 查询气象站状态
    # 检查数据质量
    # 返回检查结果
```

#### Skill 2：链路检查

```python
def check_pipeline(location: str, time: str) -> dict:
    """
    检查整个数据链路
    
    Args:
        location: 位置
        time: 时间
    
    Returns:
        {
            "data_source": {"status": "正常", "detail": "..."},
            "collection": {"status": "正常", "detail": "..."},
            "processing": {"status": "正常", "detail": "..."},
            "storage": {"status": "正常", "detail": "..."},
            "publishing": {"status": "正常", "detail": "..."}
        }
    """
    # 检查数据源
    # 检查采集链路（Kafka）
    # 检查处理链路（Flink）
    # 检查存储（HBase）
    # 检查发布（API）
```

#### Skill 3：气象数据查询

```python
def query_weather_data(location: str, time: str, data_type: str) -> dict:
    """
    查询气象数据
    
    Args:
        location: 位置
        time: 时间
        data_type: 数据类型
    
    Returns:
        {
            "temperature": 25.0,
            "humidity": 30.0,
            "wind_speed": 3.0,
            "precipitation": 0.0
        }
    """
    # 查询 HBase / API
    # 返回结构化数据
```

#### Skill 4：预警数据查询

```python
def query_alert_data(location: str, time: str) -> dict:
    """
    查询预警数据
    
    Args:
        location: 位置
        time: 时间
    
    Returns:
        {
            "has_alert": true,
            "alert_type": "暴雨",
            "alert_level": "黄色",
            "alert_time": "2024-01-15 13:30"
        }
    """
    # 查询预警系统
    # 返回预警数据
```

#### Skill 5：体感温度计算

```python
def calculate_feels_like(temperature: float, humidity: float, wind_speed: float) -> dict:
    """
    计算体感温度
    
    Args:
        temperature: 实际温度（℃）
        humidity: 相对湿度（%）
        wind_speed: 风速（m/s）
    
    Returns:
        {
            "feels_like": 25.0,
            "comfort": "温暖",
            "description": "实际温度25℃，体感温度25℃"
        }
    """
    # 计算风寒指数（低温+大风）
    # 计算热指数（高温+高湿）
    # 返回体感温度
```

#### Skill 6：知识检索（RAG）

```python
def search_knowledge(query: str) -> list:
    """
    RAG 检索相似案例和气象知识
    
    Args:
        query: 查询内容
    
    Returns:
        [
            {
                "content": "案例内容",
                "solution": "解决方案",
                "score": 0.95
            }
        ]
    """
    # 向量检索
    # 返回相似案例
```

#### Skill 7：发送通知

```python
def send_notification(user_id: str, content: str) -> bool:
    """
    发送通知给用户
    
    Args:
        user_id: 用户ID
        content: 通知内容
    
    Returns:
        是否发送成功
    """
    # 调用推送服务
    # 返回结果
```

### 4.3 Function Calling 定义

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "check_data_source",
            "description": "检查数据源状态，包括气象站状态、数据质量、覆盖范围",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "位置（城市名或经纬度）"
                    },
                    "time": {
                        "type": "string",
                        "description": "时间（日期或时间范围）"
                    },
                    "data_type": {
                        "type": "string",
                        "description": "数据类型（temperature/wind_speed/precipitation等）"
                    }
                },
                "required": ["location", "time", "data_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_pipeline",
            "description": "检查整个数据链路状态，包括数据源、采集、处理、存储、发布",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "位置"
                    },
                    "time": {
                        "type": "string",
                        "description": "时间"
                    }
                },
                "required": ["location", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_weather_data",
            "description": "查询气象数据，包括温度、湿度、风速、降水等",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "位置"
                    },
                    "time": {
                        "type": "string",
                        "description": "时间"
                    },
                    "data_type": {
                        "type": "string",
                        "description": "数据类型"
                    }
                },
                "required": ["location", "time", "data_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_alert_data",
            "description": "查询预警数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "位置"
                    },
                    "time": {
                        "type": "string",
                        "description": "时间"
                    }
                },
                "required": ["location", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_feels_like",
            "description": "计算体感温度，考虑风寒指数和热指数",
            "parameters": {
                "type": "object",
                "properties": {
                    "temperature": {
                        "type": "number",
                        "description": "实际温度（℃）"
                    },
                    "humidity": {
                        "type": "number",
                        "description": "相对湿度（%）"
                    },
                    "wind_speed": {
                        "type": "number",
                        "description": "风速（m/s）"
                    }
                },
                "required": ["temperature", "humidity", "wind_speed"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "检索相似案例和气象知识",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "查询内容"
                    }
                },
                "required": ["query"]
            }
        }
    }
]
```

### 4.4 Prompt 设计

```python
SYSTEM_PROMPT = """
你是气象数据质量分析专家，负责分析用户反馈的气象数据问题。

## 你的能力：
1. 分析用户反馈，判断问题类型
2. 检查整个数据链路，定位问题环节
3. 计算体感温度，解释用户感受
4. 检索相似案例，参考历史方案
5. 生成分析报告和回复内容

## 排查流程：
1. 理解用户反馈：提取关键信息（位置、时间、问题类型）
2. 查询气象数据：获取实际数据
3. 检查数据链路：定位问题环节
4. 计算体感温度：解释用户感受（如需要）
5. 检索相似案例：参考历史方案
6. 生成报告：输出结构化分析报告

## 气象知识：
- 体感温度 ≠ 实际温度，受阳光、风速、湿度影响
- 风寒指数：低温+大风时，体感温度比实际温度低
- 热指数：高温+高湿时，体感温度比实际温度高
- 露点温度 > 24℃时，感觉闷热

## 输出格式：
{
    "feedback_type": "问题类型",
    "location": "位置",
    "time": "时间",
    "user_claim": "用户声称的情况",
    "actual_data": "实际数据",
    "check_results": "链路检查结果",
    "comparison": "对比分析",
    "root_cause": "问题根因",
    "meteorological_explanation": "气象原理解释",
    "suggestion": "改进建议",
    "reply_content": "回复用户内容"
}
"""
```

---

## 五、接口设计

### 5.1 核心接口

#### 接口 1：分析负反馈

```
POST /api/v1/agent/analyze

请求：
{
    "feedback_id": "FB20240115001",
    "content": "北京温度不准，显示25度，实际30度",
    "time": "2024-01-15",
    "location": "北京",
    "user_id": "U10001",
    "source": "APP"
}

响应：
{
    "code": 200,
    "data": {
        "analysis_id": "A20240115001",
        "feedback_type": "天气不准",
        "problem_location": "用户侧",
        "root_cause": "用户在阳光直射下，体感温度比实际温度高",
        "actual_data": {
            "temperature": 25.0,
            "humidity": 30.0,
            "wind_speed": 3.0,
            "feels_like": 25.0
        },
        "check_results": {
            "data_source": {"status": "正常"},
            "collection": {"status": "正常"},
            "processing": {"status": "正常"},
            "storage": {"status": "正常"},
            "publishing": {"status": "正常"},
            "user_side": {"status": "异常", "detail": "用户位置和气象站不匹配"}
        },
        "meteorological_explanation": "阳光直射时，体感温度可能比实际温度高5-10℃",
        "suggestion": "建议APP增加体感温度显示",
        "reply_content": "您好！经过分析，当天实际温度25℃，体感温度25℃。您感受到的30度可能是阳光直射导致的体感差异。"
    }
}
```

#### 接口 2：批量分析

```
POST /api/v1/agent/batch-analyze

请求：
{
    "feedback_ids": ["FB20240115001", "FB20240115002", ...]
}

响应：
{
    "code": 200,
    "data": {
        "batch_id": "B20240115001",
        "total": 100,
        "completed": 50,
        "results": [...]
    }
}
```

#### 接口 3：获取分析结果

```
GET /api/v1/agent/analysis/{analysis_id}

响应：
{
    "code": 200,
    "data": {
        "analysis_id": "A20240115001",
        "status": "completed",
        "result": {...}
    }
}
```

### 5.2 数据库设计

```sql
-- 分析记录表
CREATE TABLE agent_analysis (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    analysis_id VARCHAR(64) NOT NULL COMMENT '分析ID',
    feedback_id VARCHAR(64) NOT NULL COMMENT '反馈ID',
    feedback_type VARCHAR(32) COMMENT '问题类型',
    location VARCHAR(128) COMMENT '位置',
    time DATETIME COMMENT '时间',
    problem_location VARCHAR(32) COMMENT '问题环节',
    root_cause TEXT COMMENT '问题根因',
    suggestion TEXT COMMENT '改进建议',
    reply_content TEXT COMMENT '回复内容',
    actual_data JSON COMMENT '实际数据',
    check_results JSON COMMENT '检查结果',
    status VARCHAR(16) DEFAULT 'pending' COMMENT '状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_analysis_id (analysis_id),
    INDEX idx_feedback_id (feedback_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) COMMENT '分析记录表';

-- 知识库表
CREATE TABLE agent_knowledge (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    problem_type VARCHAR(32) COMMENT '问题类型',
    problem_desc TEXT COMMENT '问题描述',
    root_cause TEXT COMMENT '问题根因',
    solution TEXT COMMENT '解决方案',
    embedding BLOB COMMENT '向量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_problem_type (problem_type)
) COMMENT '知识库表';
```

---

## 六、落地计划

### 6.1 阶段划分

| 阶段 | 时间 | 内容 | 产出 |
|------|------|------|------|
| 阶段 1 | 1-2 周 | 数据准备、Skill 开发 | Skill 接口 |
| 阶段 2 | 2-3 周 | Agent 开发、Prompt 优化 | Agent 服务 |
| 阶段 3 | 1 周 | 测试、优化 | 测试报告 |
| 阶段 4 | 1 周 | 部署、上线 | 上线服务 |

### 6.2 详细计划

```
第 1 周：数据准备
├── 收集负反馈数据，整理成结构化格式
├── 收集气象、预警、AQI 数据接口
├── 整理历史案例，构建知识库
└── 设计数据库表结构

第 2 周：Skill 开发
├── 开发数据源检查 Skill
├── 开发链路检查 Skill
├── 开发数据查询 Skill
├── 开发计算工具 Skill
└── 测试 Skill 接口

第 3 周：Agent 开发
├── 集成 LangChain
├── 定义 Function Calling
├── 设计 Prompt
├── 实现 Agent 流程
└── 初步测试

第 4 周：优化测试
├── Prompt 优化
├── 性能优化
├── 功能测试
└── 压力测试

第 5 周：部署上线
├── 部署服务
├── 接入反馈系统
├── 监控告警
└── 文档完善
```

---

## 七、风险评估

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| LLM 准确率不够 | 分析结果不准确 | Prompt 优化、人工审核 |
| Skill 接口不稳定 | 排查失败 | 重试机制、降级方案 |
| 数据量大 | 性能问题 | 异步处理、批量分析 |
| 知识库不完善 | 检索效果差 | 持续积累、人工补充 |

---

## 八、预期效果

| 指标 | 现状 | 目标 | 提升 |
|------|------|------|------|
| 排查时间 | 2 小时/个 | 5 分钟/个 | 24 倍 |
| 排查准确率 | 70% | 95% | 35% |
| 响应速度 | 2-3 天 | 5 分钟 | 100 倍 |
| 人力成本 | 100 人天/月 | 10 人天/月 | 10 倍 |

---

## 九、总结

本项目通过构建智能 Agent 系统，实现负反馈自动分析和链路排查，解决人工排查耗时、响应慢、链路复杂等痛点。

**核心架构**：Skill + Agent 混合架构
- Agent 层：负责智能决策（理解反馈、制定计划、生成回复）
- Skill 层：负责固定功能（数据查询、链路检查、计算工具）

**核心价值**：
- 排查时间从 2 小时降到 5 分钟
- 人力成本降低 90%
- 响应速度提升 100 倍
