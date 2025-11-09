"""
PER情報のデータモデル
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PERInfo:
    """PER分析情報"""
    current_per: Optional[float] = None  # 現在のPER
    avg_per: Optional[float] = None  # 過去N年の平均PER
    min_per: Optional[float] = None  # 過去N年の最小PER
    max_per: Optional[float] = None  # 過去N年の最大PER
    per_cv: Optional[float] = None  # PER変動係数
    is_low_per: bool = False  # 現在のPERが平均より大幅に低いか


@dataclass
class PERAnalysisResult:
    """PER分析結果"""
    avg_per: Optional[float] = None
    cv: Optional[float] = None
    current_per: Optional[float] = None
