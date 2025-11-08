"""
データ更新画面
株価データをyfinanceから取得してMySQLに保存
"""

import streamlit as st
from datetime import datetime
import sys
import os

# パスを追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.db_config import DatabaseConfig, DatabaseManager
from database.data_updater import StockDataUpdater

st.set_page_config(
    page_title="データ更新 - 株価分析アプリ",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 データベース更新管理")

# サイドバー
st.sidebar.header("データ更新")

# データベース接続確認
db_config = DatabaseConfig()
db_manager = DatabaseManager()
updater = StockDataUpdater()

# タブ作成
tab1, tab2, tab3, tab4 = st.tabs(["🔄 データ更新", "📊 データベース状態", "⚙️ 設定確認", "📚 更新履歴"])

with tab1:
    st.header("データ更新")

    st.info("""
    💡 **データ更新について**
    - 初回更新: 全銘柄のデータを取得（1-2時間）
    - 差分更新: 最近更新された銘柄のみ（10-20分）
    - 単一更新: 特定銘柄のみ更新（数秒）
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("全銘柄更新")

        # 並列処理数の選択
        max_workers = st.slider("並列処理数", 1, 10, 3, help="同時に処理する銘柄数（推奨: 2-3、多すぎるとレート制限エラー）")
        st.info("⚠️ レート制限を避けるため、並列処理数は2-3を推奨します。5以上は高確率でエラーになります。")

        # JPXから銘柄リストを取得して更新を開始
        if st.button("🔄 プライム市場全銘柄を更新", type="primary"):
            with st.spinner("銘柄リストを取得中..."):
                # メインアプリの関数をインポート
                from stock_analysis_app import get_premium_market_stocks

                stocks = get_premium_market_stocks()

                if stocks and len(stocks) > 0:
                    st.success(f"✅ {len(stocks)}銘柄を取得しました")
                    st.info(f"⏳ {len(stocks)}銘柄の更新を開始します...")

                    start_time = datetime.now()

                    # 更新履歴を記録
                    query = """
                    INSERT INTO update_history (update_type, status, started_at)
                    VALUES ('full', 'running', %s)
                    """
                    db_manager.execute_query(query, (start_time,), fetch=False)

                    # 全銘柄更新
                    success_count, error_count = updater.update_all_stocks(stocks, max_workers=max_workers)

                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()

                    # 更新履歴を更新
                    query = """
                    UPDATE update_history
                    SET status = 'success',
                        records_updated = %s,
                        completed_at = %s
                    WHERE started_at = %s
                    """
                    db_manager.execute_query(query, (success_count, end_time, start_time), fetch=False)

                    st.success(f"""
                    ✅ 更新完了！
                    - 成功: {success_count}銘柄
                    - 失敗: {error_count}銘柄
                    - 所要時間: {duration/60:.1f}分
                    """)
                else:
                    st.error("❌ 銘柄リストの取得に失敗しました")

    with col2:
        st.subheader("単一銘柄更新")

        ticker_input = st.text_input("銘柄コード", "7203.T", help="例: 7203.T（トヨタ）")
        name_input = st.text_input("銘柄名", "トヨタ自動車")

        if st.button("🔄 この銘柄を更新"):
            with st.spinner(f"{ticker_input}のデータを取得中..."):
                success, error = updater.fetch_and_save_single_stock(ticker_input, name_input)

                if success:
                    st.success(f"✅ {ticker_input} ({name_input}) の更新完了")
                else:
                    st.error(f"❌ エラー: {error}")

    st.divider()

    st.subheader("差分更新（推奨）")
    st.info("📅 最終更新から24時間以上経過した銘柄のみを更新します")

    days_old = st.number_input("何日以上前のデータを更新するか", 1, 30, 1)

    if st.button("🔄 差分更新を実行"):
        # 古いデータの銘柄リストを取得
        query = f"""
        SELECT ticker, name FROM stocks
        WHERE updated_at < DATE_SUB(NOW(), INTERVAL {days_old} DAY)
        """
        old_stocks = db_manager.execute_query(query)

        if old_stocks:
            st.info(f"⏳ {len(old_stocks)}銘柄を更新します...")

            stocks_dict = {row['ticker']: row['name'] for row in old_stocks}
            success_count, error_count = updater.update_all_stocks(stocks_dict, max_workers=5)

            st.success(f"""
            ✅ 差分更新完了！
            - 成功: {success_count}銘柄
            - 失敗: {error_count}銘柄
            """)
        else:
            st.info("✅ 更新が必要な銘柄はありません")

with tab2:
    st.header("データベース状態")

    col1, col2, col3 = st.columns(3)

    # 統計情報を取得
    stats_queries = {
        "銘柄数": "SELECT COUNT(*) as count FROM stocks",
        "財務指標レコード数": "SELECT COUNT(*) as count FROM financial_metrics",
        "配当レコード数": "SELECT COUNT(*) as count FROM dividends",
        "株価レコード数": "SELECT COUNT(*) as count FROM stock_prices",
    }

    for idx, (label, query) in enumerate(stats_queries.items()):
        result = db_manager.execute_query(query)
        count = result[0]['count'] if result else 0

        with [col1, col2, col3][idx % 3]:
            st.metric(label, f"{count:,}")

    st.divider()

    # 最近更新された銘柄
    st.subheader("最近更新された銘柄（上位10件）")
    recent_stocks = db_manager.execute_query("""
        SELECT ticker, name, sector, updated_at
        FROM stocks
        ORDER BY updated_at DESC
        LIMIT 10
    """)

    if recent_stocks:
        st.dataframe(recent_stocks, use_container_width=True)

    # データの古い銘柄
    st.subheader("更新が古い銘柄（上位10件）")
    old_stocks = db_manager.execute_query("""
        SELECT ticker, name, sector, updated_at,
               DATEDIFF(NOW(), updated_at) as days_old
        FROM stocks
        ORDER BY updated_at ASC
        LIMIT 10
    """)

    if old_stocks:
        st.dataframe(old_stocks, use_container_width=True)

with tab3:
    st.header("設定確認")

    # 環境変数の確認
    st.subheader("環境変数")

    env_vars = {
        "MYSQL_HOST": os.getenv('MYSQL_HOST', '未設定'),
        "MYSQL_PORT": os.getenv('MYSQL_PORT', '未設定'),
        "MYSQL_USER": os.getenv('MYSQL_USER', '未設定'),
        "MYSQL_PASSWORD": "***" if os.getenv('MYSQL_PASSWORD') else '未設定',
        "MYSQL_DATABASE": os.getenv('MYSQL_DATABASE', '未設定'),
    }

    for key, value in env_vars.items():
        col1, col2 = st.columns([1, 3])
        with col1:
            st.write(f"**{key}**")
        with col2:
            if value == '未設定':
                st.error(value)
            else:
                st.success(value)

    st.divider()

    # 接続テスト
    st.subheader("データベース接続テスト")

    if st.button("接続テスト実行"):
        with st.spinner("接続中..."):
            success, message = db_config.test_connection()

            if success:
                st.success(f"✅ 接続成功: {message}")
            else:
                st.error(f"❌ 接続失敗: {message}")
                st.info("""
                💡 トラブルシューティング:
                1. MySQLサーバーが起動していることを確認
                2. 環境変数が正しく設定されていることを確認
                3. ユーザーに適切な権限があることを確認
                """)

with tab4:
    st.header("更新履歴")

    # 更新履歴を取得
    history = db_manager.execute_query("""
        SELECT
            update_type,
            ticker,
            status,
            records_updated,
            error_message,
            started_at,
            completed_at,
            TIMESTAMPDIFF(SECOND, started_at, completed_at) as duration_seconds
        FROM update_history
        ORDER BY started_at DESC
        LIMIT 50
    """)

    if history:
        st.dataframe(history, use_container_width=True)
    else:
        st.info("まだ更新履歴がありません")

    # クリアボタン
    if st.button("🗑️ 履歴をクリア"):
        db_manager.execute_query("DELETE FROM update_history", fetch=False)
        st.success("✅ 履歴をクリアしました")
        st.rerun()
