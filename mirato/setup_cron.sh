#!/bin/bash
# Mirato自動化スクリプト cron登録スクリプト
# 実行方法: bash setup_cron.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(which python3)"
LOG_DIR="$SCRIPT_DIR/logs"

mkdir -p "$LOG_DIR"

MORNING_CMD="cd $SCRIPT_DIR && $PYTHON morning_report.py >> $LOG_DIR/morning_report.log 2>&1"
EVENING_CMD="cd $SCRIPT_DIR && $PYTHON evening_report.py >> $LOG_DIR/evening_report.log 2>&1"
COMMENT_CMD="cd $SCRIPT_DIR && $PYTHON comment_processor.py >> $LOG_DIR/comment_processor.log 2>&1"

# Remove existing Mirato cron entries, add new ones
(crontab -l 2>/dev/null | grep -v "mirato\|morning_report\|evening_report\|comment_processor" ; \
  echo "# Mirato自動化スクリプト"; \
  echo "0 9 * * 1-5 $MORNING_CMD"; \
  echo "0 18 * * 1-5 $EVENING_CMD"; \
  echo "*/30 * * * * $COMMENT_CMD" \
) | crontab -

echo "✅ cronジョブ登録完了"
echo ""
echo "登録内容："
crontab -l | grep -A5 "Mirato"
echo ""
echo "確認コマンド: crontab -l | grep -E 'morning|evening|comment'"
