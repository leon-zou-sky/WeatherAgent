"""
问题预警监控 API
监控负反馈趋势，提前预警
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import text

from app.skills.db import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitor", tags=["问题预警"])


def _get_stats(hours: int = 24) -> dict:
    """获取统计信息"""
    session = get_session()
    try:
        since = datetime.now() - timedelta(hours=hours)

        # 总数
        total = session.execute(text("""
            SELECT COUNT(*) FROM analysis_result
            WHERE created_at >= :since
        """), {"since": since}).fetchone()[0]

        # 问题类型分布
        type_dist = session.execute(text("""
            SELECT feedback_type, COUNT(*) as cnt
            FROM analysis_result
            WHERE created_at >= :since
            GROUP BY feedback_type
            ORDER BY cnt DESC
        """), {"since": since}).fetchall()

        # 地区分布
        location_dist = session.execute(text("""
            SELECT location, COUNT(*) as cnt
            FROM analysis_result
            WHERE created_at >= :since AND location IS NOT NULL
            GROUP BY location
            ORDER BY cnt DESC
            LIMIT 10
        """), {"since": since}).fetchall()

        # 状态分布
        status_dist = session.execute(text("""
            SELECT status, COUNT(*) as cnt
            FROM analysis_result
            WHERE created_at >= :since
            GROUP BY status
        """), {"since": since}).fetchall()

        return {
            "total": total,
            "type_distribution": {r[0]: r[1] for r in type_dist},
            "location_distribution": {r[0]: r[1] for r in location_dist},
            "status_distribution": {r[0]: r[1] for r in status_dist},
        }
    finally:
        session.close()


def _detect_anomalies(stats: dict) -> list[dict]:
    """检测异常趋势"""
    alerts = []

    # 1. 反馈量突增（与前一天对比）
    # 简化：直接用阈值判断
    if stats["total"] > 100:
        alerts.append({
            "level": "high",
            "type": "volume_spike",
            "message": f"过去24小时反馈量 {stats['total']} 条，超过阈值 100",
        })

    # 2. 某类问题占比过高
    total = stats["total"] or 1
    for feedback_type, count in stats["type_distribution"].items():
        ratio = count / total
        if ratio > 0.5:
            alerts.append({
                "level": "medium",
                "type": "type_concentration",
                "message": f"问题类型 '{feedback_type}' 占比 {ratio:.0%}，超过 50%",
            })

    # 3. 某地区反馈集中
    for location, count in stats["location_distribution"].items():
        if count > 20:
            alerts.append({
                "level": "medium",
                "type": "location_concentration",
                "message": f"地区 '{location}' 反馈 {count} 条，超过阈值 20",
            })

    # 4. 高严重度占比
    high_count = stats["type_distribution"].get("high", 0)
    if high_count / total > 0.3:
        alerts.append({
            "level": "high",
            "type": "severity_alert",
            "message": f"高严重度问题占比 {high_count/total:.0%}，超过 30%",
        })

    return alerts


@router.get("/overview", summary="监控概览")
async def get_overview(hours: int = 24):
    """
    获取监控概览

    - **hours**: 统计时间范围（默认24小时）
    """
    stats = _get_stats(hours)
    alerts = _detect_anomalies(stats)

    return {
        "code": 200,
        "data": {
            "time_range": f"最近 {hours} 小时",
            "stats": stats,
            "alerts": alerts,
            "alert_count": len(alerts),
            "health": "正常" if not alerts else "异常",
        },
    }


@router.get("/trend", summary="反馈趋势")
async def get_trend(days: int = 7):
    """
    获取反馈趋势（按天）

    - **days**: 统计天数（默认7天）
    """
    session = get_session()
    try:
        rows = session.execute(text("""
            SELECT DATE(created_at) as date, COUNT(*) as cnt
            FROM analysis_result
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
            GROUP BY DATE(created_at)
            ORDER BY date
        """), {"days": days}).fetchall()

        trend = [{"date": str(r[0]), "count": r[1]} for r in rows]

        return {
            "code": 200,
            "data": {
                "days": days,
                "trend": trend,
            },
        }
    finally:
        session.close()


@router.get("/hot-issues", summary="热点问题")
async def get_hot_issues(hours: int = 24, limit: int = 10):
    """
    获取热点问题

    - **hours**: 统计时间范围
    - **limit**: 返回数量
    """
    session = get_session()
    try:
        # 高频问题类型
        types = session.execute(text("""
            SELECT feedback_type, COUNT(*) as cnt
            FROM analysis_result
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL :hours HOUR)
            GROUP BY feedback_type
            ORDER BY cnt DESC
            LIMIT :limit
        """), {"hours": hours, "limit": limit}).fetchall()

        # 高频地区
        locations = session.execute(text("""
            SELECT location, COUNT(*) as cnt
            FROM analysis_result
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL :hours HOUR)
              AND location IS NOT NULL
            GROUP BY location
            ORDER BY cnt DESC
            LIMIT :limit
        """), {"hours": hours, "limit": limit}).fetchall()

        # 高频问题描述
        issues = session.execute(text("""
            SELECT feedback_content, feedback_type, location, COUNT(*) as cnt
            FROM analysis_result
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL :hours HOUR)
            GROUP BY feedback_content, feedback_type, location
            ORDER BY cnt DESC
            LIMIT :limit
        """), {"hours": hours, "limit": limit}).fetchall()

        return {
            "code": 200,
            "data": {
                "hot_types": [{"type": r[0], "count": r[1]} for r in types],
                "hot_locations": [{"location": r[0], "count": r[1]} for r in locations],
                "hot_issues": [
                    {
                        "content": r[0][:50] + "..." if r[0] and len(r[0]) > 50 else r[0],
                        "type": r[1],
                        "location": r[2],
                        "count": r[3],
                    }
                    for r in issues
                ],
            },
        }
    finally:
        session.close()
