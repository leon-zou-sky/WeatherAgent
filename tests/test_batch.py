"""
批量分析测试
测试批量提交、进度查询、结果获取
"""

import asyncio
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE_URL = "http://localhost:8000"


def test_batch_analyze():
    """测试批量分析"""
    print("=" * 50)
    print("批量分析测试")
    print("=" * 50)

    # 准备测试数据
    feedbacks = [
        {"feedback_id": "BATCH001", "content": "我看一直阴天，什么时候下雨", "location": "朝阳"},
        {"feedback_id": "BATCH002", "content": "怎么雷雨预警了", "location": "北京"},
        {"feedback_id": "BATCH003", "content": "热死了，什么时候下雨啊", "location": "广州"},
    ]

    # 1. 提交批量任务
    print(f"\n1. 提交批量任务 ({len(feedbacks)} 条)")
    resp = httpx.post(f"{BASE_URL}/api/v1/agent/batch-analyze", json={"feedbacks": feedbacks}, timeout=60)
    data = resp.json()
    batch_id = data["data"]["batch_id"]
    print(f"   batch_id: {batch_id}")
    print(f"   total: {data['data']['total']}")
    print(f"   status: {data['data']['status']}")

    # 2. 轮询进度
    print("\n2. 查询进度...")
    for i in range(10):
        time.sleep(2)
        resp = httpx.get(f"{BASE_URL}/api/v1/agent/batch/{batch_id}", timeout=60)
        progress = resp.json()["data"]
        print(f"   [{i+1}] progress: {progress['progress']}, status: {progress['status']}")

        if progress["status"] == "completed":
            break

    # 3. 获取结果
    print("\n3. 获取结果")
    resp = httpx.get(f"{BASE_URL}/api/v1/agent/batch/{batch_id}/results", timeout=60)
    results = resp.json()["data"]

    print(f"   status: {results['status']}")
    print(f"   total: {results['total']}")
    print(f"   completed: {results['completed']}")
    print(f"   failed: {results['failed']}")

    print("\n   分析结果:")
    for r in results["results"]:
        if "error" in r:
            print(f"   - {r['feedback_id']}: ❌ {r['error']}")
        else:
            print(f"   - {r['analysis_id']}: {r.get('feedback_type', '未知')} - {r.get('root_cause', '未知')[:50]}...")


def main():
    print("🚀 批量分析测试\n")

    try:
        # 检查服务是否运行
        resp = httpx.get(f"{BASE_URL}/health", timeout=30)
        if resp.status_code != 200:
            print("❌ 服务未运行，请先启动: python main.py")
            return
    except Exception as e:
        print(f"❌ 无法连接服务: {e}")
        print("请先启动: python main.py")
        return

    test_batch_analyze()
    print("\n✅ 测试完成")


if __name__ == "__main__":
    main()
