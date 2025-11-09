"""
テクニカル指標計算ロジック
"""

import pandas as pd
from typing import Tuple


class TechnicalCalculator:
    """テクニカル指標を計算するクラス"""
    
    @staticmethod
    def calculate_sma(prices: pd.Series, window: int) -> pd.Series:
        """
        単純移動平均（SMA）を計算
        
        Args:
            prices: 価格系列
            window: 期間
            
        Returns:
            SMA系列
        """
        return prices.rolling(window=window).mean()
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        ボリンジャーバンドを計算
        
        Args:
            prices: 価格系列
            window: 期間
            num_std: 標準偏差の倍数
            
        Returns:
            (上限バンド, 中間線, 下限バンド)
        """
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        return upper, sma, lower
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
        """
        RSI（Relative Strength Index）を計算
        
        Args:
            prices: 価格系列
            window: 期間
            
        Returns:
            RSI系列
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
