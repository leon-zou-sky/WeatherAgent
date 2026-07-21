"""
天气现象映射数据导入
从 weather_icon.xlsx 导入到 weather_icon 表
用法: python -m downloader.init_weather_icon
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv(Path(__file__).resolve().parent.parent / ".env.example")


def get_db_url():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3307")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    db = os.getenv("DB_NAME", "weather")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"


def main():
    xlsx_path = Path(__file__).resolve().parent / "weather_icon.xlsx"
    if not xlsx_path.exists():
        print(f"❌ 文件不存在: {xlsx_path}")
        return

    # 读取 Excel
    df = pd.read_excel(xlsx_path)
    df = df.where(pd.notnull(df), None)
    print(f"读取 Excel: {len(df)} 条")

    # 写入数据库
    engine = create_engine(get_db_url())
    df.to_sql("weather_icon", engine, if_exists="replace", index=False)
    print(f"✅ 写入 weather_icon 表: {len(df)} 条")

    # 验证
    with engine.connect() as conn:
        result = conn.execute(
            __import__("sqlalchemy").text(
                "SELECT DISTINCT weather_id, condition_zh FROM weather_icon ORDER BY weather_id"
            )
        ).fetchall()
        print(f"\n天气映射:")
        for r in result:
            print(f"  {r[0]}: {r[1]}")


if __name__ == "__main__":
    main()
