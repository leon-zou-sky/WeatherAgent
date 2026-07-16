"""
从实况接口提取城市信息，写入 city 表
用法: python -m downloader.init_city
"""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from sqlalchemy.dialects.mysql import insert

from downloader.models import get_engine, get_session, City

load_dotenv(Path(__file__).resolve().parent.parent / ".env.example")


def fetch_cities(api_key: str) -> list[dict]:
    """从实况接口获取城市列表"""
    url = f"http://bjtqyb.com/moji/observev2all/keys/{api_key}"
    resp = httpx.get(url, timeout=30)
    data = resp.json()
    if data.get("code") != 0 or not data.get("data"):
        print("❌ 接口返回异常")
        return []

    cities = []
    for item in data["data"]:
        cities.append({
            "city_id": item["cityId"],
            "city_name": item.get("cityName", ""),
        })
    return cities


def save_cities(engine, cities: list[dict]):
    """写入 city 表，city_id 重复则跳过"""
    session = get_session(engine)
    try:
        stmt = insert(City).values(cities)
        stmt = stmt.on_duplicate_key_update(city_name=stmt.inserted.city_name)
        session.execute(stmt)
        session.commit()
        print(f"✅ 写入/更新 {len(cities)} 个城市")
    except Exception as e:
        session.rollback()
        print(f"❌ 写入失败: {e}")
    finally:
        session.close()


def main():
    api_key = os.getenv("BJ_API_KEY", "")
    if not api_key:
        print("❌ 未配置 BJ_API_KEY")
        return

    db_url = (
        f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD', '')}"
        f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3307')}"
        f"/{os.getenv('DB_NAME', 'weather')}?charset=utf8mb4"
    )
    engine = get_engine(url=db_url)

    print("正在从实况接口获取城市信息...")
    cities = fetch_cities(api_key)
    if cities:
        save_cities(engine, cities)

    # 验证
    session = get_session(engine)
    count = session.query(City).count()
    print(f"city 表当前共 {count} 条记录")
    session.close()


if __name__ == "__main__":
    main()
