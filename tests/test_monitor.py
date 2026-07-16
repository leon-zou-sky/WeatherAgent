"""
内部监控报告
检查数据延迟、数据完整性、各模块状态
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.skills.db import get_session


def check_data_delay() -> list[dict]:
    """检查各表数据延迟"""
    session = get_session()
    results = []

    tables = [
        ("weather_cn", "city_id", "update_time", "实况数据", "10分钟"),
        ("weather_hh", "city_id", "update_time", "逐时预报", "1小时"),
        ("weather_ff", "city_id", "update_time", "逐天预报", "1天"),
        ("alert_data", "city_id", "update_time", "预警数据", "实时"),
    ]

    try:
        for table, id_col, time_col, desc, interval in tables:
            row = session.execute(text(f"""
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT {id_col}) as city_count,
                       MAX({time_col}) as latest
                FROM {table}
            """)).fetchone()

            results.append({
                "table": table,
                "desc": desc,
                "total": row[0],
                "city_count": row[1],
                "latest": str(row[2]),
                "expected_interval": interval,
            })
    finally:
        session.close()

    return results


def check_data_completeness() -> list[dict]:
    """检查数据完整性（关键字段是否为空）"""
    session = get_session()
    results = []

    checks = [
        ("weather_cn", "temp", "温度"),
        ("weather_cn", "humidity", "湿度"),
        ("weather_cn", "wspd", "风速"),
        ("weather_hh", "temp", "温度"),
        ("weather_hh", "humidity", "湿度"),
        ("weather_ff", "temp_high", "最高温"),
        ("weather_ff", "temp_low", "最低温"),
    ]

    try:
        for table, field, desc in checks:
            row = session.execute(text(f"""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN {field} IS NULL THEN 1 ELSE 0 END) as null_count
                FROM {table}
            """)).fetchone()

            total = row[0]
            null_count = row[1] or 0
            null_rate = null_count / total if total > 0 else 0

            results.append({
                "table": table,
                "field": desc,
                "total": total,
                "null_count": null_count,
                "null_rate": f"{null_rate:.2%}",
                "status": "正常" if null_rate < 0.05 else "异常",
            })
    finally:
        session.close()

    return results


def check_city_coverage() -> dict:
    """检查城市覆盖情况"""
    session = get_session()
    try:
        # 城市表总数
        city_total = session.execute(text("SELECT COUNT(*) FROM city")).fetchone()[0]

        # 各表覆盖的城市数
        cn_cities = session.execute(text("SELECT COUNT(DISTINCT city_id) FROM weather_cn")).fetchone()[0]
        hh_cities = session.execute(text("SELECT COUNT(DISTINCT city_id) FROM weather_hh")).fetchone()[0]
        ff_cities = session.execute(text("SELECT COUNT(DISTINCT city_id) FROM weather_ff")).fetchone()[0]
        alert_cities = session.execute(text("SELECT COUNT(DISTINCT city_id) FROM alert_data")).fetchone()[0]

        return {
            "city_total": city_total,
            "weather_cn": cn_cities,
            "weather_hh": hh_cities,
            "weather_ff": ff_cities,
            "alert_data": alert_cities,
        }
    finally:
        session.close()


def check_alert_status() -> dict:
    """检查预警状态"""
    session = get_session()
    try:
        # 当前生效预警数
        active = session.execute(text("""
            SELECT COUNT(*) FROM alert_data WHERE end_time >= NOW()
        """)).fetchone()[0]

        # 预警类型分布
        type_dist = session.execute(text("""
            SELECT alert_type, COUNT(*) as cnt
            FROM alert_data
            WHERE end_time >= NOW()
            GROUP BY alert_type
            ORDER BY cnt DESC
        """)).fetchall()

        # 预警级别分布
        level_dist = session.execute(text("""
            SELECT alert_level, COUNT(*) as cnt
            FROM alert_data
            WHERE end_time >= NOW()
            GROUP BY alert_level
            ORDER BY cnt DESC
        """)).fetchall()

        return {
            "active_count": active,
            "type_distribution": {r[0]: r[1] for r in type_dist},
            "level_distribution": {r[0]: r[1] for r in level_dist},
        }
    finally:
        session.close()


async def generate_report():
    """生成监控报告"""
    print("=" * 60)
    print(f"📊 内部监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 数据延迟检查
    print("\n📌 一、数据延迟检查")
    print("-" * 40)
    delays = check_data_delay()
    for d in delays:
        print(f"  {d['desc']:10} ({d['table']:12}): {d['total']:6}条, "
              f"{d['city_count']:3}个城市, 最新: {d['latest']}")

    # 2. 数据完整性检查
    print("\n📌 二、数据完整性检查")
    print("-" * 40)
    completeness = check_data_completeness()
    for c in completeness:
        status_icon = "✅" if c["status"] == "正常" else "❌"
        print(f"  {status_icon} {c['table']:12} {c['field']:6}: "
              f"总计{c['total']:6}, 空值{c['null_count']:4}, 空值率{c['null_rate']}")

    # 3. 城市覆盖检查
    print("\n📌 三、城市覆盖检查")
    print("-" * 40)
    coverage = check_city_coverage()
    print(f"  城市表总数: {coverage['city_total']}")
    print(f"  实况覆盖:   {coverage['weather_cn']}")
    print(f"  逐时覆盖:   {coverage['weather_hh']}")
    print(f"  逐天覆盖:   {coverage['weather_ff']}")
    print(f"  预警覆盖:   {coverage['alert_data']}")

    # 4. 预警状态
    print("\n📌 四、当前预警状态")
    print("-" * 40)
    alert = check_alert_status()
    print(f"  生效预警数: {alert['active_count']}")
    if alert["type_distribution"]:
        print("  类型分布:")
        for t, cnt in alert["type_distribution"].items():
            print(f"    {t}: {cnt}条")
    if alert["level_distribution"]:
        print("  级别分布:")
        for l, cnt in alert["level_distribution"].items():
            print(f"    {l}: {cnt}条")

    # 5. 汇总
    print("\n📌 五、健康状态汇总")
    print("-" * 40)

    issues = []
    for c in completeness:
        if c["status"] != "正常":
            issues.append(f"{c['table']}.{c['field']} 空值率过高")

    if not issues:
        print("  ✅ 全部正常，无异常")
    else:
        print("  ❌ 发现异常:")
        for issue in issues:
            print(f"    - {issue}")

    print("\n" + "=" * 60)
    print("报告生成完成")


if __name__ == "__main__":
    asyncio.run(generate_report())
