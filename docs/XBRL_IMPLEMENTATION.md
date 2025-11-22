# XBRL形式の財務データ解析機能 - 実装完了

## 実装概要

EDINET APIから取得した財務諸表をXBRL形式で解析し、構造化されたデータとして抽出する機能を実装しました。

## 変更したファイル

### 1. repository/edinet_repository.py

**追加したメソッド:**

#### `parse_xbrl_to_dataframe(xbrl_content: bytes) -> Optional[Dict[str, pd.DataFrame]]`

XBRLファイル（XML形式）をパースして、財務データをpandas DataFrameに変換します。

**抽出する財務指標:**

| カテゴリ | 指標 | 検索パターン |
|---------|------|--------------|
| 損益計算書 | 売上高 | `売上高\|NetSales\|Revenue` |
| 損益計算書 | 営業利益 | `営業利益\|OperatingIncome\|OperatingProfit` |
| 損益計算書 | 当期純利益 | `当期純利益\|NetIncome\|ProfitLoss` |
| 貸借対照表 | 総資産 | `総資産\|TotalAssets\|Assets` |
| 貸借対照表 | 純資産 | `純資産\|NetAssets\|Equity` |
| キャッシュフロー計算書 | 営業CF | `営業.*キャッシュ\|OperatingCashFlow\|CashFlowsFromOperating` |

**データ構造:**

各項目は以下の情報を含みます：
- 項目名（日本語）
- XBRLタグ名
- 値
- コンテキスト情報（期間など）
- 単位情報（円、千円など）

**修正したメソッド:**

#### `get_financial_statements()`

書類取得形式を変更：
- **変更前:** `doc_type=5` (CSV形式)
- **変更後:** `doc_type=1` (XBRL形式)

処理フロー：
1. 書類をダウンロード（ZIPファイル）
2. ZIPからXBRLファイルを抽出
3. XBRLをXMLとしてパース
4. 財務指標を正規表現でマッチング
5. pandas DataFrameに変換
6. カテゴリ別に整理して返却

## 使用技術

### XMLパース
```python
import xml.etree.ElementTree as ET

root = ET.fromstring(xbrl_content)
for elem in root.iter():
    tag_name = elem.tag.split('}')[1] if '}' in elem.tag else elem.tag
    # 名前空間を除去してタグ名を取得
```

### 正規表現マッチング
```python
import re

if re.search(r'(売上高|NetSales|Revenue)', tag_name, re.IGNORECASE):
    # 売上高として処理
```

## デバッグログの改善

詳細なログを追加し、各ステップの状況を把握できるようにしました：

```
→ 書類ダウンロード試行: S100VWVY | 種類: 120
  ✓ ダウンロード成功 (206425 bytes)
  ✓ XBRL抽出成功 (185320 bytes)
  ✓ XBRL解析成功: 3 カテゴリ
    - 損益計算書: 15 項目
    - 貸借対照表: 8 項目
    - キャッシュフロー計算書: 5 項目
```

## 解決した問題

### 以前の問題
- CSV形式（type=5）では財務データが含まれていませんでした
- 書類のダウンロードは成功していましたが、ZIPファイル内にCSVファイルが存在しませんでした
- 結果として、財務データを取得できませんでした

### 解決方法
- XBRL形式（type=1）に切り替え
- XBRL XMLをパースして財務指標を抽出
- 構造化されたDataFrameに変換

## テスト方法

### 1. アプリを起動
```bash
cd /d/gupiao_app
d:/gupiao_app/venv/Scripts/python.exe -m streamlit run main.py
```

### 2. EDINET財務分析を選択
- サイドバーから「📈 EDINET財務分析」を選択

### 3. APIキーを入力
- EDINET APIキーを入力欄に貼り付け

### 4. 企業コードを入力
- 例: トヨタ自動車 → `7203`
- 例: ソニーグループ → `6758`

### 5. 財務データを取得
- 「財務データ取得」ボタンをクリック
- デバッグログで進捗を確認
- 取得した財務データがテーブルで表示されます

## 次のステップ

### 短期（今後数日）
- [ ] より多くの財務指標を抽出
  - ROE（自己資本利益率）
  - ROA（総資産利益率）
  - 自己資本比率
  - 流動比率
  - など

### 中期（今後数週間）
- [ ] 時系列データの整理機能
  - 複数期間のデータを一つのDataFrameに統合
  - 前年比・前期比の自動計算
  - トレンド分析機能

### 長期（今後数ヶ月）
- [ ] キャッシュ機能の実装
  - 一度取得したデータをデータベースに保存
  - 再取得時はキャッシュから読み込み
  - APIコール回数の削減

- [ ] より高度なXBRL解析
  - すべての勘定科目を自動抽出
  - 連結・個別の自動判定
  - 注記情報の抽出

## 参考資料

- [EDINET API仕様書](https://disclosure2.edinet-fsa.go.jp/WZEK0040.aspx)
- [XBRL仕様](https://www.xbrl.org/)
- [Python xml.etree.ElementTree](https://docs.python.org/3/library/xml.etree.elementtree.html)
- [pandas DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html)

## まとめ

XBRL形式への切り替えにより、EDINET APIから実際の財務データを取得できるようになりました。これで以下が可能になります：

✅ 有価証券報告書・四半期報告書から財務諸表を自動抽出
✅ 損益計算書、貸借対照表、キャッシュフロー計算書を構造化データとして取得
✅ pandas DataFrameで分析・可視化が可能
✅ 複数企業・複数期間のデータを比較分析

今後は、より多くの財務指標を抽出し、時系列分析やトレンド可視化などの高度な機能を追加していく予定です。
