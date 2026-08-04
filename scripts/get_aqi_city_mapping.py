#!/usr/bin/env python
"""
获取在意空气城市ID映射
从API获取城市信息，建立与系统城市ID的映射关系
"""

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

load_dotenv()


def get_city_mapping():
    """从API获取城市信息，建立映射关系"""
    api_key = os.getenv("AIR_MATTERS_KEY", "")
    if not api_key or api_key == "你的在意空气API密钥":
        print("❌ API Key未配置")
        return {}

    # 从utils.py获取城市ID列表
    from downloader.aqi.aqi.spiders.utils import air_matters_map

    city_ids = air_matters_map("city")

    # 去重
    city_ids = list(set(city_ids))
    print(f"获取到 {len(city_ids)} 个城市ID（去重后）")

    url = "https://api-cn.air-matters.com/batch"
    headers = {"Authorization": api_key}

    # 分批获取城市信息
    batch_size = 50
    all_cities = {}

    for i in range(0, len(city_ids), batch_size):
        batch_ids = city_ids[i : i + batch_size]
        saved_places = [{"place_id": pid} for pid in batch_ids]

        body = json.dumps(
            {
                "saved_places": saved_places,
                "user_info": {"lang": "zh-Hans", "preferred_standard": "aqi_cn"},
                "scope": ["place", "latest", "saved_places"],
            },
            ensure_ascii=False,
        )

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(url, headers=headers, content=body.encode("utf-8"))
                resp.raise_for_status()
                data = resp.json()

                for item in data.get("saved_places", []):
                    place_info = item.get("place", {})
                    place_id = place_info.get("place_id")
                    place_name = place_info.get("name")
                    place_type = place_info.get("type")
                    description = place_info.get("description", "")

                    if place_id and place_name:
                        all_cities[place_id] = {
                            "name": place_name,
                            "type": place_type,
                            "description": description,
                        }

                print(
                    f"批次 {i // batch_size + 1}: 获取 {len(data.get('saved_places', []))} 个城市"
                )

        except Exception as e:
            print(f"批次 {i // batch_size + 1} 失败: {e}")

    print(f"总共获取 {len(all_cities)} 个城市信息")
    return all_cities


def match_cities(air_cities: dict):
    """匹配在意空气城市与系统城市"""
    # 从数据库获取系统城市
    from sqlalchemy import text

    from downloader.models import get_engine, get_session

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3307")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    db = os.getenv("DB_NAME", "weather")
    db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"

    try:
        engine = get_engine(url=db_url)
        session = get_session(engine)

        # 获取系统城市
        result = session.execute(text("SELECT city_id, city_name FROM city"))
        system_cities = {}
        for row in result:
            city_id, city_name = row
            system_cities[city_name] = city_id

        session.close()

        print(f"系统城市数量: {len(system_cities)}")

        # 匹配城市
        mapping = {}
        for air_id, air_info in air_cities.items():
            air_name = air_info["name"]

            # 精确匹配
            if air_name in system_cities:
                mapping[air_id] = {
                    "air_name": air_name,
                    "system_id": system_cities[air_name],
                    "match_type": "exact",
                }
            else:
                # 模糊匹配
                for sys_name, sys_id in system_cities.items():
                    if air_name in sys_name or sys_name in air_name:
                        mapping[air_id] = {
                            "air_name": air_name,
                            "system_id": sys_id,
                            "match_type": "fuzzy",
                        }
                        break

        print(f"匹配成功: {len(mapping)} 个城市")
        return mapping

    except Exception as e:
        print(f"数据库连接失败: {e}")
        return {}


def save_mapping(mapping: dict):
    """保存映射关系到文件"""
    output_file = Path(__file__).resolve().parent.parent / "downloader" / "aqi_city_mapping.json"

    # 转换格式
    city_mapping = {}
    for air_id, info in mapping.items():
        city_mapping[air_id] = (info["air_name"], info["system_id"])

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(city_mapping, f, ensure_ascii=False, indent=2)

    print(f"映射关系已保存到: {output_file}")
    return city_mapping


def main():
    print("获取在意空气城市ID映射")
    print("=" * 50)

    # 获取城市信息
    air_cities = get_city_mapping()
    if not air_cities:
        return

    # 匹配城市
    mapping = match_cities(air_cities)
    if not mapping:
        return

    # 保存映射
    city_mapping = save_mapping(mapping)

    # 显示部分映射
    print()
    print("部分映射示例:")
    for _i, (air_id, (name, sys_id)) in enumerate(list(city_mapping.items())[:10]):
        print(f"  {air_id}: {name} -> {sys_id}")

    print()
    print("下一步:")
    print("1. 检查映射是否正确")
    print("2. 更新 downloader/aqi_downloader.py 中的 CITY_MAPPING")
    print("3. 重新运行下载脚本")


if __name__ == "__main__":
    main()
