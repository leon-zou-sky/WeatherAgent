"""
Function Calling 工具定义
定义 LLM 可调用的 Skill 接口
"""

# Function Calling 工具列表
TOOLS = [
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
                        "description": "位置（城市名或经纬度）",
                    },
                    "time": {
                        "type": "string",
                        "description": "时间（日期或时间范围）",
                    },
                    "data_type": {
                        "type": "string",
                        "description": "数据类型（temperature/wind_speed/precipitation等）",
                    },
                },
                "required": ["location", "time", "data_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_pipeline",
            "description": "检查整个数据链路状态，包括数据源、采集、处理、存储、发布",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "位置"},
                    "time": {"type": "string", "description": "时间"},
                },
                "required": ["location", "time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_weather_data",
            "description": "查询气象数据，包括温度、湿度、风速、降水等",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "位置"},
                    "time": {"type": "string", "description": "时间"},
                    "data_type": {"type": "string", "description": "数据类型"},
                },
                "required": ["location", "time", "data_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_alert_data",
            "description": "查询预警数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "位置"},
                    "time": {"type": "string", "description": "时间"},
                },
                "required": ["location", "time"],
            },
        },
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
                        "description": "实际温度（℃）",
                    },
                    "humidity": {
                        "type": "number",
                        "description": "相对湿度（%）",
                    },
                    "wind_speed": {
                        "type": "number",
                        "description": "风速（m/s）",
                    },
                },
                "required": ["temperature", "humidity", "wind_speed"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "检索相似案例和气象知识",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "查询内容"},
                },
                "required": ["query"],
            },
        },
    },
]

# Skill 函数映射表（将 function name 映射到实际函数）
TOOL_MAP = {}  # 在 Agent 初始化时填充
