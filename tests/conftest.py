"""
Pytest 配置文件
提供通用的 fixtures 和测试配置
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 设置测试环境变量
os.environ["APP_ENV"] = "testing"
os.environ["DB_HOST"] = os.getenv("TEST_DB_HOST", "127.0.0.1")
os.environ["DB_PORT"] = os.getenv("TEST_DB_PORT", "3306")
os.environ["DB_NAME"] = os.getenv("TEST_DB_NAME", "weather_test")
os.environ["DB_USER"] = os.getenv("TEST_DB_USER", "root")
os.environ["DB_PASSWORD"] = os.getenv("TEST_DB_PASSWORD", "123456")


# ============ Event Loop 配置 ============


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============ 数据库 Fixtures ============


@pytest.fixture(scope="session")
def db_engine():
    """数据库引擎（测试会话级别）"""
    from downloader.models import get_engine

    engine = get_engine()
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """数据库会话（每个测试函数级别）"""
    from downloader.models import get_session

    session = get_session(db_engine)
    yield session
    session.rollback()
    session.close()


# ============ Mock Fixtures ============


@pytest.fixture
def mock_llm_response():
    """模拟LLM响应"""
    mock = AsyncMock()
    mock.return_value = MagicMock(
        content="这是一个模拟的LLM响应", usage=MagicMock(total_tokens=100)
    )
    return mock


@pytest.fixture
def mock_weather_api_response():
    """模拟气象API响应"""
    return {
        "code": 0,
        "data": [
            {
                "cityId": "101010100",
                "cityName": "北京",
                "temp": 25.0,
                "humidity": 60,
                "speed": 3.5,
                "degrees": 180,
                "weather": "01",
                "lastUpdate": "2024-01-15 10:00:00",
            }
        ],
    }


@pytest.fixture
def mock_aqi_api_response():
    """模拟AQI API响应"""
    return {
        "saved_places": [
            {
                "place": {
                    "place_id": "ec8399ca",
                    "type": "city",
                    "name": "北京",
                    "city_name": "北京",
                },
                "latest": {
                    "update_time": "2024-01-15 10:00:00",
                    "readings": [
                        {"kind": "aqi", "value": "75"},
                        {"kind": "pm25", "value": "55"},
                        {"kind": "pm10", "value": "85"},
                        {"kind": "so2", "value": "12"},
                        {"kind": "no2", "value": "45"},
                        {"kind": "o3", "value": "65"},
                        {"kind": "co", "value": "0.8"},
                    ],
                },
            }
        ]
    }


# ============ 测试数据 Fixtures ============


@pytest.fixture
def sample_feedback_request():
    """示例反馈请求"""
    from app.models.schemas import FeedbackRequest

    return FeedbackRequest(
        feedback_id="TEST001",
        content="北京温度不准，显示25度，实际30度",
        location="北京",
        time="2024-01-15",
    )


@pytest.fixture
def sample_weather_data():
    """示例气象数据"""
    return {
        "city_id": "101010100",
        "city_name": "北京",
        "temp": 25.0,
        "humidity": 60,
        "wspd": 3.5,
        "wdir": "南风",
        "weather_zh": "晴",
        "update_time": "2024-01-15 10:00:00",
    }


@pytest.fixture
def sample_aqi_data():
    """示例AQI数据"""
    return {
        "city_id": "101010100",
        "city_name": "北京",
        "aqi": 75,
        "pm25": 55.0,
        "pm10": 85.0,
        "so2": 12.0,
        "no2": 45.0,
        "o3": 65.0,
        "co": 0.8,
        "update_time": "2024-01-15 10:00:00",
    }


# ============ 辅助函数 ============


@pytest.fixture
def assert_dict_contains():
    """断言字典包含指定键值对"""

    def _assert(actual: dict, expected: dict):
        for key, value in expected.items():
            assert key in actual, f"缺少键: {key}"
            assert actual[key] == value, f"键 {key} 的值不匹配: {actual[key]} != {value}"

    return _assert


@pytest.fixture
def assert_datetime_format():
    """断言日期时间格式"""

    def _assert(dt_str: str, format: str = "%Y-%m-%d %H:%M:%S"):
        try:
            datetime.strptime(dt_str, format)
            return True
        except ValueError:
            pytest.fail(f"日期时间格式不正确: {dt_str}，期望格式: {format}")

    return _assert
