"""
气象数据下载器 - 主入口

用法:
    python -m downloader.main                    # 下载全部三种数据
    python -m downloader.main --type condition   # 只下载实况
    python -m downloader.main --type hourly      # 只下载逐时
    python -m downloader.main --type forecast    # 只下载逐天
    python -m downloader.main --init-db          # 只建表不下载
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from downloader.models import get_engine, create_tables, get_session
from downloader.fetcher import fetch_condition, fetch_hourly, fetch_forecast

# 加载项目根目录的 .env.example
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


def save_to_db(engine, records: list):
    """批量写入数据库"""
    if not records:
        return
    session = get_session(engine)
    try:
        session.add_all(records)
        session.commit()
        logger.info(f"✅ 写入 {len(records)} 条记录")
    except Exception as e:
        session.rollback()
        logger.error(f"❌ 写入失败: {e}")
    finally:
        session.close()


def run_download(engine, api_key: str, data_type: str):
    """执行下载"""
    fetchers = {
        "condition": fetch_condition,
        "hourly": fetch_hourly,
        "forecast": fetch_forecast,
    }

    types = [data_type] if data_type != "all" else list(fetchers.keys())

    for t in types:
        logger.info(f"{'='*40}")
        logger.info(f"开始下载: {t}")
        logger.info(f"{'='*40}")
        # if t!='forecast':
        #     continue
        try:
            records = fetchers[t](api_key)
            save_to_db(engine, records)
        except Exception as e:
            logger.error(f"下载 {t} 失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="北京局气象数据下载器")
    parser.add_argument(
        "--type", choices=["all", "condition", "hourly", "forecast"],
        default="all", help="下载数据类型"
    )
    parser.add_argument("--init-db", action="store_true", help="只建表不下载")
    args = parser.parse_args()

    engine = get_engine(url=get_db_url())

    if args.init_db:
        create_tables(engine)
        return

    api_key = os.getenv("BJ_API_KEY", "")
    if not api_key:
        logger.error("❌ 未配置 BJ_API_KEY，请在 .env 中设置")
        sys.exit(1)

    create_tables(engine)
    run_download(engine, api_key, args.type)
    logger.info("🎉 全部完成")


if __name__ == "__main__":
    main()
