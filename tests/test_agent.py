"""
Agent 分析流程测试
测试完整的负反馈分析流程
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.schemas import FeedbackRequest
from app.agent.core import get_agent


async def test_analyze():
    """测试单条反馈分析"""
    print("=" * 50)
    print("Agent 分析流程测试")
    print("=" * 50)

    agent = get_agent()

    feedback = FeedbackRequest(
        feedback_id="TEST001",
        content="朝阳早上感觉挺凉快，怎么就高温预警了",
        location="朝阳",
        time="2026-07-16",
        user_id="U001",
        source="APP",
    )

    print(f"\n反馈: {feedback.content}")
    print(f"位置: {feedback.location}")
    print(f"时间: {feedback.time}")
    print("\n分析中...\n")

    result = await agent.analyze(feedback)

    print("分析结果:")
    print(f"  分析ID: {result.analysis_id}")
    print(f"  问题类型: {result.feedback_type}")
    print(f"  问题定位: {result.problem_location}")
    print(f"  根因: {result.root_cause}")
    print(f"\n实况数据:")
    print(f"  温度: {result.actual_data.temperature}℃")
    print(f"  湿度: {result.actual_data.humidity}%")
    print(f"  风速: {result.actual_data.wind_speed}m/s")
    print(f"\n体感分析:")
    if result.feels_like:
        print(f"  体感温度: {result.feels_like.feels_like}℃")
        print(f"  舒适度: {result.feels_like.comfort}")
        print(f"  说明: {result.feels_like.description}")
    print(f"\n预警信息:")
    if result.alert_data:
        print(f"  有预警: {result.alert_data.alert_type} {result.alert_data.alert_level}")
        print(f"  时间: {result.alert_data.alert_time}")
        if result.alert_data.detail:
            print(f"  详情: {result.alert_data.detail[:80]}...")
    else:
        print(f"  无生效预警")
    print(f"\n气象解释: {result.meteorological_explanation}")
    print(f"\n建议: {result.suggestion}")
    print(f"\n回复内容: {result.reply_content}")


async def main():
    print("🤖 Agent 分析流程测试\n")
    await test_analyze()
    print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(main())
