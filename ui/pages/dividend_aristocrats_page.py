"""
配当貴族・配当成長株スクリーニングページ
長期的な配当成長銘柄を発見
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services.dividend_aristocrats import DividendAristocrats


class DividendAristocratsPage:
    """配当貴族スクリーニングページクラス"""

    @staticmethod
    def show():
        """ページを表示"""

        st.title("👑 配当貴族・配当成長株スクリーニング")

        st.markdown("""
        長期的な配当成長を実現している優良銘柄を発見します。
        **配当貴族**: 連続増配10年以上、**配当成長株**: 連続増配5年以上
        """)

        # タブで機能を分割
        tab1, tab2 = st.tabs([
            "🔍 配当貴族スクリーニング",
            "📊 個別銘柄分析"
        ])

        # タブ1: スクリーニング
        with tab1:
            DividendAristocratsPage._show_screening()

        # タブ2: 個別銘柄分析
        with tab2:
            DividendAristocratsPage._show_individual_analysis()

        # フッター
        st.markdown("---")
        st.markdown("""
        ### 💡 配当貴族とは？
        **配当貴族（Dividend Aristocrats）**は、長期にわたって連続で配当を増やし続けている優良企業を指します。

        **一般的な定義:**
        - 🇺🇸 **米国**: S&P500構成銘柄で25年以上連続増配
        - 🇯🇵 **日本**: 明確な定義はないが、10年以上連続増配が目安

        **投資メリット:**
        - ✅ 安定した配当収入
        - ✅ 業績の持続性が高い
        - ✅ 長期投資に適している
        - ✅ インフレヘッジとしての機能

        ### 📊 主な指標の見方

        **連続増配年数**
        - 5年以上: 配当成長株
        - 10年以上: 配当貴族候補
        - 20年以上: 真の配当貴族

        **配当CAGR (年平均成長率)**
        - 3%以上: 良好
        - 5%以上: 優秀
        - 10%以上: 非常に優秀

        **配当性向**
        - 30%未満: 増配余地大
        - 30-60%: 健全
        - 60-80%: やや高い
        - 80%以上: 減配リスクあり
        """)

    @staticmethod
    def _show_screening():
        """配当貴族スクリーニング表示"""
        st.header("🔍 配当貴族スクリーニング")

        st.markdown("""
        連続増配銘柄をスクリーニングします。配当の持続性と成長性を重視する投資家向けです。
        """)

        with st.expander("⚙️ カスタマイズ設定", expanded=False):
            use_default_screening = st.checkbox("デフォルト設定を使用（配当貴族）", value=True)

            st.markdown("---")
            st.markdown("**🚀 パフォーマンス設定**")

            col1, col2 = st.columns(2)
            with col1:
                use_cache = st.checkbox(
                    "キャッシュを使用（高速）",
                    value=True,
                    help="DBキャッシュを使用して高速化。無効にすると常にyfinanceから取得"
                )
            with col2:
                cache_age_hours = st.selectbox(
                    "キャッシュ有効期間",
                    [6, 12, 24, 48, 72],
                    index=2,
                    help="この期間内のキャッシュを使用"
                )

            if use_cache:
                st.info("⚡ キャッシュモード: DBから高速取得（数秒）")
            else:
                st.warning("🐌 リアルタイムモード: yfinanceから取得（数分かかります）")

            # キャッシュ管理セクション
            st.markdown("---")
            st.markdown("**💾 キャッシュ管理**")

            from repository.database_manager import DatabaseManager
            db_manager = DatabaseManager()

            # キャッシュ統計を表示
            cache_stats = db_manager.get_cached_metrics_count()
            quality_stats = db_manager.get_cache_quality_stats()

            if cache_stats:
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    st.metric("キャッシュ済み銘柄", f"{cache_stats['total']} 銘柄")
                with col_stat2:
                    if cache_stats['latest_update']:
                        st.metric("最終更新", cache_stats['latest_update'].strftime('%Y-%m-%d %H:%M'))
                    else:
                        st.metric("最終更新", "未更新")
                with col_stat3:
                    quality_score = quality_stats.get('overall_quality_score', 0)
                    st.metric("データ品質スコア", f"{quality_score:.1f}/100")

                # データ品質の内訳を表示
                if quality_stats.get('by_quality'):
                    with st.expander("📊 データ品質の詳細", expanded=False):
                        for row in quality_stats['by_quality']:
                            quality = row['data_quality']
                            count = row['count']
                            pct = row['percentage']

                            if quality == 'complete':
                                icon = "✅"
                                label = "完全"
                            elif quality == 'partial':
                                icon = "⚠️"
                                label = "部分的"
                            else:
                                icon = "❌"
                                label = "不完全"

                            st.write(f"{icon} **{label}**: {count} 銘柄 ({pct}%)")

            # キャッシュ更新ボタン
            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                update_limit = st.number_input(
                    "更新銘柄数",
                    min_value=5,
                    max_value=10000,
                    value=50,
                    step=10,
                    help="一度に更新する銘柄数（全件更新は1621を指定）"
                )

            with col_btn2:
                if st.button("🔄 キャッシュを更新", help="指定した銘柄数のキャッシュを更新します"):
                    DividendAristocratsPage._update_cache(update_limit)

        if use_default_screening:
            st.info("🎯 デフォルト: 配当貴族（連続増配10年以上、CAGR 3%以上、配当性向80%以下）")

            min_consecutive_years = 10
            min_cagr = 3.0
            max_payout_ratio = 80.0
            analysis_years = 5

            # デフォルト銘柄リスト（日本の大型株）
            default_tickers = [
                "7203.T", "6758.T", "9432.T", "9433.T", "9434.T",
                "8316.T", "8411.T", "8001.T", "8002.T", "2914.T"
            ]
            ticker_list = default_tickers

            st.markdown("**対象銘柄（デフォルト）:**")
            ticker_info = pd.DataFrame({
                "銘柄コード": ["7203.T", "6758.T", "9432.T", "9433.T", "9434.T",
                             "8316.T", "8411.T", "8001.T", "8002.T", "2914.T"],
                "銘柄名": ["トヨタ", "ソニー", "NTT", "KDDI", "ソフトバンク",
                         "三井住友FG", "みずほFG", "伊藤忠", "丸紅", "JT"],
                "セクター": ["自動車", "電機", "通信", "通信", "通信",
                           "金融", "金融", "商社", "商社", "食品"]
            })
            st.dataframe(ticker_info, width='stretch', hide_index=True)

        else:
            st.info("✏️ カスタマイズ: 独自の条件を設定")

            col1, col2 = st.columns(2)

            with col1:
                min_consecutive_years = st.slider(
                    "最低連続増配年数",
                    min_value=1,
                    max_value=20,
                    value=5,
                    step=1,
                    help="5年以上: 配当成長株、10年以上: 配当貴族"
                )

                min_cagr = st.number_input(
                    "最低配当CAGR (%/年)",
                    min_value=0.0,
                    max_value=20.0,
                    value=3.0,
                    step=0.5,
                    help="配当の年平均成長率"
                )

            with col2:
                max_payout_ratio = st.number_input(
                    "最大配当性向 (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=80.0,
                    step=5.0,
                    help="80%以下が健全、それ以上は減配リスクあり"
                )

                analysis_years = st.selectbox(
                    "分析期間",
                    [3, 4, 5, 10],
                    index=2,
                    help="過去何年分の配当データを分析するか"
                )

            # 銘柄選択方法
            st.markdown("**📋 銘柄選択**")
            ticker_selection_mode = st.radio(
                "銘柄選択方法",
                ["手動入力", "プライム市場全銘柄"],
                horizontal=True
            )

            if ticker_selection_mode == "手動入力":
                ticker_input = st.text_area(
                    "銘柄コードを入力（カンマ区切り）",
                    value="7203.T, 6758.T, 9432.T, 9433.T, 8316.T, 8001.T",
                    help="日本株は.T、米国株はそのまま"
                )
                ticker_list = [t.strip() for t in ticker_input.split(",") if t.strip()]
            else:
                # プライム市場全銘柄を取得
                prime_tickers = db_manager.get_prime_market_tickers()
                ticker_list = prime_tickers
                st.info(f"🎯 プライム市場全銘柄: {len(ticker_list)} 銘柄を対象にスクリーニングします")
                st.caption("⚠️ キャッシュを使用することを強く推奨します（キャッシュなしの場合は数時間かかります）")

        if st.button("🔍 スクリーニング実行", type="primary"):
            if not ticker_list:
                st.warning("銘柄コードを入力してください")
            else:
                with st.spinner(f"{len(ticker_list)}銘柄を分析中..."):
                    # スクリーニング実行（キャッシュパラメータを追加）
                    df_results = DividendAristocrats.screen_dividend_aristocrats(
                        ticker_list=ticker_list,
                        min_consecutive_years=min_consecutive_years,
                        min_cagr=min_cagr,
                        max_payout_ratio=max_payout_ratio,
                        years=analysis_years,
                        use_cache=use_cache,
                        max_cache_age_hours=cache_age_hours
                    )

                    if df_results.empty:
                        st.warning("条件に一致する銘柄が見つかりませんでした。条件を緩和してみてください。")
                    else:
                        st.success(f"✅ {len(df_results)}銘柄が条件に一致しました")

                        # 結果表示
                        st.subheader("📊 スクリーニング結果")

                        # 表示用にフォーマット
                        df_display = df_results.copy()
                        if '現在配当利回り' in df_display.columns:
                            df_display['現在配当利回り'] = df_display['現在配当利回り'].apply(
                                lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A"
                            )
                        if '配当CAGR' in df_display.columns:
                            df_display['配当CAGR'] = df_display['配当CAGR'].apply(
                                lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A"
                            )
                        if '配当性向' in df_display.columns:
                            df_display['配当性向'] = df_display['配当性向'].apply(
                                lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A"
                            )

                        st.dataframe(df_display, width='stretch', hide_index=True)

                        # グラフ表示
                        col1, col2 = st.columns(2)

                        with col1:
                            st.subheader("📈 連続増配年数 vs 配当CAGR")

                            # 完全にPandas/NumPy形式に変換（Narwhals対策）
                            try:
                                # Pandas DataFrameに変換
                                if hasattr(df_results, 'to_pandas'):
                                    df_plot = df_results.to_pandas()
                                else:
                                    df_plot = df_results.copy()

                                # 全列をPythonのリストに変換してから新しいDataFrameを作成
                                plot_dict = {col: df_plot[col].tolist() for col in df_plot.columns}
                                df_numeric = pd.DataFrame(plot_dict)

                                # NaN除外
                                df_numeric = df_numeric.dropna(subset=['連続増配年数', '配当CAGR', '現在配当利回り'])

                                if not df_numeric.empty:
                                    fig = px.scatter(
                                        df_numeric,
                                        x='連続増配年数',
                                        y='配当CAGR',
                                        size='現在配当利回り',
                                        color='ステータス',
                                        hover_data=['銘柄コード', '銘柄名', '配当性向'],
                                        title="配当成長分析マップ"
                                    )
                                    fig.update_layout(height=400)
                                    st.plotly_chart(fig, width='stretch')
                                else:
                                    st.info("グラフ表示に必要なデータがありません")
                            except Exception as e:
                                st.error(f"グラフ生成エラー: {str(e)}")

                        with col2:
                            st.subheader("📊 配当性向分布")

                            # 配当性向のヒストグラム（Narwhals対策）
                            try:
                                # df_numericが既に作成されている場合はそれを使用
                                if 'df_numeric' in locals() and not df_numeric.empty:
                                    payout_values = df_numeric['配当性向'].dropna().tolist()
                                else:
                                    # df_resultsから直接取得
                                    payout_series = df_results['配当性向']
                                    payout_values = [x for x in payout_series.tolist() if pd.notna(x)]

                                if payout_values:
                                    fig2 = go.Figure()
                                    fig2.add_trace(go.Histogram(
                                        x=payout_values,
                                        nbinsx=10,
                                        marker_color='lightblue'
                                    ))

                                    # 健全範囲をハイライト
                                    fig2.add_vline(x=60, line_dash="dash", line_color="green",
                                                  annotation_text="健全上限(60%)")
                                    fig2.add_vline(x=80, line_dash="dash", line_color="orange",
                                                  annotation_text="警戒ライン(80%)")

                                    fig2.update_layout(
                                        title="配当性向の分布",
                                        xaxis_title="配当性向 (%)",
                                        yaxis_title="銘柄数",
                                        height=400
                                    )
                                    st.plotly_chart(fig2, width='stretch')
                                else:
                                    st.info("配当性向データがありません")
                            except Exception as e:
                                st.error(f"ヒストグラム生成エラー: {str(e)}")

                        # 統計情報
                        st.subheader("📈 統計情報")

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            avg_consecutive = df_results['連続増配年数'].mean()
                            st.metric("平均連続増配年数", f"{avg_consecutive:.1f}年")

                        with col2:
                            avg_cagr = df_results['配当CAGR'].mean()
                            st.metric("平均配当CAGR", f"{avg_cagr:.2f}%")

                        with col3:
                            avg_yield = df_results['現在配当利回り'].mean()
                            st.metric("平均配当利回り", f"{avg_yield:.2f}%")

                        with col4:
                            avg_payout = df_results['配当性向'].mean()
                            st.metric("平均配当性向", f"{avg_payout:.1f}%")

    @staticmethod
    def _show_individual_analysis():
        """個別銘柄分析表示"""
        st.header("📊 個別銘柄の配当成長分析")

        st.markdown("""
        特定の銘柄について、配当成長の詳細を分析します。
        """)

        col1, col2 = st.columns([2, 1])

        with col1:
            ticker_symbol = st.text_input(
                "銘柄コード",
                value="7203.T",
                help="例: 7203.T (トヨタ), AAPL (Apple)"
            )

        with col2:
            analysis_years_individual = st.selectbox(
                "分析期間（年）",
                [3, 4, 5, 10],
                index=2,
                key="individual_years"
            )

        if st.button("📊 分析実行", type="primary", key="analyze_individual"):
            with st.spinner(f"{ticker_symbol} を分析中..."):
                analysis = DividendAristocrats.analyze_dividend_growth(
                    ticker_symbol,
                    years=analysis_years_individual
                )

                if 'エラー' in analysis:
                    st.error(f"❌ エラー: {analysis['エラー']}")
                else:
                    # 結果表示
                    st.subheader(f"📈 {analysis['銘柄名']} ({analysis['銘柄コード']})")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            "現在配当利回り",
                            f"{analysis['現在配当利回り']:.2f}%" if analysis['現在配当利回り'] else "N/A"
                        )

                    with col2:
                        st.metric(
                            f"配当CAGR ({analysis_years_individual}年)",
                            f"{analysis['配当CAGR']:.2f}%" if analysis['配当CAGR'] else "N/A"
                        )

                    with col3:
                        st.metric(
                            "連続増配年数",
                            f"{analysis['連続増配年数']}年"
                        )

                    with col4:
                        st.metric(
                            "配当性向",
                            f"{analysis['配当性向']:.2f}%" if analysis['配当性向'] else "N/A",
                            delta=analysis['配当性向評価']
                        )

                    # ステータス表示
                    st.info(f"**ステータス:** {analysis['ステータス']}")

                    # 評価コメント
                    st.subheader("💬 評価コメント")

                    comments = []

                    if analysis['連続増配年数'] >= 10:
                        comments.append("🏆 **配当貴族候補**: 10年以上連続で増配を実現しています。")
                    elif analysis['連続増配年数'] >= 5:
                        comments.append("⭐ **配当成長株**: 5年以上連続増配を達成しています。")

                    if analysis.get('配当CAGR') and analysis['配当CAGR'] > 5:
                        comments.append(f"📈 **高成長**: 配当のCAGRが{analysis['配当CAGR']:.1f}%と高い成長率です。")
                    elif analysis.get('配当CAGR') and analysis['配当CAGR'] > 3:
                        comments.append(f"📊 **安定成長**: 配当のCAGRが{analysis['配当CAGR']:.1f}%と安定した成長です。")

                    if analysis.get('配当性向'):
                        if analysis['配当性向'] < 30:
                            comments.append("💰 **増配余地大**: 配当性向が低く、今後の増配余地が大きいです。")
                        elif analysis['配当性向'] < 60:
                            comments.append("✅ **健全な配当性向**: バランスの取れた配当政策です。")
                        elif analysis['配当性向'] < 80:
                            comments.append("⚠️ **やや高めの配当性向**: 今後の増配余地は限定的かもしれません。")
                        else:
                            comments.append("❌ **高い配当性向**: 減配リスクに注意が必要です。")

                    for comment in comments:
                        st.markdown(comment)

    @staticmethod
    def _update_cache(limit: int = 50):
        """UI内でキャッシュを更新"""
        from repository.database_manager import DatabaseManager
        import time

        db_manager = DatabaseManager()

        # プライム市場銘柄を取得
        tickers = db_manager.get_prime_market_tickers()

        if limit:
            tickers = tickers[:limit]

        st.info(f"🔄 {len(tickers)} 銘柄のキャッシュを更新中...")

        # プログレスバー
        progress_bar = st.progress(0)
        status_text = st.empty()

        success_count = 0
        error_count = 0
        start_time = time.time()

        for i, ticker in enumerate(tickers):
            try:
                # 進捗表示
                progress = (i + 1) / len(tickers)
                progress_bar.progress(progress)
                status_text.text(f"[{i+1}/{len(tickers)}] {ticker} を処理中...")

                # 配当分析を実行
                metrics = DividendAristocrats.analyze_dividend_growth(ticker, years=5)

                if 'エラー' not in metrics:
                    # データベースに保存
                    db_manager.upsert_dividend_aristocrat_metrics(ticker, metrics)
                    success_count += 1
                else:
                    error_count += 1

                # API制限対策: 0.5秒待機
                time.sleep(0.5)

            except Exception as e:
                error_count += 1
                st.warning(f"⚠️ {ticker}: {str(e)}")

        elapsed_time = time.time() - start_time

        # 完了メッセージ
        progress_bar.progress(1.0)
        status_text.empty()

        st.success(f"""
        ✅ キャッシュ更新完了

        - 成功: {success_count} 銘柄
        - エラー: {error_count} 銘柄
        - 所要時間: {elapsed_time:.1f}秒
        - 平均処理時間: {elapsed_time/len(tickers):.2f}秒/銘柄
        """)
