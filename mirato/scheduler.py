#!/usr/bin/env python3
"""
Mirato自動化スケジューラー（常駐プロセス版）
crontab が利用できない環境での代替手段。

実行方法:
  python3 scheduler.py &         # バックグラウンド実行
  nohup python3 scheduler.py &   # セッション終了後も継続

スケジュール:
  - 平日 09:00 → 朝礼レポート作成
  - 平日 18:00 → 終礼レポート作成
  - 毎30分       → Notionコメント処理
"""

import os
import sys
import logging
import schedule
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(LOG_DIR, "scheduler.log"), encoding="utf-8"
        ),
    ],
)
logger = logging.getLogger(__name__)


def run_morning_report():
    logger.info("=== 朝礼レポート実行開始 ===")
    try:
        import morning_report
        morning_report.run()
    except Exception as e:
        logger.error(f"朝礼レポートエラー：{e}")


def run_evening_report():
    logger.info("=== 終礼レポート実行開始 ===")
    try:
        import evening_report
        evening_report.run()
    except Exception as e:
        logger.error(f"終礼レポートエラー：{e}")


def run_comment_processor():
    logger.info("=== コメント処理実行開始 ===")
    try:
        import comment_processor
        comment_processor.run()
    except Exception as e:
        logger.error(f"コメント処理エラー：{e}")


def is_weekday() -> bool:
    return datetime.now().weekday() < 5  # 月〜金


def scheduled_morning():
    if is_weekday():
        run_morning_report()
    else:
        logger.info("土日のため朝礼レポートをスキップ")


def scheduled_evening():
    if is_weekday():
        run_evening_report()
    else:
        logger.info("土日のため終礼レポートをスキップ")


def main():
    logger.info("Miratorスケジューラー起動")
    logger.info(f"PID: {os.getpid()}")

    schedule.every().day.at("09:00").do(scheduled_morning)
    schedule.every().day.at("18:00").do(scheduled_evening)
    schedule.every(30).minutes.do(run_comment_processor)

    logger.info("スケジュール登録完了:")
    logger.info("  朝礼レポート  : 平日 09:00")
    logger.info("  終礼レポート  : 平日 18:00")
    logger.info("  コメント処理  : 30分ごと")

    # 起動時にコメント処理を一度実行
    run_comment_processor()

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
