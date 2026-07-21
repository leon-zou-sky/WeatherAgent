"""
RAG 检索质量评估脚本
支持：单次评估、定时评估、报告输出、告警

用法:
    python tests/eval_rag.py                  # 运行评估
    python tests/eval_rag.py --report         # 生成报告文件
    python tests/eval_rag.py --threshold 85   # 自定义阈值
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.skills.knowledge import search_knowledge

# 配置
DATASET_PATH = Path(__file__).resolve().parent / "test_dataset.json"
REPORT_DIR = Path(__file__).resolve().parent.parent / "reports"
DEFAULT_THRESHOLD = 90  # 默认命中率阈值


def load_dataset() -> list[dict]:
    """加载测试集"""
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


async def evaluate_single(query: str, expected_module: str, expected_tags: str) -> dict:
    """评估单条"""
    results = await search_knowledge(query, top_k=3)

    retrieved_modules = []
    retrieved_tags = []
    for r in results:
        # 从 content 提取 module: "[实况][数据偏差] xxx"
        if r.content.startswith("["):
            parts = r.content.split("]")
            if len(parts) >= 2:
                module = parts[0].lstrip("[")
                retrieved_modules.append(module)
        # 从 solution 提取 tags
        if r.solution:
            retrieved_tags.append(r.solution[:20])

    top1_hit = len(retrieved_modules) > 0 and retrieved_modules[0] == expected_module
    top3_hit = expected_module in retrieved_modules

    return {
        "query": query,
        "expected_module": expected_module,
        "expected_tags": expected_tags,
        "retrieved_modules": retrieved_modules,
        "top1_hit": top1_hit,
        "top3_hit": top3_hit,
    }


async def run_evaluation() -> dict:
    """运行完整评估"""
    dataset = load_dataset()
    results = []
    badcases = []

    for case in dataset:
        result = await evaluate_single(
            case["query"],
            case.get("expected_module", ""),
            case.get("expected_tags", ""),
        )
        results.append(result)

        if not result["top3_hit"]:
            badcases.append(result)

    # 统计
    total = len(results)
    top1_hits = sum(1 for r in results if r["top1_hit"])
    top3_hits = sum(1 for r in results if r["top3_hit"])

    # 按模块统计
    module_stats = {}
    for r in results:
        m = r["expected_module"]
        if m not in module_stats:
            module_stats[m] = {"total": 0, "top1_hit": 0, "top3_hit": 0}
        module_stats[m]["total"] += 1
        if r["top1_hit"]:
            module_stats[m]["top1_hit"] += 1
        if r["top3_hit"]:
            module_stats[m]["top3_hit"] += 1

    return {
        "timestamp": datetime.now().isoformat(),
        "total": total,
        "top1_hits": top1_hits,
        "top3_hits": top3_hits,
        "top1_rate": top1_hits / total if total > 0 else 0,
        "top3_rate": top3_hits / total if total > 0 else 0,
        "module_stats": module_stats,
        "badcases": badcases,
        "results": results,
    }


def generate_report(report: dict, threshold: float) -> str:
    """生成文本报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("📊 RAG 检索质量评估报告")
    lines.append("=" * 60)
    lines.append(f"评估时间: {report['timestamp']}")
    lines.append(f"测试用例: {report['total']} 个")
    lines.append(f"命中率阈值: {threshold}%")
    lines.append("")

    # 总体结果
    top1 = report['top1_rate'] * 100
    top3 = report['top3_rate'] * 100
    status1 = "✅" if top1 >= threshold else "⚠️"
    status3 = "✅" if top3 >= threshold else "⚠️"

    lines.append("📌 总体结果")
    lines.append("-" * 40)
    lines.append(f"  Top-1 命中率: {top1:.1f}% {status1} ({report['top1_hits']}/{report['total']})")
    lines.append(f"  Top-3 命中率: {top3:.1f}% {status3} ({report['top3_hits']}/{report['total']})")
    lines.append("")

    # 分模块统计
    lines.append("📌 分模块统计")
    lines.append("-" * 40)
    for module, stats in report["module_stats"].items():
        m_top1 = stats["top1_hit"] / stats["total"] * 100 if stats["total"] > 0 else 0
        m_top3 = stats["top3_hit"] / stats["total"] * 100 if stats["total"] > 0 else 0
        lines.append(f"  {module:12} Top-1: {m_top1:5.1f}%  Top-3: {m_top3:5.1f}%  ({stats['total']}条)")
    lines.append("")

    # Badcase
    if report["badcases"]:
        lines.append(f"❌ Badcase ({len(report['badcases'])} 条)")
        lines.append("-" * 40)
        for bc in report["badcases"][:10]:  # 最多显示 10 条
            lines.append(f"  查询: \"{bc['query']}\"")
            lines.append(f"    期望: {bc['expected_module']}")
            lines.append(f"    检索: {bc['retrieved_modules']}")
            lines.append("")
    else:
        lines.append("✅ 无 Badcase")
        lines.append("")

    # 告警
    if top1 < threshold or top3 < threshold:
        lines.append("⚠️ 告警：命中率低于阈值！")
        lines.append(f"  Top-1: {top1:.1f}% (阈值 {threshold}%)")
        lines.append(f"  Top-3: {top3:.1f}% (阈值 {threshold}%)")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def save_report(report_text: str, report: dict):
    """保存报告文件"""
    REPORT_DIR.mkdir(exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_path = REPORT_DIR / f"eval_report_{date_str}.txt"
    json_path = REPORT_DIR / f"eval_report_{date_str}.json"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    # 保存 JSON（不含完整 results，太大）
    summary = {k: v for k, v in report.items() if k != "results"}
    summary["badcase_count"] = len(report["badcases"])
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"📄 报告已保存: {report_path}")
    print(f"📄 JSON 已保存: {json_path}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="RAG 检索质量评估")
    parser.add_argument("--report", action="store_true", help="生成报告文件")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="命中率阈值")
    args = parser.parse_args()

    print("🔍 开始评估...\n")
    report = await run_evaluation()
    report_text = generate_report(report, args.threshold)

    print(report_text)

    if args.report:
        save_report(report_text, report)

    # 返回码：命中率低于阈值返回 1
    if report["top1_rate"] * 100 < args.threshold:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
