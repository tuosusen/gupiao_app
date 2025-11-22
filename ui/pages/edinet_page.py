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
        
        years = st.slider("分析年数", 1, 10, 1)  # デフォルトを1年に変更
        st.caption("💡 最大180日間を毎日チェックします")

        use_all_doc_types = st.checkbox("すべての書類種類を検索", value=False)

        doc_type_options = {
            '有価証券報告書': '120',
            '訂正有価証券報告書': '130',
            '四半期報告書': '140',
            '訂正四半期報告書': '150',
            '半期報告書': '160',
            '訂正半期報告書': '170',
            '内部統制報告書': '220',
            '訂正内部統制報告書': '230'
        }

        if use_all_doc_types:
            selected_doc_type_codes = None  # None = すべての書類種類
            st.info("📋 すべての書類種類を検索します")
        else:
            selected_doc_types = st.multiselect(
                "書類の種類を選択",
                options=list(doc_type_options.keys()),
                default=['有価証券報告書', '四半期報告書', '内部統制報告書']
            )
            selected_doc_type_codes = [doc_type_options[key] for key in selected_doc_types]
        
        if st.button("財務データ取得"):
            with st.spinner("財務データを取得中..."):
                # デバッグ情報を表示
                with st.expander("🔍 検索条件の詳細", expanded=False):
                    st.write(f"**企業コード:** {company_code}")
                    st.write(f"**分析年数:** {years}年")
                    if selected_doc_type_codes is None:
                        st.write(f"**書類種類:** すべて")
                    else:
                        st.write(f"**書類種類コード:** {selected_doc_type_codes}")
                        st.write(f"**書類種類名:** {', '.join(selected_doc_types)}")

                try:
                    financial_data = edinet_repo.get_financial_statements(
                        company_code, years, selected_doc_type_codes
                    )

                    # デバッグ: 取得したデータの構造を表示
                    st.info(f"✅ API呼び出し完了 - 取得期間数: {len(financial_data) if financial_data else 0}")

                    if financial_data and len(financial_data) > 0:
                        st.success(f"🎉 {len(financial_data)}期分の財務データを取得しました")

                        # 財務指標の計算
                        ratios = EDINETPage._calculate_financial_ratios(financial_data)

                        # 結果の表示
                        EDINETPage._display_financial_analysis(financial_data, ratios)
                    else:
                        st.error("❌ 財務データを取得できませんでした")
                        st.warning("""
                        **考えられる原因:**
                        - 企業コードが正しくない可能性があります（証券コード4桁: 例 7203）
                        - 指定期間内に該当する書類が提出されていない可能性があります
                        - APIキーが無効または期限切れの可能性があります
                        - EDINET APIのレート制限に達している可能性があります

                        **確認事項:**
                        1. 企業コードは証券コード4桁（例: 7203）で入力してください
                        2. APIキーが有効か確認してください（https://api.edinet-fsa.go.jp/）
                        3. 書類の種類と期間を調整してみてください
                        4. しばらく待ってから再試行してください

                        **よくある企業コード例:**
                        - トヨタ自動車: 7203
                        - ソニーグループ: 6758
                        - ソフトバンクグループ: 9984
                        """)

                        # API接続テスト
                        with st.expander("🔧 API接続テスト", expanded=False):
                            from datetime import datetime
                            test_date = datetime.now().strftime('%Y-%m-%d')
                            st.write(f"テスト日付: {test_date}")
                            test_result = edinet_repo.get_documents_list(test_date)
                            if test_result:
                                st.success("✅ EDINET APIへの接続は成功しています")
                                st.write(f"取得した書類数: {len(test_result.get('results', []))}")
                            else:
                                st.error("❌ EDINET APIへの接続に失敗しました - APIキーを確認してください")

                except Exception as e:
                    st.error(f"❌ エラーが発生しました: {str(e)}")
                    import traceback
                    with st.expander("エラー詳細", expanded=False):
                        st.code(traceback.format_exc())
    
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

        # データ処理サービスをインポート
        from services.edinet_data_processor import EDINETDataProcessor
        processor = EDINETDataProcessor()

        # 主要財務指標のサマリーを作成
        metrics_df = processor.extract_key_metrics(financial_data)

        if not metrics_df.empty:
            # 成長率を計算
            metrics_with_growth = processor.calculate_growth_rates(metrics_df)

            # 主要財務指標の表示
            st.subheader("財務指標")

            # 表示用に数値カラムを除外
            display_cols = [col for col in metrics_with_growth.columns if not col.endswith('_数値')]
            display_df = metrics_with_growth[display_cols]

            st.dataframe(display_df, use_container_width=True)

            # グラフ表示
            st.subheader("推移グラフ")
            chart_data = processor.prepare_chart_data(metrics_df)

            if '損益推移' in chart_data:
                st.write("**売上高・利益の推移**")
                st.line_chart(chart_data['損益推移'])

            if '資産推移' in chart_data:
                st.write("**総資産・純資産の推移**")
                st.line_chart(chart_data['資産推移'])

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
