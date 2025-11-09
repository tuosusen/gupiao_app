"""
スクリーニング条件のデータモデル
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScreeningConditions:
    """銘柄スクリーニングの条件"""
    # 市場条件
    market: Optional[str] = None  # "プライム", "主要銘柄", "米国株"等
    
    # 基本的な配当条件
    min_dividend_yield: Optional[float] = None
    dividend_growth: bool = False
    
    # 高度な配当条件
    min_avg_dividend_yield: Optional[float] = None
    min_dividend_quality_score: Optional[float] = None
    max_dividend_cv: Optional[float] = None
    
    # バリュエーション条件
    max_per: Optional[float] = None
    min_per: Optional[float] = None
    max_pbr: Optional[float] = None
    min_pbr: Optional[float] = None
    
    # 高度なPER条件
    min_avg_per: Optional[float] = None
    max_avg_per: Optional[float] = None
    max_per_cv: Optional[float] = None
    low_current_high_avg_per: bool = False
    
    # 業績条件
    min_profit_margin: Optional[float] = None
    min_roe: Optional[float] = None
    revenue_growth: bool = False
    min_revenue_growth: Optional[float] = None
    profit_growth: bool = False
    
    # その他条件
    max_debt_to_equity: Optional[float] = None
    min_market_cap: Optional[float] = None
    
    def to_db_conditions(self) -> dict:
        """データベーススクリーニング用の条件辞書に変換"""
        conditions = {}
        
        if self.min_dividend_yield:
            conditions['min_dividend_yield'] = self.min_dividend_yield
        if self.min_avg_dividend_yield:
            conditions['min_avg_dividend_yield'] = self.min_avg_dividend_yield
        if self.min_dividend_quality_score:
            conditions['min_dividend_quality_score'] = self.min_dividend_quality_score
        if self.max_per:
            conditions['max_per'] = self.max_per
        if self.max_pbr:
            conditions['max_pbr'] = self.max_pbr
        if self.min_profit_margin:
            conditions['min_profit_margin'] = self.min_profit_margin
        if self.revenue_growth:
            conditions['revenue_growth'] = True
        if self.min_avg_per:
            conditions['min_avg_per'] = self.min_avg_per
        if self.max_avg_per:
            conditions['max_avg_per'] = self.max_avg_per
        if self.max_per_cv:
            conditions['max_per_cv'] = self.max_per_cv
        if self.low_current_high_avg_per:
            conditions['low_current_high_avg_per'] = True
        if self.market:
            conditions['market'] = self.market
            
        return conditions
