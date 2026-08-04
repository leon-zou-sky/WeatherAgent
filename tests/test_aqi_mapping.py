#!/usr/bin/env python
"""
测试AQI城市映射
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from downloader.aqi_downloader import CITY_MAPPING, STATION_MAPPING


def test_city_mapping():
    """测试城市映射"""
    print("=== 城市映射测试 ===")
    print(f"总共 {len(CITY_MAPPING)} 个城市映射")
    print()

    # 按城市名排序
    sorted_cities = sorted(CITY_MAPPING.items(), key=lambda x: x[1][0])

    for air_matters_id, (city_name, system_id) in sorted_cities[:20]:  # 只显示前20个
        print(f"{city_name:10} | 在意空气ID: {air_matters_id:10} | 系统ID: {system_id}")

    print()
    print("... 更多城市省略 ...")
    print()


def test_station_mapping():
    """测试监测站映射"""
    print("=== 监测站映射测试 ===")
    print(f"总共 {len(STATION_MAPPING)} 个监测站映射")
    print()

    # 显示前10个
    for i, (station_id, station_name) in enumerate(list(STATION_MAPPING.items())[:10]):
        print(f"{station_name:15} | 监测站ID: {station_id}")

    print()
    print("... 更多监测站省略 ...")
    print()


def test_id_format():
    """测试ID格式"""
    print("=== ID格式测试 ===")

    # 在意空气ID格式
    sample_air_id = "29a34245"
    print(f"在意空气ID格式: {sample_air_id}")
    print(f"  - 长度: {len(sample_air_id)}")
    print("  - 字符类型: 字母+数字混合")

    # 系统ID格式
    sample_system_id = "101010100"
    print(f"系统ID格式: {sample_system_id}")
    print(f"  - 长度: {len(sample_system_id)}")
    print("  - 字符类型: 纯数字")

    print()
    print("两种ID格式完全不同，需要映射表关联")
    print()


def test_city_coverage():
    """测试城市覆盖度"""
    print("=== 城市覆盖度测试 ===")

    # 提取所有城市名
    city_names = set()
    for city_name, _ in CITY_MAPPING.values():
        city_names.add(city_name)

    print(f"覆盖城市数量: {len(city_names)}")
    print()

    # 按省份分组（简单示例）
    provinces = {
        "北京": ["北京"],
        "上海": ["上海"],
        "广东": ["广州", "深圳"],
        "浙江": ["杭州", "宁波", "温州"],
        "江苏": ["南京", "苏州", "无锡", "常州", "徐州"],
        # ... 可以继续扩展
    }

    for province, cities in provinces.items():
        covered = [c for c in cities if c in city_names]
        if covered:
            print(f"{province}: {', '.join(covered)}")

    print()


def main():
    print("AQI城市映射测试")
    print("=" * 50)
    print()

    test_id_format()
    test_city_mapping()
    test_station_mapping()
    test_city_coverage()

    print("测试完成！")
    print()
    print("说明:")
    print("1. 在意空气使用字母数字混合ID (如 29a34245)")
    print("2. 系统使用纯数字ID (如 101010100)")
    print("3. 需要映射表来关联两个系统的数据")
    print("4. 可以通过城市名进行模糊匹配")


if __name__ == "__main__":
    main()
