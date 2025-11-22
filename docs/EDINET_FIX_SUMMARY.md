# EDINET API データ取得の修正

## 問題点

ユーザーがEDINET APIキーを入力しても、財務データを取得できない問題が発生していました。

## 根本原因

[repository/edinet_repository.py:146](repository/edinet_repository.py#L146)の`get_financial_statements`メソッドに以下の問題がありました:

```python
# 修正前の問題コード
for year_offset in range(years):
    target_date = (datetime.now() - timedelta(days=365*year_offset)).strftime('%Y-%m-%d')
    documents = self.get_documents_list(target_date)  # 1年に1日しかチェックしない!
```

**問題:**
- 各年について**1日分のデータしか取得していませんでした**
- EDINET APIは特定の日付に提出された書類を返すため、その1日にたまたま書類が提出されていない限り、何も取得できません
- 企業の決算日は企業ごとに異なるため、任意の日付では書類が見つかりません

## 修正内容

### 1. repository/edinet_repository.py の改善

**変更点:**
- 1年に1日だけチェックする方式から、**30日ごとにサンプリングする方式**に変更
- 指定された年数の期間全体をカバーするようになりました
- デバッグ情報を追加（チェックした日付数、書類があった日付数、マッチした書類数）

```python
# 修正後のコード
end_date = datetime.now()
start_date = end_date - timedelta(days=365 * years)

# 30日ごとにサンプリング
current_date = end_date
while current_date >= start_date:
    date_str = current_date.strftime('%Y-%m-%d')
    documents = self.get_documents_list(date_str)
    # ... 書類をフィルタリング
    current_date -= timedelta(days=30)
```

**効果:**
- 5年間指定の場合: 5日分 → **約60日分**をチェック
- 書類を見つけられる確率が大幅に向上

### 2. ui/pages/edinet_page.py のUI改善

**追加機能:**

1. **検索条件の詳細表示**
   - expanderで検索条件を確認可能
   - 企業コード、年数、書類種類を明示

2. **より詳細なエラーメッセージ**
   - よくある企業コード例を追加（トヨタ: 7203、ソニー: 6758など）
   - レート制限の可能性も追加
   - APIキー確認URLを提供

3. **API接続テスト機能**
   - データ取得失敗時に、API自体への接続をテスト
   - APIキーが有効かどうかを確認可能
   - 今日の日付で書類一覧が取得できるかチェック

4. **例外処理の強化**
   - try-exceptブロックで全体をラップ
   - エラー詳細をexpanderで表示（トレースバック含む）

## 使用方法

1. main.pyを実行
2. サイドバーから「📈 EDINET財務分析」を選択
3. APIキーを入力
4. 企業コード（例: 7203）を入力
5. 「財務データ取得」ボタンをクリック

## トラブルシューティング

データが取得できない場合:

1. **「🔍 検索条件の詳細」を確認**
   - 企業コードが正しいか確認
   - 書類種類が適切か確認

2. **「🔧 API接続テスト」を実行**
   - APIキーが有効か確認
   - EDINET APIへの接続が成功しているか確認

3. **企業コードの例:**
   - トヨタ自動車: 7203
   - ソニーグループ: 6758
   - ソフトバンクグループ: 9984

## 今後の改善案

- [ ] 書類検索の最適化（全期間を毎回検索するのではなく、キャッシュを使用）
- [ ] より詳細な進捗表示（何日分チェック中か表示）
- [ ] 企業名での検索機能（証券コードを知らなくても検索可能に）
- [ ] 取得した書類の一覧を表示（どの期間の書類が見つかったか）
