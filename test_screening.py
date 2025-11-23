"""配当貴族スクリーニングのテスト（キャッシュあり/なし）"""
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import time
from services.dividend_aristocrats import DividendAristocrats

def test_screening():
    """スクリーニングテスト"""

    # テスト条件
    min_years = 5
    min_cagr = 3.0
    max_payout = 80
    analysis_years = 5

    print("=" * 60)
    print("配当貴族スクリーニング テスト")
    print("=" * 60)
    print(f"条件: 連続増配{min_years}年以上、CAGR{min_cagr}%以上、配当性向{max_payout}%以下")
    print()

    # テスト1: キャッシュあり（最大1時間前のデータを使用）
    print("[テスト1] キャッシュあり（最大1時間前のデータ）")
    print("-" * 60)
    start_time = time.time()

    results_cached = DividendAristocrats.screen_dividend_aristocrats(
        min_consecutive_years=min_years,
        min_cagr=min_cagr,
        max_payout_ratio=max_payout,
        years=analysis_years,
        use_cache=True,
        max_cache_age_hours=1
    )

    elapsed_cached = time.time() - start_time

    print(f"結果: {len(results_cached)} 銘柄")
    print(f"所要時間: {elapsed_cached:.2f}秒")

    if not results_cached.empty:
        print("\n上位3銘柄:")
        for i, (idx, stock) in enumerate(results_cached.head(3).iterrows(), 1):
            print(f"  [{i}] {stock['銘柄コード']} - {stock['銘柄名']}")
            print(f"      連続増配: {stock['連続増配年数']}年 | CAGR: {stock['配当CAGR']:.2f}% | 利回り: {stock['現在配当利回り']:.2f}%")

    print()
    print("=" * 60)

    # テスト2: キャッシュなし（yfinanceから直接取得）
    print("[テスト2] キャッシュなし（yfinanceから直接取得 - 5銘柄のみ）")
    print("-" * 60)
    print("注: 時間がかかるため5銘柄のみテストします")

    # 5銘柄だけでテスト
    from repository.database_manager import DatabaseManager
    db = DatabaseManager()
    test_tickers = db.get_prime_market_tickers()[:5]

    start_time = time.time()

    # 一時的にキャッシュを無効化してテスト
    results_nocache = []
    for ticker in test_tickers:
        analysis = DividendAristocrats.analyze_dividend_growth(ticker, years=analysis_years)

        if 'エラー' not in analysis:
            # フィルタリング条件を適用
            if (analysis.get('連続増配年数', 0) >= min_years and
                analysis.get('配当CAGR', 0) >= min_cagr and
                analysis.get('配当性向', 100) <= max_payout):
                results_nocache.append(analysis)

    elapsed_nocache = time.time() - start_time

    print(f"結果: {len(results_nocache)} 銘柄（5銘柄中）")
    print(f"所要時間: {elapsed_nocache:.2f}秒")
    print(f"平均: {elapsed_nocache/5:.2f}秒/銘柄")

    print()
    print("=" * 60)
    print("パフォーマンス比較")
    print("=" * 60)
    print(f"キャッシュあり: {elapsed_cached:.2f}秒")
    print(f"キャッシュなし（5銘柄のみ）: {elapsed_nocache:.2f}秒")

    if len(test_tickers) > 5:
        estimated_full = elapsed_nocache / 5 * len(test_tickers)
        speedup = estimated_full / elapsed_cached if elapsed_cached > 0 else 0
        print(f"\n全{len(test_tickers)}銘柄の場合の推定時間: {estimated_full:.1f}秒")
        print(f"スピードアップ: 約{speedup:.0f}倍")

    print()

if __name__ == '__main__':
    test_screening()
