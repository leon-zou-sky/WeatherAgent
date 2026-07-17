"""
生活指数 Function Calling 定义 + 执行器
用于分析指数相关反馈
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

from app.skills.index_engine import IndexEngine
from app.skills.db import get_session

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env.example")

# 规则引擎实例
_index_engine = IndexEngine()

# ============ Function 定义 ============

INDEX_FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_index_data",
            "description": "获取指定城市、日期的生活指数数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名或城市编号"
                    },
                    "date": {
                        "type": "string",
                        "description": "日期，格式 YYYY-MM-DD"
                    },
                    "index_type": {
                        "type": "string",
                        "description": "指数类型",
                        "enum": ["穿衣", "紫外线", "中暑", "感冒", "运动", "舒适度", "出行"]
                    }
                },
                "required": ["city", "date", "index_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_index_rules",
            "description": "获取生活指数的计算规则和判断条件",
            "parameters": {
                "type": "object",
                "properties": {
                    "index_type": {
                        "type": "string",
                        "description": "指数类型",
                        "enum": ["穿衣", "紫外线", "中暑", "感冒", "运动", "舒适度", "出行"]
                    }
                },
                "required": ["index_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_for_index",
            "description": "获取计算指数时使用的天气数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名或城市编号"
                    },
                    "date": {
                        "type": "string",
                        "description": "日期，格式 YYYY-MM-DD"
                    }
                },
                "required": ["city", "date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_indices",
            "description": "获取指定城市、日期的所有生活指数",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名或城市编号"
                    },
                    "date": {
                        "type": "string",
                        "description": "日期，格式 YYYY-MM-DD"
                    }
                },
                "required": ["city", "date"]
            }
        }
    }
]


# ============ Function 执行器 ============

def _resolve_city_id(city: str) -> str | None:
    """城市名转 city_id"""
    if city.isdigit():
        return city
    session = get_session()
    try:
        row = session.execute(
            text("SELECT city_id FROM city WHERE city_name = :name LIMIT 1"),
            {"name": city},
        ).fetchone()
        return row[0] if row else None
    finally:
        session.close()


def get_index_data(city: str, date: str, index_type: str) -> dict:
    """获取指定指数数据"""
    city_id = _resolve_city_id(city)
    if not city_id:
        return {"error": f"未找到城市: {city}"}

    session = get_session()
    try:
        row = session.execute(text("""
            SELECT city_id, city_name, index_date, index_type, level, score, tip, risk_factors
            FROM live_index
            WHERE city_id = :cid AND index_date = :date AND index_type = :type
        """), {"cid": city_id, "date": date, "type": index_type}).fetchone()

        if not row:
            return {"error": f"未找到指数数据: {city} {date} {index_type}"}

        return {
            "city_id": row[0],
            "city_name": row[1],
            "date": str(row[2]),
            "index_type": row[3],
            "level": row[4],
            "score": row[5],
            "tip": row[6],
            "risk_factors": json.loads(row[7]) if row[7] else [],
        }
    finally:
        session.close()


def get_index_rules(index_type: str) -> dict:
    """获取指数计算规则"""
    rules = _index_engine.get_rules(index_type)
    if not rules:
        return {"error": f"未找到规则: {index_type}"}
    return rules


def get_weather_for_index(city: str, date: str) -> dict:
    """获取计算指数用的天气数据"""
    city_id = _resolve_city_id(city)
    if not city_id:
        return {"error": f"未找到城市: {city}"}

    session = get_session()
    try:
        # 从 live_index 的 calc_input 获取
        row = session.execute(text("""
            SELECT calc_input
            FROM live_index
            WHERE city_id = :cid AND index_date = :date
            LIMIT 1
        """), {"cid": city_id, "date": date}).fetchone()

        if row and row[0]:
            return json.loads(row[0])

        # 从 weather_ff 获取
        row = session.execute(text("""
            SELECT city_id, temp_high, temp_low, humidity_day, weather_day, wind_level_day
            FROM weather_ff
            WHERE city_id = :cid AND predict_date LIKE :date
            ORDER BY created_at DESC LIMIT 1
        """), {"cid": city_id, "date": f"{date}%"}).fetchone()

        if not row:
            return {"error": f"未找到天气数据: {city} {date}"}

        return {
            "city": row[0],
            "date": date,
            "temp_high": float(row[1]) if row[1] else None,
            "temp_low": float(row[2]) if row[2] else None,
            "humidity": float(row[3]) if row[3] else None,
            "condition": str(row[4]) if row[4] else None,
            "wind_level": int(row[5]) if row[5] else None,
        }
    finally:
        session.close()


def get_all_indices(city: str, date: str) -> dict:
    """获取所有指数"""
    city_id = _resolve_city_id(city)
    if not city_id:
        return {"error": f"未找到城市: {city}"}

    session = get_session()
    try:
        rows = session.execute(text("""
            SELECT index_type, level, score, tip, risk_factors
            FROM live_index
            WHERE city_id = :cid AND index_date = :date
        """), {"cid": city_id, "date": date}).fetchall()

        if not rows:
            return {"error": f"未找到指数数据: {city} {date}"}

        return {
            row[0]: {
                "level": row[1],
                "score": row[2],
                "tip": row[3],
                "risk_factors": json.loads(row[4]) if row[4] else [],
            }
            for row in rows
        }
    finally:
        session.close()


# ============ Function 路由 ============

FUNCTION_MAP = {
    "get_index_data": get_index_data,
    "get_index_rules": get_index_rules,
    "get_weather_for_index": get_weather_for_index,
    "get_all_indices": get_all_indices,
}


async def execute_index_function(func_name: str, func_args: dict) -> dict:
    """执行 Function"""
    func = FUNCTION_MAP.get(func_name)
    if not func:
        return {"error": f"未知函数: {func_name}"}
    return func(**func_args)
