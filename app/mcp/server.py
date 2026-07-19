"""
WeatherAgent MCP Server
7 个核心工具，服务客服 + 运营两个角色

工具列表：
  客服用：query_weather / query_alert / get_life_index / search_knowledge / analyze_feedback
  运营用：check_pipeline / get_monitor_overview
"""

import json
import logging
from datetime import datetime

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# ============ MCP Server 定义 ============

mcp = FastMCP(
    "WeatherAgent",
    instructions="气象负反馈分析 Agent - 提供天气查询、预警、知识检索、反馈分析、链路检查、监控概览等能力",
)


# ============ 客服用 Tools ============


@mcp.tool()
async def query_weather(location: str, time: str = "") -> dict:
    """查询城市实况气象数据

    查询指定城市的当前天气观测数据，包括温度、体感温度、湿度、风速风向、
    天气现象、能见度、气压、降水量等。

    Args:
        location: 城市名称或城市编号，如"北京"、"海淀"、"101010100"
        time: 查询时间，格式 YYYY-MM-DD，默认当天
    """
    from app.skills.weather import query_weather_data

    logger.info(f"[MCP] query_weather: location={location}, time={time}")
    result = await query_weather_data(location, time)
    return result.model_dump()


@mcp.tool()
async def query_alert(location: str, time: str = "") -> dict:
    """查询城市当前生效的气象预警

    查询指定城市当前正在生效的气象预警信息，包括预警类型（暴雨/高温/大风等）、
    预警级别（蓝/黄/橙/红）、生效时间、预警详情等。

    Args:
        location: 城市名称或城市编号，如"北京"、"海淀"
        time: 查询时间，格式 YYYY-MM-DD，默认当天
    """
    from app.skills.alert import query_alert_data

    logger.info(f"[MCP] query_alert: location={location}, time={time}")
    result = await query_alert_data(location, time)
    return result.model_dump()


@mcp.tool()
async def get_life_index(city: str, date: str = "", index_type: str = "") -> dict:
    """查询城市生活指数数据

    查询指定城市的生活指数，包括穿衣、紫外线、中暑、感冒、运动、舒适度、出行等 7 种指数。
    每种指数包含等级、分数（1-5分，5分最适宜）和建议文案。

    Args:
        city: 城市名称或城市编号，如"北京"、"海淀"
        date: 查询日期，格式 YYYY-MM-DD，默认当天
        index_type: 指数类型，可选值：穿衣/紫外线/中暑/感冒/运动/舒适度/出行，为空则返回全部指数
    """
    from app.agent.index_functions import get_index_data, get_all_indices

    logger.info(f"[MCP] get_life_index: city={city}, date={date}, index_type={index_type}")

    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    if index_type:
        result = get_index_data(city, date, index_type)
    else:
        result = get_all_indices(city, date)

    return result


@mcp.tool()
async def search_knowledge(query: str, top_k: int = 3) -> list[dict]:
    """检索气象知识库，查找相似历史案例和解决方案

    从气象反馈知识库中检索与用户问题相似的历史案例，返回案例描述、
    根因分析和解决方案。支持语义检索（向量）和关键词匹配两种策略。

    Args:
        query: 检索内容，如"温度不准"、"没收到预警"、"体感温度不对"
        top_k: 返回结果数量，默认3条
    """
    from app.skills.knowledge import search_knowledge as _search

    logger.info(f"[MCP] search_knowledge: query={query}, top_k={top_k}")
    results = await _search(query, top_k)
    return [r.model_dump() for r in results]


@mcp.tool()
async def analyze_feedback(
    content: str, location: str = "", time: str = ""
) -> dict:
    """分析气象负反馈，自动判断问题类型并生成分析报告

    自动分析用户反馈内容，判断问题类型（数据偏差/时空误差/时效延迟/认知偏差/体验缺陷），
    收集相关气象数据，计算体感温度，检索知识库，最终生成分析报告和建议回复。

    Args:
        content: 用户反馈内容，如"北京温度不准，显示25度实际30度"
        location: 反馈涉及的城市，如"北京"
        time: 反馈涉及的时间，格式 YYYY-MM-DD，默认当天
    """
    from app.agent.core import get_agent
    from app.models.schemas import FeedbackRequest

    logger.info(f"[MCP] analyze_feedback: content={content[:50]}..., location={location}")

    agent = get_agent()
    req = FeedbackRequest(
        feedback_id=f"MCP{datetime.now().strftime('%Y%m%d%H%M%S')}",
        content=content,
        location=location or "未知",
        time=time or datetime.now().strftime("%Y-%m-%d"),
    )
    result = await agent.smart_analyze(req)
    return result.model_dump()


# ============ 运营用 Tools ============


@mcp.tool()
async def check_pipeline(location: str, time: str = "") -> dict:
    """检查气象数据链路健康状态

    检查指定城市气象数据的全链路状态，包括数据源、采集、处理、存储、发布
    各环节是否正常，检查数据量、最新更新时间、数据质量等。

    Args:
        location: 城市名称或城市编号，如"北京"
        time: 检查时间，格式 YYYY-MM-DD，默认当天
    """
    from app.skills.pipeline import check_pipeline as _check

    logger.info(f"[MCP] check_pipeline: location={location}, time={time}")
    result = await _check(location, time)
    return result.model_dump()


@mcp.tool()
async def get_monitor_overview(hours: int = 24) -> dict:
    """获取负反馈监控概览

    获取最近一段时间的负反馈监控数据，包括反馈总量、问题类型分布、
    地区集中度、状态分布，以及自动检测的异常告警（反馈量突增、
    某类问题占比过高、某地区反馈集中等）。

    Args:
        hours: 统计时间范围（小时），默认24小时
    """
    from app.api.v1.endpoints.alert_monitor import _get_stats, _detect_anomalies

    logger.info(f"[MCP] get_monitor_overview: hours={hours}")
    stats = _get_stats(hours)
    alerts = _detect_anomalies(stats)
    return {
        "time_range": f"最近 {hours} 小时",
        "stats": stats,
        "alerts": alerts,
        "alert_count": len(alerts),
        "health": "正常" if not alerts else "异常",
    }
