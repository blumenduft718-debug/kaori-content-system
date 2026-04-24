import requests
import logging
from datetime import date
from config import NOTION_BASE_URL, NOTION_HEADERS, PARENT_PAGE_ID

logger = logging.getLogger(__name__)


def get_headers():
    """Return fresh headers (picks up env var at call time)."""
    import os
    from config import NOTION_VERSION
    api_key = os.environ.get("NOTION_API_KEY", "")
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def create_page_under_parent(title: str, content_blocks: list) -> dict:
    """Create a Notion page as a child of PARENT_PAGE_ID."""
    payload = {
        "parent": {"page_id": PARENT_PAGE_ID},
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        },
        "children": content_blocks,
    }
    resp = requests.post(
        f"{NOTION_BASE_URL}/pages",
        headers=get_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def create_calendar_entry(db_id: str, title: str, target_date: date) -> dict:
    """Create an entry in the Notion calendar database."""
    date_str = target_date.isoformat()
    payload = {
        "parent": {"database_id": db_id},
        "properties": {
            "名前": {
                "title": [{"type": "text", "text": {"content": title}}]
            },
            "日付": {
                "date": {"start": date_str}
            },
        },
    }
    resp = requests.post(
        f"{NOTION_BASE_URL}/pages",
        headers=get_headers(),
        json=payload,
        timeout=30,
    )
    if resp.status_code == 400:
        # Try English property names as fallback
        payload["properties"] = {
            "Name": {
                "title": [{"type": "text", "text": {"content": title}}]
            },
            "Date": {
                "date": {"start": date_str}
            },
        }
        resp = requests.post(
            f"{NOTION_BASE_URL}/pages",
            headers=get_headers(),
            json=payload,
            timeout=30,
        )
    resp.raise_for_status()
    return resp.json()


def get_child_pages(page_id: str) -> list:
    """Return child blocks of type 'child_page' for the given page."""
    pages = []
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        resp = requests.get(
            f"{NOTION_BASE_URL}/blocks/{page_id}/children",
            headers=get_headers(),
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        for block in data.get("results", []):
            if block.get("type") == "child_page":
                pages.append({
                    "id": block["id"],
                    "title": block["child_page"]["title"],
                })
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return pages


def get_comments(page_id: str) -> list:
    """Return all comments for a page."""
    comments = []
    cursor = None
    while True:
        params = {"block_id": page_id, "page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        resp = requests.get(
            f"{NOTION_BASE_URL}/comments",
            headers=get_headers(),
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        comments.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return comments


def add_comment(page_id: str, text: str) -> dict:
    """Add a comment to a Notion page."""
    payload = {
        "parent": {"page_id": page_id},
        "rich_text": [{"type": "text", "text": {"content": text}}],
    }
    resp = requests.post(
        f"{NOTION_BASE_URL}/comments",
        headers=get_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def append_blocks_to_page(page_id: str, blocks: list) -> dict:
    """Append content blocks to an existing page."""
    payload = {"children": blocks}
    resp = requests.patch(
        f"{NOTION_BASE_URL}/blocks/{page_id}/children",
        headers=get_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def text_block(content: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": content}}]
        },
    }


def heading2_block(content: str) -> dict:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": content}}]
        },
    }


def bullet_block(content: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": content}}]
        },
    }


def divider_block() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}
