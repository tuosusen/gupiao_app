# 株価分析アプリ

高度な配当分析とスクリーニング機能を持つ株価分析Streamlitアプリケーション

## 特徴

- **個別銘柄分析**: yfinanceを使用した詳細な銘柄分析
- **高度なスクリーニング**:
  - 過去の配当履歴分析（平均利回り、変動係数、トレンド）
  - 特別配当の自動検出と除外
  - 配当品質スコア（0-100）
  - PER/PBRなどのバリュエーション指標
- **MySQLデータベース統合**: 高速スクリーニングのためのデータ保存
- **データ更新管理**: Streamlit UIからのデータ更新
- **東証プライム市場全銘柄対応**: ~1,800銘柄

## システム要件

- Python 3.8以上
- MySQL 5.7以上（またはMariaDB 10.3以上）
- 8GB RAM以上推奨

## インストール

### 1. リポジトリのクローン

```bash
cd d:\gupiao_app
```

### 2. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

必要なパッケージ:
- streamlit
- yfinance
- pandas
- numpy
- scipy
- matplotlib
- plotly
- requests
- mysql-connector-python
- xlrd
- openpyxl

### 3. MySQLデータベースのセットアップ

#### 3.1 MySQLサーバーの起動

MySQLが既にインストールされている場合は起動してください：

```bash
# Windowsの場合（管理者権限で）
net start MySQL

# または MySQLサービスを手動で起動
services.msc
```

#### 3.2 データベースとテーブルの作成

MySQLにログインしてデータベースを作成：

```bash
mysql -u root -p
```

SQLスクリプトを実行：

```sql
source d:/gupiao_app/database/schema.sql
```

または、MySQLクライアントから：

```bash
mysql -u root -p < d:\gupiao_app\database\schema.sql
```

#### 3.3 ユーザーと権限の設定（オプション）

rootユーザーを使わない場合、専用ユーザーを作成：

```sql
CREATE USER 'stock_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON stock_analysis.* TO 'stock_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. 環境変数の設定

環境変数を設定してデータベース接続情報を保存します。

#### Windowsの場合

**方法1: コマンドプロンプト（一時的）**

```cmd
set MYSQL_HOST=localhost
set MYSQL_PORT=3306
set MYSQL_USER=root
set MYSQL_PASSWORD=your_mysql_password
set MYSQL_DATABASE=stock_analysis
```

**方法2: PowerShell（一時的）**

```powershell
$env:MYSQL_HOST="localhost"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="your_mysql_password"
$env:MYSQL_DATABASE="stock_analysis"
```

**方法3: システム環境変数（永続的・推奨）**

1. 「Windowsキー + R」を押して「sysdm.cpl」を実行
2. 「詳細設定」タブ → 「環境変数」ボタン
3. 「ユーザー環境変数」または「システム環境変数」で「新規」をクリック
4. 以下の変数を追加：
   - 変数名: `MYSQL_HOST`、値: `localhost`
   - 変数名: `MYSQL_PORT`、値: `3306`
   - 変数名: `MYSQL_USER`、値: `root`
   - 変数名: `MYSQL_PASSWORD`、値: `your_mysql_password`
   - 変数名: `MYSQL_DATABASE`、値: `stock_analysis`
5. 「OK」をクリックして保存
6. コマンドプロンプト/PowerShellを再起動

#### Linux/Macの場合

**~/.bashrc または ~/.zshrc に追加（永続的）**

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_mysql_password
export MYSQL_DATABASE=stock_analysis
```

変更を反映：

```bash
source ~/.bashrc  # または source ~/.zshrc
```

## 使用方法

### 1. アプリケーションの起動

```bash
cd d:\gupiao_app
streamlit run stock_analysis_app.py
```

ブラウザが自動的に開き、アプリケーションが表示されます（通常は http://localhost:8501）。

### 2. 初回データ更新

初めて使用する場合、データベースにデータを登録する必要があります：

1. サイドバーから「データ更新」ページを選択
2. 「データ更新」タブを開く
3. 「プライム市場全銘柄を更新」ボタンをクリック
4. 並列処理数を選択（推奨: 5）
5. 「更新開始」ボタンをクリック

**注意**: 初回の全銘柄更新には1-2時間かかる場合があります。

### 3. スクリーニングの実行

#### データベーススクリーニング（推奨・高速）

1. サイドバーから「銘柄スクリーニング」モードを選択
2. 「データベースから検索（推奨）」にチェック
3. サイドバーで条件を設定：
   - 最低配当利回り
   - 最大PER/PBR
   - 平均配当利回り（過去4年）
   - 配当品質スコア
4. 「スクリーニング実行」ボタンをクリック
5. 結果が即座に表示されます

#### リアルタイムスクリーニング

1. 「データベースから検索」のチェックを外す
2. 条件を設定
3. 「スクリーニング実行」ボタンをクリック

**注意**: リアルタイムスクリーニングは時間がかかります（15-30分）。

### 4. 個別銘柄分析

1. サイドバーから「個別銘柄分析」モードを選択
2. 銘柄コードを入力（例: `7203.T` トヨタ自動車）
3. 「分析開始」ボタンをクリック

スクリーニング結果から銘柄を選択して詳細分析することもできます。

## ファイル構成

```
gupiao_app/
├── stock_analysis_app.py      # メインアプリケーション
├── pages/
│   └── data_update.py          # データ更新画面
├── database/
│   ├── __init__.py             # パッケージ初期化
│   ├── schema.sql              # データベーススキーマ
│   ├── db_config.py            # データベース接続管理
│   └── data_updater.py         # データ取得・更新ロジック
├── requirements.txt            # 必要なパッケージリスト
└── README.md                   # このファイル
```

## データベーススキーマ

### テーブル

1. **stocks**: 銘柄基本情報
2. **financial_metrics**: 財務指標（年次）
3. **dividends**: 配当履歴
4. **stock_prices**: 株価履歴（日次）
5. **dividend_analysis**: 配当分析結果（計算済み）
6. **update_history**: データ更新履歴

### ビュー

- **v_screening_data**: スクリーニング用の統合ビュー

## データ更新の推奨スケジュール

- **毎日**: 差分更新（24時間以上経過した銘柄）
- **毎週**: プライム市場全銘柄更新
- **決算シーズン後**: 全銘柄更新

自動更新を設定したい場合は、Windowsタスクスケジューラーを使用できます。

## トラブルシューティング

### データベース接続エラー

```
❌ データベース接続エラー
```

**解決方法**:
1. MySQLサーバーが起動していることを確認
2. 環境変数が正しく設定されていることを確認
3. データ更新画面の「設定確認」タブで接続テストを実行
4. ファイアウォールがMySQLポート（3306）をブロックしていないか確認

### yfinanceエラー

```
❌ データの取得に失敗しました
```

**解決方法**:
1. インターネット接続を確認
2. 銘柄コードの形式を確認（日本株は `.T` が必要、例: `7203.T`）
3. yfinanceのレート制限に達している可能性があるため、しばらく待ってから再試行

### データが古い

**解決方法**:
1. データ更新画面から差分更新または全銘柄更新を実行
2. 「データベース状態」タブで最終更新日時を確認

## パフォーマンス最適化

### データベース

- **インデックス**: 主要な検索列にはインデックスが設定済み
- **ビュー**: v_screening_dataビューを使用した高速検索

### 並列処理

- データ更新時の並列処理数を調整（推奨: 5-10）
- 高すぎるとyfinanceのレート制限に達する可能性あり

### ストレージ

約1,800銘柄、5年分のデータで必要な容量:
- 銘柄基本情報: ~1MB
- 財務指標: ~10MB
- 配当履歴: ~5MB
- 株価履歴: ~500MB（日次、5年分）
- 合計: 約 500-600MB

## ライセンス

このプロジェクトは個人使用目的です。

## 注意事項

1. yfinanceから取得するデータは参考値です。投資判断は自己責任で行ってください。
2. APIレート制限を守り、過度なリクエストを避けてください。
3. データの正確性は保証されません。公式の開示情報を必ず確認してください。
4. このアプリケーションは投資助言を提供するものではありません。

## サポート

問題が発生した場合:
1. このREADMEのトラブルシューティングセクションを確認
2. データ更新画面の「設定確認」タブで環境をチェック
3. MySQLのログを確認（通常は `C:\ProgramData\MySQL\MySQL Server X.X\Data\` にあります）

## 更新履歴

- 2025-01-09: 初版リリース
  - MySQL統合
  - データ更新画面追加
  - 高速DBスクリーニング実装
