#!/usr/bin/env python3
"""
MCP Server 功能测试
直接调用各工具验证是否正常
"""

import asyncio


async def test_query_weather():
    """测试天气查询"""
    from app.skills.weather import query_weather_data

    result = await query_weather_data("北京")
    print(f"✅ query_weather: {result.city_name} {result.temperature}℃ {result.weather_zh}")
    return result


async def test_query_alert():
    """测试预警查询"""
    from app.skills.alert import query_alert_data

    result = await query_alert_data("北京")
    print(f"✅ query_alert: has_alert={result.has_alert}, type={result.alert_type}")
    return result


async def test_search_knowledge():
    """测试知识检索"""
    from app.skills.knowledge import search_knowledge

    results = await search_knowledge("温度不准", top_k=2)
    print(f"✅ search_knowledge: {len(results)} 条结果")
    for r in results:
        print(f"   - [{r.score:.2f}] {r.content[:50]}...")
    return results


async def test_check_pipeline():
    """测试链路检查"""
    from app.skills.pipeline import check_pipeline

    result = await check_pipeline("北京")
    print(f"✅ check_pipeline: 数据源={result.data_source.status}, 存储={result.storage.status}")
    return result


async def test_calculate_feels_like():
    """测试体感计算"""
    from app.skills.feels_like import calculate_feels_like

    result = await calculate_feels_like(30.0, 59.0, 6.0)
    print(f"✅ calculate_feels_like: {result.feels_like}℃ {result.comfort}")
    return result


async def test_mcp_tools():
    """测试 MCP Server 的工具注册"""
    from app.mcp.server import mcp

    tools = [t.name for t in mcp._tool_manager._tools.values()]
    print(f"✅ MCP Server 注册了 {len(tools)} 个工具: {tools}")
    return tools


async def main():
    print("=" * 50)
    print("MCP Server 功能测试")
    print("=" * 50)
    print()

    # 测试工具注册
    await test_mcp_tools()
    print()

    # 测试各工具
    await test_query_weather()
    await test_query_alert()
    await test_search_knowledge()
    await test_check_pipeline()
    await test_calculate_feels_like()

    print()
    print("=" * 50)
    print("所有测试通过！MCP Server 功能正常。")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
