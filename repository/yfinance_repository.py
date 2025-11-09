"""
yfinanceからデータを取得するリポジトリ
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Tuple, Optional, Dict, Any


class YFinanceRepository:
    """yfinanceを使用した株価データ取得"""
    
    @staticmethod
    def get_stock_data(ticker: str, start_date: datetime, end_date: datetime) -> Tuple:
        """
        株価データを取得
        
        Args:
            ticker: 銘柄コード
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            (hist, info, financials, balance_sheet, cashflow, dividends)
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)

            # 基本情報を取得
            info = stock.info

            # 財務諸表を取得（年次データ）
            financials = stock.financials  # 年次損益計算書
            balance_sheet = stock.balance_sheet  # 年次貸借対照表
            cashflow = stock.cashflow  # 年次キャッシュフロー

            dividends = stock.dividends

            return hist, info, financials, balance_sheet, cashflow, dividends
        except Exception as e:
            return None, None, None, None, None, None
    
    @staticmethod
    def get_ticker_object(ticker: str):
        """
        yfinance Tickerオブジェクトを取得
        
        Args:
            ticker: 銘柄コード
            
        Returns:
            yf.Ticker オブジェクト
        """
        return yf.Ticker(ticker)
    
    @staticmethod
    def get_stock_info(ticker: str) -> Optional[Dict[str, Any]]:
        """
        銘柄の基本情報を取得
        
        Args:
            ticker: 銘柄コード
            
        Returns:
            info 辞書
        """
        try:
            stock = yf.Ticker(ticker)
            return stock.info
        except Exception:
            return None
    
    @staticmethod
    def get_historical_prices(ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        過去の株価データを取得
        
        Args:
            ticker: 銘柄コード
            period: 期間（例: "1y", "5y", "max"）
            
        Returns:
            株価DataFrame
        """
        try:
            stock = yf.Ticker(ticker)
            return stock.history(period=period)
        except Exception:
            return None
    
    @staticmethod
    def get_dividends(ticker: str) -> Optional[pd.Series]:
        """
        配当履歴を取得
        
        Args:
            ticker: 銘柄コード
            
        Returns:
            配当Series
        """
        try:
            stock = yf.Ticker(ticker)
            return stock.dividends
        except Exception:
            return None
