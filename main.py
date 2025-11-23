"""
株価分析アプリ - 統合メインエントリーポイント
ts_app_claudeスタイルのアーキテクチャ

すべての機能にアクセス可能:
- 基本機能（個別銘柄分析、スクリーニング、EDINET、データ更新）
- 配当重視投資家向け機能
- テクニカル分析向け機能（将来実装）
"""

import streamlit as st
from config import APP_CONFIG

# Streamlitページ設定
st.set_page_config(
    page_title=APP_CONFIG.page_title,
    page_icon=APP_CONFIG.page_icon,
    layout=APP_CONFIG.layout,
    initial_sidebar_state=APP_CONFIG.initial_sidebar_state
)

# サイドバーでカテゴリーを選択
st.sidebar.title("📊 機能カテゴリー選択")

category = st.sidebar.radio(
    "カテゴリーを選択してください",
    [
        "🏠 基本機能",
        "💰 配当重視投資家向け",
        "📈 テクニカル分析向け（準備中）"
    ],
    index=0
)

st.sidebar.markdown("---")

# カテゴリーごとに機能を表示
if category == "🏠 基本機能":
    st.sidebar.subheader("基本機能")
    app_mode = st.sidebar.radio(
        "機能を選択してください",
        [
            "🔍 株価分析（個別銘柄＆スクリーニング）",
            "⚙️ スクリーニング管理",
            "📈 EDINET財務分析",
            "🔄 データベース更新管理"
        ],
        index=0
    )

    # 選択されたアプリケーションを実行
    if app_mode == "🔍 株価分析（個別銘柄＆スクリーニング）":
        # 既存の株価分析アプリを実行（st.set_page_config部分をスキップ）
        with open('stock_analysis_app.py', 'r', encoding='utf-8') as f:
            code = f.read()
            # st.set_page_config行を除外
            lines = code.split('\n')
            filtered_lines = []
            skip_config = False

            for line in lines:
                if 'st.set_page_config' in line:
                    skip_config = True
                    continue
                if skip_config and ')' in line and 'st.set_page_config' not in line:
                    skip_config = False
                    continue
                if skip_config:
                    continue
                filtered_lines.append(line)

            filtered_code = '\n'.join(filtered_lines)
            exec(filtered_code, globals())

    elif app_mode == "⚙️ スクリーニング管理":
        # スクリーニング管理ページを表示
        from ui.pages.screening_config_page import ScreeningConfigPage
        ScreeningConfigPage.show()

    elif app_mode == "📈 EDINET財務分析":
        # EDINET分析ページを表示
        from ui.pages.edinet_page import EDINETPage
        EDINETPage.show()

    elif app_mode == "🔄 データベース更新管理":
        # データ更新ページを表示
        with open('old_backup/pages_old/data_update.py', 'r', encoding='utf-8') as f:
            code = f.read()
            # st.set_page_config, st.titleを除外
            lines = code.split('\n')
            filtered_lines = []
            skip_config = False
            skip_title = False

            for line in lines:
                # st.set_page_configをスキップ
                if 'st.set_page_config' in line:
                    skip_config = True
                    continue
                if skip_config and ')' in line:
                    skip_config = False
                    continue
                if skip_config:
                    continue

                # st.titleとst.sidebar.headerをスキップ（main.pyのタイトルを使う）
                if line.strip().startswith('st.title'):
                    continue
                if 'st.sidebar.header("データ更新")' in line:
                    continue

                filtered_lines.append(line)

            filtered_code = '\n'.join(filtered_lines)
            exec(filtered_code, globals())

elif category == "💰 配当重視投資家向け":
    st.sidebar.subheader("💰 配当重視投資家向け")
    dividend_mode = st.sidebar.radio(
        "機能を選択してください",
        [
            "📅 配当ダッシュボード",
            "👑 配当貴族スクリーニング",
            "📊 配当カバレッジ分析（準備中）"
        ],
        index=0
    )

    if dividend_mode == "📅 配当ダッシュボード":
        # 配当ダッシュボードを表示
        from ui.pages.dividend_dashboard_page import DividendDashboardPage
        DividendDashboardPage.show()

    elif dividend_mode == "👑 配当貴族スクリーニング":
        # 配当貴族スクリーニングを表示
        from ui.pages.dividend_aristocrats_page import DividendAristocratsPage
        DividendAristocratsPage.show()

    elif dividend_mode == "📊 配当カバレッジ分析（準備中）":
        st.title("📊 配当カバレッジ分析")
        st.info("🚧 この機能は現在準備中です。近日公開予定です。")
        st.markdown("""
        ### 予定されている機能
        - 配当性向分析
        - フリーキャッシュフロー配当性向
        - 配当カバレッジレシオ
        - 減配リスク警告
        """)

elif category == "📈 テクニカル分析向け（準備中）":
    st.sidebar.subheader("📈 テクニカル分析向け")
    st.sidebar.info("🚧 準備中")

    st.title("📈 テクニカル分析向け機能")
    st.info("🚧 この機能カテゴリーは現在準備中です。")
    st.markdown("""
    ### 将来実装予定の機能
    - 📊 25日移動平均線上の銘柄スクリーニング
    - 📈 ゴールデンクロス/デッドクロス検出
    - 📉 RSI・MACD分析
    - 🎯 テクニカル指標組み合わせスクリーニング
    """)

# フッター
st.sidebar.markdown("---")
st.sidebar.info("""
### 📖 使い方
- **株価分析**: 個別銘柄の詳細分析とスクリーニング
- **EDINET**: 金融庁EDINETから財務諸表を取得
- **データ更新**: データベースの更新管理

### 🏗️ アーキテクチャ
- ts_app_claudeスタイルの4層構造
- すべてのページが ui/pages/ に統合
- Domain層、Repository層、Services層、UI層
""")
