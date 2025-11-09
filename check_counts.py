"""
各テーブルの件数を確認
"""
from database.db_config import DatabaseManager

db = DatabaseManager()

tables = ['stocks', 'financial_metrics', 'dividends', 'dividend_analysis']

for table in tables:
    result = db.execute_query(f'SELECT COUNT(*) as count FROM {table}')
    print(f'{table}: {result[0]["count"]}件')
