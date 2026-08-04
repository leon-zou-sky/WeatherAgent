"""
天气现象映射数据导入 v2
从 weatherid.xlsx 导入到 weather_icon_v2 表
字段名去掉大写F前缀，第一列id保持不变

用法: python -m downloader.init_weather_icon_v2
"""

import os
from pathlib import Path

import openpyxl
from dotenv import load_dotenv
from sqlalchemy import text

from downloader.models import WeatherIconV2, create_tables, get_engine, get_session

load_dotenv(Path(__file__).resolve().parent.parent / ".env.example")


def get_db_url():
    """获取数据库连接URL"""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3307")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    db = os.getenv("DB_NAME", "weather")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"


def read_excel_data(file_path: str) -> list:
    """读取Excel数据

    Args:
        file_path: Excel文件路径

    Returns:
        list: 数据列表，每项为字典
    """
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return []

    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active

    # 读取列名（第一行）
    headers = []
    for cell in sheet[1]:
        header = cell.value
        if header:
            # 去掉大写F前缀，但保持id不变
            if header == "Fid":
                headers.append("id")
            elif header.startswith("F"):
                headers.append(header[1:])  # 去掉F前缀
            else:
                headers.append(header)
        else:
            headers.append(None)

    print("列名映射:")
    for _i, (old, new) in enumerate(zip([cell.value for cell in sheet[1]], headers, strict=False)):
        if old and old != new:
            print(f"  {old} -> {new}")

    # 读取数据
    data = []
    for _row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        row_data = {}
        for col_idx, value in enumerate(row):
            if col_idx < len(headers) and headers[col_idx]:
                # 数据清洗
                header = headers[col_idx]
                if value is not None:
                    # 整数列处理
                    if header in [
                        "id",
                        "weather_code",
                        "bg_code",
                        "icon_day",
                        "icon_night",
                        "accu_icon",
                        "smartweather",
                    ]:
                        try:
                            value = int(value) if value else None
                        except (ValueError, TypeError):
                            value = None
                    # 字符串列处理
                    elif isinstance(value, str) and value.strip() == "":
                        value = None
                row_data[header] = value
        data.append(row_data)

    print(f"读取数据: {len(data)} 条")
    return data


def save_to_db(data: list):
    """保存数据到数据库

    Args:
        data: 数据列表
    """
    if not data:
        print("没有数据可保存")
        return

    # 获取数据库连接
    db_url = get_db_url()
    engine = get_engine(url=db_url)

    # 删除旧表（如果存在）
    from sqlalchemy import text

    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS weather_icon_v2"))
        conn.commit()
        print("删除旧的 weather_icon_v2 表")

    # 创建表
    create_tables(engine)

    session = get_session(engine)

    try:
        print("创建新的 weather_icon_v2 表")

        # 批量插入数据
        count = 0
        for row_data in data:
            # 创建记录
            record = WeatherIconV2(**row_data)
            session.add(record)
            count += 1

            # 每100条提交一次
            if count % 100 == 0:
                session.commit()
                print(f"已插入 {count} 条")

        session.commit()
        print(f"✅ 成功插入 {count} 条数据到 weather_icon_v2 表")

    except Exception as e:
        session.rollback()
        print(f"❌ 插入数据失败: {e}")
    finally:
        session.close()


def verify_data():
    """验证数据"""
    db_url = get_db_url()
    engine = get_engine(url=db_url)
    session = get_session(engine)

    try:
        # 查询数据
        result = session.execute(text("SELECT COUNT(*) FROM weather_icon_v2"))
        count = result.scalar()
        print("\n验证结果:")
        print(f"  weather_icon_v2 表共有 {count} 条记录")

        # 查询部分数据
        result = session.execute(
            text("""
            SELECT id, weather_code, condition_zh, condition_en
            FROM weather_icon_v2
            ORDER BY id
            LIMIT 10
        """)
        )

        print("\n前10条数据:")
        for row in result:
            print(f"  ID: {row[0]}, 天气代码: {row[1]}, 中文: {row[2]}, 英文: {row[3]}")

    except Exception as e:
        print(f"验证失败: {e}")
    finally:
        session.close()


def main():
    print("天气现象映射数据导入 v2")
    print("=" * 50)

    # Excel文件路径
    xlsx_path = Path(__file__).resolve().parent / "weatherid.xlsx"

    # 读取数据
    data = read_excel_data(str(xlsx_path))

    if data:
        # 保存到数据库
        save_to_db(data)

        # 验证数据
        verify_data()

    print("\n导入完成！")


if __name__ == "__main__":
    main()
