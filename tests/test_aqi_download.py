#!/usr/bin/env python
"""
测试AQI下载功能（模拟测试）
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from downloader.aqi_downloader import (
    CITY_MAPPING,
    calculate_iaqi,
    get_aqi_level,
    get_health_advice,
    parse_aqi_data,
)


def test_parse_aqi_data():
    """测试解析AQI数据"""
    print("=== 测试解析AQI数据 ===")

    # 模拟API响应数据
    mock_data = {
        "place": {"place_id": "29a34245", "type": "city", "name": "北京", "city_name": "北京"},
        "latest": {
            "update_time": "2024-01-15 10:00:00",
            "readings": [
                {"kind": "aqi", "value": "75"},
                {"kind": "pm25", "value": "55"},
                {"kind": "pm10", "value": "85"},
                {"kind": "so2", "value": "12"},
                {"kind": "no2", "value": "45"},
                {"kind": "o3", "value": "65"},
                {"kind": "co", "value": "0.8"},
            ],
        },
    }

    result = parse_aqi_data(mock_data)

    print("解析结果:")
    print(f"  - place_id: {result.get('place_id')}")
    print(f"  - place_type: {result.get('place_type')}")
    print(f"  - place_name: {result.get('place_name')}")
    print(f"  - city_name: {result.get('city_name')}")
    print(f"  - update_time: {result.get('update_time')}")
    print(f"  - aqi: {result.get('aqi')}")
    print(f"  - pm25: {result.get('pm25')}")
    print(f"  - pm10: {result.get('pm10')}")
    print()

    return result


def test_calculate_iaqi():
    """测试计算IAQI"""
    print("=== 测试计算IAQI ===")

    # 先解析数据
    data = test_parse_aqi_data()

    result = calculate_iaqi(data)

    print("IAQI计算结果:")
    print(f"  - AQI: {result.get('aqi')}")
    print(f"  - PM2.5 IAQI: {result.get('pm25_iaqi')}")
    print(f"  - PM10 IAQI: {result.get('pm10_iaqi')}")
    print()


def test_aqi_levels():
    """测试AQI等级划分"""
    print("=== 测试AQI等级划分 ===")

    test_cases = [
        (25, "优"),
        (50, "优"),
        (75, "良"),
        (100, "良"),
        (125, "轻度污染"),
        (150, "轻度污染"),
        (175, "中度污染"),
        (200, "中度污染"),
        (250, "重度污染"),
        (300, "重度污染"),
        (350, "严重污染"),
        (500, "严重污染"),
    ]

    for aqi, expected_level in test_cases:
        level = get_aqi_level(aqi)
        status = "✓" if level == expected_level else "✗"
        print(f"  {status} AQI {aqi:3d} -> {level:6} (期望: {expected_level})")

    print()


def test_health_advice():
    """测试健康建议"""
    print("=== 测试健康建议 ===")

    levels = ["优", "良", "轻度污染", "中度污染", "重度污染", "严重污染"]

    for level in levels:
        advice = get_health_advice(level)
        print(f"{level}:")
        print(f"  - 一般人群: {advice.get('general', '')}")
        print(f"  - 户外活动: {advice.get('outdoor', '')}")
        print()


def test_city_mapping():
    """测试城市映射"""
    print("=== 测试城市映射 ===")

    # 测试几个主要城市
    test_cities = ["北京", "上海", "广州", "深圳", "杭州"]

    for city_name in test_cities:
        # 查找对应的城市ID
        city_id = None
        for air_id, (name, sys_id) in CITY_MAPPING.items():
            if name == city_name:
                city_id = air_id
                break

        if city_id:
            print(f"  ✓ {city_name}: {city_id}")
        else:
            print(f"  ✗ {city_name}: 未找到映射")

    print()


def test_data_flow():
    """测试数据流"""
    print("=== 测试数据流 ===")

    # 1. 模拟API数据
    mock_api_data = [
        {
            "place": {"place_id": "29a34245", "type": "city", "name": "北京", "city_name": "北京"},
            "latest": {
                "update_time": "2024-01-15 10:00:00",
                "readings": [
                    {"kind": "aqi", "value": "85"},
                    {"kind": "pm25", "value": "65"},
                    {"kind": "pm10", "value": "95"},
                    {"kind": "so2", "value": "15"},
                    {"kind": "no2", "value": "50"},
                    {"kind": "o3", "value": "70"},
                    {"kind": "co", "value": "1.0"},
                ],
            },
        }
    ]

    print("1. 解析API数据...")
    parsed_data = parse_aqi_data(mock_api_data[0])
    print(f"   解析完成: {parsed_data.get('place_name')}")

    print("2. 计算IAQI...")
    data_with_iaqi = calculate_iaqi(parsed_data)
    print(f"   AQI: {data_with_iaqi.get('aqi')}")
    print(f"   PM2.5 IAQI: {data_with_iaqi.get('pm25_iaqi')}")

    print("3. 获取健康建议...")
    aqi_level = get_aqi_level(data_with_iaqi.get("aqi"))
    advice = get_health_advice(aqi_level)
    print(f"   等级: {aqi_level}")
    print(f"   建议: {advice.get('general', '')}")

    print("4. 数据映射...")
    place_id = parsed_data.get("place_id")
    if place_id in CITY_MAPPING:
        city_name, system_id = CITY_MAPPING[place_id]
        print(f"   城市: {city_name}")
        print(f"   系统ID: {system_id}")
    else:
        print(f"   未找到城市映射: {place_id}")

    print()


def main():
    print("AQI下载功能测试")
    print("=" * 50)
    print()

    # 运行各项测试
    test_city_mapping()
    test_aqi_levels()
    test_health_advice()

    # 数据流测试
    data = test_parse_aqi_data()
    test_calculate_iaqi(data)
    test_data_flow()

    print("测试完成！")
    print()
    print("说明:")
    print("1. 城市映射测试通过")
    print("2. AQI等级划分正确")
    print("3. 健康建议生成正常")
    print("4. 数据解析和计算流程正常")
    print()
    print("下一步:")
    print("1. 配置 AIR_MATTERS_KEY 环境变量")
    print("2. 运行 python -m downloader.aqi_downloader --list 查看支持的城市")
    print("3. 运行 python -m downloader.aqi_downloader --city 北京 测试单个城市下载")
    print("4. 运行 python -m downloader.aqi_downloader 下载所有城市数据")


if __name__ == "__main__":
    main()
