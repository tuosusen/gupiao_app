"""
データベース接続設定
環境変数からMySQL接続情報を取得
"""

import os
import mysql.connector
from mysql.connector import Error
import streamlit as st

class DatabaseConfig:
    """データベース接続設定クラス"""

    def __init__(self):
        """環境変数から接続情報を読み込み"""
        self.host = os.getenv('MYSQL_HOST', 'localhost')
        self.port = int(os.getenv('MYSQL_PORT', '3306'))
        self.user = os.getenv('MYSQL_USER', 'root')
        self.password = os.getenv('MYSQL_PASSWORD', '')
        self.database = os.getenv('MYSQL_DATABASE', 'stock_analysis')

    def get_connection(self):
        """データベース接続を取得"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                autocommit=False
            )
            return connection
        except Error as e:
            st.error(f"❌ データベース接続エラー: {e}")
            st.info("💡 環境変数を確認してください: MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE")
            return None

    def test_connection(self):
        """接続テスト"""
        connection = self.get_connection()
        if connection and connection.is_connected():
            db_info = connection.get_server_info()
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()[0]
            cursor.close()
            connection.close()
            return True, f"MySQL Server version: {db_info}, Database: {db_name}"
        return False, "接続失敗"

    def create_database_if_not_exists(self):
        """データベースが存在しない場合は作成"""
        try:
            # データベース名を指定せずに接続
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset='utf8mb4'
            )
            cursor = connection.cursor()

            # データベース作成
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute(f"USE {self.database}")

            cursor.close()
            connection.close()
            return True, f"データベース '{self.database}' を作成/確認しました"

        except Error as e:
            return False, f"データベース作成エラー: {e}"


class DatabaseManager:
    """データベース操作を管理するクラス"""

    def __init__(self):
        self.config = DatabaseConfig()

    def execute_query(self, query, params=None, fetch=True):
        """クエリを実行"""
        connection = self.config.get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())

            if fetch:
                result = cursor.fetchall()
            else:
                connection.commit()
                result = cursor.rowcount

            cursor.close()
            connection.close()
            return result

        except Error as e:
            st.error(f"❌ クエリ実行エラー: {e}")
            if connection:
                connection.rollback()
                connection.close()
            return None

    def execute_many(self, query, data_list):
        """複数レコードを一括挿入"""
        if not data_list or len(data_list) == 0:
            return 0

        connection = self.config.get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()
            cursor.executemany(query, data_list)
            connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            connection.close()
            return affected_rows

        except Error as e:
            # エラーの詳細を表示（最初の数件のみ）
            st.error(f"❌ 一括挿入エラー: {e}")
            st.error(f"クエリ: {query[:100]}...")
            st.error(f"データサンプル: {data_list[0] if data_list else 'なし'}")
            if connection:
                connection.rollback()
                connection.close()
            return 0

    def get_stocks_list(self):
        """全銘柄リストを取得"""
        query = "SELECT ticker, name, sector, market FROM stocks ORDER BY ticker"
        return self.execute_query(query)

    def get_screening_data(self, conditions=None):
        """スクリーニング用データを取得"""
        query = """
        SELECT * FROM v_screening_data
        WHERE 1=1
        """
        params = []

        if conditions:
            if conditions.get('min_dividend_yield'):
                query += " AND dividend_yield >= %s"
                params.append(conditions['min_dividend_yield'])

            if conditions.get('max_per'):
                query += " AND per <= %s AND per > 0"
                params.append(conditions['max_per'])

            if conditions.get('max_pbr'):
                query += " AND pbr <= %s AND pbr > 0"
                params.append(conditions['max_pbr'])

            if conditions.get('min_avg_dividend_yield'):
                query += " AND avg_dividend_yield >= %s"
                params.append(conditions['min_avg_dividend_yield'])

            if conditions.get('min_dividend_quality_score'):
                query += " AND dividend_quality_score >= %s"
                params.append(conditions['min_dividend_quality_score'])

            if conditions.get('market'):
                query += " AND market = %s"
                params.append(conditions['market'])

        query += " ORDER BY dividend_quality_score DESC"

        return self.execute_query(query, params)


# グローバルインスタンス
db_manager = DatabaseManager()
