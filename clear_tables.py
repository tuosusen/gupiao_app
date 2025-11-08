"""
データベーステーブルのクリアとIDリセットスクリプト
"""

from database.db_config import DatabaseManager

def clear_tables():
    db = DatabaseManager()
    
    # 外部キー制約を一時的に無効化
    db.execute_query("SET FOREIGN_KEY_CHECKS = 0;", fetch=False)
    
    # 各テーブルのTRUNCATEコマンド
    truncate_commands = [
        "TRUNCATE TABLE financial_metrics;",
        "TRUNCATE TABLE dividends;",
        "TRUNCATE TABLE stock_prices;",
        "TRUNCATE TABLE update_history;",
        "DELETE FROM dividend_analysis;",
        "DELETE FROM stocks;"
    ]
    
    try:
        for command in truncate_commands:
            result = db.execute_query(command, fetch=False)
            print(f"実行: {command} -> {'成功' if result is not None else '失敗'}")
            
    finally:
        # 外部キー制約を再度有効化
        db.execute_query("SET FOREIGN_KEY_CHECKS = 1;", fetch=False)
        
if __name__ == "__main__":
    clear_tables()