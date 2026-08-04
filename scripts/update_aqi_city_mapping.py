#!/usr/bin/env python
"""
更新AQI城市映射
从映射文件中提取所有城市，更新CITY_MAPPING
"""

import json
from pathlib import Path


def update_city_mapping():
    """更新CITY_MAPPING"""
    # 读取映射文件
    mapping_file = Path("downloader/aqi_city_mapping.json")
    if not mapping_file.exists():
        print(f"❌ 映射文件不存在: {mapping_file}")
        return

    with open(mapping_file, encoding="utf-8") as f:
        mapping = json.load(f)

    print(f"读取映射文件: {len(mapping)} 个城市")

    # 读取现有的aqi_downloader.py
    downloader_file = Path("downloader/aqi_downloader.py")
    with open(downloader_file, encoding="utf-8") as f:
        content = f.read()

    # 找到CITY_MAPPING的开始和结束位置
    start_marker = "CITY_MAPPING = {"

    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("❌ 未找到CITY_MAPPING定义")
        return

    # 找到匹配的结束大括号
    brace_count = 0
    end_idx = start_idx
    for i in range(start_idx, len(content)):
        if content[i] == "{":
            brace_count += 1
        elif content[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break

    # 生成新的CITY_MAPPING
    new_mapping_lines = ["CITY_MAPPING = {"]

    # 按城市名排序
    sorted_cities = sorted(mapping.items(), key=lambda x: x[1][0])

    for air_id, (name, sys_id) in sorted_cities:
        new_mapping_lines.append(f'    "{air_id}": ("{name}", "{sys_id}"),')

    new_mapping_lines.append("}")

    new_mapping_content = "\n".join(new_mapping_lines)

    # 替换内容
    new_content = content[:start_idx] + new_mapping_content + content[end_idx:]

    # 写入文件
    with open(downloader_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ 更新CITY_MAPPING: {len(mapping)} 个城市")
    print()
    print("下一步:")
    print("1. 检查更新是否正确")
    print("2. 重新运行下载脚本: python -m downloader.aqi_downloader")


def main():
    print("更新AQI城市映射")
    print("=" * 50)
    update_city_mapping()


if __name__ == "__main__":
    main()
