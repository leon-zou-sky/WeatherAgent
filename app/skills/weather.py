"""
Skill 3: 气象数据查询
从 MySQL 读取实况、逐时预报、逐天预报数据
"""

from sqlalchemy import text

from app.models.schemas import WeatherData, HourlyData, ForecastData
from app.skills.db import get_session


# ============ 城市名 → city_id 映射 ============

def _resolve_city_id(location: str) -> str | None:
    """城市名转 city_id，如果传入的已是 ID 则直接返回"""
    # 如果传入的像 city_id（纯数字），直接返回
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


# ============ 实况数据 ============

async def query_weather_data(
    location: str, time: str = "", data_type: str = "all"
) -> WeatherData:
    """
    查询实况气象数据

    Args:
        location: 城市名或城市编号
        time: 时间（兼容接口，实况取最新数据）
        data_type: 数据类型（兼容接口）

    Returns:
        WeatherData: 实况数据
    """
    city_id = _resolve_city_id(location)
    if not city_id:
        return WeatherData()

    session = get_session()
    try:
        row = session.execute(
            text("""
                SELECT city_id, temp, real_feel, humidity, wspd, wdir,
                       wind_level, weather_zh, vis, pressure, precip_1h,
                       update_time
                FROM weather_cn
                WHERE city_id = :cid
                ORDER BY get_time DESC
                LIMIT 1
            """),
            {"cid": city_id},
        ).fetchone()

        if not row:
            return WeatherData(city_id=city_id)

        # 查城市名
        city_row = session.execute(
            text("SELECT city_name FROM city WHERE city_id = :cid LIMIT 1"),
            {"cid": city_id},
        ).fetchone()
        city_name = city_row[0] if city_row else None

        return WeatherData(
            city_id=row[0],
            city_name=city_name,
            temperature=float(row[1]) if row[1] else None,
            real_feel=float(row[2]) if row[2] else None,
            humidity=float(row[3]) if row[3] else None,
            wind_speed=float(row[4]) if row[4] else None,
            wind_dir=row[5],
            wind_level=int(row[6]) if row[6] else None,
            weather_zh=row[7],
            visibility=float(row[8]) if row[8] else None,
            pressure=float(row[9]) if row[9] else None,
            precipitation=float(row[10]) if row[10] else None,
            update_time=row[11],
        )
    finally:
        session.close()


# ============ 逐时预报 ============

async def query_hourly_data(
    location: str, hours: int = 24
) -> list[HourlyData]:
    """
    查询逐时预报数据

    Args:
        location: 城市名或城市编号
        hours: 返回小时数（默认24）

    Returns:
        list[HourlyData]: 逐时预报列表
    """
    city_id = _resolve_city_id(location)
    if not city_id:
        return []

    session = get_session()
    try:
        rows = session.execute(
            text("""
                SELECT city_id, predict_date, predict_hour, temp, humidity,
                       wspd, wdir, weather_zh, pop, qpf, pressure, vis
                FROM weather_hh
                WHERE city_id = :cid
                ORDER BY predict_timestamp ASC
                LIMIT :limit
            """),
            {"cid": city_id, "limit": hours},
        ).fetchall()

        return [
            HourlyData(
                city_id=r[0],
                predict_time=f"{r[1]} {r[2]:02d}:00",
                temperature=float(r[3]) if r[3] else None,
                humidity=float(r[4]) if r[4] else None,
                wind_speed=float(r[5]) if r[5] else None,
                wind_dir=r[6],
                weather_zh=r[7],
                pop=float(r[8]) if r[8] else None,
                precipitation=float(r[9]) if r[9] else None,
                pressure=float(r[10]) if r[10] else None,
                visibility=float(r[11]) if r[11] else None,
            )
            for r in rows
        ]
    finally:
        session.close()


# ============ 逐天预报 ============

async def query_forecast_data(
    location: str, days: int = 15
) -> list[ForecastData]:
    """
    查询逐天预报数据

    Args:
        location: 城市名或城市编号
        days: 返回天数（默认15）

    Returns:
        list[ForecastData]: 逐天预报列表
    """
    city_id = _resolve_city_id(location)
    if not city_id:
        return []

    session = get_session()
    try:
        rows = session.execute(
            text("""
                SELECT city_id, predict_date, temp_high, temp_low,
                       weather_day, weather_night,
                       wind_dir_day, wind_level_day, wind_dir_night, wind_level_night,
                       humidity_day, humidity_night,
                       pop_day, pop_night, sunrise, sunset
                FROM weather_ff
                WHERE city_id = :cid
                ORDER BY predict_date ASC
                LIMIT :limit
            """),
            {"cid": city_id, "limit": days},
        ).fetchall()

        return [
            ForecastData(
                city_id=r[0],
                predict_date=r[1],
                temp_high=float(r[2]) if r[2] else None,
                temp_low=float(r[3]) if r[3] else None,
                weather_day=r[4],
                weather_night=r[5],
                wind_dir_day=r[6],
                wind_level_day=r[7],
                wind_dir_night=r[8],
                wind_level_night=r[9],
                humidity_day=float(r[10]) if r[10] else None,
                humidity_night=float(r[11]) if r[11] else None,
                pop_day=float(r[12]) if r[12] else None,
                pop_night=float(r[13]) if r[13] else None,
                sunrise=r[14],
                sunset=r[15],
            )
            for r in rows
        ]
    finally:
        session.close()
