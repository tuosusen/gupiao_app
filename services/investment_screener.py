"""
投資スクリーニングサービス
配当利回り重視・低リスク銘柄の選定
"""

import pandas as pd
import yfinance as yf
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta


class InvestmentScreener:
    """投資スクリーニング機能"""

    @staticmethod
    def calculate_regular_dividend_yield(ticker_symbol: str) -> Tuple[Optional[float], str]:
        """
        通常配当利回りを計算（特別配当を除く）

        Args:
            ticker_symbol: 銘柄コード

        Returns:
            (配当利回り(%), メッセージ)
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info

            # 現在株価
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            if not current_price:
                return None, "株価データなし"

            # 配当データを取得
            dividends = ticker.dividends
            if dividends is None or dividends.empty:
                return 0.0, "配当なし"

            # 過去1年間の配当を取得
            one_year_ago = datetime.now() - timedelta(days=365)
            recent_dividends = dividends[dividends.index > one_year_ago]

            if recent_dividends.empty:
                return 0.0, "過去1年間配当なし"

            # 配当の頻度を分析して特別配当を除外
            # 日本株の場合、通常は年1-2回
            dividend_counts = len(recent_dividends)

            # 異常に高額な配当（中央値の2倍以上）を特別配当とみなす
            if dividend_counts > 0:
                median_dividend = recent_dividends.median()
                regular_dividends = recent_dividends[recent_dividends <= median_dividend * 2]

                # 年間配当額（特別配当除く）
                annual_dividend = regular_dividends.sum()

                # 配当利回り = (年間配当 / 株価) × 100
                dividend_yield = (annual_dividend / current_price) * 100

                # 特別配当があった場合はメッセージに含める
                special_dividend_count = dividend_counts - len(regular_dividends)
                if special_dividend_count > 0:
                    message = f"通常配当のみ（特別配当{special_dividend_count}回除外）"
                else:
                    message = "通常配当"

                return dividend_yield, message

            return 0.0, "配当データ不足"

        except Exception as e:
            return None, f"エラー: {str(e)[:30]}"

    @staticmethod
    def assess_bankruptcy_risk(ticker_symbol: str) -> Tuple[str, Dict[str, any], str]:
        """
        倒産リスクを評価

        Args:
            ticker_symbol: 銘柄コード

        Returns:
            (リスクレベル, 指標辞書, 詳細メッセージ)
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            balance_sheet = ticker.balance_sheet
            info = ticker.info

            if balance_sheet is None or balance_sheet.empty:
                return "不明", {}, "財務データなし"

            # 最新の財務データ
            latest = balance_sheet.iloc[:, 0]

            metrics = {}
            risk_points = 0  # リスクポイント（高いほど危険）

            # 1. 自己資本比率（高いほど安全）
            total_assets = latest.get('Total Assets')
            total_equity = latest.get('Total Equity Gross Minority Interest') or latest.get('Stockholders Equity')

            if total_assets and total_equity and total_assets > 0:
                equity_ratio = (total_equity / total_assets) * 100
                metrics['自己資本比率'] = f"{equity_ratio:.1f}%"

                if equity_ratio < 20:
                    risk_points += 3  # 非常に危険
                elif equity_ratio < 40:
                    risk_points += 1  # やや危険
                # 40%以上は安全
            else:
                metrics['自己資本比率'] = "N/A"
                risk_points += 1

            # 2. 流動比率（高いほど安全、短期支払能力）
            current_assets = latest.get('Current Assets')
            current_liabilities = latest.get('Current Liabilities')

            if current_assets and current_liabilities and current_liabilities > 0:
                current_ratio = (current_assets / current_liabilities) * 100
                metrics['流動比率'] = f"{current_ratio:.1f}%"

                if current_ratio < 100:
                    risk_points += 2  # 危険
                elif current_ratio < 150:
                    risk_points += 1  # やや注意
                # 150%以上は安全
            else:
                metrics['流動比率'] = "N/A"
                risk_points += 1

            # 3. 有利子負債比率（低いほど安全）
            total_debt = latest.get('Total Debt') or 0
            if total_equity and total_equity > 0:
                debt_equity_ratio = (total_debt / total_equity) * 100
                metrics['有利子負債比率'] = f"{debt_equity_ratio:.1f}%"

                if debt_equity_ratio > 200:
                    risk_points += 3  # 非常に危険
                elif debt_equity_ratio > 100:
                    risk_points += 1  # やや注意
                # 100%以下は安全
            else:
                metrics['有利子負債比率'] = "N/A"
                risk_points += 1

            # 4. 時価総額（大きいほど安定）
            market_cap = info.get('marketCap')
            if market_cap:
                market_cap_oku = market_cap / 100_000_000
                metrics['時価総額'] = f"{market_cap_oku:,.0f}億円"

                if market_cap_oku < 100:
                    risk_points += 1  # 小型株はやや注意
            else:
                metrics['時価総額'] = "N/A"

            # リスクレベルを判定
            if risk_points == 0:
                risk_level = "低リスク"
                detail = "✅ 財務状態良好"
            elif risk_points <= 2:
                risk_level = "中リスク"
                detail = "⚠️ 一部指標に注意"
            elif risk_points <= 4:
                risk_level = "高リスク"
                detail = "⚠️ 複数の懸念指標あり"
            else:
                risk_level = "非常に高リスク"
                detail = "❌ 財務状態に重大な懸念"

            return risk_level, metrics, detail

        except Exception as e:
            return "不明", {}, f"エラー: {str(e)[:30]}"

    @staticmethod
    def screen_high_dividend_low_risk(ticker_symbols: List[str],
                                     min_dividend_yield: float = 4.0) -> pd.DataFrame:
        """
        高配当・低リスク銘柄をスクリーニング

        Args:
            ticker_symbols: 銘柄コードのリスト
            min_dividend_yield: 最低配当利回り（デフォルト4%）

        Returns:
            スクリーニング結果のDataFrame
        """
        results = []

        for symbol in ticker_symbols:
            # 配当利回りを計算
            div_yield, div_msg = InvestmentScreener.calculate_regular_dividend_yield(symbol)

            # 倒産リスクを評価
            risk_level, risk_metrics, risk_detail = InvestmentScreener.assess_bankruptcy_risk(symbol)

            # 最低配当利回りをクリアした銘柄のみ
            if div_yield and div_yield >= min_dividend_yield:
                result = {
                    '銘柄コード': symbol,
                    '配当利回り': f"{div_yield:.2f}%",
                    '配当利回り_数値': div_yield,
                    '配当種別': div_msg,
                    'リスクレベル': risk_level,
                    'リスク詳細': risk_detail,
                }

                # リスク指標を追加
                result.update(risk_metrics)

                results.append(result)

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)

        # 配当利回り降順、リスクレベル昇順でソート
        risk_order = {'低リスク': 1, '中リスク': 2, '高リスク': 3, '非常に高リスク': 4, '不明': 5}
        df['_risk_order'] = df['リスクレベル'].map(risk_order)
        df = df.sort_values(['_risk_order', '配当利回り_数値'], ascending=[True, False])
        df = df.drop(columns=['_risk_order'])

        return df
