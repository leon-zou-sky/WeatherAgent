"""
RAG 检索质量评估
人工标注测试用例，自动计算命中率
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.skills.knowledge import search_knowledge

# 测试用例：query + 期望匹配的 module
TEST_CASES = [
    {"query": "温度比预报高5度", "expected_module": "实况", "desc": "温度偏差"},
    {"query": "温度比预报低3度", "expected_module": "实况", "desc": "温度偏差"},
    {"query": "又淋雨了预报没说", "expected_module": "实况", "desc": "降雨偏差"},
    {"query": "暴雨预警迟了半小时", "expected_module": "天气预警", "desc": "预警延迟"},
    {"query": "没收到台风预警", "expected_module": "天气预警", "desc": "预警推送"},
    {"query": "热死了", "expected_module": "实况", "desc": "体感温度"},
    {"query": "雾霾好严重", "expected_module": "空气质量", "desc": "空气质量"},
    {"query": "AQI不准", "expected_module": "空气质量", "desc": "空气质量"},
    {"query": "雷达图看不懂", "expected_module": "格点可视化", "desc": "雷达解读"},
    {"query": "App闪退", "expected_module": "App体验", "desc": "App体验"},
    {"query": "紫外线太强", "expected_module": "生活指数", "desc": "生活指数"},
    {"query": "台风路径不准", "expected_module": "台风预报", "desc": "台风预报"},
    {"query": "气压一直在降", "expected_module": "实况", "desc": "气压数据"},
    {"query": "定位不准", "expected_module": "定位", "desc": "定位问题"},
    {"query": "数据更新太慢", "expected_module": "数据时效", "desc": "数据时效"},
]


async def evaluate():
    """运行评估"""
    print("=" * 60)
    print("RAG 检索质量评估")
    print("=" * 60)

    total = len(TEST_CASES)
    hit_top1 = 0
    hit_top3 = 0
    results_detail = []

    for case in TEST_CASES:
        query = case["query"]
        expected = case["expected_module"]

        retrieved = await search_knowledge(query, top_k=3)
        retrieved_modules = []
        for r in retrieved:
            # 从 content 中提取 module: "[实况][数据偏差] xxx"
            if r.content.startswith("["):
                module = r.content.split("]")[0].lstrip("[")
                retrieved_modules.append(module)

        # 判断命中
        top1_hit = len(retrieved_modules) > 0 and retrieved_modules[0] == expected
        top3_hit = expected in retrieved_modules

        if top1_hit:
            hit_top1 += 1
        if top3_hit:
            hit_top3 += 1

        status_top1 = "✅" if top1_hit else "❌"
        status_top3 = "✅" if top3_hit else "❌"

        results_detail.append({
            "query": query,
            "desc": case["desc"],
            "expected": expected,
            "retrieved": retrieved_modules,
            "top1_hit": top1_hit,
            "top3_hit": top3_hit,
        })

        print(f"\n查询: \"{query}\" ({case['desc']})")
        print(f"  期望: {expected}")
        print(f"  Top1: {retrieved_modules[0] if retrieved_modules else '无'} {status_top1}")
        print(f"  Top3: {retrieved_modules} {status_top3}")

    # 汇总
    print("\n" + "=" * 60)
    print("评估结果汇总")
    print("=" * 60)
    print(f"总用例数: {total}")
    print(f"Top-1 命中率: {hit_top1}/{total} = {hit_top1/total:.1%}")
    print(f"Top-3 命中率: {hit_top3}/{total} = {hit_top3/total:.1%}")

    # Badcase 分析
    badcases = [r for r in results_detail if not r["top3_hit"]]
    if badcases:
        print(f"\n❌ Badcase ({len(badcases)} 条):")
        for bc in badcases:
            print(f"  - \"{bc['query']}\": 期望 {bc['expected']}, 检索到 {bc['retrieved']}")


if __name__ == "__main__":
    asyncio.run(evaluate())
