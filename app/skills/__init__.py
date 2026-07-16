"""
Skills 包：导出所有 Skill 函数供 Agent 调用
"""

from app.skills.data_source import check_data_source
from app.skills.pipeline import check_pipeline
from app.skills.weather import query_weather_data, query_hourly_data, query_forecast_data
from app.skills.alert import query_alert_data
from app.skills.feels_like import calculate_feels_like
from app.skills.knowledge import search_knowledge
from app.skills.notification import send_notification

__all__ = [
    "check_data_source",
    "check_pipeline",
    "query_weather_data",
    "query_hourly_data",
    "query_forecast_data",
    "query_alert_data",
    "calculate_feels_like",
    "search_knowledge",
    "send_notification",
]
