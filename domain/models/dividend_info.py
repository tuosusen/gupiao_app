"""
配当情報のデータモデル
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DividendInfo:
    """配当情報"""
    dividend_yield: Optional[float] = None  # 現在の配当利回り（%）
    annual_dividend: Optional[float] = None  # 年間配当金
    payout_ratio: Optional[float] = None  # 配当性向（%）
    dividend_date: Optional[str] = None  # 配当落ち日
    ex_dividend_date: Optional[str] = None  # 権利落ち日
    
    # 高度な配当分析
    avg_dividend_yield: Optional[float] = None  # 過去N年平均配当利回り
    dividend_cv: Optional[float] = None  # 配当変動係数
    dividend_trend: Optional[float] = None  # 配当トレンド（線形回帰の傾き）
    has_special_dividend: bool = False  # 特別配当の有無
    dividend_quality_score: Optional[float] = None  # 配当品質スコア（0-100）


@dataclass
class DividendAnalysisResult:
    """配当分析結果"""
    avg_yield: Optional[float] = None
    cv: Optional[float] = None
    current_yield: Optional[float] = None
    trend: Optional[float] = None
    has_special_div: bool = False
    quality_score: Optional[float] = None
