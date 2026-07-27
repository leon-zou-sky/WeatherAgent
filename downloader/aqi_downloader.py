"""
AQI 数据下载器（简化版）
从在意空气（Air Matters）API获取AQI数据

用法:
    python -m downloader.aqi_downloader              # 下载所有城市AQI
    python -m downloader.aqi_downloader --city 北京   # 下载指定城市AQI
    python -m downloader.aqi_downloader --list        # 列出支持的城市
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime

import httpx
from dotenv import load_dotenv

from downloader.models import get_engine, get_session, create_tables, AQICity, AQIStation

# 加载环境变量
load_dotenv(Path(__file__).resolve().parent.parent / ".env.example")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ============ 城市映射 ============
# 在意空气城市ID -> (城市名, 系统城市ID)
# 系统城市ID用于与其他数据表关联

CITY_MAPPING = {
    # 直辖市
    "29a34245": ("北京", "101010100"),
    "1212a003": ("上海", "101020100"),
    "064e3cde": ("广州", "101280101"),
    "aa1376ab": ("深圳", "101280601"),

    # 省会城市
    "bdcd4251": ("天津", "101030100"),
    "cfd250a8": ("重庆", "101040100"),
    "cde644ca": ("杭州", "101210101"),
    "b792a6a1": ("南京", "101190101"),
    "691a5067": ("武汉", "101200101"),
    "c87f2070": ("成都", "101270101"),
    "f86116aa": ("西安", "101110101"),
    "a6732605": ("长沙", "101250101"),
    "ef533581": ("郑州", "101180101"),
    "cc63e78c": ("济南", "101120101"),
    "1134b7c4": ("太原", "101100101"),
    "037646cc": ("合肥", "101220101"),
    "6d74101f": ("福州", "101230101"),
    "3535f7e3": ("南昌", "101240101"),
    "78e79a2a": ("昆明", "101290101"),
    "8d4e6fbc": ("贵阳", "101260101"),
    "1b252c75": ("成都", "101270101"),  # 备用
    "194b348b": ("哈尔滨", "101050101"),

    # 其他主要城市
    "07af6bd6": ("台北", "101340101"),
    "c1d0ba27": ("高雄", "101340201"),
    "b87143e9": ("台中", "101340401"),
    "1f64186f": ("台南", "101340301"),
    "9d42496f": ("新北", "101340102"),

    # 港澳
    "995f7a4c": ("香港", "101320101"),
    "e7b693b4": ("澳门", "101330101"),

    # 其他省会
    "83499bd6": ("石家庄", "101090101"),
    "ed4d93e2": ("兰州", "101160101"),
    "649a546c": ("西宁", "101150101"),
    "7f267533": ("海口", "101310101"),
    "0928d406": ("南宁", "101300101"),
    "f291f9bc": ("银川", "101170101"),
    "7418bb74": ("乌鲁木齐", "101130101"),
    "6589f2ea": ("拉萨", "101140101"),
    "3fcca97e": ("呼和浩特", "101080101"),
    "c0e05355": ("沈阳", "101070101"),
    "e6cb9277": ("长春", "101060101"),
    "882cfb57": ("大连", "101070201"),
    "916d4c97": ("青岛", "101120201"),

    # 其他城市（可根据需要扩展）
    "eb7463ff": ("苏州", "101190401"),
    "ee40d9c9": ("无锡", "101190201"),
    "8b9bf6d6": ("常州", "101191101"),
    "f6df2af6": ("徐州", "101190801"),
    "097b6899": ("宁波", "101210401"),
    "a45bef13": ("温州", "101210701"),
    "d68d7466": ("厦门", "101230201"),
    "6db0e745": ("泉州", "101230501"),
}

# 监测站映射（部分示例）
STATION_MAPPING = {
    "bbafa1b1": "阿城会宁",
    "35bafa91": "阿里藏医院",
    "67aae2d8": "阿里监测站",
    "b78f1733": "艾青诗歌馆",
    "9fa31383": "安钢职工学校",
    "d7b3176e": "安吉城东",
    # ... 可从 utils.py 的 air_matters_map('point') 中提取更多
}


def get_db_url():
    """获取数据库连接URL"""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3307")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    db = os.getenv("DB_NAME", "weather")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"


def fetch_aqi_batch(place_ids: list) -> list:
    """批量获取AQI数据"""
    api_key = os.getenv("AIR_MATTERS_KEY", "")
    if not api_key:
        logger.error("❌ 未配置 AIR_MATTERS_KEY，请在 .env 中设置")
        return []

    url = "https://api-cn.air-matters.com/batch"
    headers = {"Authorization": api_key}

    saved_places = [{"place_id": pid} for pid in place_ids]
    body = json.dumps({
        "saved_places": saved_places,
        "user_info": {"lang": "zh-Hans", "preferred_standard": "aqi_cn"},
        "scope": ["place", "latest", "saved_places"]
    }, ensure_ascii=False)

    try:
        with httpx.Client(timeout=30) as client:
            # 确保请求体是字节类型
            if isinstance(body, str):
                body = body.encode('utf-8')
            logger.debug(f"请求URL: {url}")
            logger.debug(f"请求头: {headers}")
            logger.debug(f"请求体: {body[:100]}...")
            resp = client.post(url, headers=headers, content=body)
            logger.debug(f"响应状态码: {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            return data.get("saved_places", [])
    except Exception as e:
        logger.error(f"请求失败: {type(e).__name__}: {str(e)}")
        return []


def parse_aqi_data(item: dict) -> dict:
    """解析单条AQI数据"""
    place_info = item.get("place", {})
    latest_info = item.get("latest", {})
    readings = latest_info.get("readings", [])

    if not readings:
        return None

    result = {
        "place_id": place_info.get("place_id"),
        "place_type": place_info.get("type"),  # city 或 station
        "place_name": place_info.get("name"),
        "city_name": place_info.get("city_name"),
        "update_time": latest_info.get("update_time"),
    }

    # 解析各项污染物数据
    for reading in readings:
        kind = reading.get("kind", "").lower()
        value = reading.get("value")
        if kind and value:
            try:
                result[kind] = float(value)
            except (ValueError, TypeError):
                pass

    return result


def calculate_iaqi(result: dict) -> dict:
    """计算IAQI分指数（简化版）"""
    # 这里简化处理，实际应该使用完整的IAQI计算公式
    # 参考 downloader/aqi/aqi/spiders/utils.py 中的计算逻辑

    # PM2.5 IAQI
    if "pm25" in result and result["pm25"]:
        pm25 = result["pm25"]
        if pm25 <= 35:
            result["pm25_iaqi"] = int(pm25 * 50 / 35)
        elif pm25 <= 75:
            result["pm25_iaqi"] = int(50 + (pm25 - 35) * 50 / 40)
        elif pm25 <= 115:
            result["pm25_iaqi"] = int(100 + (pm25 - 75) * 50 / 40)
        elif pm25 <= 150:
            result["pm25_iaqi"] = int(150 + (pm25 - 115) * 50 / 35)
        elif pm25 <= 250:
            result["pm25_iaqi"] = int(200 + (pm25 - 150) * 100 / 100)
        elif pm25 <= 350:
            result["pm25_iaqi"] = int(300 + (pm25 - 250) * 100 / 100)
        else:
            result["pm25_iaqi"] = int(400 + (pm25 - 350) * 100 / 150)

    # PM10 IAQI
    if "pm10" in result and result["pm10"]:
        pm10 = result["pm10"]
        if pm10 <= 50:
            result["pm10_iaqi"] = int(pm10)
        elif pm10 <= 150:
            result["pm10_iaqi"] = int(50 + (pm10 - 50) * 50 / 100)
        elif pm10 <= 250:
            result["pm10_iaqi"] = int(100 + (pm10 - 150) * 50 / 100)
        elif pm10 <= 350:
            result["pm10_iaqi"] = int(150 + (pm10 - 250) * 50 / 100)
        elif pm10 <= 420:
            result["pm10_iaqi"] = int(200 + (pm10 - 350) * 100 / 70)
        elif pm10 <= 500:
            result["pm10_iaqi"] = int(300 + (pm10 - 420) * 100 / 80)
        else:
            result["pm10_iaqi"] = int(400 + (pm10 - 500) * 100 / 100)

    # AQI取最大值
    iaqi_values = []
    for key in ["pm25_iaqi", "pm10_iaqi", "so2_iaqi", "no2_iaqi", "o3_iaqi", "co_iaqi"]:
        if key in result and result[key]:
            iaqi_values.append(result[key])

    if iaqi_values:
        result["aqi"] = max(iaqi_values)

    return result


def save_city_aqi(session, data: dict):
    """保存城市AQI数据"""
    place_id = data.get("place_id")
    city_info = CITY_MAPPING.get(place_id)

    if not city_info:
        logger.warning(f"未知城市ID: {place_id}")
        return False

    city_name, system_city_id = city_info

    # 计算IAQI
    data = calculate_iaqi(data)

    # 创建记录
    record = AQICity(
        city_id=place_id,
        city_name=city_name,
        update_time=data.get("update_time"),
        aqi=data.get("aqi"),
        pm25=data.get("pm25"),
        pm25_iaqi=data.get("pm25_iaqi"),
        pm10=data.get("pm10"),
        pm10_iaqi=data.get("pm10_iaqi"),
        so2=data.get("so2"),
        so2_iaqi=data.get("so2_iaqi"),
        no2=data.get("no2"),
        no2_iaqi=data.get("no2_iaqi"),
        o3=data.get("o3"),
        o3_iaqi=data.get("o3_iaqi"),
        co=data.get("co"),
        co_iaqi=data.get("co_iaqi"),
        source="air_matters",
    )

    session.add(record)
    return True


def save_station_aqi(session, data: dict):
    """保存监测站AQI数据"""
    place_id = data.get("place_id")
    station_name = STATION_MAPPING.get(place_id, data.get("place_name", "未知站点"))

    # 计算IAQI
    data = calculate_iaqi(data)

    # 创建记录
    record = AQIStation(
        station_code=place_id,
        station_name=station_name,
        city_id=data.get("city_id"),
        city_name=data.get("city_name"),
        update_time=data.get("update_time"),
        aqi=data.get("aqi"),
        pm25=data.get("pm25"),
        pm25_iaqi=data.get("pm25_iaqi"),
        pm10=data.get("pm10"),
        pm10_iaqi=data.get("pm10_iaqi"),
        so2=data.get("so2"),
        so2_iaqi=data.get("so2_iaqi"),
        no2=data.get("no2"),
        no2_iaqi=data.get("no2_iaqi"),
        o3=data.get("o3"),
        o3_iaqi=data.get("o3_iaqi"),
        co=data.get("co"),
        co_iaqi=data.get("co_iaqi"),
        source="air_matters",
    )

    session.add(record)
    return True


def download_all():
    """下载所有城市AQI数据"""
    logger.info("开始下载AQI数据...")

    # 获取所有城市ID
    city_ids = list(CITY_MAPPING.keys())
    logger.info(f"准备下载 {len(city_ids)} 个城市的数据")

    # 分批下载（每批最多100个）
    batch_size = 100
    all_data = []

    for i in range(0, len(city_ids), batch_size):
        batch_ids = city_ids[i:i+batch_size]
        logger.info(f"下载批次 {i//batch_size + 1}: {len(batch_ids)} 个城市")

        batch_data = fetch_aqi_batch(batch_ids)
        all_data.extend(batch_data)

        # 避免请求过于频繁
        if i + batch_size < len(city_ids):
            time.sleep(1)

    logger.info(f"获取到 {len(all_data)} 条数据")

    # 连接数据库
    engine = get_engine(url=get_db_url())
    create_tables(engine)
    session = get_session(engine)

    try:
        city_count = 0
        station_count = 0

        for item in all_data:
            data = parse_aqi_data(item)
            if not data:
                continue

            if data.get("place_type") == "station":
                if save_station_aqi(session, data):
                    station_count += 1
            else:
                if save_city_aqi(session, data):
                    city_count += 1

        session.commit()
        logger.info(f"✅ 下载完成: 城市 {city_count} 条, 监测站 {station_count} 条")

    except Exception as e:
        session.rollback()
        logger.error(f"❌ 保存失败: {e}")
    finally:
        session.close()


def download_city(city_name: str):
    """下载指定城市AQI数据"""
    # 查找城市ID
    city_id = None
    for pid, (name, _) in CITY_MAPPING.items():
        if name == city_name:
            city_id = pid
            break

    if not city_id:
        logger.error(f"未找到城市: {city_name}")
        logger.info(f"支持的城市: {', '.join(set(name for name, _ in CITY_MAPPING.values()))}")
        return

    logger.info(f"Downloading AQI data for {city_name}...")

    # 下载数据
    data_list = fetch_aqi_batch([city_id])

    if not data_list:
        logger.warning("未获取到数据")
        return

    # 连接数据库
    engine = get_engine(url=get_db_url())
    create_tables(engine)
    session = get_session(engine)

    try:
        for item in data_list:
            data = parse_aqi_data(item)
            if not data:
                continue

            if data.get("place_type") == "station":
                if save_station_aqi(session, data):
                    logger.info(f"保存监测站数据: {data.get('place_name')}")
            else:
                if save_city_aqi(session, data):
                    logger.info(f"保存城市数据: {city_name}")

        session.commit()
        logger.info("✅ 下载完成")

    except Exception as e:
        session.rollback()
        logger.error(f"❌ 保存失败: {e}")
    finally:
        session.close()


def list_cities():
    """列出支持的城市"""
    print("支持的城市列表:")
    print("=" * 50)

    cities = set()
    for city_id, (name, system_id) in CITY_MAPPING.items():
        cities.add((name, city_id, system_id))

    for name, city_id, system_id in sorted(cities):
        print(f"{name:10} | {city_id:10} | {system_id}")


def get_aqi_level(aqi: int) -> str:
    """获取AQI等级

    Args:
        aqi: AQI指数

    Returns:
        str: AQI等级
    """
    if aqi is None:
        return None

    if aqi <= 50:
        return "优"
    elif aqi <= 100:
        return "良"
    elif aqi <= 150:
        return "轻度污染"
    elif aqi <= 200:
        return "中度污染"
    elif aqi <= 300:
        return "重度污染"
    else:
        return "严重污染"


def get_aqi_description(level: str) -> str:
    """获取AQI等级描述

    Args:
        level: AQI等级

    Returns:
        str: 等级描述
    """
    descriptions = {
        "优": "空气质量令人满意，基本无空气污染",
        "良": "空气质量可接受，某些污染物可能对少数人健康有轻微影响",
        "轻度污染": "敏感人群症状有轻度加剧，健康人群出现刺激症状",
        "中度污染": "进一步加剧敏感人群症状，可能对心脏和呼吸系统有影响",
        "重度污染": "健康人群运动耐受力降低，有明显强烈症状",
        "严重污染": "健康人群运动耐受力降低，有明显强烈症状，提前采取措施"
    }
    return descriptions.get(level, "")


def get_health_advice(level: str) -> dict:
    """获取健康建议

    Args:
        level: AQI等级

    Returns:
        dict: 健康建议
    """
    advice = {
        "优": {
            "general": "适宜户外活动",
            "sensitive": "可正常进行户外活动",
            "outdoor": "适宜",
            "mask": "不需要"
        },
        "良": {
            "general": "可正常户外活动",
            "sensitive": "减少长时间、高强度的户外活动",
            "outdoor": "适宜",
            "mask": "不需要"
        },
        "轻度污染": {
            "general": "减少户外活动",
            "sensitive": "避免户外活动，外出时佩戴防护口罩",
            "outdoor": "减少",
            "mask": "敏感人群需要"
        },
        "中度污染": {
            "general": "减少户外活动，外出时佩戴防护口罩",
            "sensitive": "避免户外活动，尽量留在室内",
            "outdoor": "减少",
            "mask": "需要"
        },
        "重度污染": {
            "general": "避免户外活动，外出时佩戴防护口罩",
            "sensitive": "留在室内，关闭门窗",
            "outdoor": "避免",
            "mask": "必须佩戴"
        },
        "严重污染": {
            "general": "留在室内，关闭门窗",
            "sensitive": "留在室内，开启空气净化器",
            "outdoor": "禁止",
            "mask": "必须佩戴"
        }
    }
    return advice.get(level, {})


def main():
    parser = argparse.ArgumentParser(description="AQI数据下载器")
    parser.add_argument("--city", type=str, help="下载指定城市AQI数据")
    parser.add_argument("--list", action="store_true", help="列出支持的城市")

    args = parser.parse_args()

    if args.list:
        list_cities()
    elif args.city:
        download_city(args.city)
    else:
        download_all()


if __name__ == "__main__":
    main()
