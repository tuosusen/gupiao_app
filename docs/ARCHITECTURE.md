# gupiao_app アーキテクチャドキュメント

## 概要

`gupiao_app`は`ts_app_claude`のアーキテクチャパターンを採用した株価分析アプリケーションです。

## アーキテクチャ図

```
┌─────────────────────────────────────────────┐
│           UI層 (Streamlit) ✅               │
│  - main.py                                  │
│  - stock_analysis_app.py                    │
│  - ui/pages/edinet_page.py                  │
│  - pages/screening_config.py                │
└────────────┬────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────┐
│       サービス層 ✅                          │
│  - services/                                │
│    - investment_screener.py                 │
│    - screening_presets.py                   │
│    - edinet_data_processor.py               │
└────────────┬────────────────────────────────┘
             │
       ┌─────┴─────┐
       ↓           ↓
┌──────────────┐ ┌──────────────────────────┐
│ Repository層 │ │      Domain層 ✅         │
│      ✅      │ │  - models/               │
│              │ │    - stock_info.py       │
│ - database_  │ │    - financial_ratios.py │
│   manager    │ │    - dividend_info.py    │
│ - yfinance_  │ │    - per_info.py         │
│   repository │ │    - screening_          │
│ - stock_list_│ │      conditions.py       │
│   repository │ │                          │
│ - edinet_    │ │  純粋なビジネスロジック    │
│   repository │ │  外部依存なし             │
└──────┬───────┘ └──────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────────┐
│         外部システム                         │
│  - MySQL データベース                        │
│  - yfinance API                             │
│  - JPX 銘柄リスト                            │
│  - EDINET API                               │
└─────────────────────────────────────────────┘
```

## ディレクトリ構造

```
d:/gupiao_app/
├── config.py                    # ✅ 設定管理（DB、アプリ設定）
├── main.py                      # ✅ メインエントリーポイント
├── stock_analysis_app.py        # ✅ 株価分析アプリ
├── edinet_app.py                # ✅ EDINETアプリエントリーポイント
│
├── domain/                      # ✅ ドメイン層（完全実装済み）
│   └── models/                  # データモデル
│       ├── stock_info.py
│       ├── financial_ratios.py
│       ├── dividend_info.py
│       ├── per_info.py
│       └── screening_conditions.py
│
├── repository/                  # ✅ データアクセス層（完全実装済み）
│   ├── database_manager.py      # MySQL接続管理
│   ├── yfinance_repository.py   # yfinance API
│   ├── stock_list_repository.py # 銘柄リスト取得
│   └── edinet_repository.py     # EDINET API
│
├── services/                    # ✅ サービス層（実装済み）
│   ├── investment_screener.py   # スクリーニングサービス
│   ├── screening_presets.py     # プリセット管理
│   └── edinet_data_processor.py # EDINETデータ処理
│
├── ui/                          # ✅ UI層（部分実装）
│   └── pages/                   # ページコンポーネント
│       └── edinet_page.py       # EDINET分析ページ
│
├── pages/                       # ✅ Streamlitマルチページ
│   └── screening_config.py      # スクリーニング管理画面
│
├── database/                    # ✅ データベース関連
│   ├── db_config.py             # DB設定（旧版、移行済み）
│   ├── data_updater.py          # データ更新ロジック
│   └── schema.sql               # データベーススキーマ
│
├── scripts/                     # スクリプト
│   └── config.py                # 設定（ルートにコピー済み）
│
├── docs/                        # ドキュメント
│   ├── ARCHITECTURE.md          # 本ドキュメント
│   ├── COMPLETION_REPORT.md     # 完了レポート
│   ├── DIVIDEND_FOCUSED_IMPROVEMENTS.md
│   ├── EDINET_FIX_SUMMARY.md
│   ├── EDINET_LIMITATIONS.md
│   ├── SETUP_GUIDE.md
│   └── UI_IMPROVEMENT_PROPOSAL.md
│
└── old_backup/                  # バックアップ
    ├── stock_analysis_app.py.backup
    ├── edinet_app.py.backup
    ├── database.backup/
    └── pages_old/
```

## 各層の責務

### 1. Domain層（ドメイン層）
**責務**: 純粋なビジネスロジックとデータ構造
- **依存**: なし（他の層に依存しない）
- **特徴**: 
  - 外部ライブラリへの依存を最小化
  - テストが容易
  - 再利用性が高い

**サブモジュール**:
- `models/`: データクラス（@dataclass使用）
- `calculators/`: 計算ロジック（財務指標、配当分析、PER分析等）
- `utils/`: ヘルパー関数（翻訳辞書等）
- `validators/`: バリデーションロジック

### 2. Repository層（リポジトリ層）
**責務**: 外部データソースへのアクセス
- **依存**: config, domain/models
- **特徴**:
  - データ取得の詳細を隠蔽
  - 複数のデータソースを統一的に扱う
  - エラーハンドリング

**実装済みリポジトリ**:
- `DatabaseManager`: MySQL接続とクエリ実行
- `YFinanceRepository`: yfinance APIラッパー
- `StockListRepository`: JPXから銘柄リスト取得
- `EDINETRepository`: EDINET API統合

### 3. Services層（サービス層）✅ 実装済み
**責務**: ビジネスロジックの統合とオーケストレーション
- **依存**: repository, domain
- **特徴**:
  - 複数のリポジトリを組み合わせた操作
  - トランザクション管理
  - エラーハンドリングと再試行

**実装済みサービス**:
- `InvestmentScreener`: スクリーニングロジック（配当分析、倒産リスク評価）
- `ScreeningPresets`: プリセット管理とフォーマット
- `EDINETDataProcessor`: EDINET財務データ処理

### 4. UI層（UI層）✅ 実装済み
**責務**: ユーザーインターフェース
- **依存**: services, repository
- **特徴**:
  - Streamlitウィジェット
  - ページ単位の分割
  - マルチページアプリケーション

**実装済みページ**:
- `main.py`: メインエントリーポイント（アプリケーション選択）
- `stock_analysis_app.py`: 株価分析メインアプリ（個別分析＆スクリーニング）
- `ui/pages/edinet_page.py`: EDINET財務分析ページ
- `pages/screening_config.py`: スクリーニング管理画面

## データフロー

### 個別銘柄分析の例

```
1. ユーザー入力（UI層）
   ↓
2. サービス層で処理（今後実装）
   ↓
3. YFinanceRepository.get_stock_data()
   ↓
4. FinancialCalculator.calculate_ratios()
   ↓
5. 結果をUI層に返す
   ↓
6. Streamlitで表示
```

### スクリーニングの例

```
1. ユーザーが条件を設定（UI層）
   ↓
2. ScreeningConditions モデル作成
   ↓
3. ScreeningService（今後実装）
   ├─ DatabaseManager で高速検索
   └─ YFinanceRepository でリアルタイム検索
   ↓
4. DividendCalculator、PERCalculator で分析
   ↓
5. 結果をUI層に返す
```

## 設定管理

### config.py
```python
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    host: str = os.getenv('MYSQL_HOST', 'localhost')
    port: int = int(os.getenv('MYSQL_PORT', '3306'))
    user: str = os.getenv('MYSQL_USER', 'root')
    password: str = os.getenv('MYSQL_PASSWORD', '')
    database: str = os.getenv('MYSQL_DATABASE', 'stock_analysis')

@dataclass
class AppConfig:
    page_title: str = "株価分析アプリ"
    layout: str = "wide"
```

## 実行方法

### メインアプリケーション（推奨）
```bash
cd d:/gupiao_app
streamlit run main.py
```

起動後、サイドバーで以下の機能を選択：
- 🔍 株価分析（個別銘柄＆スクリーニング）
- 📈 EDINET財務分析
- 🔄 データベース更新管理

### マルチページアプリ
main.py起動後、サイドバーに自動表示されるページ：
- **main** - メインページ
- **screening config** - スクリーニング管理画面

### 個別実行（オプション）
```bash
# EDINET財務分析のみ
streamlit run edinet_app.py

# 株価分析のみ
streamlit run stock_analysis_app.py
```

## テスト戦略（今後実装）

### ユニットテスト
- **Domain層**: 計算ロジックのテスト
- **Repository層**: モックデータでのテスト
- **Services層**: 統合テスト

### 実行方法
```bash
pytest tests/
```

## 実装状況

### ✅ 完了済み

#### Domain層
- ✅ models/ - 全データモデル（StockInfo, FinancialRatios, DividendInfo, PERInfo, ScreeningConditions）

#### Repository層
- ✅ DatabaseManager - MySQL接続管理
- ✅ YFinanceRepository - yfinance API
- ✅ StockListRepository - JPX銘柄リスト
- ✅ EDINETRepository - EDINET API

#### Services層
- ✅ InvestmentScreener - スクリーニングサービス
- ✅ ScreeningPresets - プリセット管理
- ✅ EDINETDataProcessor - EDINETデータ処理

#### UI層
- ✅ main.py - メインアプリ
- ✅ stock_analysis_app.py - 株価分析
- ✅ ui/pages/edinet_page.py - EDINET分析
- ✅ pages/screening_config.py - スクリーニング管理

### 🔲 今後の拡張可能性

#### テストとCI/CD
- [ ] ユニットテスト（pytest）
- [ ] 統合テスト
- [ ] GitHub Actions

#### UI改善
- [ ] ui/components/ - 再利用可能コンポーネント（必要に応じて）
- [ ] グラフの高度化
- [ ] レスポンシブデザイン

#### 機能拡張
- [ ] ポートフォリオ管理機能
- [ ] アラート通知機能
- [ ] レポート自動生成

## 設計原則

1. **単一責任の原則**: 各クラス・関数は1つの責務のみ
2. **依存性逆転の原則**: 上位層が下位層に依存
3. **開放閉鎖の原則**: 拡張に開いて、修正に閉じている
4. **インターフェース分離の原則**: 必要なインターフェースのみに依存
5. **DRY（Don't Repeat Yourself）**: コードの重複を避ける

## 参考アーキテクチャ

本プロジェクトは`ts_app_claude`のアーキテクチャパターンを参考にしています：
- レイヤードアーキテクチャ
- リポジトリパターン
- サービスパターン
- データクラスの活用

## リファクタリング完了記録

### 完了日
2024年11月

### 主な成果
1. **レイヤー分離の完成**: Domain, Repository, Services, UI層を完全に実装
2. **保守性向上**: 各ファイルが適切なサイズに分割（200-500行程度）
3. **再利用性**: コンポーネント化されたサービスとモデル
4. **拡張性**: 新機能の追加が容易な構造
5. **可読性**: 明確な責任分離とドキュメント化

### 移行元ファイル
- `stock_analysis_app.py` (2000+ 行) → 複数のモジュールに分割
- `database/` → `repository/` + `database/`に整理
- モノリシックなコード → レイヤードアーキテクチャ

### バックアップ
すべての旧ファイルは `old_backup/` に保存済み
