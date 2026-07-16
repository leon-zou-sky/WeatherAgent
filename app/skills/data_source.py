"""
Skill 1: 数据源检查
检查城市数据是否存在、数据质量是否正常
"""

from sqlalchemy import text

from app.models.schemas import DataSourceResult
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


async def check_data_source(
    location: str, time: str = "", data_type: str = "all"
) -> DataSourceResult:
    """
    检查数据源状态

    Args:
        location: 城市名或城市编号
        time: 时间（兼容接口）
        data_type: 数据类型（兼容接口）

    Returns:
        DataSourceResult: 数据源检查结果
    """
    city_id = _resolve_city_id(location)
    if not city_id:
        return DataSourceResult(
            status="异常",
            detail=f"未找到城市: {location}",
            coverage=False,
        )

    session = get_session()
    try:
        # 检查实况数据是否有最近记录
        row = session.execute(
            text("""
                SELECT COUNT(*) as cnt,
                       MAX(update_time) as latest,
                       SUM(CASE WHEN temp IS NULL THEN 1 ELSE 0 END) as null_temp,
                       SUM(CASE WHEN humidity IS NULL THEN 1 ELSE 0 END) as null_humidity
                FROM weather_cn
                WHERE city_id = :cid
            """),
            {"cid": city_id},
        ).fetchone()

        if not row or row[0] == 0:
            return DataSourceResult(
                status="异常",
                station_id=city_id,
                data_quality="无数据",
                coverage=False,
                detail=f"城市 {location} 无实况数据",
            )

        total = row[0]
        latest = row[1]
        null_temp = row[2] or 0
        null_humidity = row[3] or 0

        # 判断数据质量
        null_rate = (null_temp + null_humidity) / (total * 2) if total > 0 else 0
        if null_rate < 0.01:
            quality = "优"
        elif null_rate < 0.05:
            quality = "良"
        else:
            quality = "差"

        return DataSourceResult(
            status="正常",
            station_id=city_id,
            data_quality=quality,
            coverage=True,
            detail=f"数据量: {total}条, 最新: {latest}, 质量: {quality}",
        )

    finally:
        session.close()
