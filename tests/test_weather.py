"""
气象数据查询测试
测试实况、逐时、逐天数据查询
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.skills.weather import query_weather_data, query_hourly_data, query_forecast_data


async def test_condition():
    """测试实况数据"""
    print("=" * 50)
    print("实况数据测试")
    print("=" * 50)

    locations = ["海淀", "北京", "101010200"]
    for loc in locations:
        result = await query_weather_data(loc)
        print(f"\n查询: \"{loc}\"")
        print(f"  城市: {result.city_name} ({result.city_id})")
        print(f"  温度: {result.temperature}℃")
        print(f"  湿度: {result.humidity}%")
        print(f"  风速: {result.wind_speed}m/s {result.wind_dir}")
        print(f"  更新: {result.update_time}")


async def test_hourly():
    """测试逐时预报"""
    print("\n" + "=" * 50)
    print("逐时预报测试")
    print("=" * 50)

    results = await query_hourly_data("海淀", hours=6)
    print(f"\n查询: \"海淀\" → {len(results)} 条")
    for r in results:
        print(f"  {r.predict_time}: {r.temperature}℃ 湿度{r.humidity}%")


async def test_forecast():
    """测试逐天预报"""
    print("\n" + "=" * 50)
    print("逐天预报测试")
    print("=" * 50)

    results = await query_forecast_data("海淀", days=5)
    print(f"\n查询: \"海淀\" → {len(results)} 条")
    for r in results:
        print(f"  {r.predict_date}: {r.temp_low}~{r.temp_high}℃ "
              f"白天{r.weather_day} 夜间{r.weather_night}")


async def main():
    print("🌤️ 气象数据查询测试\n")

    await test_condition()
    await test_hourly()
    await test_forecast()

    print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(main())
