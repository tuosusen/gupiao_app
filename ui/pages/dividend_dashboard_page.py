"""
配当専用ダッシュボードページ
配当利回り重視投資家のための専用インターフェース
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import yfinance as yf


class DividendDashboardPage:
    """配当専用ダッシュボードページクラス"""

    @staticmethod
    def show():
        """ダッシュボードを表示"""

        st.title("💰 配当専用ダッシュボード")

        st.markdown("""
        配当利回り重視投資家のための専用ダッシュボードです。
        配当カレンダー、月次配当シミュレーション、配当再投資効果を可視化します。
        """)

        # タブで機能を分割
        tab1, tab2, tab3 = st.tabs([
            "📅 配当カレンダー",
            "💵 月次配当収入シミュレーター",
            "📈 配当再投資シミュレーション"
        ])

        # タブ1: 配当カレンダー
        with tab1:
            DividendDashboardPage._show_dividend_calendar()

        # タブ2: 月次配当収入シミュレーター
        with tab2:
            DividendDashboardPage._show_monthly_income_simulator()

        # タブ3: 配当再投資シミュレーション
        with tab3:
            DividendDashboardPage._show_reinvestment_simulator()

        # フッター
        st.markdown("---")
        st.markdown("""
        ### 💡 ヒント
        - **配当カレンダー**: 配当スケジュールを把握して資金計画を立てましょう
        - **月次配当収入**: NISA口座を活用すれば税金0%で配当を受け取れます
        - **配当再投資**: 長期投資では複利効果が非常に大きくなります

        ### ⚠️ 注意事項
        - 配当金額は予測であり、実際の配当は企業の業績により変動します
        - シミュレーションは過去のデータに基づく推定であり、将来を保証するものではありません
        """)

    @staticmethod
    def _show_dividend_calendar():
        """配当カレンダー表示"""
        st.header("📅 配当カレンダー")

        st.markdown("""
        保有銘柄または監視銘柄の配当スケジュールを確認できます。
        """)

        # デフォルト設定
        with st.expander("⚙️ カスタマイズ設定", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                input_method = st.radio(
                    "銘柄入力方法",
                    ["サンプル銘柄を使用（デフォルト）", "手動で銘柄を入力"]
                )

            with col2:
                calendar_months = st.slider(
                    "表示期間（月）",
                    min_value=3,
                    max_value=12,
                    value=6,
                    step=1
                )

        # デフォルト: サンプル銘柄
        if input_method == "サンプル銘柄を使用（デフォルト）":
            st.info("🎯 デフォルト: 日本の高配当銘柄サンプル")
            default_tickers = ["8316.T", "8411.T", "9434.T", "9432.T", "8001.T"]
            ticker_list = default_tickers

            # サンプル銘柄の説明
            sample_info = pd.DataFrame({
                "銘柄コード": ["8316.T", "8411.T", "9434.T", "9432.T", "8001.T"],
                "銘柄名": ["三井住友FG", "みずほFG", "ソフトバンク", "NTT", "伊藤忠商事"],
                "セクター": ["金融", "金融", "通信", "通信", "商社"]
            })
            st.dataframe(sample_info, width='stretch', hide_index=True)

        else:
            # カスタマイズ: 手動入力
            st.info("✏️ カスタマイズ: 銘柄を手動で入力")
            ticker_input = st.text_area(
                "銘柄コードを入力（カンマ区切り）",
                value="8316.T, 8411.T, 9434.T",
                help="例: 8316.T, 8411.T, 9434.T（日本株は.T、米国株はそのまま）"
            )
            ticker_list = [t.strip() for t in ticker_input.split(",") if t.strip()]

        if st.button("📅 配当カレンダーを表示", type="primary"):
            if not ticker_list:
                st.warning("銘柄コードを入力してください")
            else:
                with st.spinner("配当情報を取得中..."):
                    calendar_data = []

                    for ticker_symbol in ticker_list:
                        try:
                            ticker = yf.Ticker(ticker_symbol)
                            info = ticker.info
                            dividends = ticker.dividends

                            if dividends is not None and not dividends.empty:
                                # 過去の配当履歴から配当月を推定
                                recent_dividends = dividends.tail(4)  # 直近4回の配当

                                for date, amount in recent_dividends.items():
                                    # 将来の配当予測（同じ月に配当があると仮定）
                                    next_year_date = date + relativedelta(years=1)

                                    if next_year_date >= datetime.now():
                                        calendar_data.append({
                                            "銘柄コード": ticker_symbol,
                                            "銘柄名": info.get('longName', ticker_symbol),
                                            "配当予定日": next_year_date.strftime("%Y-%m-%d"),
                                            "予想配当金": f"¥{amount:.2f}",
                                            "月": next_year_date.strftime("%Y年%m月")
                                        })

                        except Exception as e:
                            st.error(f"❌ {ticker_symbol} の取得に失敗: {str(e)[:50]}")
                            continue

                    if calendar_data:
                        df_calendar = pd.DataFrame(calendar_data)
                        df_calendar = df_calendar.sort_values("配当予定日")

                        st.success(f"✅ {len(ticker_list)}銘柄の配当カレンダーを表示")

                        # カレンダー表示
                        st.dataframe(df_calendar, width='stretch', hide_index=True)

                        # 月別集計
                        st.subheader("📊 月別配当予測")

                        # 配当金を数値に変換
                        df_calendar['配当金_数値'] = df_calendar['予想配当金'].str.replace('¥', '').astype(float)
                        monthly_summary = df_calendar.groupby('月')['配当金_数値'].sum().reset_index()
                        monthly_summary.columns = ['月', '合計配当金']
                        monthly_summary['合計配当金'] = monthly_summary['合計配当金'].apply(lambda x: f"¥{x:.2f}")

                        st.dataframe(monthly_summary, width='stretch', hide_index=True)
                    else:
                        st.warning("配当情報が取得できませんでした")

    @staticmethod
    def _show_monthly_income_simulator():
        """月次配当収入シミュレーター"""
        st.header("💵 月次配当収入シミュレーター")

        st.markdown("""
        投資額に対する月次配当収入をシミュレーションします。
        """)

        with st.expander("⚙️ カスタマイズ設定", expanded=False):
            use_default_portfolio = st.checkbox("デフォルト設定を使用", value=True)

        if use_default_portfolio:
            st.info("🎯 デフォルト: バランス型ポートフォリオ（配当利回り4%想定）")
            total_investment = 10000000  # 1000万円
            avg_yield = 4.0
            tax_rate = 20.315
        else:
            st.info("✏️ カスタマイズ: 独自の設定を入力")

            col1, col2, col3 = st.columns(3)

            with col1:
                total_investment = st.number_input(
                    "総投資額（円）",
                    min_value=100000,
                    max_value=100000000,
                    value=10000000,
                    step=100000
                )

            with col2:
                avg_yield = st.number_input(
                    "平均配当利回り（%）",
                    min_value=0.0,
                    max_value=10.0,
                    value=4.0,
                    step=0.1
                )

            with col3:
                tax_rate = st.number_input(
                    "税率（%）",
                    min_value=0.0,
                    max_value=30.0,
                    value=20.315,
                    step=0.1,
                    help="日本株: 20.315%、NISA: 0%"
                )

        # 計算
        annual_dividend = total_investment * (avg_yield / 100)
        monthly_dividend = annual_dividend / 12

        annual_dividend_after_tax = annual_dividend * (1 - tax_rate / 100)
        monthly_dividend_after_tax = annual_dividend_after_tax / 12

        # 結果表示
        st.subheader("📊 シミュレーション結果")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "総投資額",
                f"¥{total_investment:,.0f}"
            )

        with col2:
            st.metric(
                "年間配当（税引前）",
                f"¥{annual_dividend:,.0f}"
            )

        with col3:
            st.metric(
                "年間配当（税引後）",
                f"¥{annual_dividend_after_tax:,.0f}"
            )

        with col4:
            st.metric(
                "月次配当（税引後）",
                f"¥{monthly_dividend_after_tax:,.0f}"
            )

        # グラフ表示
        st.subheader("📈 月次配当収入の推移")

        months = [f"{i+1}月" for i in range(12)]
        monthly_values = [monthly_dividend_after_tax] * 12

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=months,
            y=monthly_values,
            text=[f"¥{v:,.0f}" for v in monthly_values],
            textposition='outside',
            marker_color='lightblue'
        ))

        fig.update_layout(
            title="月次配当収入（税引後）",
            xaxis_title="月",
            yaxis_title="配当金（円）",
            showlegend=False,
            height=400
        )

        st.plotly_chart(fig, width='stretch')

    @staticmethod
    def _show_reinvestment_simulator():
        """配当再投資シミュレーション"""
        st.header("📈 配当再投資シミュレーション")

        st.markdown("""
        配当を再投資した場合の複利効果をシミュレーションします。
        """)

        with st.expander("⚙️ カスタマイズ設定", expanded=False):
            use_default_reinvest = st.checkbox("デフォルト設定を使用（再投資）", value=True, key="reinvest_default")

        if use_default_reinvest:
            st.info("🎯 デフォルト: 配当利回り4%、配当成長率3%、投資期間20年")
            initial_investment = 10000000
            dividend_yield = 4.0
            dividend_growth_rate = 3.0
            investment_years = 20
            reinvest = True
        else:
            st.info("✏️ カスタマイズ: 独自の設定を入力")

            col1, col2 = st.columns(2)

            with col1:
                initial_investment = st.number_input(
                    "初期投資額（円）",
                    min_value=100000,
                    max_value=100000000,
                    value=10000000,
                    step=100000,
                    key="reinvest_investment"
                )

                dividend_yield = st.number_input(
                    "初年度配当利回り（%）",
                    min_value=0.0,
                    max_value=10.0,
                    value=4.0,
                    step=0.1,
                    key="reinvest_yield"
                )

            with col2:
                dividend_growth_rate = st.number_input(
                    "配当成長率（%/年）",
                    min_value=0.0,
                    max_value=15.0,
                    value=3.0,
                    step=0.5,
                    help="年間の配当増加率"
                )

                investment_years = st.slider(
                    "投資期間（年）",
                    min_value=5,
                    max_value=30,
                    value=20,
                    step=1
                )

            reinvest = st.checkbox("配当を再投資する", value=True)

        # シミュレーション計算
        if st.button("📊 シミュレーション実行", type="primary", key="run_simulation"):
            years = []
            portfolio_values_with_reinvest = []
            portfolio_values_without_reinvest = []
            annual_dividends = []

            # 再投資あり
            portfolio_value_with = initial_investment
            # 再投資なし
            portfolio_value_without = initial_investment

            for year in range(investment_years + 1):
                years.append(year)

                # 配当利回りは成長率で増加
                current_yield = dividend_yield * ((1 + dividend_growth_rate / 100) ** year)

                # 再投資ありの場合
                annual_dividend_with = portfolio_value_with * (current_yield / 100)
                if reinvest and year > 0:
                    portfolio_value_with += annual_dividend_with

                # 再投資なしの場合
                annual_dividend_without = portfolio_value_without * (current_yield / 100)

                portfolio_values_with_reinvest.append(portfolio_value_with)
                portfolio_values_without_reinvest.append(portfolio_value_without)
                annual_dividends.append(annual_dividend_with)

            # 結果表示
            st.subheader("📊 シミュレーション結果")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "最終ポートフォリオ価値（再投資あり）",
                    f"¥{portfolio_values_with_reinvest[-1]:,.0f}",
                    delta=f"+¥{portfolio_values_with_reinvest[-1] - initial_investment:,.0f}"
                )

            with col2:
                st.metric(
                    "最終ポートフォリオ価値（再投資なし）",
                    f"¥{portfolio_values_without_reinvest[-1]:,.0f}"
                )

            with col3:
                difference = portfolio_values_with_reinvest[-1] - portfolio_values_without_reinvest[-1]
                st.metric(
                    "複利効果による差額",
                    f"¥{difference:,.0f}"
                )

            # グラフ表示
            st.subheader("📈 ポートフォリオ価値の推移")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=years,
                y=portfolio_values_with_reinvest,
                mode='lines+markers',
                name='配当再投資あり',
                line=dict(color='green', width=3)
            ))

            fig.add_trace(go.Scatter(
                x=years,
                y=portfolio_values_without_reinvest,
                mode='lines+markers',
                name='配当再投資なし',
                line=dict(color='blue', width=3, dash='dash')
            ))

            fig.update_layout(
                title=f"{investment_years}年間の複利効果シミュレーション",
                xaxis_title="経過年数",
                yaxis_title="ポートフォリオ価値（円）",
                hovermode='x unified',
                height=500
            )

            st.plotly_chart(fig, width='stretch')

            # 詳細データ表
            with st.expander("📋 詳細データを表示"):
                df_simulation = pd.DataFrame({
                    "経過年数": years,
                    "再投資あり（円）": [f"¥{v:,.0f}" for v in portfolio_values_with_reinvest],
                    "再投資なし（円）": [f"¥{v:,.0f}" for v in portfolio_values_without_reinvest],
                    "年間配当（円）": [f"¥{d:,.0f}" for d in annual_dividends]
                })

                st.dataframe(df_simulation, width='stretch', hide_index=True)
