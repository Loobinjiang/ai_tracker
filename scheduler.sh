#!/bin/bash
# 用 cron 定时调度 AI Tracker
# 添加到 crontab 示例（每6小时运行一次）：
#   crontab -e
#   0 */6 * * * /path/to/ai_tracker/scheduler.sh >> /path/to/ai_tracker/logs/cron.log 2>&1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${SCRIPT_DIR}/.venv/bin/python"

# 如果没有虚拟环境，使用系统python3
if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始抓取..."
cd "$SCRIPT_DIR"
"$PYTHON" main.py --days 1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 抓取完成"
