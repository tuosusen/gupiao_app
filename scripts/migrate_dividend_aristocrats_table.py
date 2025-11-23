"""
配当貴族指標テーブルのマイグレーションスクリプト
既存のデータベースに新しいテーブルを追加
"""

import sys
import io
from pathlib import Path

# Windows環境での文字エンコーディング問題を回避
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from repository.database_manager import DatabaseManager


def migrate_dividend_aristocrats_table():
    """配当貴族指標テーブルを作成"""
    
    db_manager = DatabaseManager()
    
    print("=" * 60)
    print("配当貴族指標テーブル マイグレーション")
    print("=" * 60)
    
    # テーブル作成SQL
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS dividend_aristocrats_metrics (
        ticker VARCHAR(10) PRIMARY KEY COMMENT '銘柄コード',
        company_name VARCHAR(100) COMMENT '銘柄名',
        
        -- 配当利回り
        current_dividend_yield DECIMAL(10,4) COMMENT '現在配当利回り(%)',
        after_tax_yield DECIMAL(10,4) COMMENT '税引後利回り(%)',
        
        -- 配当成長指標
        consecutive_increase_years INT DEFAULT 0 COMMENT '連続増配年数',
        dividend_cagr_5y DECIMAL(10,4) COMMENT '配当CAGR 5年(%)',
        dividend_cagr_10y DECIMAL(10,4) COMMENT '配当CAGR 10年(%)',
        
        -- 配当性向
        payout_ratio DECIMAL(10,4) COMMENT '配当性向(%)',
        payout_ratio_status VARCHAR(50) COMMENT '配当性向評価',
        fcf_payout_ratio DECIMAL(10,4) COMMENT 'FCF配当性向(%)',
        fcf_payout_status VARCHAR(50) COMMENT 'FCF配当性向評価',
        
        -- ステータス
        aristocrat_status VARCHAR(50) COMMENT 'ステータス（配当貴族候補等）',
        
        -- メタデータ
        data_quality VARCHAR(20) DEFAULT 'complete' COMMENT 'データ品質（complete/partial/incomplete）',
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最終更新日時',
        calculation_error TEXT COMMENT '計算エラーメッセージ',
        
        FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE,
        INDEX idx_consecutive_years (consecutive_increase_years),
        INDEX idx_dividend_cagr (dividend_cagr_5y),
        INDEX idx_payout_ratio (payout_ratio),
        INDEX idx_status (aristocrat_status),
        INDEX idx_last_updated (last_updated)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='配当貴族指標（キャッシュ）'
    """
    
    print("テーブルを作成中...")
    result = db_manager.execute_query(create_table_sql, fetch=False)
    
    if result is not None:
        print("[OK] テーブル作成成功")
        
        # テーブル情報を確認
        check_query = """
            SELECT 
                TABLE_NAME, 
                TABLE_ROWS, 
                CREATE_TIME, 
                UPDATE_TIME
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'dividend_aristocrats_metrics'
        """
        
        table_info = db_manager.execute_query(check_query)
        if table_info and len(table_info) > 0:
            info = table_info[0]
            print(f"\nテーブル情報:")
            print(f"  テーブル名: {info['TABLE_NAME']}")
            print(f"  レコード数: {info['TABLE_ROWS']}")
            print(f"  作成日時: {info['CREATE_TIME']}")
            print(f"  更新日時: {info['UPDATE_TIME']}")
        
        print("\n[OK] マイグレーション完了")
    else:
        print("[ERROR] テーブル作成失敗")
    
    print("=" * 60)


if __name__ == '__main__':
    migrate_dividend_aristocrats_table()
