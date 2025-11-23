# 配当貴族スクリーニング キャッシュシステム

## クイックスタート

### 1. テーブル作成（初回のみ）

```bash
python scripts/migrate_dividend_aristocrats_table.py
```

### 2. キャッシュ更新

**方法A: UI内で更新（推奨）**

1. Streamlitアプリを起動: `streamlit run main.py`
2. 「👑 配当貴族・配当成長株スクリーニング」を開く
3. ⚙️ カスタマイズ設定 → 💾 キャッシュ管理
4. 🔄 キャッシュを更新ボタンをクリック

**方法B: コマンドラインで更新**

```bash
# 50銘柄を更新
python scripts/update_dividend_aristocrats_cache.py --limit 50

# 全銘柄を更新
python scripts/update_dividend_aristocrats_cache.py
```

### 3. スクリーニング実行

UI上で通常通りスクリーニングを実行すると、キャッシュが自動的に使用されます。

## パフォーマンス

- **キャッシュあり**: < 1秒（1500銘柄）
- **キャッシュなし**: 約60分（1500銘柄）
- **スピードアップ**: 約3600倍

## ドキュメント

- [詳細マニュアル](docs/dividend_aristocrats_cache.md)
- [実装サマリー](IMPLEMENTATION_SUMMARY.md)
- [UI更新ガイド](UI_CACHE_UPDATE_GUIDE.md)

## 主な機能

✅ データベースキャッシュによる高速化
✅ UI内で簡単にキャッシュ更新
✅ プログレスバーでリアルタイム進捗表示
✅ 自動的なキャッシュ鮮度管理
✅ コマンドラインでのバッチ更新

## ファイル構成

```
gupiao_app/
├── database/
│   └── schema.sql                              # dividend_aristocrats_metricsテーブル
├── repository/
│   └── database_manager.py                     # CRUD操作
├── services/
│   └── dividend_aristocrats.py                 # キャッシュ統合スクリーニング
├── ui/pages/
│   └── dividend_aristocrats_page.py            # UI + キャッシュ更新機能
├── scripts/
│   ├── migrate_dividend_aristocrats_table.py   # テーブル作成
│   └── update_dividend_aristocrats_cache.py    # バッチ更新
└── docs/
    └── dividend_aristocrats_cache.md           # 詳細ドキュメント
```

## トラブルシューティング

### キャッシュが見つからない

```bash
# データベースを確認
python inspect_db.py
```

### 古いキャッシュを更新

UI内またはコマンドラインで全銘柄を再更新してください。

### yfinance APIエラー

- 待機時間を増やす: `--delay 2.0`
- 更新銘柄数を減らす: `--limit 50`
