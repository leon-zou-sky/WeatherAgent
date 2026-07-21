#!/bin/bash
# =============================================
# RAG 检索质量评估脚本
# 用法: bash scripts/eval_rag.sh
# =============================================

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="/Users/skyfei/opt/miniconda3/envs/py311/bin/python"
REPORT_DIR="$PROJECT_DIR/reports"
LOG_FILE="$REPORT_DIR/eval.log"

# 阈值
THRESHOLD=${1:-90}

# 确保报告目录存在
mkdir -p "$REPORT_DIR"

echo "========================================"
echo "RAG 检索质量评估"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "阈值: ${THRESHOLD}%"
echo "========================================"

# 运行评估
cd "$PROJECT_DIR"
$PYTHON tests/eval_rag.py --report --threshold "$THRESHOLD" 2>&1 | tee -a "$LOG_FILE"

# 检查退出码
if [ $? -eq 1 ]; then
    echo ""
    echo "⚠️ 告警：命中率低于阈值 ${THRESHOLD}%"
    # 这里可以加告警逻辑，比如发钉钉/邮件
    # curl -X POST "https://oapi.dingtalk.com/robot/send?access_token=xxx" \
    #   -H 'Content-Type: application/json' \
    #   -d "{\"msgtype\": \"text\", \"text\": {\"content\": \"RAG 评估告警: 命中率低于 ${THRESHOLD}%\"}}"
fi

echo ""
echo "评估完成，报告已保存到 $REPORT_DIR"
