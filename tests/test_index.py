"""
生活指数测试
测试指数生产、查询、Function Calling 分析
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def test_index_query():
    """测试指数查询"""
    print("=" * 50)
    print("指数查询测试")
    print("=" * 50)

    from app.agent.index_functions import get_all_indices, get_index_data

    # 查询所有指数
    result = get_all_indices("海淀", "2026-07-17")
    print(f"\n海淀 2026-07-17 所有指数:")
    for name, data in result.items():
        print(f"  {name}: {data['level']} (分数{data['score']}) - {data['tip']}")

    # 查询单个指数
    result = get_index_data("海淀", "2026-07-17", "运动")
    print(f"\n运动指数详情: {result}")


async def test_index_rules():
    """测试指数规则查询"""
    print("\n" + "=" * 50)
    print("指数规则测试")
    print("=" * 50)

    from app.agent.index_functions import get_index_rules

    for index_type in ["穿衣", "运动", "中暑"]:
        rules = get_index_rules(index_type)
        print(f"\n{index_type}指数规则:")
        print(f"  描述: {rules.get('description', '无')}")
        print(f"  因素: {rules.get('factors', [])}")


async def test_index_fc():
    """测试 Function Calling 分析"""
    print("\n" + "=" * 50)
    print("指数 Function Calling 分析测试")
    print("=" * 50)

    from app.models.schemas import FeedbackRequest
    from app.agent.core import get_agent

    agent = get_agent()

    feedback = FeedbackRequest(
        feedback_id="IDX001",
        content="你们建议我穿长裤，这天都热死了，咋推荐的",
        location="朝阳",
        time="2026-07-17",
    )

    print(f"\n反馈: {feedback.content}")
    print(f"位置: {feedback.location}")
    print("\n分析中（Function Calling 2次 LLM 调用）...\n")

    result = await agent.analyze_index(feedback)

    print("分析结果:")
    print(f"  分析ID: {result.analysis_id}")
    print(f"  问题类型: {result.feedback_type}")
    print(f"  根因: {result.root_cause}")
    print(f"\n回复内容: {result.reply_content}")


async def main():
    print("🌤️ 生活指数测试\n")

    await test_index_query()
    await test_index_rules()
    # await test_index_fc()

    print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(main())
