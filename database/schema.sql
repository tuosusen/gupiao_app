-- 株価分析アプリ用データベーススキーマ
-- 作成日: 2025-01-09

-- データベース作成
CREATE DATABASE IF NOT EXISTS stock_analysis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE stock_analysis;

-- 1. 銘柄基本情報テーブル
CREATE TABLE IF NOT EXISTS stocks (
    ticker VARCHAR(10) PRIMARY KEY COMMENT '銘柄コード（例: 7203.T）',
    name VARCHAR(100) NOT NULL COMMENT '銘柄名',
    sector VARCHAR(100) COMMENT 'セクター',
    industry VARCHAR(100) COMMENT '業種',
    market VARCHAR(50) COMMENT '市場区分（プライム、スタンダード等）',
    market_cap BIGINT COMMENT '時価総額',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '登録日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_sector (sector),
    INDEX idx_market (market),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='銘柄基本情報';

-- 2. 財務指標テーブル（年次データ）
CREATE TABLE IF NOT EXISTS financial_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL COMMENT '銘柄コード',
    fiscal_date DATE NOT NULL COMMENT '決算日',
    per DECIMAL(10,2) COMMENT 'PER（株価収益率）',
    pbr DECIMAL(10,2) COMMENT 'PBR（株価純資産倍率）',
    roe DECIMAL(10,4) COMMENT 'ROE（自己資本利益率）',
    dividend_yield DECIMAL(10,4) COMMENT '配当利回り(%)',
    dividend_rate DECIMAL(10,2) COMMENT '年間配当金',
    payout_ratio DECIMAL(10,4) COMMENT '配当性向',
    profit_margin DECIMAL(10,4) COMMENT '利益率',
    revenue_growth DECIMAL(10,4) COMMENT '売上高成長率',
    net_income BIGINT COMMENT '純利益',
    total_revenue BIGINT COMMENT '売上高',
    total_assets BIGINT COMMENT '総資産',
    total_equity BIGINT COMMENT '純資産',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_ticker_date (ticker, fiscal_date),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE,
    INDEX idx_ticker (ticker),
    INDEX idx_fiscal_date (fiscal_date),
    INDEX idx_dividend_yield (dividend_yield),
    INDEX idx_per (per)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='財務指標（年次）';

-- 3. 配当履歴テーブル
CREATE TABLE IF NOT EXISTS dividends (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL COMMENT '銘柄コード',
    ex_date DATE NOT NULL COMMENT '権利落ち日',
    amount DECIMAL(10,2) NOT NULL COMMENT '配当金額',
    is_special BOOLEAN DEFAULT FALSE COMMENT '特別配当フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_ticker_date (ticker, ex_date),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE,
    INDEX idx_ticker (ticker),
    INDEX idx_ex_date (ex_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='配当履歴';

-- 4. 株価履歴テーブル（日次）
CREATE TABLE IF NOT EXISTS stock_prices (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL COMMENT '銘柄コード',
    date DATE NOT NULL COMMENT '日付',
    open DECIMAL(10,2) COMMENT '始値',
    high DECIMAL(10,2) COMMENT '高値',
    low DECIMAL(10,2) COMMENT '安値',
    close DECIMAL(10,2) NOT NULL COMMENT '終値',
    volume BIGINT COMMENT '出来高',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_ticker_date (ticker, date),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE,
    INDEX idx_ticker (ticker),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='株価履歴（日次）';

-- 5. 配当分析結果テーブル（計算済みデータ）
CREATE TABLE IF NOT EXISTS dividend_analysis (
    ticker VARCHAR(10) PRIMARY KEY COMMENT '銘柄コード',
    analysis_years INT DEFAULT 5 COMMENT '分析期間（年）',
    avg_dividend_yield DECIMAL(10,4) COMMENT '平均配当利回り',
    dividend_cv DECIMAL(10,4) COMMENT '配当変動係数',
    current_dividend_yield DECIMAL(10,4) COMMENT '最新配当利回り',
    dividend_trend DECIMAL(10,4) COMMENT '配当トレンド（線形回帰の傾き）',
    has_special_dividend BOOLEAN DEFAULT FALSE COMMENT '特別配当有無',
    dividend_quality_score INT COMMENT '配当クオリティスコア（0-100）',
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '計算日時',
    FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE,
    INDEX idx_avg_dividend_yield (avg_dividend_yield),
    INDEX idx_quality_score (dividend_quality_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='配当分析結果';

-- 6. データ更新履歴テーブル
CREATE TABLE IF NOT EXISTS update_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    update_type VARCHAR(50) NOT NULL COMMENT '更新タイプ（full/incremental/single）',
    ticker VARCHAR(10) COMMENT '銘柄コード（単一更新の場合）',
    status VARCHAR(20) NOT NULL COMMENT 'ステータス（success/failed/running）',
    records_updated INT DEFAULT 0 COMMENT '更新レコード数',
    error_message TEXT COMMENT 'エラーメッセージ',
    started_at TIMESTAMP NOT NULL COMMENT '開始日時',
    completed_at TIMESTAMP COMMENT '完了日時',
    INDEX idx_update_type (update_type),
    INDEX idx_status (status),
    INDEX idx_started_at (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='データ更新履歴';

-- ビュー: スクリーニング用の統合ビュー
CREATE OR REPLACE VIEW v_screening_data AS
SELECT
    s.ticker,
    s.name,
    s.sector,
    s.industry,
    s.market,
    s.market_cap,
    fm.per,
    fm.pbr,
    fm.roe,
    fm.dividend_yield,
    fm.dividend_rate,
    fm.payout_ratio,
    fm.profit_margin,
    fm.revenue_growth,
    da.avg_dividend_yield,
    da.dividend_cv,
    da.dividend_trend,
    da.has_special_dividend,
    da.dividend_quality_score,
    s.updated_at
FROM stocks s
LEFT JOIN financial_metrics fm ON s.ticker = fm.ticker
    AND fm.fiscal_date = (SELECT MAX(fiscal_date) FROM financial_metrics WHERE ticker = s.ticker)
LEFT JOIN dividend_analysis da ON s.ticker = da.ticker;

-- 初期データ確認用クエリ
-- SELECT * FROM stocks LIMIT 10;
-- SELECT * FROM v_screening_data WHERE dividend_yield > 3.0 ORDER BY dividend_quality_score DESC LIMIT 20;
