"""
EDINET財務分析ページ
"""

import streamlit as st
import pandas as pd
from typing import Dict, Optional
from repository.edinet_repository import EDINETRepository


class EDINETPage:
    """EDINET APIを使用した財務分析ページ"""
    
    @staticmethod
    def show():
        """ページを表示"""
        st.title("EDINET APIを使用した財務分析アプリ")
        
        # APIキーの入力
        api_key = st.sidebar.text_input("EDINET APIキー", type="password")
        
        if not api_key:
            st.info("EDINET APIキーを入力してください")
            st.write("APIキーの取得方法:")
            st.write("1. https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1 にアクセス")
            st.write("2. アカウントを作成し、APIキーを発行")
            return
        
        edinet_repo = EDINETRepository(api_key)
        
        # 企業コード入力
        company_code = st.text_input("企業コード（例: 7203 または 7203.T）", "7203")
        
        years = st.slider("分析年数", 1, 10, 5)

        doc_type_options = {
            '有価証券報告書': '120',
            '訂正有価証券報告書': '130',
            '四半期報告書': '140',
            '訂正四半期報告書': '150',
            '半期報告書': '160',
            '訂正半期報告書': '170'
        }
        selected_doc_types = st.multiselect(
            "書類の種類を選択",
            options=list(doc_type_options.keys()),
            default=['有価証券報告書', '四半期報告書']
        )
        selected_doc_type_codes = [doc_type_options[key] for key in selected_doc_types]
        
        if st.button("財務データ取得"):
            with st.spinner("財務データを取得中..."):
                financial_data = edinet_repo.get_financial_statements(
                    company_code, years, selected_doc_type_codes
                )
                
                if financial_data:
                    st.success(f"{len(financial_data)}期分の財務データを取得しました")
                    
                    # 財務指標の計算
                    ratios = EDINETPage._calculate_financial_ratios(financial_data)
                    
                    # 結果の表示
                    EDINETPage._display_financial_analysis(financial_data, ratios)
                else:
                    st.error("財務データを取得できませんでした")
    
    @staticmethod
    def _extract_revenue_data(data: Dict) -> Optional[list]:
        """売上高データを抽出"""
        try:
            for df in data.values():
                if '売上高' in df.columns:
                    return df['売上高'].values
            return None
        except Exception:
            return None
    
    @staticmethod
    def _calculate_financial_ratios(financial_data: Dict) -> Dict:
        """財務指標を計算"""
        ratios = {}
        
        try:
            for period, data in financial_data.items():
                period_ratios = {}
                
                revenue_data = EDINETPage._extract_revenue_data(data)
                if revenue_data and len(revenue_data) > 1:
                    current_revenue = revenue_data[-1]
                    previous_revenue = revenue_data[-2]
                    growth_rate = ((current_revenue - previous_revenue) / previous_revenue) * 100
                    period_ratios['売上高成長率'] = growth_rate
                
                ratios[period] = period_ratios
                
        except Exception as e:
            st.error(f"財務指標計算エラー: {e}")
        
        return ratios
    
    @staticmethod
    def _display_financial_analysis(financial_data: Dict, ratios: Dict):
        """財務分析結果を表示"""
        st.header("財務分析結果")
        
        # 財務指標テーブル
        if ratios:
            ratios_df = pd.DataFrame(ratios).T
            st.subheader("財務指標")
            st.dataframe(ratios_df)
            
            # グラフ表示
            st.subheader("推移グラフ")
            if '売上高成長率' in ratios_df.columns:
                st.line_chart(ratios_df['売上高成長率'])
        
        # 詳細データの表示
        st.subheader("詳細財務データ")
        for period, data in financial_data.items():
            with st.expander(f"期間: {period}"):
                for file_name, df in data.items():
                    st.write(f"ファイル: {file_name}")
                    st.dataframe(df.head())


# スタンドアロン実行用
if __name__ == "__main__":
    st.set_page_config(
        page_title="EDINET財務分析",
        layout="wide"
    )
    EDINETPage.show()
