#!/bin/bash
# =============================================
# 每日数据更新脚本
# 下载天气数据 + 生产指数
# 用法: bash scripts/daily_update.sh
# =============================================

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="/Users/skyfei/opt/miniconda3/envs/py311/bin/python"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/daily_$(date '+%Y%m%d').log"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

echo "========================================" | tee -a "$LOG_FILE"
echo "每日数据更新" | tee -a "$LOG_FILE"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

cd "$PROJECT_DIR"

# 1. 下载实况数据
echo "" | tee -a "$LOG_FILE"
echo "📌 1. 下载实况数据..." | tee -a "$LOG_FILE"
$PYTHON -m downloader.main --type condition 2>&1 | tee -a "$LOG_FILE"

# 2. 下载逐时预报
echo "" | tee -a "$LOG_FILE"
echo "📌 2. 下载逐时预报..." | tee -a "$LOG_FILE"
$PYTHON -m downloader.main --type hourly 2>&1 | tee -a "$LOG_FILE"

# 3. 下载逐天预报
echo "" | tee -a "$LOG_FILE"
echo "📌 3. 下载逐天预报..." | tee -a "$LOG_FILE"
$PYTHON -m downloader.main --type forecast 2>&1 | tee -a "$LOG_FILE"

# 4. 下载预警数据
echo "" | tee -a "$LOG_FILE"
echo "📌 4. 下载预警数据..." | tee -a "$LOG_FILE"
$PYTHON -m downloader.alert 2>&1 | tee -a "$LOG_FILE"

# 5. 生产生活指数
echo "" | tee -a "$LOG_FILE"
echo "📌 5. 生产生活指数..." | tee -a "$LOG_FILE"
$PYTHON -m downloader.index_producer 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "✅ 每日更新完成" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
