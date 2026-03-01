#!/usr/bin/env python3
"""
Hacker News トップ記事取得スクリプト
Firebase API を使ってトップ30記事の詳細を取得し、JSON で出力する。
"""

from __future__ import annotations

import json
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

import datetime

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
TOP_STORIES_URL = f"{HN_API_BASE}/topstories.json"
ITEM_URL_TEMPLATE = f"{HN_API_BASE}/item/{{}}.json"
HN_ITEM_PAGE = "https://news.ycombinator.com/item?id={}"
MAX_FETCH = 200  # フィルタ前に取得する最大件数
HOURS_WINDOW = 24  # 直近何時間以内の記事を対象にするか


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
    }


def main():
    story_ids = fetch_json(TOP_STORIES_URL)
    if not story_ids:
        print("Error: Failed to fetch top stories", file=sys.stderr)
        sys.exit(1)

    story_ids = story_ids[:MAX_FETCH]
    stories = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_item, sid): sid for sid in story_ids}
        for future in as_completed(futures):
            result = future.result()
            if result:
                stories.append(result)

    # 直近24時間以内の記事のみに絞り込む
    now = datetime.datetime.now().timestamp()
    cutoff = now - HOURS_WINDOW * 3600
    stories = [s for s in stories if s["time"] >= cutoff]

    stories.sort(key=lambda x: x["score"] + x["comments"], reverse=True)

    output = {
        "fetched_at": datetime.datetime.now().isoformat(),
        "count": len(stories),
        "stories": stories,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
