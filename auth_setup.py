#!/usr/bin/env python3
"""Googleカレンダー初回認証スクリプト"""
import json, urllib.parse, urllib.request, secrets, hashlib, base64
from pathlib import Path

creds = json.loads(Path("credentials.json").read_text())["installed"]
client_id     = creds["client_id"]
client_secret = creds["client_secret"]
token_uri     = creds["token_uri"]
scope         = "https://www.googleapis.com/auth/calendar.readonly"
redirect_uri  = "urn:ietf:wg:oauth:2.0:oob"

# 認証URLを生成（PKCEなし）
params = urllib.parse.urlencode({
    "client_id": client_id,
    "redirect_uri": redirect_uri,
    "response_type": "code",
    "scope": scope,
    "access_type": "offline",
    "prompt": "consent",
})
auth_url = f"https://accounts.google.com/o/oauth2/auth?{params}"
print("\n【STEP 1】以下のURLをスマホのブラウザで開いてください：\n")
print(auth_url)
print()

code = input("【STEP 2】ブラウザに表示されたコードを貼り付けてください: ").strip()

# トークン取得
data = urllib.parse.urlencode({
    "code": code,
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": redirect_uri,
    "grant_type": "authorization_code",
}).encode()

req = urllib.request.Request(token_uri, data=data, method="POST")
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read())

# token.json 形式で保存
token_data = {
    "token": token.get("access_token"),
    "refresh_token": token.get("refresh_token"),
    "token_uri": token_uri,
    "client_id": client_id,
    "client_secret": client_secret,
    "scopes": [scope],
}
Path("token.json").write_text(json.dumps(token_data))
print("\n✅ 認証完了！token.json を保存しました。")
print("これからは「おはよう」だけでカレンダーが自動取得されます。\n")
