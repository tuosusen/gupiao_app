# 配当利回り重視投資家向け機能改善提案

## 現状分析

現在の株価分析アプリは以下の優れた配当分析機能を持っています：
- ✅ 特別配当の自動検出と除外
- ✅ 過去5年間の配当履歴分析
- ✅ 配当品質スコア（0-100）
- ✅ 通常配当利回りの計算
- ✅ 配当の変動係数（CV）による安定性評価

## 改善提案

### 1. 配当専用ダッシュボードの追加 ⭐⭐⭐

**目的**: 利回り重視投資家に最適化された専用インターフェース

**機能**:
- 配当カレンダー表示（権利確定日・配当支払日）
- 月次配当収入シミュレーター
- ポートフォリオ全体の利回り可視化
- 配当再投資シミュレーション（複利効果）

**実装優先度**: 高

---

### 2. 配当貴族・配当成長株スクリーニング ⭐⭐⭐

**目的**: 長期的な配当成長銘柄を発見

**条件**:
- 連続増配年数でフィルタ（5年、10年、20年+）
- 配当成長率（CAGR: Compound Annual Growth Rate）
- 配当性向（20-60%が健全範囲）
- 最低減配なし期間

**実装例**:
```python
# 配当成長率を計算
def calculate_dividend_cagr(dividends_history, years=5):
    """配当のCAGR（年平均成長率）を計算"""
    if len(dividends_history) < years:
        return None

    first_div = dividends_history[-years]
    last_div = dividends_history[-1]

    if first_div <= 0:
        return None

    cagr = ((last_div / first_div) ** (1/years) - 1) * 100
    return cagr
```

**実装優先度**: 高

---

### 3. セクター別配当利回りランキング ⭐⭐

**目的**: 業種別の配当利回り比較

**機能**:
- 11セクター別の平均利回り表示
- セクター内での相対ランキング
- 高配当セクターの特定（REIT、金融、公益事業など）
- セクター分散度の可視化

**表示例**:
```
セクター          | 平均利回り | 銘柄数 | トップ3銘柄
-----------------+----------+-------+------------------
金融             | 4.2%     | 85    | 三菱UFJ, ...
電気・ガス       | 3.8%     | 24    | 東京電力, ...
不動産           | 3.5%     | 45    | 三井不動産, ...
```

**実装優先度**: 中

---

### 4. 配当カバレッジ分析 ⭐⭐⭐

**目的**: 配当の持続可能性を評価

**指標**:
- **配当性向**: 純利益に対する配当の割合
  - 理想: 30-60%（成長余地あり）
  - 警戒: 80%以上（減配リスク）
- **フリーキャッシュフロー配当性向**
- **配当カバレッジレシオ**: EPS / 配当金

**警告表示**:
```
⚠️ 配当性向85% - 減配リスクあり
✅ 配当性向45% - 健全
🚀 FCF配当性向35% - 増配余地あり
```

**実装優先度**: 高

---

### 5. 配当再投資シミュレーター ⭐⭐

**目的**: 長期保有の複利効果を可視化

**機能**:
- 初期投資額を入力
- 保有期間を設定（5年、10年、20年）
- 配当再投資ありなしの比較グラフ
- 税引後配当利回りの考慮

**計算式**:
```python
def simulate_dividend_reinvestment(
    initial_amount: float,
    annual_dividend_yield: float,
    years: int,
    dividend_growth_rate: float = 0.0,
    tax_rate: float = 0.20315  # 日本の配当税率
):
    """配当再投資シミュレーション"""
    total_no_reinvest = initial_amount
    total_with_reinvest = initial_amount

    for year in range(1, years + 1):
        # 配当成長を考慮
        current_yield = annual_dividend_yield * (1 + dividend_growth_rate) ** year

        # 税引後配当
        after_tax_yield = current_yield * (1 - tax_rate)

        # 再投資なし
        dividend_no_reinvest = initial_amount * after_tax_yield / 100

        # 再投資あり
        dividend_with_reinvest = total_with_reinvest * after_tax_yield / 100
        total_with_reinvest += dividend_with_reinvest

    return {
        'no_reinvest': total_no_reinvest,
        'with_reinvest': total_with_reinvest,
        'gain': total_with_reinvest - total_no_reinvest
    }
```

**実装優先度**: 中

---

### 6. 配当利回り vs リスク散布図 ⭐⭐

**目的**: リスクリターンの可視化

**軸**:
- X軸: 配当利回り
- Y軸: リスク指標（配当変動係数、株価ボラティリティ、倒産リスクスコア）
- バブルサイズ: 時価総額
- 色: セクター

**理想的なエリア**: 高利回り × 低リスク（右下）

**実装優先度**: 中

---

### 7. 高配当ポートフォリオビルダー ⭐⭐⭐

**目的**: 分散投資ポートフォリオの構築支援

**機能**:
- 目標利回り設定（例: 4%）
- セクター分散制約（最大30%）
- 最大銘柄数制約（5-20銘柄）
- リスク許容度設定（低・中・高）

**出力**:
- 推奨銘柄リスト
- 投資比率
- ポートフォリオ全体の期待利回り
- 分散度スコア

**実装優先度**: 中

---

### 8. 配当支払い頻度フィルター ⭐

**目的**: 毎月配当を受け取りたい投資家向け

**条件**:
- 年間配当回数（年1回、年2回、年4回、毎月）
- 配当月でフィルタ（3月、9月など）
- 配当カレンダー表示

**実装優先度**: 低

---

### 9. 税引後利回り計算 ⭐⭐

**目的**: 実質的な手取り利回りを表示

**考慮事項**:
- 日本株: 20.315%（所得税+住民税+復興税）
- 米国株: 10%（現地税）+ 20.315%（国内税）- 外国税額控除
- NISA口座: 非課税

**表示例**:
```
税引前利回り: 5.0%
税引後利回り: 3.98% (NISA: 5.0%)
```

**実装優先度**: 中

---

### 10. 配当アラート機能 ⭐

**目的**: 重要な配当イベント通知

**通知内容**:
- 配当発表日
- 増配・減配の検出
- 権利確定日の接近
- 利回り目標達成銘柄

**実装優先度**: 低（将来機能）

---

## 実装ロードマップ

### フェーズ1（最優先）
1. ✅ 特別配当除外機能（完了）
2. ✅ 通常配当利回り計算（完了）
3. 配当貴族スクリーニング
4. 配当カバレッジ分析

### フェーズ2（次期）
5. 配当専用ダッシュボード
6. セクター別ランキング
7. 税引後利回り計算

### フェーズ3（将来）
8. 配当再投資シミュレーター
9. ポートフォリオビルダー
10. 配当アラート機能

---

## データベース拡張案

現在のスキーマに追加すべきテーブル：

```sql
-- 配当詳細情報
CREATE TABLE dividend_details (
    ticker VARCHAR(20),
    fiscal_year YEAR,
    consecutive_years INT,              -- 連続配当年数
    consecutive_increase_years INT,     -- 連続増配年数
    payout_ratio DECIMAL(5,2),         -- 配当性向
    fcf_payout_ratio DECIMAL(5,2),     -- FCF配当性向
    dividend_cagr_5y DECIMAL(5,2),     -- 5年配当CAGR
    ex_dividend_date DATE,              -- 権利確定日
    payment_date DATE,                  -- 支払日
    dividend_frequency INT,             -- 年間配当回数
    PRIMARY KEY (ticker, fiscal_year),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);

-- ポートフォリオ管理
CREATE TABLE portfolios (
    portfolio_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    portfolio_name VARCHAR(100),
    target_yield DECIMAL(5,2),
    risk_tolerance ENUM('low', 'medium', 'high'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE portfolio_holdings (
    holding_id INT PRIMARY KEY AUTO_INCREMENT,
    portfolio_id INT,
    ticker VARCHAR(20),
    shares DECIMAL(15,4),
    weight_pct DECIMAL(5,2),
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);
```

---

## UI/UX改善案

### スクリーニング画面の簡素化

**現状の問題**:
- 条件が多すぎて初心者に複雑
- 重要な指標が埋もれている

**改善案**:

1. **プリセットフィルター**:
   ```
   🎯 人気のスクリーニング
   - 高配当・安定配当（利回り4%+、CV<0.3）
   - 配当貴族（連続増配10年+）
   - 低リスク高配当（倒産リスク低、利回り3%+）
   - バリュー高配当（PER<15、利回り3%+）
   ```

2. **シンプルモード vs 詳細モード**:
   - シンプル: 利回り、リスクレベルのみ
   - 詳細: 全条件表示

3. **結果の見やすさ向上**:
   - カラーコーディング（緑: 優良、黄: 注意、赤: 警告）
   - ソート機能の強化
   - 配当カレンダービュー追加

---

## まとめ

**即座に実装すべき機能（高優先度）**:
1. 配当貴族スクリーニング（連続増配年数）
2. 配当カバレッジ分析（配当性向）
3. 配当専用ダッシュボード

**中期的に実装すべき機能（中優先度）**:
4. セクター別配当ランキング
5. 税引後利回り計算
6. 配当利回り vs リスク散布図

**長期的な機能（低優先度）**:
7. 配当再投資シミュレーター
8. ポートフォリオビルダー
9. 配当アラート機能

これらの改善により、利回り重視の投資家にとって最も使いやすい株価分析ツールになります。
