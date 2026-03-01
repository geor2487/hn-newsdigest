#!/bin/bash
set -e

TODAY=$(date +%Y-%m-%d)
DIGEST_DIR="$HOME/hn-digest/docs/digests"
OUTPUT_FILE="${DIGEST_DIR}/${TODAY}.md"
INDEX_FILE="$HOME/hn-digest/docs/index.md"
REPO_DIR="$HOME/hn-digest"
LOG_FILE="$HOME/hn-digest/last-run.log"

# --- ネット接続チェック ---
check_internet() {
    curl -s --max-time 5 https://hacker-news.firebaseio.com/v0/topstories.json > /dev/null 2>&1
}

# 最大5回、30秒間隔でリトライ（スリープ復帰直後はWi-Fiが未接続の場合がある）
for i in 1 2 3 4 5; do
    if check_internet; then
        break
    fi
    if [ "$i" -eq 5 ]; then
        echo "$(date): ネット接続なし。スキップ。" >> "$LOG_FILE"
        exit 0
    fi
    echo "$(date): ネット未接続。30秒後にリトライ ($i/5)..." >> "$LOG_FILE"
    sleep 30
done

# --- 今日のファイルがあればスキップ ---
mkdir -p "$DIGEST_DIR"

if [ -f "$OUTPUT_FILE" ]; then
    echo "$(date): 生成済み: $OUTPUT_FILE" >> "$LOG_FILE"
    exit 0
fi

echo "$(date): ダイジェスト生成開始..." >> "$LOG_FILE"

# --- Claude Codeでダイジェスト生成 ---
# ※ claudeのパスは `which claude` の結果に置き換える
claude -p "$(cat $HOME/.claude/commands/hn.md)" >> "$LOG_FILE" 2>&1

# --- ファイル生成確認 ---
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "$(date): エラー: ファイルが生成されなかった" >> "$LOG_FILE"
    exit 1
fi

# --- index.mdにリンク追加 ---
LINK="- [${TODAY}](digests/${TODAY}.md)"
if ! grep -q "$TODAY" "$INDEX_FILE" 2>/dev/null; then
    # macOS対応のsed
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "/## 最新のダイジェスト/a\\
\\
${LINK}" "$INDEX_FILE"
    else
        sed -i "/## 最新のダイジェスト/a\\
\\
${LINK}" "$INDEX_FILE"
    fi
fi

# --- GitHubにpush ---
cd "$REPO_DIR"
git add docs/
git commit -m "Add HN digest for ${TODAY}" || true
git push origin main >> "$LOG_FILE" 2>&1

echo "$(date): 完了" >> "$LOG_FILE"
