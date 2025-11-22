"""
株式情報のデータモデル
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import yfinance as yf


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
        # 日本語名を取得（yfinanceは英語名しか返さないため、独自に取得）
        ticker_symbol = data.get('symbol', '')
        company_name = cls._get_japanese_name(ticker_symbol, data)

        return cls(
            ticker=ticker_symbol,
            name=company_name,
            sector=data.get('sector'),
            market=data.get('market'),
            current_price=data.get('currentPrice') or data.get('regularMarketPrice'),
            market_cap=data.get('marketCap'),
            currency=data.get('currency'),
            exchange=data.get('exchange')
        )

    @staticmethod
    def _get_japanese_name(ticker: str, info_data: Dict[str, Any]) -> Optional[str]:
        """
        日本語の会社名を取得

        Args:
            ticker: 銘柄コード
            info_data: yfinance.info辞書

        Returns:
            日本語会社名（取得できない場合は英語名）
        """
        # まずyfinanceから取得（英語名の可能性が高い）
        english_name = info_data.get('longName') or info_data.get('shortName')

        # 日本株の場合（.Tで終わる）、追加情報から日本語名を取得を試みる
        if ticker.endswith('.T'):
            try:
                # yfinanceの追加情報から取得
                ticker_obj = yf.Ticker(ticker)
                # quoteType情報に日本語名が含まれることがある
                quote_type = ticker_obj.get_info().get('quoteType')

                # 代表的な日本企業の名前マッピング（一時的な対応）
                japanese_names = {
                    '4310.T': 'ドリームインキュベータ',
                    '7203.T': 'トヨタ自動車',
                    '6758.T': 'ソニーグループ',
                    '9984.T': 'ソフトバンクグループ',
                    '7974.T': '任天堂',
                    '6861.T': 'キーエンス',
                    '8306.T': '三菱UFJフィナンシャル・グループ',
                    # 必要に応じて追加
                }

                if ticker in japanese_names:
                    return japanese_names[ticker]
            except:
                pass

        return english_name
