"""
銘柄リスト取得リポジトリ
"""

import pandas as pd
import requests
import io
from typing import Dict, Optional


class StockListRepository:
    """銘柄リストを取得するリポジトリ"""
    
    @staticmethod
    def get_premium_market_stocks() -> Optional[Dict[str, str]]:
        """
        東証プライム市場の全銘柄を取得
        
        Returns:
            {ticker: name} の辞書、またはNone
        """
        try:
            # JPXの上場銘柄一覧をダウンロード
            urls = [
                ("https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls", 'xlrd'),
                ("https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xlsx", 'openpyxl'),
            ]

            df = None
            last_error = None

            for url, engine in urls:
                try:
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    df = pd.read_excel(io.BytesIO(response.content), engine=engine)
                    break
                except Exception as e:
                    last_error = e
                    continue

            if df is None:
                raise Exception(f"全てのURLで取得失敗: {last_error}")

            # プライム市場のみをフィルタ
            market_col = None
            for col in df.columns:
                if '市場' in str(col) or 'market' in str(col).lower() or '商品区分' in str(col):
                    market_col = col
                    break

            if market_col:
                premium_df = df[df[market_col].astype(str).str.contains('プライム|Prime', na=False, case=False)]
                if len(premium_df) == 0:
                    premium_df = df
            else:
                premium_df = df

            # 銘柄辞書を作成
            stocks = {}
            code_col = None
            name_col = None

            for col in df.columns:
                col_str = str(col)
                if col_str == 'コード' or col_str == '証券コード':
                    code_col = col
                    break
                elif 'コード' in col_str and '規模' not in col_str and code_col is None:
                    code_col = col

            for col in df.columns:
                col_str = str(col)
                if '銘柄名' in col_str or 'name' in col_str.lower() or '名称' in col_str:
                    name_col = col
                    break

            if code_col is None or name_col is None:
                raise Exception(f"必要な列が見つかりません")

            for idx, row in premium_df.iterrows():
                try:
                    code_raw = row[code_col]
                    name_raw = row[name_col]

                    if pd.notna(code_raw):
                        code_str = str(code_raw).strip()
                        if code_str in ['-', '', 'nan', 'None']:
                            continue

                        try:
                            float_val = float(code_str)
                            if float_val == int(float_val):
                                code = str(int(float_val))
                            else:
                                code = code_str
                        except ValueError:
                            code = code_str
                    else:
                        continue

                    if pd.notna(name_raw):
                        name = str(name_raw)
                    else:
                        continue

                    ticker = f"{code}.T"
                    stocks[ticker] = name

                except Exception:
                    continue

            if len(stocks) == 0:
                raise Exception("銘柄が取得できませんでした")

            return stocks

        except Exception:
            return None
    
    @staticmethod
    def get_major_stocks() -> Dict[str, str]:
        """
        主要銘柄のリストを取得
        
        Returns:
            {ticker: name} の辞書
        """
        return {
            "7203.T": "トヨタ自動車",
            "6758.T": "ソニーグループ",
            "9984.T": "ソフトバンクグループ",
            "6861.T": "キーエンス",
            "9433.T": "KDDI",
            "8306.T": "三菱UFJフィナンシャル・グループ",
            "6981.T": "村田製作所",
            "4063.T": "信越化学工業",
            "9432.T": "日本電信電話",
            "8035.T": "東京エレクトロン",
            # 以下省略...
        }
    
    @staticmethod
    def get_sp500_stocks() -> Dict[str, str]:
        """
        S&P500の主要銘柄を取得
        
        Returns:
            {ticker: name} の辞書
        """
        return {
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation",
            "GOOGL": "Alphabet Inc.",
            "AMZN": "Amazon.com Inc.",
            "NVDA": "NVIDIA Corporation",
            "META": "Meta Platforms Inc.",
            "TSLA": "Tesla Inc.",
            # 以下省略...
        }
    
    @staticmethod
    def get_stock_list(market: str) -> Dict[str, str]:
        """
        市場別の銘柄リストを取得
        
        Args:
            market: "日本株（東証プライム市場全銘柄）", "日本株（東証主要銘柄）", "米国株（S&P500）"
            
        Returns:
            {ticker: name} の辞書
        """
        if market == "日本株（東証プライム市場全銘柄）":
            stocks = StockListRepository.get_premium_market_stocks()
            if stocks is None:
                return StockListRepository.get_major_stocks()
            return stocks
        elif market == "日本株（東証主要銘柄）":
            return StockListRepository.get_major_stocks()
        elif market == "米国株（S&P500）":
            return StockListRepository.get_sp500_stocks()
        else:
            return {}
