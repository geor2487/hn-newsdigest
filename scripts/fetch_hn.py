#!/usr/bin/env python3
"""
Hacker News トップ記事取得スクリプト
Firebase API でトップ記事を取得し、記事本文とコメントも含めて JSON で出力する。
"""

from __future__ import annotations

import datetime
import json
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

import trafilatura

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
TOP_STORIES_URL = f"{HN_API_BASE}/topstories.json"
ITEM_URL_TEMPLATE = f"{HN_API_BASE}/item/{{}}.json"
HN_ITEM_PAGE = "https://news.ycombinator.com/item?id={}"
NUM_STORIES = 10
TOP_COMMENTS = 5


def fetch_json(url: str) -> dict | list | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HN-Digest/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        print(f"Warning: Failed to fetch {url}: {e}", file=sys.stderr)
        return None


def fetch_item(item_id: int) -> dict | None:
    data = fetch_json(ITEM_URL_TEMPLATE.format(item_id))
    if not data:
        return None
    return {
        "id": data.get("id"),
        "title": data.get("title", ""),
        "url": data.get("url", HN_ITEM_PAGE.format(data.get("id"))),
        "hn_url": HN_ITEM_PAGE.format(data.get("id")),
        "score": data.get("score", 0),
        "comments": data.get("descendants", 0),
        "by": data.get("by", ""),
        "time": data.get("time", 0),
        "type": data.get("type", "story"),
        "kids": data.get("kids", []),
    }


def fetch_comment(comment_id: int) -> dict | None:
    data = fetch_json(ITEM_URL_TEMPLATE.format(comment_id))
    if not data or data.get("deleted") or data.get("dead"):
        return None
    return {
        "by": data.get("by", ""),
        "text": data.get("text", ""),
    }


def fetch_article_content(url: str) -> str:
    """trafilaturaで記事本文を抽出する。"""
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return ""
        text = trafilatura.extract(downloaded) or ""
        # 長すぎる場合は先頭3000文字に切り詰める
        return text[:3000]
    except Exception as e:
        print(f"Warning: Failed to extract content from {url}: {e}", file=sys.stderr)
        return ""


def enrich_story(story: dict) -> dict:
    """記事に本文とトップコメントを追加する。"""
    # 記事本文を取得
    story["content"] = fetch_article_content(story["url"])

    # トップコメントを取得
    comment_ids = story.pop("kids", [])[:TOP_COMMENTS]
    comments = []
    if comment_ids:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_comment, cid): cid for cid in comment_ids}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    comments.append(result)
    story["top_comments"] = comments
    return story


def main():
    story_ids = fetch_json(TOP_STORIES_URL)
    if not story_ids:
        print("Error: Failed to fetch top stories", file=sys.stderr)
        sys.exit(1)

    # トップ30件の基本情報を並列取得
    story_ids = story_ids[:30]
    stories = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_item, sid): sid for sid in story_ids}
        for future in as_completed(futures):
            result = future.result()
            if result:
                stories.append(result)

    # 求人系を除外し、スコア+コメント数でソートして上位10件を選定
    stories = [s for s in stories if s["type"] != "job"]
    stories.sort(key=lambda x: x["score"] + x["comments"], reverse=True)
    stories = stories[:NUM_STORIES]

    # 選定した10件に対して記事本文+コメントを並列取得
    with ThreadPoolExecutor(max_workers=5) as executor:
        stories = list(executor.map(enrich_story, stories))

    output = {
        "fetched_at": datetime.datetime.now().isoformat(),
        "count": len(stories),
        "stories": stories,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
