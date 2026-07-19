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
# 50 个用例，覆盖 14 个产品模块 + 5 种问题模式
TEST_CASES = [
    # ===== 实况数据（15个）=====
    {"query": "温度比预报高5度", "expected_module": "实况", "desc": "温度偏差-偏高"},
    {"query": "温度比预报低3度", "expected_module": "实况", "desc": "温度偏差-偏低"},
    {"query": "体感温度不准跟实际差太多", "expected_module": "实况", "desc": "体感温度"},
    {"query": "热死了", "expected_module": "实况", "desc": "体感温度-高温"},
    {"query": "冷得要命", "expected_module": "实况", "desc": "体感温度-低温"},
    {"query": "湿度显示90%但我感觉没那么湿", "expected_module": "实况", "desc": "湿度偏差"},
    {"query": "风速不准明明很大风", "expected_module": "实况", "desc": "风速偏差"},
    {"query": "能见度数据不对", "expected_module": "实况", "desc": "能见度偏差"},
    {"query": "气压一直在降", "expected_module": "实况", "desc": "气压数据"},
    {"query": "天气现象显示晴但外面在下雨", "expected_module": "实况", "desc": "天气现象"},
    {"query": "降水量0但外面明明在下", "expected_module": "实况", "desc": "降水偏差"},
    {"query": "南方35度湿热为啥比北方38度干热更难受", "expected_module": "实况", "desc": "体感对比"},
    {"query": "App显示25度但我温度计量的30度", "expected_module": "实况", "desc": "温度偏差-设备对比"},
    {"query": "紫外线指数不准", "expected_module": "实况", "desc": "紫外线偏差"},
    {"query": "实况数据一个小时没更新了", "expected_module": "实况", "desc": "数据时效"},

    # ===== 天气预警（8个）=====
    {"query": "暴雨预警迟了半小时", "expected_module": "天气预警", "desc": "预警延迟"},
    {"query": "没收到台风预警", "expected_module": "天气预警", "desc": "预警推送"},
    {"query": "预警解除了但App还显示", "expected_module": "天气预警", "desc": "预警解除"},
    {"query": "预警级别不准应该是橙色不是黄色", "expected_module": "天气预警", "desc": "预警级别"},
    {"query": "高温预警没收到推送", "expected_module": "天气预警", "desc": "预警推送-高温"},
    {"query": "雷电预警来得太突然", "expected_module": "天气预警", "desc": "预警时效"},
    {"query": "预警范围不准我不在预警区但收到了", "expected_module": "天气预警", "desc": "预警范围"},
    {"query": "大风预警发了但没那么大风", "expected_module": "天气预警", "desc": "预警准确性"},

    # ===== 逐天预报（6个）=====
    {"query": "明天预报不准差了好几度", "expected_module": "逐天预报", "desc": "预报偏差"},
    {"query": "说好的晴天怎么下雨了", "expected_module": "逐天预报", "desc": "预报偏差-晴转雨"},
    {"query": "7天预报后面几天不准", "expected_module": "逐天预报", "desc": "长期预报"},
    {"query": "日出日落时间不准", "expected_module": "逐天预报", "desc": "日出日落"},
    {"query": "昼夜温差预报差太多", "expected_module": "逐天预报", "desc": "温差预报"},
    {"query": "周末预报能不能准点", "expected_module": "逐天预报", "desc": "周末预报"},

    # ===== 逐时预报（5个）=====
    {"query": "逐时预报温度变化太假", "expected_module": "逐小时预报", "desc": "逐时温度"},
    {"query": "未来两小时预报不准", "expected_module": "逐小时预报", "desc": "短期预报"},
    {"query": "逐时降水概率90%但没下", "expected_module": "逐小时预报", "desc": "降水概率"},
    {"query": "逐时风速预报跟实际差很多", "expected_module": "逐小时预报", "desc": "逐时风速"},
    {"query": "逐时预报更新太慢", "expected_module": "逐小时预报", "desc": "更新频率"},

    # ===== 空气质量（4个）=====
    {"query": "雾霾好严重", "expected_module": "空气质量", "desc": "空气质量-霾"},
    {"query": "AQI不准", "expected_module": "空气质量", "desc": "AQI偏差"},
    {"query": "PM2.5数据跟其他App不一样", "expected_module": "空气质量", "desc": "PM2.5偏差"},
    {"query": "空气质量预报不准", "expected_module": "空气质量", "desc": "空气质量预报"},

    # ===== 生活指数（4个）=====
    {"query": "紫外线太强", "expected_module": "生活指数", "desc": "紫外线指数"},
    {"query": "穿衣指数不准", "expected_module": "生活指数", "desc": "穿衣指数"},
    {"query": "运动指数说适宜但外面在下雨", "expected_module": "生活指数", "desc": "运动指数"},
    {"query": "感冒指数准不准", "expected_module": "生活指数", "desc": "感冒指数"},

    # ===== 定位（3个）=====
    {"query": "定位不准", "expected_module": "定位", "desc": "定位偏差"},
    {"query": "GPS定位偏了好几百米", "expected_module": "定位", "desc": "GPS偏差"},
    {"query": "切换城市后天气没更新", "expected_module": "定位", "desc": "城市切换"},

    # ===== App体验（3个）=====
    {"query": "App闪退", "expected_module": "App体验", "desc": "闪退"},
    {"query": "Widget不更新", "expected_module": "App体验", "desc": "Widget"},
    {"query": "通知推送太多能不能关", "expected_module": "App体验", "desc": "推送设置"},

    # ===== 其他（2个）=====
    {"query": "雷达图看不懂", "expected_module": "格点可视化", "desc": "雷达解读"},
    {"query": "台风路径不准", "expected_module": "台风预报", "desc": "台风预报"},
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
