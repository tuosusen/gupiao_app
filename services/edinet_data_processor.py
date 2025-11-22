"""
EDINET財務データの処理・整形サービス
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
import re


class EDINETDataProcessor:
    """EDINET財務データを処理・整形するサービス"""

    @staticmethod
    def format_financial_value(value: str) -> Optional[float]:
        """
        財務数値を整形（文字列→数値変換）

        Args:
            value: 文字列形式の数値

        Returns:
            float値、またはNone
        """
        try:
            # カンマを除去して数値に変換
            cleaned_value = value.replace(',', '').strip()
            return float(cleaned_value)
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def parse_context_to_period(context: str) -> Optional[str]:
        """
        コンテキスト情報から期間情報を抽出

        Args:
            context: コンテキスト文字列（例: "Prior4YearDuration"）

        Returns:
            期間表記（例: "2020年度"）
        """
        # Prior4YearDuration → 4年前
        # CurrentYearDuration → 当期
        # Prior1YearInstant → 1年前時点

        if 'Current' in context:
            return '当期'
        elif 'Prior' in context:
            # Prior4YearDuration から数字を抽出
            match = re.search(r'Prior(\d+)Year', context)
            if match:
                years_ago = int(match.group(1))
                return f'{years_ago}年前'

        return context

    @staticmethod
    def convert_to_oku_yen(value: float, unit: str = 'JPY') -> Tuple[float, str]:
        """
        金額を億円単位に変換

        Args:
            value: 金額
            unit: 単位（JPY等）

        Returns:
            (変換後の値, 単位表記)
        """
        if value is None:
            return None, ''

        # 1億 = 100,000,000
        oku_value = value / 100_000_000

        return oku_value, '億円'

    @staticmethod
    def extract_key_metrics(financial_data: Dict[str, Dict[str, pd.DataFrame]]) -> pd.DataFrame:
        """
        主要財務指標を抽出してサマリーDataFrameを作成

        Args:
            financial_data: {期間: {カテゴリ: DataFrame}} の辞書

        Returns:
            主要指標のDataFrame
        """
        metrics_list = []

        for period, categories in financial_data.items():
            period_metrics = {'期間': period}

            # 損益計算書から抽出
            if '損益計算書' in categories:
                pl_df = categories['損益計算書']

                # 売上高
                revenue = pl_df[pl_df['項目'] == '売上高']
                if not revenue.empty:
                    value = EDINETDataProcessor.format_financial_value(revenue.iloc[0]['値'])
                    if value:
                        oku_value, unit = EDINETDataProcessor.convert_to_oku_yen(value)
                        period_metrics['売上高'] = f'{oku_value:,.1f}{unit}'
                        period_metrics['売上高_数値'] = oku_value

                # 営業利益
                op_income = pl_df[pl_df['項目'] == '営業利益']
                if not op_income.empty:
                    value = EDINETDataProcessor.format_financial_value(op_income.iloc[0]['値'])
                    if value:
                        oku_value, unit = EDINETDataProcessor.convert_to_oku_yen(value)
                        period_metrics['営業利益'] = f'{oku_value:,.1f}{unit}'
                        period_metrics['営業利益_数値'] = oku_value

                # 当期純利益
                net_income = pl_df[pl_df['項目'] == '当期純利益']
                if not net_income.empty:
                    value = EDINETDataProcessor.format_financial_value(net_income.iloc[0]['値'])
                    if value:
                        oku_value, unit = EDINETDataProcessor.convert_to_oku_yen(value)
                        period_metrics['当期純利益'] = f'{oku_value:,.1f}{unit}'
                        period_metrics['当期純利益_数値'] = oku_value

            # 貸借対照表から抽出
            if '貸借対照表' in categories:
                bs_df = categories['貸借対照表']

                # 総資産
                total_assets = bs_df[bs_df['項目'] == '総資産']
                if not total_assets.empty:
                    value = EDINETDataProcessor.format_financial_value(total_assets.iloc[0]['値'])
                    if value:
                        oku_value, unit = EDINETDataProcessor.convert_to_oku_yen(value)
                        period_metrics['総資産'] = f'{oku_value:,.1f}{unit}'
                        period_metrics['総資産_数値'] = oku_value

                # 純資産
                net_assets = bs_df[bs_df['項目'] == '純資産']
                if not net_assets.empty:
                    value = EDINETDataProcessor.format_financial_value(net_assets.iloc[0]['値'])
                    if value:
                        oku_value, unit = EDINETDataProcessor.convert_to_oku_yen(value)
                        period_metrics['純資産'] = f'{oku_value:,.1f}{unit}'
                        period_metrics['純資産_数値'] = oku_value

            if len(period_metrics) > 1:  # 期間以外のデータがある場合のみ追加
                metrics_list.append(period_metrics)

        if not metrics_list:
            return pd.DataFrame()

        df = pd.DataFrame(metrics_list)

        # 期間でソート（当期が最後になるように）
        if '期間' in df.columns:
            df = df.sort_values('期間', ascending=False)

        return df

    @staticmethod
    def calculate_growth_rates(metrics_df: pd.DataFrame) -> pd.DataFrame:
        """
        成長率を計算

        Args:
            metrics_df: 主要指標DataFrame

        Returns:
            成長率を含むDataFrame
        """
        if metrics_df.empty or len(metrics_df) < 2:
            return metrics_df

        # 数値カラムで成長率を計算
        numeric_cols = [col for col in metrics_df.columns if col.endswith('_数値')]

        result_df = metrics_df.copy()

        for col in numeric_cols:
            metric_name = col.replace('_数値', '')
            growth_col = f'{metric_name}_成長率'

            # 前年比成長率を計算（％）
            values = result_df[col].values
            growth_rates = []

            for i in range(len(values)):
                if i == len(values) - 1:
                    growth_rates.append(None)  # 最古のデータには成長率なし
                else:
                    current = values[i]
                    previous = values[i + 1]
                    if previous and previous != 0:
                        growth_rate = ((current - previous) / previous) * 100
                        growth_rates.append(f'{growth_rate:+.1f}%')
                    else:
                        growth_rates.append(None)

            result_df[growth_col] = growth_rates

        return result_df

    @staticmethod
    def prepare_chart_data(metrics_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        グラフ表示用のデータを準備

        Args:
            metrics_df: 主要指標DataFrame

        Returns:
            {グラフ名: DataFrame} の辞書
        """
        chart_data = {}

        if metrics_df.empty:
            return chart_data

        # 期間を逆順にして時系列順に並べる
        df = metrics_df[::-1].copy()

        # 売上高・利益の推移
        profit_cols = []
        if '売上高_数値' in df.columns:
            profit_cols.append('売上高_数値')
        if '営業利益_数値' in df.columns:
            profit_cols.append('営業利益_数値')
        if '当期純利益_数値' in df.columns:
            profit_cols.append('当期純利益_数値')

        if profit_cols:
            profit_df = df[['期間'] + profit_cols].copy()
            profit_df.columns = ['期間'] + [col.replace('_数値', '（億円）') for col in profit_cols]
            profit_df = profit_df.set_index('期間')
            chart_data['損益推移'] = profit_df

        # 総資産・純資産の推移
        asset_cols = []
        if '総資産_数値' in df.columns:
            asset_cols.append('総資産_数値')
        if '純資産_数値' in df.columns:
            asset_cols.append('純資産_数値')

        if asset_cols:
            asset_df = df[['期間'] + asset_cols].copy()
            asset_df.columns = ['期間'] + [col.replace('_数値', '（億円）') for col in asset_cols]
            asset_df = asset_df.set_index('期間')
            chart_data['資産推移'] = asset_df

        return chart_data
