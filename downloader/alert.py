"""
预警数据下载器
从预警接口下载数据，写入 alert_data 表
用法: python -m downloader.alert
"""

import os
import logging
from pathlib import Path

import httpx
from dotenv import load_dotenv

from downloader.models import get_engine, get_session, create_tables, AlertData

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


def fetch_alerts() -> list[dict]:
    """从预警接口获取数据"""
    api_url = os.getenv("ALERT_API_URL", "")
    api_token = os.getenv("ALERT_API_TOKEN", "")

    if not api_url:
        logger.error("❌ 未配置 ALERT_API_URL")
        return []

    # token 拼接到 URL 末尾
    url = f"{api_url}/{api_token}" if api_token else api_url

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 0:
            logger.error(f"接口返回异常: code={data.get('code')}, msg={data.get('msg')}")
            return []

        alerts = data.get("data", [])
        logger.info(f"获取预警数据: {len(alerts)} 条")
        return alerts

    except Exception as e:
        logger.error(f"请求预警接口失败: {e}")
        return []


def save_to_db(engine, alerts: list[dict]):
    """写入数据库（upsert，alert_id 重复则更新）"""
    if not alerts:
        return

    session = get_session(engine)
    try:
        new_count = 0
        update_count = 0

        for item in alerts:
            alert_id = item.get("id", "")
            if not alert_id:
                continue

            # 查询是否已存在
            existing = session.query(AlertData).filter_by(alert_id=alert_id).first()

            if existing:
                # 更新
                existing.city_id = item.get("cityId", existing.city_id)
                existing.city_name = item.get("cityName", existing.city_name)
                existing.alert_type = item.get("type", existing.alert_type)
                existing.alert_level = item.get("level", existing.alert_level)
                existing.title = item.get("title", existing.title)
                existing.content = item.get("content", existing.content)
                existing.start_time = item.get("startTime", existing.start_time)
                existing.end_time = item.get("endTime", existing.end_time)
                existing.update_time = item.get("update_time", existing.update_time)
                update_count += 1
            else:
                # 新增
                row = AlertData(
                    alert_id=alert_id,
                    city_id=item.get("cityId", ""),
                    city_name=item.get("cityName", ""),
                    alert_type=item.get("type", ""),
                    alert_level=item.get("level", ""),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    start_time=item.get("startTime", ""),
                    end_time=item.get("endTime", ""),
                    update_time=item.get("update_time", ""),
                )
                session.add(row)
                new_count += 1

        session.commit()
        logger.info(f"✅ 写入完成: 新增 {new_count} 条, 更新 {update_count} 条")

    except Exception as e:
        session.rollback()
        logger.error(f"❌ 写入失败: {e}")
    finally:
        session.close()


def main():
    engine = get_engine(url=get_db_url())
    create_tables(engine)

    alerts = fetch_alerts()
    save_to_db(engine, alerts)

    # 验证
    session = get_session(engine)
    count = session.query(AlertData).count()
    logger.info(f"alert_data 表当前共 {count} 条记录")
    session.close()


if __name__ == "__main__":
    main()
