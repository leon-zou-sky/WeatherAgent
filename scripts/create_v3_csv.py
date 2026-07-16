"""
生成 v3 版 CSV
- 清洗 severity 脏数据
- 细化 tags
- 增加示例反馈
"""

import csv
from pathlib import Path

INPUT = Path(__file__).resolve().parent.parent / "weather_feedback_enriched_v2.csv"
OUTPUT = Path(__file__).resolve().parent.parent / "weather_feedback_enriched_v3.csv"


def clean_severity(val: str) -> str:
    """只保留 high/medium/low"""
    val = val.strip().lower()
    if val in ("high", "medium", "low"):
        return val
    return "medium"


def improve_tags(row: dict) -> str:
    """细化 tags"""
    old_tags = row.get("tags", "").strip()
    desc = row.get("problem_desc", "")
    pattern = row.get("problem_pattern", "")
    module = row.get("module", "")

    # 体感差异类
    if any(kw in desc for kw in ["体感", "闷热", "湿热", "干热", "难熬", "热死了", "冻死了"]):
        return "体感温度"

    # 预警理解类
    if any(kw in desc for kw in ["预警", "蓝色", "橙色", "黄色", "红色", "分级", "啥区别"]):
        return "预警理解"

    # 雾霾区分
    if any(kw in desc for kw in ["雾霾", "雾和霾", "灰蒙蒙", "不是雾霾"]):
        return "雾和霾"

    # 雷达图
    if any(kw in desc for kw in ["雷达图", "雷达回波", "dBZ"]):
        return "雷达解读"

    # 天气系统
    if any(kw in desc for kw in ["副高", "冷涡", "切变线", "锋面", "对流", "冷空气"]):
        return "天气系统"

    # 原来的 tags 如果是具体要素就保留
    specific_tags = ["温度", "降雨", "风力", "湿度", "气压", "能见度", "紫外线",
                     "雷电", "闪电", "台风", "暴雨", "大雾", "沙尘", "冰雹", "暴雪",
                     "闷热", "花粉", "穿衣", "运动", "洗车"]
    for t in specific_tags:
        if t in old_tags:
            return t

    # 模糊的 tags 替换
    vague_tags = {"气象知识": "气象原理", "灾害复盘": "灾害应急", "数据源": "数据质量"}
    if old_tags in vague_tags:
        return vague_tags[old_tags]

    return old_tags if old_tags else "其他"


def main():
    rows = []
    with open(INPUT, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"读取 v2: {len(rows)} 条")

    # 处理每行
    for row in rows:
        row["severity"] = clean_severity(row.get("severity", ""))
        row["tags"] = improve_tags(row)

    # 新增示例反馈
    new_rows = [
        {"module": "实况", "problem_pattern": "认知偏差", "problem_desc": "你们App说今天晴天怎么外面在下雨",
         "root_cause": "用户混淆了实时天气和预报天气", "solution": "页面区分当前实时天气和未来预报",
         "tags": "气象原理", "severity": "low"},
        {"module": "实况", "problem_pattern": "认知偏差", "problem_desc": "天气预报说多云为什么太阳这么大",
         "root_cause": "多云定义是云量60-90%仍有阳光", "solution": "多云图标增加阳光穿透效果",
         "tags": "气象原理", "severity": "low"},
        {"module": "实况", "problem_pattern": "数据偏差", "problem_desc": "我这明明在下雨App还显示晴天",
         "root_cause": "气象站与用户位置有距离", "solution": "增加附近气象站实时数据参考",
         "tags": "降雨", "severity": "high"},
        {"module": "天气预警", "problem_pattern": "认知偏差", "problem_desc": "暴雨预警解除了怎么路上还有积水",
         "root_cause": "预警解除指降雨停止但积水消退需要时间", "solution": "预警解除后增加积水消退预估时间",
         "tags": "预警理解", "severity": "low"},
        {"module": "空气质量", "problem_pattern": "认知偏差", "problem_desc": "PM2.5和PM10有什么区别",
         "root_cause": "用户不了解颗粒物粒径差异", "solution": "空气质量页增加PM2.5/PM10科普卡片",
         "tags": "空气质量", "severity": "low"},
        {"module": "实况", "problem_pattern": "认知偏差", "problem_desc": "为什么天气预报总是不准",
         "root_cause": "用户对预报精度期望过高不了解预报不确定性", "solution": "增加预报可信度和误差范围展示",
         "tags": "气象原理", "severity": "low"},
        {"module": "实况", "problem_pattern": "数据偏差", "problem_desc": "温度计显示28度App显示32度差太多",
         "root_cause": "用户室内温度计与室外气象站温度不同", "solution": "说明气象温度是室外百叶箱标准测量值",
         "tags": "温度", "severity": "medium"},
        {"module": "短临降水", "problem_pattern": "认知偏差", "problem_desc": "说好的一小时后雨停怎么还在下",
         "root_cause": "短临预报精度有限降水结束时间存在误差", "solution": "短临预报增加置信度和误差范围",
         "tags": "降雨", "severity": "medium"},
        {"module": "实况", "problem_pattern": "认知偏差", "problem_desc": "为什么台风天风这么大但雨不大",
         "root_cause": "台风外围风力强但雨带未覆盖", "solution": "台风页增加风雨分离科普说明",
         "tags": "天气系统", "severity": "low"},
        {"module": "空气质量", "problem_pattern": "认知偏差", "problem_desc": "为什么开窗通风后室内PM2.5反而升高了",
         "root_cause": "室外污染比室内严重时开窗会引入污染物", "solution": "增加室内外空气质量对比和开窗建议",
         "tags": "空气质量", "severity": "medium"},
    ]

    rows.extend(new_rows)
    print(f"新增 {len(new_rows)} 条，总计 {len(rows)} 条")

    # 写入 v3
    fieldnames = ["module", "problem_pattern", "problem_desc", "root_cause", "solution", "tags", "severity"]
    with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ 已保存: {OUTPUT}")

    # 统计
    print("\n=== severity 分布 ===")
    sev_count = {}
    for r in rows:
        s = r["severity"]
        sev_count[s] = sev_count.get(s, 0) + 1
    for k, v in sorted(sev_count.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    print("\n=== tags 分布 ===")
    tag_count = {}
    for r in rows:
        t = r["tags"]
        tag_count[t] = tag_count.get(t, 0) + 1
    for k, v in sorted(tag_count.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
