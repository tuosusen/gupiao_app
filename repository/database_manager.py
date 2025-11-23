"""
データベース接続管理
MySQL接続とクエリ実行を管理
"""

import mysql.connector
from mysql.connector import Error
import streamlit as st
from typing import List, Dict, Any, Optional, Tuple
from config import DB_CONFIG


class DatabaseManager:
    """データベース操作を管理するクラス"""

    def __init__(self, config=None):
        """
        初期化
        Args:
            config: DatabaseConfigインスタンス（デフォルトはDB_CONFIG）
        """
        self.config = config or DB_CONFIG

    def get_connection(self):
        """データベース接続を取得"""
        try:
            connection = mysql.connector.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                charset=self.config.charset,
                collation=self.config.collation,
                autocommit=False
            )
            return connection
        except Error as e:
            st.error(f"❌ データベース接続エラー: {e}")
            st.info("💡 環境変数を確認してください: MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE")
            return None

    def test_connection(self) -> Tuple[bool, str]:
        """
        接続テスト
        Returns:
            (成功フラグ, メッセージ)
        """
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

    def create_database_if_not_exists(self) -> Tuple[bool, str]:
        """
        データベースが存在しない場合は作成
        Returns:
            (成功フラグ, メッセージ)
        """
        try:
            connection = mysql.connector.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                charset=self.config.charset
            )
            cursor = connection.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {self.config.database} "
                f"CHARACTER SET {self.config.charset} "
                f"COLLATE {self.config.collation}"
            )
            cursor.execute(f"USE {self.config.database}")
            cursor.close()
            connection.close()
            return True, f"データベース '{self.config.database}' を作成/確認しました"
        except Error as e:
            return False, f"データベース作成エラー: {e}"

    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Optional[List[Dict[str, Any]]]:
        """
        クエリを実行
        Args:
            query: SQL文
            params: パラメータ
            fetch: 結果を取得するか（SELECT等の場合True、INSERT等の場合False）
        Returns:
            結果（辞書のリスト）またはNone
        """
        connection = self.get_connection()
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

    def execute_many(self, query: str, data_list: List[tuple]) -> int:
        """
        複数レコードを一括挿入
        Args:
            query: SQL文（プレースホルダ付き）
            data_list: データリスト
        Returns:
            影響を受けた行数
        """
        if not data_list or len(data_list) == 0:
            return 0

        connection = self.get_connection()
        if not connection:
            return 0

        try:
            cursor = connection.cursor()
            cursor.executemany(query, data_list)
            connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            connection.close()
            return affected_rows

        except Error as e:
            st.error(f"❌ 一括挿入エラー: {e}")
            st.error(f"クエリ: {query[:100]}...")
            st.error(f"データサンプル: {data_list[0] if data_list else 'なし'}")
            if connection:
                connection.rollback()
                connection.close()
            return 0

    def get_table_stats(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        テーブルの統計情報を取得
        Args:
            table_name: テーブル名
        Returns:
            統計情報（行数など）
        """
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        if result and len(result) > 0:
            return result[0]
        return None

    def get_dividend_aristocrat_tickers(self) -> List[str]:
        """
        配当貴族スクリーニング用の銘柄コードリストを取得
        
        Returns:
            銘柄コード(ticker)のリスト
        """
        query = """
            SELECT DISTINCT ticker 
            FROM stocks 
            WHERE ticker IS NOT NULL 
            ORDER BY ticker
        """
        result = self.execute_query(query)
        if result:
            return [row['ticker'] for row in result]
        return []

    def get_prime_market_tickers(self) -> List[str]:
        """
        プライム市場銘柄のリストを取得
        現状は日本市場全銘柄を対象とする（将来的に市場区分を細分化）

        Returns:
            銘柄コードリスト
        """
        query = """
            SELECT ticker
            FROM stocks
            WHERE (market = 'プライム' OR market = 'jp_market')
                AND ticker IS NOT NULL
            ORDER BY ticker
        """
        result = self.execute_query(query)
        if result:
            return [row['ticker'] for row in result]
        return []

    def get_dividend_aristocrats_metrics(
        self, 
        tickers: Optional[List[str]] = None,
        min_consecutive_years: int = 0,
        max_cache_age_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        配当貴族指標をDBから取得
        
        Args:
            tickers: 銘柄コードリスト（Noneの場合は全件）
            min_consecutive_years: 最低連続増配年数フィルタ
            max_cache_age_hours: キャッシュの最大有効期間（時間）
        
        Returns:
            指標データのリスト
        """
        if tickers:
            placeholders = ','.join(['%s'] * len(tickers))
            ticker_condition = f"AND ticker IN ({placeholders})"
            params = tuple(tickers) + (min_consecutive_years,)
        else:
            ticker_condition = ""
            params = (min_consecutive_years,)
        
        query = f"""
            SELECT 
                ticker,
                company_name,
                current_dividend_yield,
                after_tax_yield,
                consecutive_increase_years,
                dividend_cagr_5y,
                dividend_cagr_10y,
                payout_ratio,
                payout_ratio_status,
                fcf_payout_ratio,
                fcf_payout_status,
                aristocrat_status,
                data_quality,
                last_updated,
                calculation_error
            FROM dividend_aristocrats_metrics
            WHERE consecutive_increase_years >= %s
                {ticker_condition}
                AND last_updated >= DATE_SUB(NOW(), INTERVAL {max_cache_age_hours} HOUR)
            ORDER BY consecutive_increase_years DESC, dividend_cagr_5y DESC
        """
        
        result = self.execute_query(query, params)
        return result if result else []

    def upsert_dividend_aristocrat_metrics(
        self,
        ticker: str,
        metrics: Dict[str, Any]
    ) -> bool:
        """
        配当貴族指標をDBに保存（UPSERT）
        
        Args:
            ticker: 銘柄コード
            metrics: 指標データ
        
        Returns:
            成功フラグ
        """
        query = """
            INSERT INTO dividend_aristocrats_metrics (
                ticker,
                company_name,
                current_dividend_yield,
                after_tax_yield,
                consecutive_increase_years,
                dividend_cagr_5y,
                dividend_cagr_10y,
                payout_ratio,
                payout_ratio_status,
                fcf_payout_ratio,
                fcf_payout_status,
                aristocrat_status,
                data_quality,
                calculation_error
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                company_name = VALUES(company_name),
                current_dividend_yield = VALUES(current_dividend_yield),
                after_tax_yield = VALUES(after_tax_yield),
                consecutive_increase_years = VALUES(consecutive_increase_years),
                dividend_cagr_5y = VALUES(dividend_cagr_5y),
                dividend_cagr_10y = VALUES(dividend_cagr_10y),
                payout_ratio = VALUES(payout_ratio),
                payout_ratio_status = VALUES(payout_ratio_status),
                fcf_payout_ratio = VALUES(fcf_payout_ratio),
                fcf_payout_status = VALUES(fcf_payout_status),
                aristocrat_status = VALUES(aristocrat_status),
                data_quality = VALUES(data_quality),
                calculation_error = VALUES(calculation_error),
                last_updated = CURRENT_TIMESTAMP
        """
        
        params = (
            ticker,
            metrics.get('銘柄名') or metrics.get('company_name'),
            metrics.get('現在配当利回り') or metrics.get('current_dividend_yield'),
            metrics.get('税引後利回り') or metrics.get('after_tax_yield'),
            metrics.get('連続増配年数', 0) or metrics.get('consecutive_increase_years', 0),
            metrics.get('配当CAGR') or metrics.get('dividend_cagr_5y'),
            metrics.get('dividend_cagr_10y'),
            metrics.get('配当性向') or metrics.get('payout_ratio'),
            metrics.get('配当性向評価', '') or metrics.get('payout_ratio_status', ''),
            metrics.get('FCF配当性向') or metrics.get('fcf_payout_ratio'),
            metrics.get('FCF配当性向評価', '') or metrics.get('fcf_payout_status', ''),
            metrics.get('ステータス', '') or metrics.get('aristocrat_status', ''),
            metrics.get('data_quality', 'complete'),
            metrics.get('エラー') or metrics.get('calculation_error')
        )
        
        result = self.execute_query(query, params, fetch=False)
        return result is not None and result > 0

    def get_cached_metrics_count(self) -> Dict[str, Any]:
        """
        キャッシュ統計を取得

        Returns:
            統計情報（総数、最終更新日時）
        """
        query = """
            SELECT
                COUNT(*) as total,
                MAX(last_updated) as latest_update
            FROM dividend_aristocrats_metrics
        """

        result = self.execute_query(query)
        if result and len(result) > 0:
            return result[0]
        return {'total': 0, 'latest_update': None}

    def get_cache_quality_stats(self) -> Dict[str, Any]:
        """
        キャッシュのデータ品質統計を取得

        Returns:
            品質別の統計情報
        """
        query = """
            SELECT
                data_quality,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM dividend_aristocrats_metrics), 2) as percentage
            FROM dividend_aristocrats_metrics
            GROUP BY data_quality
            ORDER BY
                CASE data_quality
                    WHEN 'complete' THEN 1
                    WHEN 'partial' THEN 2
                    WHEN 'incomplete' THEN 3
                    ELSE 4
                END
        """

        result = self.execute_query(query)
        if result:
            stats = {
                'by_quality': result,
                'total': sum(row['count'] for row in result)
            }

            # 品質スコア（complete=100, partial=50, incomplete=0の加重平均）
            quality_weights = {'complete': 100, 'partial': 50, 'incomplete': 0}
            total_score = sum(
                row['count'] * quality_weights.get(row['data_quality'], 0)
                for row in result
            )
            stats['overall_quality_score'] = round(total_score / stats['total'], 2) if stats['total'] > 0 else 0

            return stats

        return {'by_quality': [], 'total': 0, 'overall_quality_score': 0}
