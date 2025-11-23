"""
配当貴族指標キャッシュ更新スクリプト
プライム市場銘柄の配当成長指標をyfinanceから取得してデータベースに保存
"""

import sys
import io
import os
from pathlib import Path

# Windows環境での文字エンコーディング問題を回避
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yfinance as yf
from datetime import datetime
from typing import Dict, Optional
from repository.database_manager import DatabaseManager
from services.dividend_aristocrats import DividendAristocrats
import time


class DividendAristocratsCacheUpdater:
    """配当貴族指標キャッシュ更新クラス"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        
    def update_single_ticker(self, ticker: str) -> Dict:
        """
        単一銘柄の配当指標を更新
        
        Args:
            ticker: 銘柄コード
            
        Returns:
            更新結果の辞書
        """
        result = {
            'ticker': ticker,
            'status': 'success',
            'error': None
        }
        
        try:
            # yfinanceから配当成長分析を実行
            analysis = DividendAristocrats.analyze_dividend_growth(ticker, years=5)
            
            if 'エラー' in analysis:
                result['status'] = 'error'
                result['error'] = analysis['エラー']
                return result
                result['status'] = 'error'
                result['error'] = 'データベース保存失敗'
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            
            # エラー情報もDBに保存
            try:
                error_metrics = {
                    'company_name': ticker,
                    'data_quality': 'incomplete',
                    'calculation_error': str(e)[:500]
                }
                self.db_manager.upsert_dividend_aristocrat_metrics(ticker, error_metrics)
            except:
                pass
        
        return result
    
    def _assess_data_quality(self, analysis: Dict) -> str:
        """
        データ品質を評価
        
        Args:
            analysis: 分析結果
            
        Returns:
            品質レベル（complete/partial/incomplete）
        """
        required_fields = ['現在配当利回り', '配当CAGR', '連続増配年数', '配当性向']
        available_count = sum(1 for field in required_fields if analysis.get(field) is not None)
        
        if available_count == len(required_fields):
            return 'complete'
        elif available_count >= 2:
            return 'partial'
        else:
            return 'incomplete'
    
    def update_prime_market_stocks(
        self,
        limit: Optional[int] = None,
        delay: float = 1.0,
        incremental: bool = False,
        max_age_hours: int = 168
    ):
        """
        プライム市場銘柄の配当指標を一括更新

        Args:
            limit: 更新する銘柄数の上限（Noneの場合は全件）
            delay: API呼び出し間の待機時間（秒）
            incremental: True=増分更新（古いキャッシュのみ）、False=全件更新
            max_age_hours: 増分更新時のキャッシュ有効期間（時間）
        """
        print("=" * 60)
        if incremental:
            print(f"配当貴族指標キャッシュ増分更新開始（{max_age_hours}時間以上前を更新）")
        else:
            print("配当貴族指標キャッシュ全件更新開始")
        print("=" * 60)

        # プライム市場銘柄リストを取得
        all_tickers = self.db_manager.get_prime_market_tickers()

        if not all_tickers:
            print("[ERROR] プライム市場銘柄が見つかりませんでした")
            return

        # 増分更新の場合、古いキャッシュの銘柄のみをフィルタ
        if incremental:
            # 古いキャッシュを取得
            query = f"""
                SELECT ticker
                FROM dividend_aristocrats_metrics
                WHERE last_updated < DATE_SUB(NOW(), INTERVAL {max_age_hours} HOUR)
            """
            old_cache = self.db_manager.execute_query(query)
            old_tickers = {row['ticker'] for row in old_cache} if old_cache else set()

            # キャッシュされていない銘柄も取得
            cached_query = "SELECT ticker FROM dividend_aristocrats_metrics"
            cached = self.db_manager.execute_query(cached_query)
            cached_tickers = {row['ticker'] for row in cached} if cached else set()

            not_cached = set(all_tickers) - cached_tickers

            # 古いキャッシュ + 未キャッシュ
            tickers_to_update = list(old_tickers | not_cached)

            print(f"[INFO] 全銘柄数: {len(all_tickers)}")
            print(f"[INFO] 古いキャッシュ: {len(old_tickers)} 銘柄")
            print(f"[INFO] 未キャッシュ: {len(not_cached)} 銘柄")
            print(f"[INFO] 更新対象: {len(tickers_to_update)} 銘柄")

            tickers = tickers_to_update
        else:
            tickers = all_tickers

        if limit:
            tickers = tickers[:limit]
        
        print(f"[INFO] 対象銘柄数: {len(tickers)}")
        print(f"[INFO] API待機時間: {delay}秒")
        print()
        
        # 更新履歴を記録
        update_id = self._start_update_history('dividend_aristocrats_cache', len(tickers))
        
        success_count = 0
        error_count = 0
        start_time = time.time()
        
        for i, ticker in enumerate(tickers, 1):
            print(f"[{i}/{len(tickers)}] {ticker} を処理中...", end=" ")
            
            result = self.update_single_ticker(ticker)
            
            if result['status'] == 'success':
                print("[OK]")
                success_count += 1
            else:
                print(f"[ERROR] {result['error']}")
                error_count += 1
            
            # API制限対策の待機
            if i < len(tickers):
                time.sleep(delay)
        
        elapsed_time = time.time() - start_time
        
        # 更新履歴を完了
        self._complete_update_history(update_id, success_count, error_count)
        
        # サマリー表示
        print()
        print("=" * 60)
        print("更新完了")
        print("=" * 60)
        print(f"[OK] 成功: {success_count} 銘柄")
        print(f"[ERROR] エラー: {error_count} 銘柄")
        print(f"[TIME] 所要時間: {elapsed_time:.1f}秒")
        print(f"[TIME] 平均処理時間: {elapsed_time/len(tickers):.2f}秒/銘柄")
        print()
    
    def _start_update_history(self, update_type: str, total_records: int) -> int:
        """更新履歴の開始を記録"""
        query = """
            INSERT INTO update_history (update_type, status, records_updated, started_at)
            VALUES (%s, 'running', %s, %s)
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return 0
        
        try:
            cursor = connection.cursor()
            cursor.execute(query, (update_type, total_records, datetime.now()))
            connection.commit()
            update_id = cursor.lastrowid
            cursor.close()
            connection.close()
            return update_id
        except Exception as e:
            print(f"[WARN] 更新履歴記録エラー: {e}")
            if connection:
                connection.close()
            return 0
    
    def _complete_update_history(self, update_id: int, success_count: int, error_count: int):
        """更新履歴の完了を記録"""
        if update_id == 0:
            return
        
        status = 'success' if error_count == 0 else 'partial'
        error_message = f"{error_count} 銘柄でエラー" if error_count > 0 else None
        
        query = """
            UPDATE update_history 
            SET status = %s, records_updated = %s, error_message = %s, completed_at = %s
            WHERE id = %s
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return
        
        try:
            cursor = connection.cursor()
            cursor.execute(query, (status, success_count, error_message, datetime.now(), update_id))
            connection.commit()
            cursor.close()
            connection.close()
        except Exception as e:
            print(f"[WARN] 更新履歴完了記録エラー: {e}")
            if connection:
                connection.close()


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description='配当貴族指標キャッシュ更新')
    parser.add_argument('--limit', type=int, help='更新する銘柄数の上限（テスト用）')
    parser.add_argument('--delay', type=float, default=1.0, help='API呼び出し間の待機時間（秒）')
    parser.add_argument('--incremental', action='store_true', help='増分更新モード（古いキャッシュのみ更新）')
    parser.add_argument('--max-age', type=int, default=168, help='増分更新時のキャッシュ有効期間（時間、デフォルト168=1週間）')

    args = parser.parse_args()

    updater = DividendAristocratsCacheUpdater()
    updater.update_prime_market_stocks(
        limit=args.limit,
        delay=args.delay,
        incremental=args.incremental,
        max_age_hours=args.max_age
    )


if __name__ == '__main__':
    main()
