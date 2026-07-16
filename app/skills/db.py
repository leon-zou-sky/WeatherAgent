"""
Skill 层数据库连接工具
同步查询，供各 Skill 使用
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 加载 .env.example
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env.example")

_engine = None
_Session = None


def _get_engine():
    global _engine
    if _engine is None:
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "3307")
        user = os.getenv("DB_USER", "root")
        password = os.getenv("DB_PASSWORD", "")
        db = os.getenv("DB_NAME", "weather")
        url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"
        _engine = create_engine(url, pool_size=5, pool_recycle=3600)
    return _engine


def get_session():
    """获取数据库 session（用完需关闭）"""
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=_get_engine())
    return _Session()
