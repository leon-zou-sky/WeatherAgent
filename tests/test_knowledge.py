"""
知识库检索测试
测试向量检索和关键词匹配
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.skills.knowledge import search_knowledge, _vector_search, _keyword_search


async def test_vector_search():
    """测试向量检索"""
    print("=" * 50)
    print("向量检索测试")
    print("=" * 50)

    cases = [
        ("温度不准", "温度相关"),
        ("又淋雨了", "降雨相关"),
        ("热死了", "体感温度/闷热"),
        ("没收到预警", "预警推送"),
        ("雾霾", "空气质量"),
        ("台风来了", "台风预报"),
        ("App闪退", "App体验"),
        ("紫外线太强了", "生活指数"),
    ]

    for query, desc in cases:
        results = _vector_search(query, top_k=2)
        print(f"\n查询: \"{query}\" ({desc})")
        if results:
            for r in results:
                print(f"  [{r.score:.2f}] {r.content}")
        else:
            print("  ❌ 无结果")


async def test_keyword_search():
    """测试关键词匹配"""
    print("\n" + "=" * 50)
    print("关键词匹配测试")
    print("=" * 50)

    cases = [
        ("温度比预报低", "精确关键词"),
        ("暴雨预警", "组合关键词"),
        ("空气质量", "模块名"),
    ]

    for query, desc in cases:
        results = _keyword_search(query, top_k=2)
        print(f"\n查询: \"{query}\" ({desc})")
        if results:
            for r in results:
                print(f"  [{r.score:.2f}] {r.content}")
        else:
            print("  ❌ 无结果")


async def test_search_knowledge():
    """测试完整检索接口（向量优先，关键词兜底）"""
    print("\n" + "=" * 50)
    print("完整检索接口测试 (search_knowledge)")
    print("=" * 50)

    cases = [
        "温度不准",
        "又淋雨了",
        "热死了",
        "没收到预警",
        "雾霾",
        "副高控制是什么意思",
    ]

    for query in cases:
        results = await search_knowledge(query, top_k=2)
        print(f"\n查询: \"{query}\" → {len(results)} 条结果")
        for r in results:
            print(f"  [{r.score:.2f}] {r.content}")
            print(f"    方案: {r.solution[:50]}...")


async def main():
    print("🔍 知识库检索测试\n")

    await test_vector_search()
    await test_keyword_search()
    await test_search_knowledge()

    print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(main())
