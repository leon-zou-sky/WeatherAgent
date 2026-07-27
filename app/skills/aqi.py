"""
AQI 数据查询 Skill
提供空气质量指数查询功能
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import desc

from app.skills.db import get_db_session
from downloader.models import AQICity, AQIStation

logger = logging.getLogger(__name__)


async def query_aqi_data(city: str, time: str = "") -> dict:
    """查询城市AQI数据

    Args:
        city: 城市名称，如"北京"、"上海"
        time: 查询时间，格式 YYYY-MM-DD，默认当天

    Returns:
        dict: AQI数据，包含aqi、pm2.5、pm10等指标
    """
    logger.info(f"[AQI] 查询城市AQI: city={city}, time={time}")

    session = get_db_session()
    try:
        # 查询城市AQI数据
        query = session.query(AQICity).filter(
            AQICity.city_name == city
        ).order_by(desc(AQICity.created_at))

        # 如果指定时间，过滤当天数据
        if time:
            query = query.filter(
                AQICity.created_at >= f"{time} 00:00:00",
                AQICity.created_at <= f"{time} 23:59:59"
            )

        record = query.first()

        if not record:
            # 尝试模糊匹配
            record = session.query(AQICity).filter(
                AQICity.city_name.like(f"%{city}%")
            ).order_by(desc(AQICity.created_at)).first()

        if not record:
            return {
                "success": False,
                "error": f"未找到 {city} 的AQI数据",
                "suggestion": "请检查城市名称是否正确，或先运行数据下载"
            }

        # 获取AQI等级
        aqi_level = get_aqi_level(record.aqi) if record.aqi else None

        # 构建返回结果
        result = {
            "success": True,
            "city": record.city_name,
            "update_time": record.update_time,
            "aqi": {
                "value": record.aqi,
                "level": aqi_level,
                "description": get_aqi_description(aqi_level) if aqi_level else None
            },
            "pollutants": {
                "pm2.5": {
                    "value": record.pm25,
                    "unit": "μg/m³",
                    "iaqi": record.pm25_iaqi
                },
                "pm10": {
                    "value": record.pm10,
                    "unit": "μg/m³",
                    "iaqi": record.pm10_iaqi
                },
                "so2": {
                    "value": record.so2,
                    "unit": "μg/m³",
                    "iaqi": record.so2_iaqi
                },
                "no2": {
                    "value": record.no2,
                    "unit": "μg/m³",
                    "iaqi": record.no2_iaqi
                },
                "o3": {
                    "value": record.o3,
                    "unit": "μg/m³",
                    "iaqi": record.o3_iaqi
                },
                "co": {
                    "value": record.co,
                    "unit": "mg/m³",
                    "iaqi": record.co_iaqi
                }
            },
            "health_advice": get_health_advice(aqi_level) if aqi_level else None,
            "data_source": record.source
        }

        return result

    except Exception as e:
        logger.error(f"查询AQI数据失败: {e}")
        return {
            "success": False,
            "error": f"查询失败: {str(e)}"
        }
    finally:
        session.close()


async def query_station_aqi(station_name: str, city: str = "") -> dict:
    """查询监测站AQI数据

    Args:
        station_name: 监测站名称
        city: 城市名称（可选，用于缩小搜索范围）

    Returns:
        dict: 监测站AQI数据
    """
    logger.info(f"[AQI] 查询监测站AQI: station={station_name}, city={city}")

    session = get_db_session()
    try:
        query = session.query(AQIStation).filter(
            AQIStation.station_name.like(f"%{station_name}%")
        ).order_by(desc(AQIStation.created_at))

        if city:
            query = query.filter(AQIStation.city_name == city)

        record = query.first()

        if not record:
            return {
                "success": False,
                "error": f"未找到监测站 {station_name} 的AQI数据"
            }

        # 获取AQI等级
        aqi_level = get_aqi_level(record.aqi) if record.aqi else None

        result = {
            "success": True,
            "station": record.station_name,
            "city": record.city_name,
            "update_time": record.update_time,
            "aqi": {
                "value": record.aqi,
                "level": aqi_level,
                "description": get_aqi_description(aqi_level) if aqi_level else None
            },
            "pollutants": {
                "pm2.5": {"value": record.pm25, "unit": "μg/m³", "iaqi": record.pm25_iaqi},
                "pm10": {"value": record.pm10, "unit": "μg/m³", "iaqi": record.pm10_iaqi},
                "so2": {"value": record.so2, "unit": "μg/m³", "iaqi": record.so2_iaqi},
                "no2": {"value": record.no2, "unit": "μg/m³", "iaqi": record.no2_iaqi},
                "o3": {"value": record.o3, "unit": "μg/m³", "iaqi": record.o3_iaqi},
                "co": {"value": record.co, "unit": "mg/m³", "iaqi": record.co_iaqi}
            },
            "health_advice": get_health_advice(aqi_level) if aqi_level else None,
            "data_source": record.source
        }

        return result

    except Exception as e:
        logger.error(f"查询监测站AQI数据失败: {e}")
        return {
            "success": False,
            "error": f"查询失败: {str(e)}"
        }
    finally:
        session.close()


async def get_latest_aqi_summary() -> dict:
    """获取最新AQI数据概览

    Returns:
        dict: 各城市最新AQI数据概览
    """
    logger.info("[AQI] 获取AQI数据概览")

    session = get_db_session()
    try:
        # 获取每个城市的最新数据
        from sqlalchemy import func

        # 子查询：获取每个城市的最新更新时间
        subquery = session.query(
            AQICity.city_name,
            func.max(AQICity.created_at).label('max_time')
        ).group_by(AQICity.city_name).subquery()

        # 主查询：获取最新数据
        results = session.query(AQICity).join(
            subquery,
            (AQICity.city_name == subquery.c.city_name) &
            (AQICity.created_at == subquery.c.max_time)
        ).all()

        summary = {
            "total_cities": len(results),
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cities": []
        }

        for record in results:
            aqi_level = get_aqi_level(record.aqi) if record.aqi else None
            city_info = {
                "city": record.city_name,
                "aqi": record.aqi,
                "level": aqi_level,
                "pm2.5": record.pm25,
                "update_time": record.update_time
            }
            summary["cities"].append(city_info)

        # 按AQI排序
        summary["cities"].sort(key=lambda x: x.get("aqi") or 0, reverse=True)

        return summary

    except Exception as e:
        logger.error(f"获取AQI概览失败: {e}")
        return {
            "success": False,
            "error": f"获取概览失败: {str(e)}"
        }
    finally:
        session.close()


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


# ============ 工具函数 ============

def format_aqi_report(data: dict) -> str:
    """格式化AQI报告为可读文本

    Args:
        data: AQI数据

    Returns:
        str: 格式化后的报告
    """
    if not data.get("success"):
        return f"查询失败: {data.get('error', '未知错误')}"

    city = data.get("city", "未知")
    aqi_info = data.get("aqi", {})
    pollutants = data.get("pollutants", {})
    advice = data.get("health_advice", {})

    report = f"## {city} 空气质量报告\n\n"
    report += f"**更新时间**: {data.get('update_time', '未知')}\n\n"

    # AQI指数
    aqi_value = aqi_info.get("value")
    aqi_level = aqi_info.get("level")
    report += f"### AQI指数\n"
    report += f"- **AQI**: {aqi_value} ({aqi_level})\n"
    report += f"- **描述**: {aqi_info.get('description', '')}\n\n"

    # 主要污染物
    report += "### 主要污染物\n"
    for name, info in pollutants.items():
        if info.get("value"):
            report += f"- **{name}**: {info['value']} {info['unit']} (IAQI: {info.get('iaqi', 'N/A')})\n"

    # 健康建议
    if advice:
        report += "\n### 健康建议\n"
        report += f"- **一般人群**: {advice.get('general', '')}\n"
        report += f"- **敏感人群**: {advice.get('sensitive', '')}\n"
        report += f"- **户外活动**: {advice.get('outdoor', '')}\n"
        report += f"- **佩戴口罩**: {advice.get('mask', '')}\n"

    return report


def format_aqi_brief(data: dict) -> str:
    """格式化AQI简要信息

    Args:
        data: AQI数据

    Returns:
        str: 简要信息
    """
    if not data.get("success"):
        return f"查询失败: {data.get('error', '未知错误')}"

    city = data.get("city", "未知")
    aqi_info = data.get("aqi", {})
    aqi_value = aqi_info.get("value")
    aqi_level = aqi_info.get("level")

    return f"{city} AQI: {aqi_value} ({aqi_level})"
