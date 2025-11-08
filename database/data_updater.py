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
        if len(dividends_df) >= 4:
            q1 = dividends_df.quantile(0.25)
            q3 = dividends_df.quantile(0.75)
            iqr = q3 - q1
            upper_bound = q3 + 1.5 * iqr
            dividends_df['is_special'] = dividends_df > upper_bound
        else:
            dividends_df['is_special'] = False

        data_list = [
            (ticker, date.strftime('%Y-%m-%d'), float(amount), bool(is_special))
            for date, (amount, is_special) in dividends_df.to_frame('amount').join(
                dividends_df.to_frame('is_special')['is_special']
            ).iterrows()
        ]

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

        data_list = [
            (
                ticker,
                date.strftime('%Y-%m-%d'),
                float(row['Open']) if pd.notna(row['Open']) else None,
                float(row['High']) if pd.notna(row['High']) else None,
                float(row['Low']) if pd.notna(row['Low']) else None,
                float(row['Close']) if pd.notna(row['Close']) else None,
                int(row['Volume']) if pd.notna(row['Volume']) else None
            )
            for date, row in hist_df.iterrows()
        ]

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
            stock = yf.Ticker(ticker)
            info = stock.info

            # 基本情報
            self.update_stock_basic_info(
                ticker=ticker,
                name=name,
                sector=info.get('sector'),
                industry=info.get('industry'),
                market=info.get('market'),
                market_cap=info.get('marketCap')
            )

            # 財務指標
            metrics = {
                'per': info.get('trailingPE'),
                'pbr': info.get('priceToBook'),
                'roe': info.get('returnOnEquity'),
                'dividend_yield': info.get('dividendYield') * 100 if info.get('dividendYield') else None,
                'dividend_rate': info.get('dividendRate'),
                'payout_ratio': info.get('payoutRatio'),
                'profit_margin': info.get('profitMargins'),
                'revenue_growth': info.get('revenueGrowth')
            }

            fiscal_date = datetime.now().date()
            self.update_financial_metrics(ticker, fiscal_date, metrics)

            # 配当履歴
            dividends = stock.dividends
            if dividends is not None and len(dividends) > 0:
                self.update_dividends(ticker, dividends)

            # 株価履歴（過去5年）
            hist = stock.history(period='5y')
            if hist is not None and len(hist) > 0:
                self.update_stock_prices(ticker, hist)

            # TODO: 配当分析結果の計算と保存
            # （既存のcalculate_historical_dividend_yield関数を使用）

            return True, None

        except Exception as e:
            return False, str(e)

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
                        st.warning(f"❌ {ticker} ({name}): {error}")
                except Exception as e:
                    error_count += 1
                    st.error(f"❌ {ticker} ({name}): {e}")

                progress = idx / total
                progress_bar.progress(progress)
                status_text.text(f"進捗: {idx}/{total} (成功: {success_count}, 失敗: {error_count})")

        progress_bar.empty()
        status_text.empty()

        return success_count, error_count


# グローバルインスタンス
data_updater = StockDataUpdater()
