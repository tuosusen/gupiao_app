"""
財務指標計算ロジック
"""

import pandas as pd
from typing import Dict, Any, Optional
from domain.models.financial_ratios import FinancialRatios


class FinancialCalculator:
    """財務指標を計算するクラス"""
    
    @staticmethod
    def calculate_ratios(info: Dict[str, Any], 
                        financials: Optional[pd.DataFrame], 
                        balance_sheet: Optional[pd.DataFrame]) -> FinancialRatios:
        """
        財務指標を計算
        
        Args:
            info: yfinance.info 辞書
            financials: 損益計算書 DataFrame
            balance_sheet: 貸借対照表 DataFrame
            
        Returns:
            FinancialRatios インスタンス
        """
        ratios = FinancialRatios()
        
        try:
            # PER (株価収益率)
            ratios.per = info.get('trailingPE')
            
            # PBR (株価純資産倍率)
            ratios.pbr = info.get('priceToBook')
            
            # ROE (自己資本利益率)
            ratios.roe = info.get('returnOnEquity')
            if ratios.roe:
                ratios.roe = ratios.roe * 100  # パーセント表示
            
            # 配当利回り
            dividend_yield_raw = info.get('dividendYield')
            if dividend_yield_raw is not None:
                # yfinanceは小数形式で返す（例: 0.0303 = 3.03%）
                if dividend_yield_raw < 1:
                    ratios.dividend_yield = dividend_yield_raw * 100
                else:
                    ratios.dividend_yield = dividend_yield_raw
            
            # 売上高成長率（直近2期）
            if financials is not None and len(financials.columns) >= 2:
                if 'Total Revenue' in financials.index:
                    revenue_current = financials.loc['Total Revenue', financials.columns[0]]
                    revenue_previous = financials.loc['Total Revenue', financials.columns[1]]
                    if revenue_previous != 0:
                        ratios.revenue_growth = ((revenue_current - revenue_previous) / revenue_previous) * 100
            
            # 利益成長率（直近2期）
            if financials is not None and len(financials.columns) >= 2:
                if 'Net Income' in financials.index:
                    net_income_current = financials.loc['Net Income', financials.columns[0]]
                    net_income_previous = financials.loc['Net Income', financials.columns[1]]
                    if net_income_previous != 0:
                        ratios.profit_growth = ((net_income_current - net_income_previous) / net_income_previous) * 100
            
            # 利益率
            if financials is not None and len(financials.columns) >= 1:
                if 'Total Revenue' in financials.index and 'Net Income' in financials.index:
                    revenue = financials.loc['Total Revenue', financials.columns[0]]
                    net_income = financials.loc['Net Income', financials.columns[0]]
                    if revenue != 0:
                        ratios.profit_margin = (net_income / revenue) * 100
                        
        except Exception as e:
            # エラーが発生しても部分的な結果を返す
            pass
        
        return ratios
