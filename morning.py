#!/usr/bin/env python3
"""
朝の秘書アシスタント
「おはよう」と入力すると、以下を表示します:
  ① Googleカレンダーの今日の予定
  ② 今日のタスク一覧
  ③ 優先順位
  ④ LINE集客の投稿ネタ3つ
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ────────────────────────────────────────────
# 設定
# ────────────────────────────────────────────
TASKS_FILE = Path(__file__).parent / "tasks.json"
TEMPLATE_FILE = Path(__file__).parent / "template.md"
JST = timezone(timedelta(hours=9))


# ────────────────────────────────────────────
# ① Googleカレンダー取得
# ────────────────────────────────────────────
def fetch_calendar_events() -> list[dict]:
    """
    Google Calendar API で今日の予定を取得します。
    初回のみブラウザでGoogleログインが必要です（OAuth2）。
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds_path = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
        token_path = Path(__file__).parent / "token.json"
        scopes = ["https://www.googleapis.com/auth/calendar.readonly"]

        credentials = None
        if token_path.exists():
            credentials = Credentials.from_authorized_user_file(str(token_path), scopes)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, scopes)
                print("\n【初回認証】以下のURLをブラウザで開いてください：")
                flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
                auth_url, _ = flow.authorization_url(prompt="consent")
                print(f"\n{auth_url}\n")
                code = input("ブラウザに表示された認証コードを貼り付けてください: ").strip()
                flow.fetch_token(code=code)
                credentials = flow.credentials
            token_path.write_text(credentials.to_json())

        service = build("calendar", "v3", credentials=credentials)

        now = datetime.now(JST)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        day_end = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

        result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=day_start,
                timeMax=day_end,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return result.get("items", [])

    except ImportError:
        return []
    except FileNotFoundError:
        return []
    except Exception as e:  # noqa: BLE001
        print(f"  [カレンダー取得エラー: {e}]")
        return []


def format_calendar(events: list[dict]) -> str:
    if not events:
        return "  予定なし（または未連携）"

    lines = []
    for ev in events:
        start = ev.get("start", {})
        time_str = start.get("dateTime") or start.get("date", "")
        if "T" in time_str:
            dt = datetime.fromisoformat(time_str).astimezone(JST)
            time_label = dt.strftime("%H:%M")
        else:
            time_label = "終日"
        summary = ev.get("summary", "（タイトルなし）")
        lines.append(f"  {time_label}  {summary}")
    return "\n".join(lines)


# ────────────────────────────────────────────
# ② タスク一覧 + ③ 優先順位
# ────────────────────────────────────────────
def load_tasks() -> list[dict]:
    if not TASKS_FILE.exists():
        return []
    with TASKS_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def format_tasks(tasks: list[dict]) -> str:
    today_str = datetime.now(JST).strftime("%Y-%m-%d")
    today_tasks = [
        t for t in tasks
        if t.get("date") == today_str or t.get("date") == "everyday"
    ]
    if not today_tasks:
        return "  タスクなし"
    lines = []
    for i, t in enumerate(today_tasks, 1):
        done = "✅" if t.get("done") else "◻️"
        lines.append(f"  {done} {i}. {t['title']}")
    return "\n".join(lines)


def format_priority(tasks: list[dict]) -> str:
    today_str = datetime.now(JST).strftime("%Y-%m-%d")
    today_tasks = [
        t for t in tasks
        if (t.get("date") == today_str or t.get("date") == "everyday")
        and not t.get("done")
    ]
    if not today_tasks:
        return "  すべて完了！"

    # priority フィールドで並び替え（high > medium > low）
    order = {"high": 0, "medium": 1, "low": 2}
    sorted_tasks = sorted(today_tasks, key=lambda x: order.get(x.get("priority", "medium"), 1))
    priority_label = {"high": "🔴 高", "medium": "🟡 中", "low": "🟢 低"}

    lines = []
    for t in sorted_tasks:
        label = priority_label.get(t.get("priority", "medium"), "🟡 中")
        lines.append(f"  {label}  {t['title']}")
    return "\n".join(lines)


# ────────────────────────────────────────────
# ④ LINE集客の投稿ネタ（Claude API）
# ────────────────────────────────────────────
def generate_line_ideas() -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return (
            "  ※ ANTHROPIC_API_KEY が未設定のため自動生成できません。\n"
            "    .env に ANTHROPIC_API_KEY を設定してください。"
        )

    try:
        import anthropic

        template = TEMPLATE_FILE.read_text(encoding="utf-8") if TEMPLATE_FILE.exists() else ""
        today_str = datetime.now(JST).strftime("%Y年%m月%d日")

        prompt = f"""あなたはLINE集客コンテンツの専門家です。
以下のテンプレートと条件に従い、今日（{today_str}）のLINE配信ネタを3つ考えてください。

【コンテンツテンプレート】
{template}

【条件】
- 読者に行動を促す共感ベースの内容
- 専門用語を避けシンプルに
- 各ネタは「タイトル」と「一言説明（30文字以内）」だけを出力

【出力形式（厳守）】
ネタ1: タイトル｜一言説明
ネタ2: タイトル｜一言説明
ネタ3: タイトル｜一言説明
"""

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        lines = [f"  {line}" for line in raw.splitlines() if line.strip()]
        return "\n".join(lines)

    except ImportError:
        return "  ※ anthropic パッケージが未インストールです。pip install anthropic を実行してください。"
    except Exception as e:  # noqa: BLE001
        return f"  ※ アイデア生成エラー: {e}"


# ────────────────────────────────────────────
# メイン表示
# ────────────────────────────────────────────
DIVIDER = "─" * 44


def show_morning_report() -> None:
    now = datetime.now(JST)
    date_str = now.strftime("%Y年%m月%d日（%A）")
    # 曜日を日本語化
    weekday_ja = ["月", "火", "水", "木", "金", "土", "日"]
    date_str = now.strftime("%Y年%m月%d日（") + weekday_ja[now.weekday()] + "）"

    print()
    print(f"  おはようございます！ {date_str}")
    print(DIVIDER)

    # ① カレンダー
    print("① 今日のGoogleカレンダー")
    events = fetch_calendar_events()
    print(format_calendar(events))
    print(DIVIDER)

    # ② タスク
    print("② 今日のタスク一覧")
    tasks = load_tasks()
    print(format_tasks(tasks))
    print(DIVIDER)

    # ③ 優先順位
    print("③ 優先順位")
    print(format_priority(tasks))
    print(DIVIDER)

    # ④ LINEネタ
    print("④ LINE集客の投稿ネタ（本日の3案）")
    print(generate_line_ideas())
    print(DIVIDER)
    print()


# ────────────────────────────────────────────
# 対話モード
# ────────────────────────────────────────────
def main() -> None:
    # 引数で直接 "おはよう" を渡してもOK
    if len(sys.argv) > 1 and "おはよう" in " ".join(sys.argv[1:]):
        show_morning_report()
        return

    print("秘書アシスタント起動中... 「おはよう」と入力してください。（終了: quit）")
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n終了します。お疲れ様でした！")
            break

        if user_input in ("quit", "exit", "終了"):
            print("終了します。お疲れ様でした！")
            break
        elif "おはよう" in user_input:
            show_morning_report()
        else:
            print("「おはよう」と入力すると朝のレポートを表示します。")


if __name__ == "__main__":
    main()
