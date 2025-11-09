"""
株式情報のデータモデル
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class StockInfo:
    """銘柄基本情報"""
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    market: Optional[str] = None
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StockInfo':
        """
        辞書からStockInfoを作成
        
        Args:
            data: yfinance.info 辞書
            
        Returns:
            StockInfo インスタンス
        """
        return cls(
            ticker=data.get('symbol', ''),
            name=data.get('longName') or data.get('shortName'),
            sector=data.get('sector'),
            market=data.get('market'),
            current_price=data.get('currentPrice') or data.get('regularMarketPrice'),
            market_cap=data.get('marketCap'),
            currency=data.get('currency'),
            exchange=data.get('exchange')
        )
