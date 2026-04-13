#!/usr/bin/env python3
"""
kaori-content-system: 投稿生成スクリプト
Claude APIを使ってThreads/Instagram/LINE/LP向けのコンテンツを生成します。
"""

import argparse
import anthropic

POST_TYPES = ["threads", "instagram", "line", "lp"]

TYPE_GUIDELINES = {
    "threads": "Threads投稿: 500文字以内。1〜3段落。短くテンポよく。",
    "instagram": "Instagram投稿: キャプション形式。絵文字を適度に使用。ハッシュタグを5〜10個末尾に追加。",
    "line": "LINE配信: 読みやすい改行多め。親しみやすいトーン。スタンプを想定した一言CTAも含める。",
    "lp": "LP構成: ファーストビュー〜CTA〜FAQの流れで出力。各セクション見出し付き。",
}


def generate_post(
    target: str,
    theme: str,
    service: str,
    goal: str,
    post_type: str,
) -> str:
    client = anthropic.Anthropic()

    system_prompt = """あなたはSNSマーケティングの専門家です。
以下の条件を必ず守ってください:
- 読みやすく、専門用語を使わない
- 読者が共感できる言葉を使う
- 行動を促す（CTA必須）
- 押しつけがましくなく、自然な流れで誘導する"""

    user_prompt = f"""以下の情報をもとに、{post_type.upper()}用のコンテンツを作成してください。

【基本情報】
- ターゲット: {target}
- 発信テーマ: {theme}
- 提供サービス: {service}
- ゴール: {goal}

【投稿タイプ別ガイドライン】
{TYPE_GUIDELINES[post_type]}

【出力形式】
①フック（最初の一文で読者を引きつける）
②本文（共感→問題提起→解決策の流れ）
③CTA（具体的な行動を促す一文）
④コメント解説（この投稿のポイントを50字以内で説明）

上記の形式で出力してください。"""

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        result = stream.get_final_message()

    for block in result.content:
        if block.type == "text":
            return block.text
    return ""


def main():
    parser = argparse.ArgumentParser(
        description="kaori-content-system: SNS投稿コンテンツ生成ツール"
    )
    parser.add_argument("--target", required=True, help="ターゲット層 (例: 30代女性、起業家)")
    parser.add_argument("--theme", required=True, help="発信テーマ (例: ダイエット、副業)")
    parser.add_argument("--service", required=True, help="提供サービス (例: オンラインコーチング)")
    parser.add_argument("--goal", required=True, help="ゴール (例: LINEへの誘導、商品購入)")
    parser.add_argument(
        "--type",
        dest="post_type",
        choices=POST_TYPES,
        default="threads",
        help=f"投稿タイプ: {', '.join(POST_TYPES)} (デフォルト: threads)",
    )

    args = parser.parse_args()

    print(f"\n--- {args.post_type.upper()} 投稿生成中 ---\n")
    output = generate_post(
        target=args.target,
        theme=args.theme,
        service=args.service,
        goal=args.goal,
        post_type=args.post_type,
    )
    print(output)
    print("\n--- 生成完了 ---\n")


if __name__ == "__main__":
    main()
