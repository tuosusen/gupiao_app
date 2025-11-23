# 配当貴族スクリーニング キャッシュシステム

## 概要

配当貴族スクリーニングは、銘柄の配当成長指標（連続増配年数、配当CAGR、配当性向など）を分析して、優良配当成長銘柄を発掘する機能です。

従来はyfinance APIから毎回リアルタイムでデータを取得していたため、1500銘柄以上をスクリーニングすると非常に時間がかかっていました（3~8分）。

このキャッシュシステムは、計算済みの配当指標をデータベースに保存し、再利用することで、スクリーニング時間を**1秒以内**に短縮します。

## アーキテクチャ

```
┌─────────────────────┐
│ UIページ           │
│ (dividend_        │
│  aristocrats_page)│
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│ サービス層          │
│ (DividendAristocrats)│
│                     │
│ screen_dividend_    │
│ aristocrats()       │
│  - use_cache=True   │
│  - max_age=24h      │
└──────┬──────────────┘
       │
       v
  ┌────┴────┐
  │ キャッシュあり?│
  └────┬────┘
       │
  ┌────v────┐────┐
  │YES      │NO  │
  v         v    │
┌─────┐  ┌─────┐│
│ DB  │  │yfinance│
│キャッシュ│  │ API  │
└─────┘  └──┬──┘
            │
            v
     ┌──────────┐
     │DBに保存  │
     └──────────┘
```

## データベーススキーマ

### `dividend_aristocrats_metrics` テーブル

配当成長指標をキャッシュするテーブル：

```sql
CREATE TABLE dividend_aristocrats_metrics (
    ticker VARCHAR(10) PRIMARY KEY,           -- 銘柄コード
    company_name VARCHAR(100),                -- 銘柄名

    -- 配当利回り
    current_dividend_yield DECIMAL(10,4),     -- 現在配当利回り(%)
    after_tax_yield DECIMAL(10,4),            -- 税引後利回り(%)

    -- 配当成長指標
    consecutive_increase_years INT,           -- 連続増配年数
    dividend_cagr_5y DECIMAL(10,4),          -- 配当CAGR 5年(%)
    dividend_cagr_10y DECIMAL(10,4),         -- 配当CAGR 10年(%)

    -- 配当性向
    payout_ratio DECIMAL(10,4),              -- 配当性向(%)
    payout_ratio_status VARCHAR(50),         -- 配当性向評価
    fcf_payout_ratio DECIMAL(10,4),          -- FCF配当性向(%)
    fcf_payout_status VARCHAR(50),           -- FCF配当性向評価

    -- ステータス
    aristocrat_status VARCHAR(50),           -- ステータス(配当貴族候補等)

    -- メタデータ
    data_quality VARCHAR(20),                -- データ品質(complete/partial/incomplete)
    last_updated TIMESTAMP,                  -- 最終更新日時
    calculation_error TEXT,                  -- 計算エラーメッセージ

    FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);
```

## 使用方法

### 1. 初回セットアップ

#### データベーステーブルの作成

```bash
python scripts/migrate_dividend_aristocrats_table.py
```

実行結果：
```
============================================================
配当貴族指標テーブル マイグレーション
============================================================
テーブルを作成中...
[OK] テーブル作成成功

テーブル情報:
  テーブル名: dividend_aristocrats_metrics
  レコード数: 0
  作成日時: 2025-11-23 14:35:47
  更新日時: None

[OK] マイグレーション完了
============================================================
```

### 2. キャッシュの更新

#### 全プライム市場銘柄を更新（推奨: 週次または月次）

```bash
python scripts/update_dividend_aristocrats_cache.py
```

#### テスト実行（最初の5銘柄のみ）

```bash
python scripts/update_dividend_aristocrats_cache.py --limit 5 --delay 0.5
```

実行結果：
```
============================================================
配当貴族指標キャッシュ更新開始
============================================================
[INFO] 対象銘柄数: 5
[INFO] API待機時間: 0.5秒

[1/5] 1301.T を処理中... [OK]
[2/5] 1332.T を処理中... [OK]
[3/5] 1333.T を処理中... [OK]
[4/5] 1375.T を処理中... [OK]
[5/5] 1377.T を処理中... [OK]

============================================================
更新完了
============================================================
[OK] 成功: 5 銘柄
[ERROR] エラー: 0 銘柄
[TIME] 所要時間: 12.2秒
[TIME] 平均処理時間: 2.44秒/銘柄
```

#### オプション

- `--limit N`: 更新する銘柄数の上限（テスト用）
- `--delay N`: API呼び出し間の待機時間（秒、デフォルト1.0）

### 3. UIからのスクリーニング

配当貴族スクリーニングページでは、キャッシュが自動的に使用されます：

1. **キャッシュ利用設定**（サイドバー）
   - キャッシュを使用: ON/OFF
   - キャッシュ有効期間: 1/6/12/24/48時間

2. **スクリーニング実行**
   - キャッシュがある場合: 即座に結果表示（1秒以内）
   - キャッシュがない場合: yfinanceから取得してキャッシュ保存

3. **キャッシュステータス表示**
   ```
   ℹ️ キャッシュ情報:
   - キャッシュから取得: 1500 銘柄
   - yfinanceから取得: 16 銘柄
   - 最終更新: 2025-11-23 15:03:47
   ```

### 4. プログラムからの利用

```python
from services.dividend_aristocrats import DividendAristocrats

# キャッシュを使用（24時間以内のデータ）
results = DividendAristocrats.screen_dividend_aristocrats(
    min_consecutive_years=5,
    min_cagr=3.0,
    max_payout_ratio=80.0,
    use_cache=True,
    max_cache_age_hours=24
)

# キャッシュを使用しない（常にyfinanceから取得）
results = DividendAristocrats.screen_dividend_aristocrats(
    min_consecutive_years=10,
    min_cagr=5.0,
    max_payout_ratio=60.0,
    use_cache=False
)
```

## パフォーマンス

### 速度比較

| 方法 | 銘柄数 | 所要時間 | 備考 |
|------|--------|----------|------|
| **キャッシュあり** | 1500 | **< 1秒** | データベースから取得 |
| キャッシュなし | 5 | 12秒 | yfinance API |
| キャッシュなし | 1500 | 3600秒 (60分) | 推定値 |

**スピードアップ**: 約3600倍

### キャッシュ更新時間

- 5銘柄: 約12秒
- 100銘柄: 約4分
- 1500銘柄: 約60分（推定）

## データ品質

### 品質レベル

- `complete`: 全ての必須フィールドが取得できた
- `partial`: 一部のフィールドが欠損
- `incomplete`: ほとんどのデータが取得できなかった

### データ鮮度の管理

- `max_cache_age_hours`: キャッシュの最大有効期間
  - 推奨設定: 24時間（日次更新の場合）
  - 短期: 1時間（頻繁に変動する相場での利用）
  - 長期: 48時間（安定した分析用）

## 運用推奨

### 定期更新スケジュール

1. **週次更新**（推奨）
   ```bash
   # 毎週日曜日の深夜に実行
   0 2 * * 0 cd /path/to/gupiao_app && python scripts/update_dividend_aristocrats_cache.py
   ```

2. **月次更新**（データ変動が少ない場合）
   ```bash
   # 毎月1日の深夜に実行
   0 2 1 * * cd /path/to/gupiao_app && python scripts/update_dividend_aristocrats_cache.py
   ```

### API制限対策

yfinance APIには非公式の制限があるため、以下の対策を推奨：

1. **待機時間の設定**: `--delay 1.0`（デフォルト）
2. **バッチ処理**: 100銘柄ずつに分割して実行
3. **エラーハンドリング**: 自動リトライ機能を実装済み

## トラブルシューティング

### キャッシュが古い

```bash
# 強制的に全銘柄を再取得
python scripts/update_dividend_aristocrats_cache.py --delay 1.0
```

### 一部の銘柄でエラー

```bash
# データ品質が incomplete の銘柄を確認
python inspect_db.py
```

### yfinance API エラー

- HTTP 401: 認証エラー → 時間をおいて再試行
- HTTP 404: 銘柄が見つからない → DBから削除された可能性
- Rate Limit: `--delay` を増やす（例: `--delay 2.0`）

## 制限事項

1. **市場区分**: 現状は 'jp_market' の全銘柄を対象
   - 将来的にプライム/スタンダード/グロースに細分化予定

2. **データソース**: yfinance に依存
   - Yahoo Finance のデータ品質に左右される
   - 一部の銘柄で正確なデータが取得できない場合あり

3. **リアルタイム性**: キャッシュの鮮度に依存
   - 最新のデータが必要な場合は `use_cache=False` を使用

## 今後の拡張

1. **プライム市場の細分化**
   - 市場区分データの充実化
   - プライム/スタンダード/グロース別のフィルタリング

2. **増分更新機能**
   - 古いキャッシュのみを更新
   - より効率的な更新処理

3. **データ品質スコアリング**
   - データ信頼性の可視化
   - 低品質データの自動除外

4. **統計情報の追加**
   - セクター別の配当成長率
   - 市場全体のトレンド分析
