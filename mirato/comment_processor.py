#!/usr/bin/env python3
"""
Notionコメント処理スクリプト
30分ごとに実行：
  1. 親ページの子ページ一覧を取得
  2. 今日の日付を含むページを特定
  3. 未処理コメントをClaude APIで処理
  4. CEO（月城凛）として各部署への指示を生成
  5. 結果をNotionに記録
  6. 処理済みコメントIDをローカルに保存
"""

import sys
import json
import logging
import os
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

import anthropic

from config import (
    PARENT_PAGE_ID,
    CEO_NAME,
    CLAUDE_MODEL,
    PROCESSED_COMMENTS_FILE,
    ANTHROPIC_API_KEY,
    NOTION_API_KEY,
)
from notion_helper import (
    get_child_pages,
    get_comments,
    append_blocks_to_page,
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
            os.path.join(os.path.dirname(__file__), "logs", "comment_processor.log"),
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)


def load_processed_ids() -> set:
    if not os.path.exists(PROCESSED_COMMENTS_FILE):
        return set()
    with open(PROCESSED_COMMENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("processed_ids", []))


def save_processed_ids(ids: set):
    with open(PROCESSED_COMMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"processed_ids": list(ids)}, f, ensure_ascii=False, indent=2)


def extract_comment_text(comment: dict) -> str:
    parts = []
    for rt in comment.get("rich_text", []):
        parts.append(rt.get("plain_text", ""))
    return "".join(parts)


def find_todays_pages(child_pages: list, today: date) -> list:
    """Find pages whose title contains today's date (e.g. '4月24日')."""
    date_pattern = f"{today.month}月{today.day}日"
    matched = []
    for page in child_pages:
        if date_pattern in page["title"]:
            matched.append(page)
            logger.info(f"今日の日付に一致するページ：{page['title']} (ID: {page['id']})")
    return matched


def generate_ceo_instructions(comment_texts: list, page_title: str) -> str:
    """Call Claude API to generate CEO instructions for the given comments."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    comments_str = "\n".join(
        f"- コメント{i+1}：{text}" for i, text in enumerate(comment_texts)
    )

    prompt = f"""あなたはMirato株式会社のCEO「{CEO_NAME}」です。
以下は「{page_title}」ページに寄せられた部署からのコメント・報告です。

【受信コメント】
{comments_str}

上記のコメントを踏まえて、CEOとして各部署への具体的な指示・フィードバックを生成してください。

出力形式：
- 簡潔で明確な指示
- 部署名が分かる場合は部署別に整理
- 優先度・期限を明示
- 励ましや前向きなメッセージも含める
- 300〜500文字程度でまとめる"""

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def process_page_comments(page: dict, processed_ids: set) -> tuple[int, set]:
    """Process new comments on a page. Returns (count_processed, updated_ids)."""
    page_id = page["id"]
    page_title = page["title"]

    comments = get_comments(page_id)
    new_comments = [c for c in comments if c["id"] not in processed_ids]

    if not new_comments:
        logger.info(f"新しいコメントなし：{page_title}")
        return 0, processed_ids

    logger.info(f"{len(new_comments)}件の新しいコメントを処理：{page_title}")

    comment_texts = []
    for c in new_comments:
        text = extract_comment_text(c)
        if text.strip():
            comment_texts.append(text)

    if not comment_texts:
        for c in new_comments:
            processed_ids.add(c["id"])
        return 0, processed_ids

    try:
        instructions = generate_ceo_instructions(comment_texts, page_title)
        logger.info("Claude APIによる指示生成成功")
    except Exception as e:
        logger.error(f"Claude API呼び出し失敗：{e}")
        return 0, processed_ids

    now_str = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")
    response_blocks = [
        divider_block(),
        heading2_block(f"🤖 CEO（{CEO_NAME}）からの指示 ─ {now_str}"),
        text_block(f"対象コメント数：{len(comment_texts)}件"),
        divider_block(),
    ]
    for line in instructions.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") or stripped.startswith("・"):
            response_blocks.append(bullet_block(stripped.lstrip("- ").lstrip("・").strip()))
        else:
            response_blocks.append(text_block(stripped))
    response_blocks.append(divider_block())

    try:
        append_blocks_to_page(page_id, response_blocks)
        logger.info(f"Notionへの指示記録完了：{page_title}")
    except Exception as e:
        logger.error(f"Notion書き込み失敗：{e}")
        return 0, processed_ids

    for c in new_comments:
        processed_ids.add(c["id"])

    return len(comment_texts), processed_ids


def run():
    if not NOTION_API_KEY:
        logger.error("NOTION_API_KEY が設定されていません。環境変数または .env ファイルを確認してください。")
        sys.exit(1)
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY が設定されていません。環境変数または .env ファイルを確認してください。")
        sys.exit(1)

    today = date.today()
    logger.info(f"コメント処理開始：{today.isoformat()}")

    processed_ids = load_processed_ids()
    logger.info(f"処理済みコメントID数：{len(processed_ids)}")

    try:
        child_pages = get_child_pages(PARENT_PAGE_ID)
        logger.info(f"子ページ取得：{len(child_pages)}件")
    except Exception as e:
        logger.error(f"子ページ取得失敗：{e}")
        sys.exit(1)

    todays_pages = find_todays_pages(child_pages, today)

    if not todays_pages:
        logger.info("今日の日付を含むページが見つかりませんでした")
        print("ℹ️  今日の日付を含むページが見つかりませんでした")
        return

    total_processed = 0
    for page in todays_pages:
        count, processed_ids = process_page_comments(page, processed_ids)
        total_processed += count

    save_processed_ids(processed_ids)
    logger.info(f"コメント処理完了：{total_processed}件処理、処理済みID保存完了")
    print(f"✅ コメント処理完了：{total_processed}件を処理しました")


if __name__ == "__main__":
    run()
