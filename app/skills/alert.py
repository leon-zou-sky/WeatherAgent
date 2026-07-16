"""
Skill 4: 预警数据查询
从 alert_data 表查询预警信息
"""

from sqlalchemy import text

from app.models.schemas import AlertData
from app.skills.db import get_session


def _resolve_city_id(location: str) -> str | None:
    """城市名转 city_id"""
    if location.isdigit():
        return location

    session = get_session()
    try:
        row = session.execute(
            text("SELECT city_id FROM city WHERE city_name = :name LIMIT 1"),
            {"name": location},
        ).fetchone()
        return row[0] if row else None
    finally:
        session.close()


async def query_alert_data(location: str, time: str = "") -> AlertData:
    """
    查询预警数据

    Args:
        location: 城市名或城市编号
        time: 时间（兼容接口，查当前生效的预警）

    Returns:
        AlertData: 预警数据
    """
    city_id = _resolve_city_id(location)
    if not city_id:
        return AlertData(has_alert=False)

    session = get_session()
    try:
        # 查询当前生效的预警（end_time >= 当前时间）
        row = session.execute(
            text("""
                SELECT city_id, city_name, alert_type, alert_level,
                       title, content, start_time, end_time, update_time
                FROM alert_data
                WHERE city_id = :cid
                  AND end_time >= NOW()
                ORDER BY start_time DESC
                LIMIT 1
            """),
            {"cid": city_id},
        ).fetchone()

        if not row:
            return AlertData(has_alert=False)

        return AlertData(
            has_alert=True,
            alert_type=row[2],
            alert_level=row[3],
            alert_time=row[6],
            # 额外信息存到 detail
            detail=f"[{row[4]}] {row[5][:100]}..." if row[5] and len(row[5]) > 100 else f"[{row[4]}] {row[5]}",
        )
    finally:
        session.close()


async def query_alert_list(location: str, limit: int = 5) -> list[dict]:
    """
    查询预警列表（供其他场景使用）

    Args:
        location: 城市名或城市编号
        limit: 返回数量

    Returns:
        list[dict]: 预警列表
    """
    city_id = _resolve_city_id(location)
    if not city_id:
        return []

    session = get_session()
    try:
        rows = session.execute(
            text("""
                SELECT city_id, city_name, alert_type, alert_level,
                       title, content, start_time, end_time, update_time
                FROM alert_data
                WHERE city_id = :cid
                ORDER BY start_time DESC
                LIMIT :limit
            """),
            {"cid": city_id, "limit": limit},
        ).fetchall()

        return [
            {
                "city_id": r[0],
                "city_name": r[1],
                "alert_type": r[2],
                "alert_level": r[3],
                "title": r[4],
                "content": r[5],
                "start_time": r[6],
                "end_time": r[7],
                "update_time": r[8],
            }
            for r in rows
        ]
    finally:
        session.close()
