"""
配当データがある銘柄を確認
"""
from database.db_config import DatabaseManager

db = DatabaseManager()

# 配当データがある銘柄数
query1 = """
SELECT COUNT(DISTINCT ticker) as count
FROM dividends
"""
result1 = db.execute_query(query1)
print(f"配当データがある銘柄: {result1[0]['count']}件")

# 株価データがある銘柄数
query2 = """
SELECT COUNT(DISTINCT ticker) as count
FROM stock_prices
"""
result2 = db.execute_query(query2)
print(f"株価データがある銘柄: {result2[0]['count']}件")

# 両方あるが、dividend_analysisがない銘柄
query3 = """
SELECT COUNT(DISTINCT d.ticker) as count
FROM dividends d
INNER JOIN stock_prices sp ON d.ticker = sp.ticker
LEFT JOIN dividend_analysis da ON d.ticker = da.ticker
WHERE da.ticker IS NULL
"""
result3 = db.execute_query(query3)
print(f"配当&株価はあるが分析データがない: {result3[0]['count']}件")

# サンプルを確認
query4 = """
SELECT DISTINCT d.ticker, s.name
FROM dividends d
INNER JOIN stocks s ON d.ticker = s.ticker
LIMIT 5
"""
result4 = db.execute_query(query4)
print(f"\n配当データがある銘柄の例:")
for row in result4:
    print(f"  {row['ticker']}: {row['name']}")
