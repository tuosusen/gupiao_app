"""
PER計算ロジック
"""

import pandas as pd
from datetime import datetime
from typing import Optional
from domain.models.per_info import PERAnalysisResult


class PERCalculator:
    """PER関連の計算を行うクラス"""
    
    @staticmethod
    def calculate_historical_per(ticker_obj, years: int = 5) -> PERAnalysisResult:
        """
        過去N年のPERを計算（過去の各年末時点のPER）
        
        Args:
            ticker_obj: yfinance Ticker オブジェクト
            years: 分析する年数
            
        Returns:
            PERAnalysisResult インスタンス
        """
        try:
            # 過去N年+1年の株価データを取得
            hist = ticker_obj.history(period=f'{years + 1}y')
            if hist is None or len(hist) == 0 or 'Close' not in hist.columns:
                return PERAnalysisResult()

            # 現在のEPSを取得
            info = ticker_obj.info
            current_eps = info.get('trailingEps')
            if not current_eps or current_eps <= 0:
                return PERAnalysisResult()

            # 年次PERを計算（過去N年の各年末時点）
            yearly_pers = []
            current_date = datetime.now()

            for year_offset in range(years):
                try:
                    # N年前の年末日付を計算（12月31日）
                    target_year = current_date.year - year_offset
                    year_end = pd.Timestamp(target_year, 12, 31, tz='Asia/Tokyo')

                    # その年末以前の最も近い株価を取得
                    hist_before = hist[hist.index <= year_end]
                    if len(hist_before) > 0:
                        close_price = hist_before['Close'].iloc[-1]

                        # PER = 株価 / EPS
                        per = close_price / current_eps
                        if per > 0:
                            yearly_pers.append(per)

                except Exception:
                    continue

            if len(yearly_pers) == 0:
                return PERAnalysisResult()

            # 平均PER
            avg_per = sum(yearly_pers) / len(yearly_pers)

            # PERの変動係数
            cv = 0
            if len(yearly_pers) >= 2:
                std_dev = pd.Series(yearly_pers).std()
                cv = (std_dev / avg_per) if avg_per > 0 else float('inf')

            # 現在のPER（最新＝0年前）
            current_per = yearly_pers[0] if len(yearly_pers) > 0 else None

            return PERAnalysisResult(
                avg_per=avg_per,
                cv=cv,
                current_per=current_per
            )

        except Exception:
            return PERAnalysisResult()
