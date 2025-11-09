"""
配当計算ロジック
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, Optional
from domain.models.dividend_info import DividendAnalysisResult


class DividendCalculator:
    """配当関連の計算を行うクラス"""
    
    @staticmethod
    def calculate_historical_dividend_yield(ticker_obj, dividends: pd.Series, 
                                           hist_prices: pd.DataFrame, 
                                           years: int = 5) -> DividendAnalysisResult:
        """
        過去N年の配当利回りを計算（トレンド分析と特別配当検出付き）
        
        Args:
            ticker_obj: yfinance Ticker オブジェクト
            dividends: 配当履歴 Series
            hist_prices: 株価履歴 DataFrame
            years: 分析する年数
            
        Returns:
            DividendAnalysisResult インスタンス
        """
        try:
            if dividends is None or len(dividends) == 0 or hist_prices is None or len(hist_prices) == 0:
                return DividendAnalysisResult()

            # タイムゾーン情報を削除
            dividends = dividends.copy()
            hist_prices = hist_prices.copy()
            if hasattr(dividends.index, 'tz') and dividends.index.tz is not None:
                dividends.index = dividends.index.tz_localize(None)
            if hasattr(hist_prices.index, 'tz') and hist_prices.index.tz is not None:
                hist_prices.index = hist_prices.index.tz_localize(None)

            # 過去N年分のデータを取得
            cutoff_date = datetime.now() - timedelta(days=365 * years)
            recent_dividends = dividends[dividends.index >= cutoff_date]

            if len(recent_dividends) == 0:
                return DividendAnalysisResult()

            # 年次配当利回りを計算
            yearly_yields = []
            for year in range(years):
                year_start = datetime.now() - timedelta(days=365 * (year + 1))
                year_end = datetime.now() - timedelta(days=365 * year)

                # その年の配当合計
                year_divs = recent_dividends[(recent_dividends.index >= year_start) & (recent_dividends.index < year_end)]
                if len(year_divs) == 0:
                    continue

                total_div = year_divs.sum()

                # その年の平均株価（年初の価格を使用）
                year_prices = hist_prices[(hist_prices.index >= year_start) & (hist_prices.index < year_end)]
                if len(year_prices) == 0:
                    continue

                avg_price = year_prices['Close'].iloc[0] if len(year_prices) > 0 else None
                if avg_price and avg_price > 0:
                    yield_pct = (total_div / avg_price) * 100
                    yearly_yields.append(yield_pct)

            if len(yearly_yields) == 0:
                return DividendAnalysisResult()

            # データを新しい順から古い順に並べ替え（時系列分析用）
            yearly_yields.reverse()

            # 特別配当の検出と除外（IQR法）
            has_special_div = False
            if len(yearly_yields) >= 4:
                q1 = pd.Series(yearly_yields).quantile(0.25)
                q3 = pd.Series(yearly_yields).quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                # 外れ値（特別配当の可能性）を除外
                filtered_yields = [y for y in yearly_yields if lower_bound <= y <= upper_bound]
                has_special_div = len(filtered_yields) < len(yearly_yields)
            else:
                filtered_yields = yearly_yields

            # フィルタ後のデータで再計算
            if len(filtered_yields) == 0:
                filtered_yields = yearly_yields

            # 平均配当利回り
            avg_yield = sum(filtered_yields) / len(filtered_yields)

            # 配当の変動係数（CV）
            if len(filtered_yields) >= 2:
                std_dev = pd.Series(filtered_yields).std()
                cv = (std_dev / avg_yield) if avg_yield > 0 else float('inf')
            else:
                cv = 0

            # 配当トレンド分析（線形回帰の傾き）
            dividend_trend = 0
            if len(filtered_yields) >= 3:
                x = list(range(len(filtered_yields)))
                y = filtered_yields

                n = len(x)
                sum_x = sum(x)
                sum_y = sum(y)
                sum_xy = sum(x[i] * y[i] for i in range(n))
                sum_x2 = sum(xi ** 2 for xi in x)

                denominator = (n * sum_x2 - sum_x ** 2)
                if denominator != 0:
                    dividend_trend = (n * sum_xy - sum_x * sum_y) / denominator

            # 最新年の配当利回り
            current_yield = yearly_yields[-1] if len(yearly_yields) > 0 else None

            return DividendAnalysisResult(
                avg_yield=avg_yield,
                cv=cv,
                current_yield=current_yield,
                trend=dividend_trend,
                has_special_div=has_special_div
            )

        except Exception:
            return DividendAnalysisResult()

    @staticmethod
    def calculate_dividend_quality_score(avg_yield: Optional[float], 
                                        cv: Optional[float], 
                                        trend: Optional[float], 
                                        has_special_div: bool) -> Optional[float]:
        """
        配当の質を総合的にスコアリング（0-100点）
        
        Args:
            avg_yield: 平均配当利回り
            cv: 変動係数
            trend: トレンド（線形回帰の傾き）
            has_special_div: 特別配当の有無
            
        Returns:
            配当品質スコア（0-100）
        """
        try:
            if avg_yield is None or cv is None or trend is None:
                return None

            score = 0

            # 1. 配当利回り（最大40点）
            if avg_yield >= 5.0:
                score += 40
            elif avg_yield >= 4.0:
                score += 35
            elif avg_yield >= 3.0:
                score += 30
            elif avg_yield >= 2.0:
                score += 20
            else:
                score += 10

            # 2. 安定性（最大30点）
            if cv <= 0.15:
                score += 30  # 非常に安定
            elif cv <= 0.25:
                score += 25  # 安定
            elif cv <= 0.35:
                score += 20  # やや安定
            elif cv <= 0.50:
                score += 10  # 中程度
            else:
                score += 0   # 不安定

            # 3. トレンド（最大30点）
            if trend > 0.3:
                score += 30  # 強い増配傾向
            elif trend > 0.15:
                score += 25  # 増配傾向
            elif trend > 0:
                score += 20  # 緩やかな増配
            elif trend > -0.15:
                score += 10  # 横ばい
            else:
                score += 0   # 減配傾向

            # 4. 特別配当ペナルティ（-10点）
            if has_special_div:
                score -= 10

            # スコアを0-100の範囲に収める
            score = max(0, min(100, score))

            return score

        except Exception:
            return None
