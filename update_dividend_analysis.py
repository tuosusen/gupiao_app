"""
既存の配当・株価データから配当分析を計算してdividend_analysisテーブルに保存
"""

from database.db_config import DatabaseManager
from database.data_updater import StockDataUpdater
import yfinance as yf
import sys
import importlib

# stock_analysis_appを強制的に再読み込み
import stock_analysis_app
importlib.reload(stock_analysis_app)
from stock_analysis_app import calculate_historical_dividend_yield, calculate_dividend_quality_score

def update_dividend_analysis_for_all_stocks():
    """全銘柄の配当分析を計算して保存"""
    db = DatabaseManager()
    updater = StockDataUpdater()

    # 配当データがある銘柄のリストを取得
    query = """
    SELECT DISTINCT d.ticker, s.name
    FROM dividends d
    INNER JOIN stocks s ON d.ticker = s.ticker
    ORDER BY d.ticker
    """

    stocks_with_dividends = db.execute_query(query)

    if not stocks_with_dividends:
        print("配当データがある銘柄が見つかりません")
        return

    total = len(stocks_with_dividends)
    print(f"配当データがある銘柄: {total}件")
    print("配当分析を開始します...\n")

    success_count = 0
    error_count = 0

    for idx, stock_info in enumerate(stocks_with_dividends, 1):
        ticker = stock_info['ticker']
        name = stock_info['name']

        try:
            # yfinanceからデータを取得
            stock = yf.Ticker(ticker)
            dividends = stock.dividends
            hist = stock.history(period='5y')

            if dividends is not None and len(dividends) > 0 and hist is not None and len(hist) > 0:
                # 配当分析を実行
                avg_yield, cv, current_yield, trend, has_special = calculate_historical_dividend_yield(
                    stock, dividends, hist, years=5
                )

                # スコアを計算
                if avg_yield is not None:
                    quality_score = calculate_dividend_quality_score(avg_yield, cv, trend, has_special)

                    # 分析結果を保存
                    analysis_results = {
                        'years': 5,
                        'avg_yield': avg_yield,
                        'cv': cv,
                        'current_yield': current_yield,
                        'trend': trend,
                        'has_special': has_special,
                        'quality_score': quality_score
                    }
                    updater.update_dividend_analysis(ticker, analysis_results)

                    success_count += 1
                    print(f"OK [{idx}/{total}] {ticker} ({name}): 平均利回り={avg_yield:.2f}%, スコア={quality_score}")
                else:
                    error_count += 1
                    print(f"NG [{idx}/{total}] {ticker} ({name}): 分析データ不足")
            else:
                error_count += 1
                div_count = len(dividends) if dividends is not None else 0
                hist_count = len(hist) if hist is not None else 0
                print(f"NG [{idx}/{total}] {ticker} ({name}): データなし (配当:{div_count}件, 株価:{hist_count}件)")

        except Exception as e:
            error_count += 1
            print(f"ERROR [{idx}/{total}] {ticker} ({name}): {str(e)[:100]}")

    print(f"\n完了: 成功={success_count}件, エラー={error_count}件")

if __name__ == "__main__":
    update_dividend_analysis_for_all_stocks()
