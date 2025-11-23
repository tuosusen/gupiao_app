"""
スクリーニング機能管理画面
スクリーニングの分類、条件、設定などを一覧表示・管理する
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from services.screening_presets import ScreeningPresets


class ScreeningConfigPage:
    """スクリーニング機能管理ページクラス"""

    @staticmethod
    def show():
        """スクリーニング機能管理画面を表示"""

        # タブで機能を分割
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 スクリーニング分類一覧",
            "🔍 条件詳細",
            "📊 プリセット管理",
            "🎯 カスタム条件設定"
        ])

        # タブ1: スクリーニング分類一覧
        with tab1:
            ScreeningConfigPage._show_classification_list()

        # タブ2: 条件詳細
        with tab2:
            ScreeningConfigPage._show_condition_details()

        # タブ3: プリセット管理
        with tab3:
            ScreeningConfigPage._show_preset_management()

        # タブ4: カスタム条件設定
        with tab4:
            ScreeningConfigPage._show_custom_conditions()

        # フッター
        st.markdown("---")
        st.markdown("""
        ### 📚 参考情報

        **スクリーニングのベストプラクティス:**
        1. まずはプリセットから始める
        2. 結果を見ながら条件を調整
        3. 複数の条件を組み合わせて精度を上げる
        4. 定期的に条件を見直す

        **注意事項:**
        - データベーススクリーニングは高速ですが、データが古い場合があります
        - リアルタイムスクリーニングは最新データですが、時間がかかります
        - 条件を厳しくしすぎると、該当銘柄がなくなる可能性があります
        """)

    @staticmethod
    def _show_classification_list():
        """スクリーニング分類一覧を表示"""
        st.header("スクリーニング分類一覧")

        st.markdown("""
        本システムには以下のスクリーニングモードがあります:
        """)

        # スクリーニングモードの説明
        modes_data = [
            {
                "モード名": "基本モード",
                "アイコン": "📊",
                "説明": "シンプルな条件でスクリーニング",
                "主な用途": "初心者向け、クイックスクリーニング",
                "使用条件": "配当利回り、PER、PBRなどの基本指標"
            },
            {
                "モード名": "高度な配当分析",
                "アイコン": "💰",
                "説明": "過去の配当履歴を詳細に分析",
                "主な用途": "配当重視の投資家向け",
                "使用条件": "配当履歴、変動係数、トレンド分析、品質スコア"
            },
            {
                "モード名": "高度なPER分析",
                "アイコン": "📈",
                "説明": "過去のPER推移を考慮",
                "主な用途": "バリュー投資家向け",
                "使用条件": "PER履歴、変動係数、割安度判定"
            },
            {
                "モード名": "カスタム条件",
                "アイコン": "🎯",
                "説明": "自由に条件を組み合わせ",
                "主な用途": "上級者向け、詳細なカスタマイズ",
                "使用条件": "全ての条件を自由に設定可能"
            }
        ]

        df_modes = pd.DataFrame(modes_data)
        st.dataframe(df_modes, use_container_width=True, hide_index=True)

        st.markdown("---")

        # プリセット一覧
        st.subheader("🎁 利用可能なプリセット")

        preset_names = ScreeningPresets.get_preset_names()

        preset_data = []
        for name in preset_names:
            preset = ScreeningPresets.get_preset(name)
            preset_data.append({
                "プリセット名": f"{preset['icon']} {name}",
                "説明": preset['description'],
                "対象投資家": preset['target_user'],
                "条件数": len([k for k in preset['conditions'].keys() if k != 'use_db'])
            })

        df_presets = pd.DataFrame(preset_data)
        st.dataframe(df_presets, use_container_width=True, hide_index=True)

    @staticmethod
    def _show_condition_details():
        """条件詳細を表示"""
        st.header("🔍 スクリーニング条件詳細")

        st.markdown("""
        各スクリーニング条件の詳細な説明と設定可能な範囲を示します。
        """)

        # 条件カテゴリーごとに表示
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 配当関連条件")

            dividend_conditions = [
                {
                    "条件名": "最低配当利回り",
                    "パラメータ": "min_dividend_yield",
                    "単位": "%",
                    "推奨範囲": "2.0 - 5.0",
                    "説明": "現在の配当利回りの最低値"
                },
                {
                    "条件名": "過去平均配当利回り",
                    "パラメータ": "min_avg_dividend_yield",
                    "単位": "%",
                    "推奨範囲": "3.0 - 5.0",
                    "説明": "過去N年間の平均配当利回りの最低値"
                },
                {
                    "条件名": "配当変動係数",
                    "パラメータ": "max_dividend_cv",
                    "単位": "倍",
                    "推奨範囲": "0.2 - 0.5",
                    "説明": "配当の安定性（低いほど安定）"
                },
                {
                    "条件名": "配当品質スコア",
                    "パラメータ": "min_dividend_quality_score",
                    "単位": "点",
                    "推奨範囲": "50 - 80",
                    "説明": "配当の総合品質評価（0-100点）"
                },
                {
                    "条件名": "配当増加傾向",
                    "パラメータ": "dividend_trend",
                    "単位": "-",
                    "推奨範囲": "増加 / 安定 / 全て",
                    "説明": "配当のトレンド方向"
                },
                {
                    "条件名": "特別配当除外",
                    "パラメータ": "exclude_special_dividend",
                    "単位": "bool",
                    "推奨範囲": "True / False",
                    "説明": "特別配当がある銘柄を除外"
                }
            ]

            df_dividend = pd.DataFrame(dividend_conditions)
            st.dataframe(df_dividend, use_container_width=True, hide_index=True, height=250)

            st.subheader("💼 財務健全性条件")

            financial_conditions = [
                {
                    "条件名": "自己資本比率",
                    "パラメータ": "min_equity_ratio",
                    "単位": "%",
                    "推奨範囲": "30 - 60",
                    "説明": "財務の安定性（高いほど安全）"
                },
                {
                    "条件名": "流動比率",
                    "パラメータ": "min_current_ratio",
                    "単位": "%",
                    "推奨範囲": "100 - 200",
                    "説明": "短期支払能力（高いほど安全）"
                },
                {
                    "条件名": "有利子負債比率",
                    "パラメータ": "max_debt_equity_ratio",
                    "単位": "%",
                    "推奨範囲": "50 - 150",
                    "説明": "負債の大きさ（低いほど安全）"
                },
                {
                    "条件名": "リスクレベル",
                    "パラメータ": "risk_level",
                    "単位": "-",
                    "推奨範囲": "低 / 中 / 高",
                    "説明": "総合的な倒産リスク評価"
                }
            ]

            df_financial = pd.DataFrame(financial_conditions)
            st.dataframe(df_financial, use_container_width=True, hide_index=True, height=200)

        with col2:
            st.subheader("💰 バリュエーション条件")

            valuation_conditions = [
                {
                    "条件名": "最大PER",
                    "パラメータ": "max_per",
                    "単位": "倍",
                    "推奨範囲": "10 - 25",
                    "説明": "株価収益率の上限（低いほど割安）"
                },
                {
                    "条件名": "最小PER",
                    "パラメータ": "min_per",
                    "単位": "倍",
                    "推奨範囲": "5 - 10",
                    "説明": "株価収益率の下限（極端に低いPERを除外）"
                },
                {
                    "条件名": "過去平均PER（最大）",
                    "パラメータ": "max_avg_per",
                    "単位": "倍",
                    "推奨範囲": "12 - 20",
                    "説明": "過去N年間の平均PERの上限"
                },
                {
                    "条件名": "過去平均PER（最小）",
                    "パラメータ": "min_avg_per",
                    "単位": "倍",
                    "推奨範囲": "5 - 10",
                    "説明": "過去N年間の平均PERの下限"
                },
                {
                    "条件名": "PER変動係数",
                    "パラメータ": "max_per_cv",
                    "単位": "倍",
                    "推奨範囲": "0.3 - 0.6",
                    "説明": "PERの安定性（低いほど安定）"
                },
                {
                    "条件名": "現在PER < 平均PER",
                    "パラメータ": "low_current_high_avg_per",
                    "単位": "bool",
                    "推奨範囲": "True / False",
                    "説明": "割安度判定（現在が過去平均より低い）"
                },
                {
                    "条件名": "最大PBR",
                    "パラメータ": "max_pbr",
                    "単位": "倍",
                    "推奨範囲": "0.8 - 2.0",
                    "説明": "株価純資産倍率の上限（低いほど割安）"
                }
            ]

            df_valuation = pd.DataFrame(valuation_conditions)
            st.dataframe(df_valuation, use_container_width=True, hide_index=True, height=300)

            st.subheader("🏢 企業規模条件")

            size_conditions = [
                {
                    "条件名": "最低時価総額",
                    "パラメータ": "min_market_cap",
                    "単位": "億円",
                    "推奨範囲": "100 - 1000",
                    "説明": "企業規模の最小値"
                },
                {
                    "条件名": "最大時価総額",
                    "パラメータ": "max_market_cap",
                    "単位": "億円",
                    "推奨範囲": "1000 - 10000",
                    "説明": "企業規模の最大値"
                }
            ]

            df_size = pd.DataFrame(size_conditions)
            st.dataframe(df_size, use_container_width=True, hide_index=True, height=120)

    @staticmethod
    def _show_preset_management():
        """プリセット管理を表示"""
        st.header("📊 プリセット詳細管理")

        st.markdown("""
        各プリセットの詳細な条件設定を確認できます。
        """)

        preset_names = ScreeningPresets.get_preset_names()

        # プリセット選択
        selected_preset = st.selectbox(
            "プリセットを選択",
            preset_names,
            format_func=lambda x: ScreeningPresets.get_preset_with_icon(x)
        )

        if selected_preset:
            preset = ScreeningPresets.get_preset(selected_preset)

            col1, col2 = st.columns([2, 3])

            with col1:
                st.markdown(f"### {preset['icon']} {selected_preset}")
                st.markdown(f"**説明:** {preset['description']}")
                st.markdown(f"**対象投資家:** {preset['target_user']}")

                # 推奨表示列
                st.markdown("**推奨表示列:**")
                for col in preset.get('display_columns', []):
                    st.markdown(f"- {col}")

            with col2:
                st.markdown("### 設定条件詳細")

                conditions = preset['conditions']

                # 条件を読みやすく表示
                condition_display = []

                condition_labels = {
                    "min_dividend_yield": ("最低配当利回り", "%以上"),
                    "max_dividend_cv": ("最大配当変動係数", "以下"),
                    "min_quality_score": ("最低品質スコア", "点以上"),
                    "min_avg_yield": ("最低平均配当利回り", "%以上"),
                    "dividend_trend": ("配当トレンド", ""),
                    "max_per": ("最大PER", "倍以下"),
                    "max_pbr": ("最大PBR", "倍以下"),
                    "min_equity_ratio": ("最低自己資本比率", "%以上"),
                    "min_current_ratio": ("最低流動比率", "%以上"),
                    "use_db": ("データベース使用", ""),
                }

                for key, value in conditions.items():
                    if key == "use_db":
                        continue

                    label, unit = condition_labels.get(key, (key, ""))

                    if isinstance(value, bool):
                        value_str = "✅ はい" if value else "❌ いいえ"
                    elif isinstance(value, (int, float)):
                        value_str = f"{value} {unit}"
                    else:
                        value_str = f"{value} {unit}"

                    condition_display.append({
                        "条件項目": label,
                        "設定値": value_str
                    })

                df_conditions = pd.DataFrame(condition_display)
                st.dataframe(df_conditions, use_container_width=True, hide_index=True)

                # データベース使用の有無
                if conditions.get('use_db', False):
                    st.success("✅ このプリセットはデータベーススクリーニングに対応しています")
                else:
                    st.warning("⚠️ このプリセットはリアルタイムスクリーニングのみです")

            st.markdown("---")

            # プリセットの使用例
            st.markdown("### 💡 使用例")

            usage_examples = {
                "高配当・安定配当": """
                **投資家タイプ:** 定期的な配当収入を重視する投資家

                **使用シーン:**
                - 長期保有を前提とした銘柄選定
                - リタイア後の配当収入確保
                - ポートフォリオの安定収入源構築

                **期待される結果:**
                - 配当利回り4%以上の銘柄
                - 配当が安定している優良銘柄
                - 財務健全性が高い企業
                """,
                "配当貴族候補": """
                **投資家タイプ:** 配当成長を重視する長期投資家

                **使用シーン:**
                - 長期的な配当成長を期待
                - 複利効果を活用した資産形成
                - 配当再投資戦略

                **期待される結果:**
                - 連続増配が期待できる銘柄
                - 成長性と配当のバランスが良い企業
                - 高品質スコアの優良銘柄
                """,
                "バリュー高配当": """
                **投資家タイプ:** バリュー投資 + 高配当を求める投資家

                **使用シーン:**
                - 割安株の発掘
                - 市場の過小評価を利用
                - リスクリターンのバランス重視

                **期待される結果:**
                - PER・PBRが低い割安株
                - 配当利回りも確保
                - 上昇余地のある銘柄
                """,
                "超高配当": """
                **投資家タイプ:** 高利回りを最優先（リスク許容度高）

                **使用シーン:**
                - 短中期的な高収入確保
                - リスクを取って高リターン追求
                - ポートフォリオのサテライト戦略

                **期待される結果:**
                - 配当利回り5%以上の高配当銘柄
                - ただしリスクも高い可能性
                - 慎重な個別分析が必要
                """,
                "安定成長配当": """
                **投資家タイプ:** バランス重視の長期投資家

                **使用シーン:**
                - リスクとリターンのバランス
                - 長期的な資産形成
                - コア・サテライト戦略のコア部分

                **期待される結果:**
                - 配当成長と安定性のバランス
                - 中長期的な資産増加
                - 比較的安全な投資
                """,
                "低リスク配当株": """
                **投資家タイプ:** リスクを最小限に抑えたい保守的な投資家

                **使用シーン:**
                - 退職後の資産保全
                - 安全第一の投資
                - 元本毀損リスクの最小化

                **期待される結果:**
                - 財務健全性の高い企業
                - 倒産リスクが低い銘柄
                - 安定した配当継続
                """
            }

            if selected_preset in usage_examples:
                st.markdown(usage_examples[selected_preset])

    @staticmethod
    def _show_custom_conditions():
        """カスタム条件設定を表示"""
        st.header("🎯 カスタム条件設定")

        st.markdown("""
        独自のスクリーニング条件を設定できます。設定した条件は現在のセッションでのみ有効です。
        """)

        with st.form("custom_screening_form"):
            st.subheader("📊 配当条件")
            col1, col2 = st.columns(2)

            with col1:
                custom_min_dividend = st.number_input(
                    "最低配当利回り (%)",
                    min_value=0.0,
                    max_value=20.0,
                    value=3.0,
                    step=0.5
                )

                custom_max_dividend_cv = st.number_input(
                    "最大配当変動係数",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.3,
                    step=0.1,
                    help="0.3以下が安定、0.5以上は不安定"
                )

            with col2:
                custom_min_quality = st.slider(
                    "最低配当品質スコア",
                    min_value=0,
                    max_value=100,
                    value=60,
                    step=5
                )

                custom_dividend_trend = st.selectbox(
                    "配当トレンド",
                    ["全て", "増加", "安定", "減少除外"]
                )

            st.markdown("---")
            st.subheader("💰 バリュエーション条件")

            col3, col4 = st.columns(2)

            with col3:
                custom_max_per = st.number_input(
                    "最大PER",
                    min_value=0.0,
                    max_value=100.0,
                    value=20.0,
                    step=1.0
                )

                custom_max_pbr = st.number_input(
                    "最大PBR",
                    min_value=0.0,
                    max_value=10.0,
                    value=1.5,
                    step=0.1
                )

            with col4:
                custom_max_per_cv = st.number_input(
                    "最大PER変動係数",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.4,
                    step=0.1
                )

            st.markdown("---")
            st.subheader("💼 財務健全性条件")

            col5, col6 = st.columns(2)

            with col5:
                custom_min_equity = st.number_input(
                    "最低自己資本比率 (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=40.0,
                    step=5.0
                )

            with col6:
                custom_min_current = st.number_input(
                    "最低流動比率 (%)",
                    min_value=0.0,
                    max_value=500.0,
                    value=150.0,
                    step=10.0
                )

            st.markdown("---")
            st.subheader("🏢 企業規模条件")

            col7, col8 = st.columns(2)

            with col7:
                custom_min_market_cap = st.number_input(
                    "最低時価総額 (億円)",
                    min_value=0.0,
                    value=100.0,
                    step=50.0
                )

            with col8:
                custom_max_market_cap = st.number_input(
                    "最大時価総額 (億円)",
                    min_value=0.0,
                    value=10000.0,
                    step=500.0
                )

            submitted = st.form_submit_button("💾 条件を保存してプレビュー")

            if submitted:
                # カスタム条件をセッション状態に保存
                custom_conditions = {
                    "min_dividend_yield": custom_min_dividend,
                    "max_dividend_cv": custom_max_dividend_cv,
                    "min_quality_score": custom_min_quality,
                    "dividend_trend": custom_dividend_trend,
                    "max_per": custom_max_per,
                    "max_pbr": custom_max_pbr,
                    "max_per_cv": custom_max_per_cv,
                    "min_equity_ratio": custom_min_equity,
                    "min_current_ratio": custom_min_current,
                    "min_market_cap": custom_min_market_cap,
                    "max_market_cap": custom_max_market_cap
                }

                st.session_state['custom_screening_conditions'] = custom_conditions

                st.success("✅ カスタム条件を保存しました")

                # プレビュー表示
                st.markdown("### 📋 設定した条件のプレビュー")

                preview_data = []
                for key, value in custom_conditions.items():
                    preview_data.append({
                        "条件項目": key,
                        "設定値": value
                    })

                df_preview = pd.DataFrame(preview_data)
                st.dataframe(df_preview, use_container_width=True, hide_index=True)

                st.info("💡 メインのスクリーニング画面でこの条件を使用できます")
