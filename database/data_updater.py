"""
株価データ取得・更新モジュール
yfinanceからデータを取得してMySQLに保存
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from database.db_config import DatabaseManager
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os
import time
import random

# パスを追加してメインアプリのモジュールをインポート
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class StockDataUpdater:
    """株価データ更新クラス"""

    def __init__(self):
        self.db = DatabaseManager()

    def update_stock_basic_info(self, ticker, name, sector=None, industry=None, market=None, market_cap=None):
        """銘柄基本情報を更新"""
        query = """
        INSERT INTO stocks (ticker, name, sector, industry, market, market_cap)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            sector = VALUES(sector),
            industry = VALUES(industry),
            market = VALUES(market),
            market_cap = VALUES(market_cap),
            updated_at = CURRENT_TIMESTAMP
        """
        params = (ticker, name, sector, industry, market, market_cap)
        return self.db.execute_query(query, params, fetch=False)

    def update_financial_metrics(self, ticker, fiscal_date, metrics_dict):
        """財務指標を更新"""
        query = """
        INSERT INTO financial_metrics (
            ticker, fiscal_date, per, pbr, roe, dividend_yield,
            dividend_rate, payout_ratio, profit_margin, revenue_growth,
            net_income, total_revenue, total_assets, total_equity
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            per = VALUES(per),
            pbr = VALUES(pbr),
            roe = VALUES(roe),
            dividend_yield = VALUES(dividend_yield),
            dividend_rate = VALUES(dividend_rate),
            payout_ratio = VALUES(payout_ratio),
            profit_margin = VALUES(profit_margin),
            revenue_growth = VALUES(revenue_growth),
            net_income = VALUES(net_income),
            total_revenue = VALUES(total_revenue),
            total_assets = VALUES(total_assets),
            total_equity = VALUES(total_equity),
            updated_at = CURRENT_TIMESTAMP
        """
        params = (
            ticker,
            fiscal_date,
            metrics_dict.get('per'),
            metrics_dict.get('pbr'),
            metrics_dict.get('roe'),
            metrics_dict.get('dividend_yield'),
            metrics_dict.get('dividend_rate'),
            metrics_dict.get('payout_ratio'),
            metrics_dict.get('profit_margin'),
            metrics_dict.get('revenue_growth'),
            metrics_dict.get('net_income'),
            metrics_dict.get('total_revenue'),
            metrics_dict.get('total_assets'),
            metrics_dict.get('total_equity')
        )
        return self.db.execute_query(query, params, fetch=False)

    def update_dividends(self, ticker, dividends_df):
        """配当履歴を更新"""
        if dividends_df is None or len(dividends_df) == 0:
            return 0

        query = """
        INSERT INTO dividends (ticker, ex_date, amount, is_special)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            amount = VALUES(amount),
            is_special = VALUES(is_special)
        """

        # 特別配当の検出（IQR法）
        is_special_array = [False] * len(dividends_df)
        if len(dividends_df) >= 4:
            q1 = dividends_df.quantile(0.25)
            q3 = dividends_df.quantile(0.75)
            iqr = q3 - q1
            upper_bound = q3 + 1.5 * iqr
            is_special_array = (dividends_df > upper_bound).tolist()

        data_list = []
        for idx, (date, amount) in enumerate(dividends_df.items()):
            # dateがTimestampオブジェクトか文字列かをチェック
            if hasattr(date, 'strftime'):
                date_str = date.strftime('%Y-%m-%d')
            else:
                # 既に文字列の場合はそのまま使用
                date_str = str(date)[:10]  # YYYY-MM-DD形式に切り取り

            data_list.append((
                ticker,
                date_str,
                float(amount),
                bool(is_special_array[idx])
            ))

        return self.db.execute_many(query, data_list)

    def update_stock_prices(self, ticker, hist_df):
        """株価履歴を更新"""
        if hist_df is None or len(hist_df) == 0:
            return 0

        query = """
        INSERT INTO stock_prices (ticker, date, open, high, low, close, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            open = VALUES(open),
            high = VALUES(high),
            low = VALUES(low),
            close = VALUES(close),
            volume = VALUES(volume)
        """

        data_list = []
        for date, row in hist_df.iterrows():
            # dateがTimestampオブジェクトか文字列かをチェック
            if hasattr(date, 'strftime'):
                date_str = date.strftime('%Y-%m-%d')
            else:
                date_str = str(date)[:10]

            data_list.append((
                ticker,
                date_str,
                float(row['Open']) if pd.notna(row['Open']) else None,
                float(row['High']) if pd.notna(row['High']) else None,
                float(row['Low']) if pd.notna(row['Low']) else None,
                float(row['Close']) if pd.notna(row['Close']) else None,
                int(row['Volume']) if pd.notna(row['Volume']) else None
            ))

        return self.db.execute_many(query, data_list)

    def update_dividend_analysis(self, ticker, analysis_results):
        """配当分析結果を更新"""
        query = """
        INSERT INTO dividend_analysis (
            ticker, analysis_years, avg_dividend_yield, dividend_cv,
            current_dividend_yield, dividend_trend, has_special_dividend,
            dividend_quality_score
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            avg_dividend_yield = VALUES(avg_dividend_yield),
            dividend_cv = VALUES(dividend_cv),
            current_dividend_yield = VALUES(current_dividend_yield),
            dividend_trend = VALUES(dividend_trend),
            has_special_dividend = VALUES(has_special_dividend),
            dividend_quality_score = VALUES(dividend_quality_score),
            calculated_at = CURRENT_TIMESTAMP
        """
        params = (
            ticker,
            analysis_results.get('years', 5),
            analysis_results.get('avg_yield'),
            analysis_results.get('cv'),
            analysis_results.get('current_yield'),
            analysis_results.get('trend'),
            analysis_results.get('has_special'),
            analysis_results.get('quality_score')
        )
        return self.db.execute_query(query, params, fetch=False)

    def fetch_and_save_single_stock(self, ticker, name):
        """単一銘柄のデータを取得してDBに保存"""
        try:
            # レート制限回避のため、ランダムな遅延を追加（1.5-3.0秒）
            time.sleep(random.uniform(1.5, 3.0))

            # yfinanceからデータ取得（リトライ機能付き）
            stock = None
            info = None
            max_retries = 3

            for attempt in range(max_retries):
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    break  # 成功したらループを抜ける
                except Exception as e:
                    # レート制限エラーの場合は指数バックオフで再試行
                    if "Too Many Requests" in str(e) or "Rate limited" in str(e) or "429" in str(e):
                        if attempt < max_retries - 1:
                            wait_time = 5 * (2 ** attempt)  # 5秒、10秒、20秒
                            time.sleep(wait_time)
                            continue
                        else:
                            # 最後の試行でも失敗したら長時間待機して1回だけ再試行
                            time.sleep(30)
                            try:
                                stock = yf.Ticker(ticker)
                                info = stock.info
                            except:
                                return False, f"レート制限エラー（{max_retries}回再試行失敗）"
                    else:
                        return False, f"yfinanceエラー: {str(e)[:50]}"

            if info is None:
                return False, "データ取得失敗"

            # 基本情報を保存
            try:
                self.update_stock_basic_info(
                    ticker=ticker,
                    name=name,
                    sector=info.get('sector'),
                    industry=info.get('industry'),
                    market=info.get('market'),
                    market_cap=info.get('marketCap')
                )
            except Exception as e:
                return False, f"基本情報保存エラー: {str(e)[:50]}"

            # 財務指標を保存
            try:
                metrics = {
                    'per': info.get('trailingPE'),
                    'pbr': info.get('priceToBook'),
                    'roe': info.get('returnOnEquity'),
                    'dividend_yield': info.get('dividendYield'),  # yfinanceは既にパーセント単位で返す
                    'dividend_rate': info.get('dividendRate'),
                    'payout_ratio': info.get('payoutRatio'),
                    'profit_margin': info.get('profitMargins'),
                    'revenue_growth': info.get('revenueGrowth')
                }

                fiscal_date = datetime.now().date()
                self.update_financial_metrics(ticker, fiscal_date, metrics)
            except Exception as e:
                # 財務指標がなくても続行
                pass

            # 配当履歴を保存
            try:
                dividends = stock.dividends
                if dividends is not None and len(dividends) > 0:
                    result = self.update_dividends(ticker, dividends)
                    # デバッグ: 配当保存の成功を確認
            except Exception as e:
                # 配当がなくても続行（エラーを記録）
                pass

            # 株価履歴を保存（過去5年）
            hist = None
            try:
                hist = stock.history(period='5y')
                if hist is not None and len(hist) > 0:
                    self.update_stock_prices(ticker, hist)
            except Exception as e:
                # 株価履歴がなくても続行
                hist = None
                pass

            # 配当分析結果を計算して保存
            try:
                if dividends is not None and len(dividends) > 0 and hist is not None and len(hist) > 0:
                    # メインアプリの関数をインポート
                    from stock_analysis_app import calculate_historical_dividend_yield, calculate_dividend_quality_score

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
                        self.update_dividend_analysis(ticker, analysis_results)
                        print(f"✓ 配当分析保存: {ticker}")
            except Exception as e:
                # 配当分析エラーをログに出力
                print(f"✗ 配当分析エラー {ticker}: {str(e)}")
                pass

            return True, None

        except Exception as e:
            return False, f"予期しないエラー: {str(e)[:50]}"

    def update_all_stocks(self, stock_list, max_workers=5):
        """全銘柄を並列処理で更新"""
        total = len(stock_list)
        success_count = 0
        error_count = 0

        progress_bar = st.progress(0)
        status_text = st.empty()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.fetch_and_save_single_stock, ticker, name): (ticker, name)
                for ticker, name in stock_list.items()
            }

            for idx, future in enumerate(as_completed(futures), 1):
                ticker, name = futures[future]
                try:
                    success, error = future.result()
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        # エラーの詳細を表示（最初の10件のみ）
                        if error_count <= 10:
                            st.warning(f"❌ {ticker} ({name}): {error}")
                except Exception as e:
                    error_count += 1
                    # エラーの詳細を表示（最初の10件のみ）
                    if error_count <= 10:
                        st.error(f"❌ {ticker} ({name}): {e}")

                progress = idx / total
                progress_bar.progress(progress)
                status_text.text(f"進捗: {idx}/{total} (成功: {success_count}, 失敗: {error_count})")

        progress_bar.empty()
        status_text.empty()

        return success_count, error_count


# グローバルインスタンス
data_updater = StockDataUpdater()


def batch_update_dividend_analysis():
    """配当データがある全銘柄の配当分析を一括計算"""
    import yfinance as yf
    from stock_analysis_app import calculate_historical_dividend_yield, calculate_dividend_quality_score

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
        return 0, 0

    total = len(stocks_with_dividends)
    print(f"\n配当分析を開始: {total}件")

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
                    div_count = len(dividends) if dividends is not None else 0
                    hist_count = len(hist) if hist is not None else 0
                    print(f"NG [{idx}/{total}] {ticker} ({name}): avg_yield=None (配当:{div_count}件, 株価:{hist_count}件, cv={cv}, current={current_yield}, trend={trend})")
            else:
                error_count += 1
                div_count = len(dividends) if dividends is not None else 0
                hist_count = len(hist) if hist is not None else 0
                print(f"NG [{idx}/{total}] {ticker} ({name}): データなし (配当:{div_count}件, 株価:{hist_count}件)")

        except Exception as e:
            error_count += 1
            print(f"ERROR [{idx}/{total}] {ticker} ({name}): {str(e)[:100]}")

    print(f"\n配当分析完了: 成功={success_count}件, エラー={error_count}件")
    return success_count, error_count
