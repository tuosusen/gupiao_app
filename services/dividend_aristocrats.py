"""
配当貴族・配当成長株スクリーニングサービス
連続増配銘柄の分析と発見
"""

import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta


class DividendAristocrats:
    """配当貴族スクリーニング"""

    @staticmethod
    def calculate_dividend_cagr(dividends: pd.Series, years: int = 5) -> Optional[float]:
        """
        配当のCAGR（年平均成長率）を計算

        Args:
            dividends: 配当履歴（pd.Series）
            years: 計算期間（年）

        Returns:
            CAGR（%）またはNone
        """
        if dividends is None or dividends.empty:
            return None

        if len(dividends) < years:
            return None

        # 年ごとの配当合計を計算
        dividends_df = dividends.to_frame(name='dividend')
        dividends_df['year'] = dividends_df.index.year
        yearly_dividends = dividends_df.groupby('year')['dividend'].sum()

        if len(yearly_dividends) < years:
            return None

        # 最古と最新のN年間を比較
        recent_years = yearly_dividends.tail(years)
        first_year_div = recent_years.iloc[0]
        last_year_div = recent_years.iloc[-1]

        if first_year_div <= 0:
            return None

        # CAGR計算: ((最終値 / 初期値) ^ (1/年数) - 1) * 100
        cagr = ((last_year_div / first_year_div) ** (1 / (years - 1)) - 1) * 100

        return float(cagr)

    @staticmethod
    def count_consecutive_increases(dividends: pd.Series) -> int:
        """
        連続増配年数をカウント

        Args:
            dividends: 配当履歴

        Returns:
            連続増配年数
        """
        if dividends is None or dividends.empty:
            return 0

        # 年ごとの配当合計
        dividends_df = dividends.to_frame(name='dividend')
        dividends_df['year'] = dividends_df.index.year
        yearly_dividends = dividends_df.groupby('year')['dividend'].sum().sort_index()

        if len(yearly_dividends) < 2:
            return 0

        consecutive_years = 0

        # 最新年から過去に向かってチェック
        for i in range(len(yearly_dividends) - 1, 0, -1):
            current_year_div = yearly_dividends.iloc[i]
            previous_year_div = yearly_dividends.iloc[i - 1]

            if current_year_div > previous_year_div:
                consecutive_years += 1
            else:
                break

        return consecutive_years

    @staticmethod
    def calculate_payout_ratio(ticker_symbol: str) -> Tuple[Optional[float], str]:
        """
        配当性向を計算

        Args:
            ticker_symbol: 銘柄コード

        Returns:
            (配当性向(%), メッセージ)
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info

            # EPSと配当金を取得
            eps = info.get('trailingEps')
            dividend_per_share = info.get('dividendRate')  # 年間配当金

            if not eps or not dividend_per_share or eps <= 0:
                return None, "EPSまたは配当データなし"

            # 配当性向 = (配当金 / EPS) × 100
            payout_ratio = (dividend_per_share / eps) * 100

            # 評価メッセージ
            if payout_ratio < 30:
                message = "健全（増配余地大）"
            elif payout_ratio < 60:
                message = "健全"
            elif payout_ratio < 80:
                message = "やや高め（注意）"
            else:
                message = "高い（減配リスク）"

            return float(payout_ratio), message

        except Exception as e:
            return None, f"エラー: {str(e)[:30]}"

    @staticmethod
    def calculate_fcf_payout_ratio(ticker_symbol: str) -> Tuple[Optional[float], str]:
        """
        FCF配当性向を計算
        
        Args:
            ticker_symbol: 銘柄コード
            
        Returns:
            (FCF配当性向(%), メッセージ)
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # フリーキャッシュフローと配当総額を取得
            fcf = info.get('freeCashflow')
            dividend_paid = None
            
            # キャッシュフロー計算書から配当支払額を取得試行
            try:
                cashflow = ticker.cashflow
                if cashflow is not None and not cashflow.empty:
                    # 'Cash Dividends Paid' または類似の項目を探す
                    # yfinanceのバージョンによって項目名が異なる場合があるため注意
                    if 'Cash Dividends Paid' in cashflow.index:
                        dividend_paid = abs(cashflow.loc['Cash Dividends Paid'].iloc[0])
                    elif 'Dividends Paid' in cashflow.index:
                        dividend_paid = abs(cashflow.loc['Dividends Paid'].iloc[0])
            except Exception:
                pass
                
            # 代替手段: 配当金 * 発行済株式数
            if not dividend_paid:
                dividend_rate = info.get('dividendRate')
                shares = info.get('sharesOutstanding')
                if dividend_rate and shares:
                    dividend_paid = dividend_rate * shares

            if not fcf or not dividend_paid or fcf <= 0:
                return None, "データ不足"

            # FCF配当性向 = (配当支払額 / FCF) × 100
            fcf_payout_ratio = (dividend_paid / fcf) * 100
            
            # 評価メッセージ
            if fcf_payout_ratio < 30:
                message = "余裕あり（増配余地大）"
            elif fcf_payout_ratio < 60:
                message = "健全"
            elif fcf_payout_ratio < 80:
                message = "やや高め"
            else:
                message = "高い（余裕なし）"
                
            return float(fcf_payout_ratio), message

        except Exception as e:
            return None, f"エラー: {str(e)[:30]}"

    @staticmethod
    def analyze_dividend_growth(ticker_symbol: str, years: int = 5) -> Dict:
        """
        配当成長を総合分析
        
        Args:
            ticker_symbol: 銘柄コード
            years: 分析期間
            
        Returns:
            分析結果の辞書
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            dividends = ticker.dividends
            
            result = {
                '銘柄コード': ticker_symbol,
                '銘柄名': info.get('longName', ticker_symbol),
                '現在配当利回り': None,
                '税引後利回り': None,
                '配当CAGR': None,
                '連続増配年数': 0,
                '配当性向': None,
                '配当性向評価': '',
                'FCF配当性向': None,
                'FCF配当性向評価': '',
                'ステータス': ''
            }
            
            # 現在配当利回り & 税引後利回り
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            dividend_rate = info.get('dividendRate')
            
            if current_price and dividend_rate and current_price > 0:
                current_yield = (dividend_rate / current_price) * 100
                result['現在配当利回り'] = round(current_yield, 2)
                
                # 税引後利回り (日本株: 20.315%税率と仮定)
                tax_rate = 0.20315
                after_tax_yield = current_yield * (1 - tax_rate)
                result['税引後利回り'] = round(after_tax_yield, 2)

            # 配当CAGR
            if dividends is not None and not dividends.empty:
                cagr = DividendAristocrats.calculate_dividend_cagr(dividends, years)
                if cagr is not None:
                    result['配当CAGR'] = round(cagr, 2)
                
                # 連続増配年数
                consecutive_years = DividendAristocrats.count_consecutive_increases(dividends)
                result['連続増配年数'] = consecutive_years

            # 配当性向
            payout_ratio, payout_message = DividendAristocrats.calculate_payout_ratio(ticker_symbol)
            if payout_ratio is not None:
                result['配当性向'] = round(payout_ratio, 2)
                result['配当性向評価'] = payout_message
                
            # FCF配当性向
            fcf_ratio, fcf_message = DividendAristocrats.calculate_fcf_payout_ratio(ticker_symbol)
            if fcf_ratio is not None:
                result['FCF配当性向'] = round(fcf_ratio, 2)
                result['FCF配当性向評価'] = fcf_message

            # ステータス判定
            if result['連続増配年数'] >= 10:
                result['ステータス'] = "🏆 配当貴族候補"
            elif result['連続増配年数'] >= 5:
                result['ステータス'] = "⭐ 配当成長株"
            elif result.get('配当CAGR') and result['配当CAGR'] > 5:
                result['ステータス'] = "📈 高成長配当"
            else:
                result['ステータス'] = "📊 一般"
                
            return result

        except Exception as e:
            return {
                '銘柄コード': ticker_symbol,
                '銘柄名': ticker_symbol,
                'エラー': str(e)[:50]
            }

    @staticmethod
    def screen_dividend_aristocrats(
        ticker_list: Optional[List[str]] = None,
        min_consecutive_years: int = 5,
        min_cagr: float = 3.0,
        max_payout_ratio: float = 80.0,
        years: int = 5,
        use_cache: bool = True,
        max_cache_age_hours: int = 24
    ) -> pd.DataFrame:
        """
        配当貴族スクリーニング

        Args:
            ticker_list: 銘柄コードリスト（Noneの場合はDBから取得）
            min_consecutive_years: 最低連続増配年数
            min_cagr: 最低配当CAGR (%)
            max_payout_ratio: 最大配当性向 (%)
            years: 分析期間
            use_cache: キャッシュを使用するか（False=常にyfinance）
            max_cache_age_hours: キャッシュの最大有効期間（時間）

        Returns:
            スクリーニング結果のDataFrame
        """
        from repository.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        
        # ticker_listがNoneの場合はプライム市場銘柄を取得
        if ticker_list is None:
            ticker_list = db_manager.get_prime_market_tickers()
            
            if not ticker_list:
                # プライム市場銘柄が取得できない場合は全銘柄
                ticker_list = db_manager.get_dividend_aristocrat_tickers()
            
            if not ticker_list:
                # DBから取得できない場合はデフォルトリストを使用
                ticker_list = [
                    "7203.T", "6758.T", "9432.T", "9433.T", "9434.T",
                    "8316.T", "8411.T", "8001.T", "8002.T", "2914.T"
                ]
        
        results = []
        
        # キャッシュを使用する場合
        if use_cache:
            # DBから指標を取得
            cached_metrics = db_manager.get_dividend_aristocrats_metrics(
                tickers=ticker_list,
                min_consecutive_years=0,  # フィルタリングは後で行う
                max_cache_age_hours=max_cache_age_hours
            )
            
            # キャッシュされた銘柄のセット
            cached_tickers = {m['ticker'] for m in cached_metrics}
            
            # キャッシュされたデータを結果に追加
            for metrics in cached_metrics:
                # フィルタリング
                if metrics['consecutive_increase_years'] < min_consecutive_years:
                    continue
                
                if metrics.get('dividend_cagr_5y') is None:
                    continue
                if metrics['dividend_cagr_5y'] < min_cagr:
                    continue
                
                if metrics.get('payout_ratio') is not None:
                    if metrics['payout_ratio'] > max_payout_ratio:
                        continue
                
                # 結果フォーマットに変換
                result = {
                    '銘柄コード': metrics['ticker'],
                    '銘柄名': metrics['company_name'],
                    '現在配当利回り': metrics.get('current_dividend_yield'),
                    '税引後利回り': metrics.get('after_tax_yield'),
                    '配当CAGR': metrics.get('dividend_cagr_5y'),
                    '連続増配年数': metrics['consecutive_increase_years'],
                    '配当性向': metrics.get('payout_ratio'),
                    '配当性向評価': metrics.get('payout_ratio_status', ''),
                    'FCF配当性向': metrics.get('fcf_payout_ratio'),
                    'FCF配当性向評価': metrics.get('fcf_payout_status', ''),
                    'ステータス': metrics.get('aristocrat_status', '')
                }
                results.append(result)
            
            # キャッシュミスの銘柄をyfinanceから取得
            cache_miss_tickers = [t for t in ticker_list if t not in cached_tickers]
            
            if cache_miss_tickers:
                print(f"⚠️ {len(cache_miss_tickers)} 銘柄がキャッシュにありません。yfinanceから取得中...")
                for ticker_symbol in cache_miss_tickers:
                    analysis = DividendAristocrats.analyze_dividend_growth(ticker_symbol, years)
                    
                    # エラーチェック
                    if 'エラー' in analysis:
                        continue
                    
                    # フィルタリング
                    if analysis['連続増配年数'] < min_consecutive_years:
                        continue
                    
                    if analysis.get('配当CAGR') is None:
                        continue
                    if analysis['配当CAGR'] < min_cagr:
                        continue
                    
                    if analysis.get('配当性向') is not None:
                        if analysis['配当性向'] > max_payout_ratio:
                            continue
                    
                    results.append(analysis)
        else:
            # キャッシュを使用しない場合は全てyfinanceから取得
            for ticker_symbol in ticker_list:
                analysis = DividendAristocrats.analyze_dividend_growth(ticker_symbol, years)

                # フィルタリング
                if 'エラー' in analysis:
                    continue

                # 連続増配年数チェック
                if analysis['連続増配年数'] < min_consecutive_years:
                    continue

                # CAGR チェック
                if analysis.get('配当CAGR') is None:
                    continue
                if analysis['配当CAGR'] < min_cagr:
                    continue

                # 配当性向チェック
                if analysis.get('配当性向') is not None:
                    if analysis['配当性向'] > max_payout_ratio:
                        continue

                results.append(analysis)

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)

        # ソート: 連続増配年数降順 → CAGR降順
        df = df.sort_values(
            ['連続増配年数', '配当CAGR'],
            ascending=[False, False]
        )

        return df
