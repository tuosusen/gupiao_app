"""
財務指標のデータモデル
"""

from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class FinancialRatios:
    """財務指標"""
    per: Optional[float] = None  # PER（株価収益率）
    pbr: Optional[float] = None  # PBR（株価純資産倍率）
    roe: Optional[float] = None  # ROE（自己資本利益率）
    dividend_yield: Optional[float] = None  # 配当利回り（%）
    revenue_growth: Optional[float] = None  # 売上高成長率（%）
    profit_growth: Optional[float] = None  # 利益成長率（%）
    profit_margin: Optional[float] = None  # 利益率（%）
    debt_to_equity: Optional[float] = None  # 負債資本倍率
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'PER': self.per,
            'PBR': self.pbr,
            'ROE': self.roe,
            '配当利回り': self.dividend_yield,
            '売上高成長率': self.revenue_growth,
            '利益成長率': self.profit_growth,
            '利益率': self.profit_margin,
            '負債資本倍率': self.debt_to_equity
        }
