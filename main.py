"""
株価分析アプリ - 統合メインエントリーポイント
ts_app_claudeスタイルのアーキテクチャ

すべての機能にアクセス可能:
- 個別銘柄分析
- 銘柄スクリーニング
- EDINET財務分析
- データ更新管理
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

# サイドバーでアプリケーションを選択
st.sidebar.title("📊 アプリケーション選択")

app_mode = st.sidebar.radio(
    "使用する機能を選択してください",
    [
        "🔍 株価分析（個別銘柄＆スクリーニング）",
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
