"""
数据源检查 + 链路检查 测试
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.skills.data_source import check_data_source
from app.skills.pipeline import check_pipeline


async def test_data_source():
    """测试数据源检查"""
    print("=" * 50)
    print("数据源检查测试")
    print("=" * 50)

    locations = ["海淀", "北京", "101010200", "不存在的城市"]
    for loc in locations:
        result = await check_data_source(loc)
        print(f"\n查询: \"{loc}\"")
        print(f"  状态: {result.status}")
        print(f"  质量: {result.data_quality}")
        print(f"  覆盖: {result.coverage}")
        print(f"  详情: {result.detail}")


async def test_pipeline():
    """测试链路检查"""
    print("\n" + "=" * 50)
    print("链路检查测试")
    print("=" * 50)

    locations = ["海淀", "不存在的城市"]
    for loc in locations:
        result = await check_pipeline(loc)
        print(f"\n查询: \"{loc}\"")
        print(f"  数据源: {result.data_source.status} - {result.data_source.detail}")
        print(f"  采集:   {result.collection.status} - {result.collection.detail}")
        print(f"  处理:   {result.processing.status} - {result.processing.detail}")
        print(f"  存储:   {result.storage.status} - {result.storage.detail}")
        print(f"  发布:   {result.publishing.status} - {result.publishing.detail}")


async def main():
    print("🔍 数据源 + 链路检查测试\n")

    await test_data_source()
    await test_pipeline()

    print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(main())
