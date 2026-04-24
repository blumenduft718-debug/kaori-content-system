import os
from pathlib import Path

# Load .env file if present (environment variables take precedence)
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file, override=False)
    except ImportError:
        pass

NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# Mirato parent page
PARENT_PAGE_ID = "34605b60db6f810cb2adea27ecee6828"

# Calendar database
CALENDAR_DB_ID = "b8a0abf7-aea5-4cff-9649-80d99c2ce06e"

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-6"

# CEO persona
CEO_NAME = "月城凛"

# Processed comments tracking file
PROCESSED_COMMENTS_FILE = os.path.join(
    os.path.dirname(__file__), "processed_comments.json"
)

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}
