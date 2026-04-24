#!/usr/bin/env python3
"""
終礼レポート自動作成スクリプト
毎日18時に実行：Notionページ作成 → カレンダーDB登録
"""

import sys
import logging
from datetime import date

sys.path.insert(0, __import__("os").path.dirname(__file__))

from config import CALENDAR_DB_ID, NOTION_API_KEY
from notion_helper import (
    create_page_under_parent,
    create_calendar_entry,
    heading2_block,
    text_block,
    bullet_block,
    divider_block,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            __import__("os").path.join(
                __import__("os").path.dirname(__file__), "logs", "evening_report.log"
            ),
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)


def build_evening_blocks(today: date) -> list:
    weekdays_ja = ["月", "火", "水", "木", "金", "土", "日"]
    weekday = weekdays_ja[today.weekday()]
    date_label = f"{today.year}年{today.month}月{today.day}日（{weekday}）"

    return [
        heading2_block("📋 終礼レポート"),
        text_block(f"日付：{date_label}"),
        text_block(f"終了時刻：18:00"),
        divider_block(),
        heading2_block("1. 本日の成果・達成事項"),
        bullet_block("完了したタスク・案件を記入してください"),
        bullet_block("数値目標の達成状況"),
        divider_block(),
        heading2_block("2. 課題・未解決事項"),
        bullet_block("本日解決できなかった課題"),
        bullet_block("翌日への申し送り事項"),
        divider_block(),
        heading2_block("3. 明日の予定・準備事項"),
        bullet_block("明日の主要タスク"),
        bullet_block("事前準備が必要な事項"),
        divider_block(),
        heading2_block("4. 気づき・改善提案"),
        bullet_block("業務上の気づき・改善点"),
        bullet_block("チームへの共有事項"),
        divider_block(),
        heading2_block("5. CEO（月城凛）からの総括コメント"),
        text_block("※ コメント欄に指示を入力してください。自動処理されます。"),
        divider_block(),
        text_block("✅ 終礼レポートを自動作成しました。各自、本日の振り返りを入力してください。"),
    ]


def run():
    if not NOTION_API_KEY:
        logger.error("NOTION_API_KEY が設定されていません。環境変数または .env ファイルを確認してください。")
        sys.exit(1)

    today = date.today()
    month = today.month
    day = today.day
    title = f"終礼レポート｜{month}月{day}日"
    logger.info(f"終礼レポート作成開始：{title}")

    try:
        page = create_page_under_parent(title, build_evening_blocks(today))
        page_id = page["id"]
        page_url = page.get("url", "")
        logger.info(f"Notionページ作成成功：{page_id}")
        logger.info(f"URL：{page_url}")
    except Exception as e:
        logger.error(f"Notionページ作成失敗：{e}")
        sys.exit(1)

    try:
        calendar_title = f"終礼｜{month}月{day}日"
        create_calendar_entry(CALENDAR_DB_ID, calendar_title, today)
        logger.info(f"カレンダーDB登録成功：{calendar_title}")
    except Exception as e:
        logger.warning(f"カレンダーDB登録失敗（ページ作成は成功）：{e}")

    logger.info("終礼レポート作成完了")
    print(f"✅ 終礼レポート作成完了：{title}")
    print(f"   Notion URL: {page_url}")


if __name__ == "__main__":
    run()
