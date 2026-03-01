# HN Digest

Hacker News のトップ記事を毎日自動で取得し、日本語で初学者にもわかりやすく要約して GitHub Pages に公開するシステム。

**サイト**: https://geor2487.github.io/hn-newsdigest/

## 仕組み

```
毎朝 8:00 (macOS launchd)
    │
    ▼
run-if-needed.sh
    ├── ネット接続チェック（最大5回リトライ）
    ├── 今日のダイジェストが既にあればスキップ
    ├── Claude Code で /hn コマンド実行
    │       ├── fetch_hn.py で HN トップ10記事 + コメント取得
    │       ├── 各記事を日本語で丁寧に要約
    │       └── docs/digests/YYYY-MM-DD.md として保存
    ├── index.md にリンク追加
    └── git push → GitHub Pages に自動デプロイ
```

## ディレクトリ構成

```
hn-digest/
├── README.md
├── run-if-needed.sh          # 自動実行スクリプト（launchd から呼ばれる）
├── scripts/
│   └── fetch_hn.py           # HN Firebase API から記事・コメント取得
└── docs/                     # GitHub Pages ソース
    ├── _config.yml            # Jekyll 設定
    ├── _layouts/
    │   └── default.html       # カスタムレイアウト（ダークテーマ、カード UI）
    ├── index.md               # トップページ（ダイジェスト一覧）
    └── digests/
        └── YYYY-MM-DD.md      # 日別ダイジェスト
```

## 記事フォーマット

各記事は以下の構成で要約される：

- **ざっくり言うと** — 3〜5文。背景知識なしで理解できるレベル
- **もう少し詳しく** — 5〜10文。技術的な仕組みや背景を噛み砕いて解説
- **なぜ注目？** — 3〜5文。業界への影響、初学者が知っておくべきポイント
- **HN コメント** — 肯定的 5件 + 否定的・懐疑的 5件（アコーディオン形式）
- **用語集** — 記事末尾に 5〜10個

難しい用語には `（用語: わかりやすい解説）` の形式で文中に注釈が入る。

## セットアップ

### 前提条件

- macOS
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) がインストール済み
- Python 3 + `trafilatura`（`pip install trafilatura`）
- Git（GitHub への push 用に SSH 認証設定済み）

### 自動実行の設定

launchd plist が `~/Library/LaunchAgents/com.hn-digest.plist` にあり、毎朝 8:00 に `run-if-needed.sh` を実行する。

```bash
# 登録
launchctl load ~/Library/LaunchAgents/com.hn-digest.plist

# 解除
launchctl unload ~/Library/LaunchAgents/com.hn-digest.plist

# 手動で即時実行
bash ~/hn-digest/run-if-needed.sh
```

### 手動でダイジェスト生成

Claude Code で `/hn` コマンドを実行すると、記事取得 → 要約 → 保存 → push まで一括で行われる。

## 技術スタック

- **記事取得**: Python + HN Firebase API + trafilatura（本文抽出）
- **要約生成**: Claude Code（`claude -p` で非対話実行）
- **サイト**: GitHub Pages + Jekyll（`jekyll-theme-minimal` ベース、カスタムダークテーマ）
- **自動化**: macOS launchd
