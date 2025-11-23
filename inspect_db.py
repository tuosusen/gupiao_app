"""データベースの配当貴族メトリクスを確認"""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from repository.database_manager import DatabaseManager

db = DatabaseManager()
result = db.execute_query('SELECT * FROM dividend_aristocrats_metrics')

if result:
    print(f"キャッシュ済み銘柄数: {len(result)}")
    print("\n最初の3銘柄:")
    for i, row in enumerate(result[:3], 1):
        print(f"\n[{i}] {row['ticker']} - {row['company_name']}")
        print(f"    連続増配年数: {row['consecutive_increase_years']}年")
        print(f"    配当CAGR(5年): {row['dividend_cagr_5y']}%")
        print(f"    配当利回り: {row['current_dividend_yield']}%")
        print(f"    配当性向: {row['payout_ratio']}%")
        print(f"    ステータス: {row['aristocrat_status']}")
        print(f"    データ品質: {row['data_quality']}")
        print(f"    最終更新: {row['last_updated']}")
else:
    print("データが見つかりません")
