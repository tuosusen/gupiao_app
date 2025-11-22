# gupiao_app アーキテクチャドキュメント

## 概要

`gupiao_app`は`ts_app_claude`のアーキテクチャパターンを採用した株価分析アプリケーションです。

## アーキテクチャ図

```
┌─────────────────────────────────────────────┐
│           UI層 (Streamlit)                  │
│  - ui/pages/                                │
│  - ui/components/                           │
│  - ui/layouts/                              │
└────────────┬────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────┐
│       サービス層（今後実装）                  │
│  - services/                                │
│    - individual_stock_service.py            │
│    - screening_service.py                   │
└────────────┬────────────────────────────────┘
             │
       ┌─────┴─────┐
       ↓           ↓
┌──────────────┐ ┌──────────────────────────┐
│ Repository層 │ │      Domain層            │
│              │ │  - models/               │
│ - database_  │ │  - calculators/          │
│   manager    │ │  - utils/                │
│ - yfinance_  │ │  - validators/           │
│   repository │ │                          │
│ - stock_list_│ │  純粋なビジネスロジック    │
│   repository │ │  外部依存なし             │
│ - edinet_    │ │                          │
│   repository │ │                          │
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
├── config.py                    # 設定管理（DB、アプリ設定）
├── main.py                      # メインエントリーポイント
├── edinet_app.py                # EDINETアプリエントリーポイント
│
├── domain/                      # ドメイン層
│   ├── models/                  # データモデル
│   │   ├── stock_info.py
│   │   ├── financial_ratios.py
│   │   ├── dividend_info.py
│   │   ├── per_info.py
│   │   └── screening_conditions.py
│   ├── calculators/             # 計算ロジック
│   │   ├── financial_calculator.py
│   │   ├── dividend_calculator.py
│   │   ├── per_calculator.py
│   │   └── technical_calculator.py
│   ├── utils/                   # ユーティリティ
│   │   └── financial_translator.py
│   └── validators/              # バリデーション（今後実装）
│
├── repository/                  # データアクセス層
│   ├── database_manager.py      # MySQL接続管理
│   ├── yfinance_repository.py   # yfinance API
│   ├── stock_list_repository.py # 銘柄リスト取得
│   └── edinet_repository.py     # EDINET API
│
├── services/                    # サービス層（今後実装）
│   └── (ビジネスロジック統合)
│
├── ui/                          # UI層
│   ├── pages/                   # ページコンポーネント
│   │   └── edinet_page.py
│   ├── components/              # 再利用可能コンポーネント
│   └── layouts/                 # レイアウト
│
├── database/                    # 既存のDB関連（段階的移行中）
│   ├── db_config.py
│   └── data_updater.py
│
├── pages/                       # 既存のページ（段階的移行中）
│   └── data_update.py
│
├── old_backup/                  # バックアップ
│   ├── stock_analysis_app.py.backup
│   ├── edinet_app.py.backup
│   └── database.backup/
│
└── README_REFACTORING.md        # リファクタリング進捗
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

### 3. Services層（サービス層）※今後実装
**責務**: ビジネスロジックの統合とオーケストレーション
- **依存**: repository, domain
- **特徴**:
  - 複数のリポジトリを組み合わせた操作
  - トランザクション管理
  - エラーハンドリングと再試行

### 4. UI層（UI層）
**責務**: ユーザーインターフェース
- **依存**: services（将来）、repository（現在）
- **特徴**:
  - Streamlitウィジェット
  - ページ単位の分割
  - 再利用可能なコンポーネント

**実装済みページ**:
- `EDINETPage`: EDINET財務分析ページ

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

### 株価分析アプリ
```bash
streamlit run main.py
```

### EDINET財務分析アプリ
```bash
streamlit run edinet_app.py
```

### データ更新
```bash
# ページから実行
streamlit run main.py
# サイドバー → データ更新
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

## 今後の実装予定

### フェーズ2: Services層
- [ ] `IndividualStockService`
- [ ] `ScreeningService`
- [ ] `FinancialAnalysisService`
- [ ] `DividendAnalysisService`
- [ ] `PERAnalysisService`

### フェーズ3: UI層の完全実装
- [ ] `ui/components/charts.py`
- [ ] `ui/components/cards.py`
- [ ] `ui/components/tables.py`
- [ ] `ui/pages/individual_analysis_page.py`
- [ ] `ui/pages/screening_page.py`
- [ ] `ui/layouts/sidebar.py`

### フェーズ4: テストとCI/CD
- [ ] ユニットテスト
- [ ] 統合テスト
- [ ] GitHub Actions

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
