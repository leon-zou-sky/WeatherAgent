"""
生活指数生产脚本
读取天气数据 → 计算指数 → 写入 live_index 表
用法: python -m downloader.index_producer
"""

import os
import json
import logging
from datetime import datetime, date
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

from downloader.models import get_engine, get_session
from app.skills.index_engine import IndexEngine, WeatherInput

load_dotenv(Path(__file__).resolve().parent.parent / ".env.example")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_db_url():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3307")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    db = os.getenv("DB_NAME", "weather")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"


def get_weather_data(session, city_id: str, target_date: str) -> dict | None:
    """获取城市天气数据（从 weather_ff 逐天预报）"""
    row = session.execute(text("""
        SELECT city_id, temp_high, temp_low, humidity_day,
               weather_day, wind_level_day
        FROM weather_ff
        WHERE city_id = :cid
          AND predict_date LIKE :date
        ORDER BY created_at DESC
        LIMIT 1
    """), {"cid": city_id, "date": f"{target_date}%"}).fetchone()

    if not row:
        return None

    # 风力等级转数字
    wind_level = 0
    if row[5]:
        try:
            wind_level = int(str(row[5]).replace("<", "").replace(">", ""))
        except:
            wind_level = 0

    return {
        "city": row[0],
        "date": target_date,
        "temp_high": float(row[1]) if row[1] else 25.0,
        "temp_low": float(row[2]) if row[2] else 15.0,
        "humidity": float(row[3]) if row[3] else 50.0,
        "wind_speed": wind_level * 1.5,  # 近似风速
        "wind_level": wind_level,
        "condition": str(row[4]) if row[4] else "晴",
        "aqi": 50,  # 默认值，后续可接入 AQI 数据
        "uvi": 3,   # 默认值，后续可接入 UVI 数据
        "latitude": 39.9,  # 默认北京纬度
        "month": datetime.strptime(target_date, "%Y-%m-%d").month,
    }


def get_all_cities(session) -> list[dict]:
    """获取所有城市"""
    rows = session.execute(text("""
        SELECT city_id, city_name FROM city
    """)).fetchall()
    return [{"city_id": r[0], "city_name": r[1]} for r in rows]


def save_indices(session, city_id: str, city_name: str, target_date: str, indices: dict, calc_input: dict):
    """保存指数到数据库"""
    # 先删除旧数据
    session.execute(text("""
        DELETE FROM live_index
        WHERE city_id = :cid AND index_date = :date
    """), {"cid": city_id, "date": target_date})

    # 插入新数据
    for index_type, result in indices.items():
        session.execute(text("""
            INSERT INTO live_index
            (city_id, city_name, index_date, index_type, level, score, tip, risk_factors, calc_input, created_at)
            VALUES (:city_id, :city_name, :index_date, :index_type, :level, :score, :tip, :risk_factors, :calc_input, NOW())
        """), {
            "city_id": city_id,
            "city_name": city_name,
            "index_date": target_date,
            "index_type": index_type,
            "level": result.level,
            "score": result.score,
            "tip": result.tip,
            "risk_factors": json.dumps(result.risk_factors, ensure_ascii=False),
            "calc_input": json.dumps(calc_input, ensure_ascii=False),
        })


def produce_indices(target_date: str = None, city_ids: list[str] = None):
    """
    生产指数

    Args:
        target_date: 目标日期，默认今天
        city_ids: 指定城市列表，默认全部
    """
    if target_date is None:
        target_date = date.today().strftime("%Y-%m-%d")

    engine = get_engine(url=get_db_url())
    session = get_session(engine)
    index_engine = IndexEngine()

    try:
        # 获取城市列表
        if city_ids:
            cities = [{"city_id": cid, "city_name": ""} for cid in city_ids]
        else:
            cities = get_all_cities(session)

        logger.info(f"开始生产指数: 日期={target_date}, 城市数={len(cities)}")

        success_count = 0
        fail_count = 0

        for i, city in enumerate(cities):
            city_id = city["city_id"]
            city_name = city["city_name"]

            try:
                # 获取天气数据
                weather_data = get_weather_data(session, city_id, target_date)
                if not weather_data:
                    logger.warning(f"无天气数据: {city_id} {city_name}")
                    fail_count += 1
                    continue

                # 计算指数
                w = WeatherInput(**weather_data)
                indices = index_engine.calc_all(w)

                # 保存
                save_indices(session, city_id, city_name, target_date, indices, weather_data)
                success_count += 1

                if (i + 1) % 500 == 0:
                    session.commit()
                    logger.info(f"进度: {i+1}/{len(cities)}")

            except Exception as e:
                logger.error(f"处理失败: {city_id} {city_name}, error: {e}")
                fail_count += 1

        session.commit()
        logger.info(f"指数生产完成: 成功={success_count}, 失败={fail_count}")

    except Exception as e:
        session.rollback()
        logger.error(f"指数生产失败: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="生活指数生产脚本")
    parser.add_argument("--date", type=str, default=None, help="目标日期 (YYYY-MM-DD)")
    parser.add_argument("--cities", type=str, nargs="+", default=None, help="指定城市ID")
    args = parser.parse_args()

    produce_indices(target_date=args.date, city_ids=args.cities)
