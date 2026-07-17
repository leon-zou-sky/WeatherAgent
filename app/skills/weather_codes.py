"""
天气现象代码映射
从数据库 weather_icon 表读取
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env.example")

_cache = None


def _get_engine():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3307")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    db = os.getenv("DB_NAME", "weather")
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"
    return create_engine(url)


def _load_mapping() -> dict:
    """从 weather_icon 表加载映射"""
    global _cache
    if _cache is not None:
        return _cache

    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT weather_id, condition_zh FROM weather_icon"
        )).fetchall()
        _cache = {str(r[0]): r[1] for r in rows}
    return _cache


def get_weather_name(code: str) -> str:
    """天气代码转名称"""
    mapping = _load_mapping()
    # 先尝试直接匹配，再尝试去掉前导零匹配
    result = mapping.get(str(code))
    if result:
        return result
    # 去掉前导零： "01" -> "1", "02" -> "2"
    try:
        int_code = str(int(code))
        return mapping.get(int_code, f"未知({code})")
    except ValueError:
        return f"未知({code})"


def get_weather_code(name: str) -> str | None:
    """天气名称转代码"""
    mapping = _load_mapping()
    for code, n in mapping.items():
        if n == name:
            return code
    return None
