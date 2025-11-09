
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
import io
import requests

# Streamlitアプリの設定 - ページ設定を最初に
st.set_page_config(
    page_title="株価分析アプリ",
    layout="wide",
    initial_sidebar_state="expanded"  # サイドバーを初期表示
)

st.title("株価分析ダッシュボード")

# サイドバーにモード選択を追加
st.sidebar.header("モード選択")

# スクリーニングから詳細分析に切り替える場合
if 'current_mode' not in st.session_state:
    st.session_state['current_mode'] = "個別銘柄分析"

# 強制的に個別銘柄分析モードに切り替え
if st.session_state.get('switch_to_analysis', False):
    st.session_state['current_mode'] = "個別銘柄分析"
    st.session_state['switch_to_analysis'] = False
    mode = "個別銘柄分析"
else:
    mode = st.sidebar.radio(
        "分析モードを選択",
        ["個別銘柄分析", "銘柄スクリーニング"],
        index=0 if st.session_state['current_mode'] == "個別銘柄分析" else 1,
        key="mode_selector"
    )
    st.session_state['current_mode'] = mode

if mode == "個別銘柄分析":
    # サイドバーで銘柄コードと期間を入力
    st.sidebar.header("分析設定")

    # セッション状態から銘柄コードを取得（スクリーニングから来た場合）
    default_ticker = st.session_state.get('analyze_ticker', '7203.T')

    ticker = st.sidebar.text_input("銘柄コード（例: 7203.T, AAPL）", default_ticker)
    start_date = st.sidebar.date_input("開始日", datetime.now() - timedelta(days=365*3))
    end_date = st.sidebar.date_input("終了日", datetime.now())

    # 銘柄コードが変更されたら自動実行フラグをリセット
    if 'last_ticker' not in st.session_state or st.session_state['last_ticker'] != ticker:
        st.session_state['last_ticker'] = ticker
        st.session_state['auto_run_completed'] = False
else:
    # スクリーニング条件の設定
    st.sidebar.header("スクリーニング条件")

    # 対象市場
    st.sidebar.subheader("対象市場")
    market = st.sidebar.selectbox(
        "市場を選択",
        [
            "日本株（東証プライム市場全銘柄）",
            "日本株（東証主要銘柄）",
            "米国株（S&P500）"
        ],
        help="プライム市場全銘柄: 約1,800銘柄（時間がかかります）\n主要銘柄: 約50銘柄（高速）"
    )

    # 銘柄数の表示
    if market == "日本株（東証プライム市場全銘柄）":
        st.sidebar.info("⚠️ 全銘柄スクリーニングには15-30分程度かかる場合があります")
    elif market == "日本株（東証主要銘柄）":
        st.sidebar.info("✅ 主要銘柄のみ（高速スクリーニング）")

    # スクリーニングモード選択
    st.sidebar.subheader("スクリーニングモード")
    screening_mode = st.sidebar.radio(
        "モードを選択",
        ["基本モード", "高度な配当分析", "高度なPER分析", "カスタム条件"],
        help="基本モード: シンプルな条件でスクリーニング\n高度な配当分析: 過去の配当履歴を考慮\n高度なPER分析: 過去のPER推移を考慮"
    )

    # 配当条件
    st.sidebar.subheader("📊 配当条件")

    if screening_mode in ["基本モード", "カスタム条件"]:
        use_basic_dividend = st.sidebar.checkbox("基本的な配当利回り条件を使用", value=True)
        if use_basic_dividend:
            min_dividend_yield = st.sidebar.number_input("最低配当利回り (%)", min_value=0.0, max_value=20.0, value=2.0, step=0.5)
        else:
            min_dividend_yield = 0.0
        dividend_growth = st.sidebar.checkbox("配当増加傾向", value=False)
    else:
        use_basic_dividend = False
        min_dividend_yield = 0.0
        dividend_growth = False

    # 高度な配当条件
    if screening_mode in ["高度な配当分析", "カスタム条件"]:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🔍 高度な配当分析**")

        use_advanced_dividend = st.sidebar.checkbox("高度な配当分析を使用", value=True if screening_mode == "高度な配当分析" else False)

        if use_advanced_dividend:
            dividend_years = st.sidebar.selectbox("分析期間", [3, 4, 5], index=1, help="過去何年分のデータを分析するか")

            # プリセット条件
            dividend_preset = st.sidebar.selectbox(
                "プリセット条件",
                ["カスタム", "安定高配当株", "減配だが過去高配当"],
                help="カスタム: 自分で設定\n安定高配当株: 過去平均3.5%以上で変動が小さい\n減配だが過去高配当: 今期減配だが過去5年平均4%以上"
            )

            if dividend_preset == "安定高配当株":
                min_avg_dividend_yield = 3.5
                max_dividend_cv = 0.3
                declining_but_high_avg = False
                require_increasing_trend = False
                exclude_special_dividend = True
                min_dividend_quality_score = 60
            elif dividend_preset == "減配だが過去高配当":
                min_avg_dividend_yield = 4.0
                max_dividend_cv = None
                declining_but_high_avg = True
                require_increasing_trend = False
                exclude_special_dividend = False
                min_dividend_quality_score = None
            else:  # カスタム
                min_avg_dividend_yield = st.sidebar.number_input(
                    f"過去{dividend_years}年平均配当利回り (%) 以上",
                    min_value=0.0, max_value=20.0, value=3.5, step=0.5
                )

                use_cv = st.sidebar.checkbox("配当の安定性条件を使用", value=True, help="変動係数が小さい = 安定している")
                if use_cv:
                    max_dividend_cv = st.sidebar.number_input(
                        "配当変動係数 (CV) 以下",
                        min_value=0.0, max_value=2.0, value=0.3, step=0.1,
                        help="0.3以下が安定、0.5以上は不安定"
                    )
                else:
                    max_dividend_cv = None

                declining_but_high_avg = st.sidebar.checkbox(
                    "減配だが過去平均が高い銘柄を抽出",
                    value=False,
                    help="今期は減配だが、過去平均配当利回りが高い銘柄"
                )

                st.sidebar.markdown("**配当トレンド・特別配当**")

                require_increasing_trend = st.sidebar.checkbox(
                    "増配傾向の銘柄のみ",
                    value=False,
                    help="配当が増加傾向にある銘柄のみを抽出（減配傾向を除外）"
                )

                exclude_special_dividend = st.sidebar.checkbox(
                    "特別配当を除外",
                    value=True,
                    help="特別配当があった銘柄を除外（より安定的な配当銘柄を抽出）"
                )

                use_quality_score = st.sidebar.checkbox(
                    "配当クオリティスコアを使用",
                    value=False,
                    help="配当利回り・安定性・トレンドを総合評価（0-100点）"
                )

                if use_quality_score:
                    min_dividend_quality_score = st.sidebar.slider(
                        "最低配当クオリティスコア",
                        min_value=0, max_value=100, value=60, step=5,
                        help="60点以上: 優良、70点以上: 非常に優良"
                    )
                else:
                    min_dividend_quality_score = None
    else:
        use_advanced_dividend = False
        dividend_years = 4
        min_avg_dividend_yield = None
        max_dividend_cv = None
        declining_but_high_avg = False
        require_increasing_trend = False
        exclude_special_dividend = False
        min_dividend_quality_score = None

    # PER条件
    st.sidebar.subheader("💰 バリュエーション")

    if screening_mode in ["基本モード", "カスタム条件"]:
        use_basic_per = st.sidebar.checkbox("基本的なPER条件を使用", value=True)
        if use_basic_per:
            max_per = st.sidebar.number_input("最大PER", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
        else:
            max_per = 100.0
    else:
        use_basic_per = False
        max_per = 100.0

    # 高度なPER条件
    if screening_mode in ["高度なPER分析", "カスタム条件"]:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🔍 高度なPER分析**")

        use_advanced_per = st.sidebar.checkbox("高度なPER分析を使用", value=True if screening_mode == "高度なPER分析" else False)

        if use_advanced_per:
            per_years = st.sidebar.selectbox("PER分析期間", [3, 4, 5], index=1, help="過去何年分のPERを分析するか")

            # プリセット条件
            per_preset = st.sidebar.selectbox(
                "PERプリセット条件",
                ["カスタム", "安定低PER", "割安株発掘"],
                help="カスタム: 自分で設定\n安定低PER: 過去平均PERが低く安定\n割安株発掘: 現在PERが過去平均より大幅に低い"
            )

            if per_preset == "安定低PER":
                min_avg_per = None
                max_avg_per = 15.0
                max_per_cv = 0.4
                low_current_high_avg_per = False
            elif per_preset == "割安株発掘":
                min_avg_per = None
                max_avg_per = None
                max_per_cv = None
                low_current_high_avg_per = True
            else:  # カスタム
                col1, col2 = st.sidebar.columns(2)
                with col1:
                    use_min_per = st.checkbox("最小PER", value=False)
                    if use_min_per:
                        min_avg_per = st.number_input(f"過去{per_years}年平均PER 以上", min_value=0.0, max_value=100.0, value=5.0, step=1.0)
                    else:
                        min_avg_per = None

                with col2:
                    use_max_per = st.checkbox("最大PER", value=True)
                    if use_max_per:
                        max_avg_per = st.number_input(f"過去{per_years}年平均PER 以下", min_value=0.0, max_value=100.0, value=15.0, step=1.0)
                    else:
                        max_avg_per = None

                use_per_cv = st.sidebar.checkbox("PER安定性条件を使用", value=False)
                if use_per_cv:
                    max_per_cv = st.sidebar.number_input("PER変動係数 (CV) 以下", min_value=0.0, max_value=2.0, value=0.4, step=0.1)
                else:
                    max_per_cv = None

                low_current_high_avg_per = st.sidebar.checkbox(
                    "現在PERが過去平均より大幅に低い（割安）",
                    value=False,
                    help="現在PERが過去平均の80%未満の銘柄"
                )
    else:
        use_advanced_per = False
        per_years = 4
        min_avg_per = None
        max_avg_per = None
        max_per_cv = None
        low_current_high_avg_per = False

    # その他の条件
    max_pbr = st.sidebar.number_input("最大PBR", min_value=0.0, max_value=10.0, value=2.0, step=0.1)

    # 業績条件
    st.sidebar.subheader("📈 業績条件")
    revenue_growth = st.sidebar.checkbox("売上高増加傾向", value=False)
    min_profit_margin = st.sidebar.number_input("最低利益率 (%)", min_value=0.0, max_value=100.0, value=5.0, step=1.0)

    ticker = None  # スクリーニングモードではtickerは使わない
    start_date = datetime.now() - timedelta(days=365*3)
    end_date = datetime.now()

def get_stock_data(ticker, start_date, end_date):
    """株価データを取得"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date)

        # 基本情報を取得
        info = stock.info

        # 財務諸表を取得（年次データ - より多くの過去データを取得）
        # yfinanceは通常4年分のデータを返すが、利用可能なすべてのデータを取得
        financials = stock.financials  # 年次損益計算書
        balance_sheet = stock.balance_sheet  # 年次貸借対照表
        cashflow = stock.cashflow  # 年次キャッシュフロー

        # 四半期データも取得可能（より詳細な分析用）
        # quarterly_financials = stock.quarterly_financials
        # quarterly_balance_sheet = stock.quarterly_balance_sheet
        # quarterly_cashflow = stock.quarterly_cashflow

        dividends = stock.dividends

        return hist, info, financials, balance_sheet, cashflow, dividends
    except Exception as e:
        st.error(f"データの取得中にエラーが発生しました: {e}")
        return None, None, None, None, None, None

def calculate_financial_ratios(info, financials, balance_sheet):
    """財務指標を計算"""
    ratios = {}
    
    try:
        # PER (株価収益率)
        ratios['PER'] = info.get('trailingPE', 'N/A')
        
        # PBR (株価純資産倍率)
        ratios['PBR'] = info.get('priceToBook', 'N/A')
        
        # 配当利回り
        dividend_yield_raw = info.get('dividendYield', 'N/A')
        if dividend_yield_raw != 'N/A' and dividend_yield_raw is not None:
            # yfinanceは小数形式で返す（例: 0.0303 = 3.03%）
            # ただし、既にパーセント形式の場合もあるため、値の範囲で判定
            if dividend_yield_raw < 1:
                ratios['配当利回り'] = dividend_yield_raw * 100  # 小数からパーセントへ変換
            else:
                ratios['配当利回り'] = dividend_yield_raw  # すでにパーセント形式
        else:
            ratios['配当利回り'] = 'N/A'
        
        # 売上高成長率（直近2期）
        if financials is not None and len(financials.columns) >= 2:
            revenue_current = financials.loc['Total Revenue', financials.columns[0]]
            revenue_previous = financials.loc['Total Revenue', financials.columns[1]]
            if revenue_previous != 0:
                ratios['売上高成長率'] = ((revenue_current - revenue_previous) / revenue_previous) * 100
            else:
                ratios['売上高成長率'] = 'N/A'
        else:
            ratios['売上高成長率'] = 'N/A'
            
        # 利益成長率（直近2期）
        if financials is not None and len(financials.columns) >= 2:
            net_income_current = financials.loc['Net Income', financials.columns[0]]
            net_income_previous = financials.loc['Net Income', financials.columns[1]]
            if net_income_previous != 0:
                ratios['利益成長率'] = ((net_income_current - net_income_previous) / net_income_previous) * 100
            else:
                ratios['利益成長率'] = 'N/A'
        else:
            ratios['利益成長率'] = 'N/A'
            
    except Exception as e:
        st.warning(f"財務指標の計算中にエラーが発生しました: {e}")
    
    return ratios

@st.cache_data(ttl=86400)  # 24時間キャッシュ
def get_premium_market_stocks():
    """東証プライム市場の全銘柄を取得"""
    try:
        # JPXの上場銘柄一覧をダウンロード（複数のURLとエンジンを試す）
        urls = [
            ("https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls", 'xlrd'),
            ("https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xlsx", 'openpyxl'),
        ]

        df = None
        last_error = None

        for url, engine in urls:
            try:
                st.info(f"銘柄リストをダウンロード中... ({url.split('/')[-1]})")
                response = requests.get(url, timeout=30)
                response.raise_for_status()

                # ヘッダー行の可能性を考慮して読み込み
                # まず1行目から読んでデータを確認
                df_test = pd.read_excel(io.BytesIO(response.content), engine=engine, nrows=10)
                st.write("最初の10行（生データ）:")
                st.write(df_test)

                # 正式にデータを読み込み
                df = pd.read_excel(io.BytesIO(response.content), engine=engine)
                st.success(f"✅ ダウンロード成功（{len(df)}行）")
                break  # 成功したらループを抜ける

            except Exception as e:
                last_error = e
                continue

        if df is None:
            raise Exception(f"全てのURLで取得失敗: {last_error}")

        # 列名を確認
        st.info(f"取得した列: {df.columns.tolist()}")

        # プライム市場のみをフィルタ
        market_col = None
        for col in df.columns:
            if '市場' in str(col) or 'market' in str(col).lower() or '商品区分' in str(col):
                market_col = col
                break

        if market_col:
            # 実際のデータを確認（デバッグ）
            unique_values = df[market_col].dropna().unique()
            st.info(f"市場区分列 '{market_col}' の値の例: {unique_values[:5].tolist()}")

            # プライム市場でフィルタ（正式名称は「プライム」）
            premium_df = df[df[market_col].astype(str).str.contains('プライム|Prime', na=False, case=False)]
            st.info(f"プライム市場の銘柄: {len(premium_df)}件")

            # フィルタで0件の場合、全銘柄を使用
            if len(premium_df) == 0:
                st.warning("⚠️ プライム市場のフィルタで0件。全銘柄を使用します。")
                premium_df = df
        else:
            st.warning("⚠️ 市場区分列が見つかりません。全銘柄を使用します。")
            premium_df = df

        # 銘柄辞書を作成（コード: 銘柄名）
        stocks = {}

        # コード列と銘柄名列を探す
        code_col = None
        name_col = None

        # すべての列名を表示（デバッグ用）
        st.write("全ての列名:", df.columns.tolist())

        for col in df.columns:
            col_str = str(col)
            # 「コード」で終わる列で、「規模」が含まれていないものを優先
            if col_str == 'コード' or col_str == '証券コード':
                code_col = col
                break  # 見つかったら即座に採用
            elif 'コード' in col_str and '規模' not in col_str and code_col is None:
                code_col = col

        for col in df.columns:
            col_str = str(col)
            if '銘柄名' in col_str or 'name' in col_str.lower() or '名称' in col_str:
                name_col = col
                break

        st.info(f"✅ 使用する列 - コード: '{code_col}', 銘柄名: '{name_col}'")

        if code_col is None or name_col is None:
            raise Exception(f"必要な列が見つかりません。利用可能な列: {df.columns.tolist()}")

        # プライム市場のデータサンプルを表示
        st.write(f"プライム市場データサンプル（全{len(premium_df)}件中の最初の10行）:")
        # インデックスをリセットしてから表示
        premium_df_reset = premium_df.reset_index(drop=True)
        # コード列を文字列に変換してから表示
        display_df = premium_df_reset[[code_col, name_col, market_col]].head(10).copy()
        display_df[code_col] = display_df[code_col].astype(str)
        st.write(display_df)

        error_count = 0
        success_count = 0

        for idx, row in premium_df.iterrows():
            try:
                code_raw = row[code_col]
                name_raw = row[name_col]

                # コードを文字列に変換
                if pd.notna(code_raw):
                    code_str = str(code_raw).strip()
                    # ハイフンや空文字列をスキップ
                    if code_str in ['-', '', 'nan', 'None']:
                        continue

                    # 数字のみの場合は整数化（例: 7203.0 → 7203）
                    # 英字を含む場合はそのまま（例: 130A → 130A）
                    try:
                        # floatとして読めて、整数値なら整数化
                        float_val = float(code_str)
                        if float_val == int(float_val):
                            code = str(int(float_val))
                        else:
                            code = code_str
                    except ValueError:
                        # floatに変換できない（文字が含まれる）場合はそのまま使用
                        code = code_str
                else:
                    continue

                # 銘柄名を文字列に変換
                if pd.notna(name_raw):
                    name = str(name_raw)
                else:
                    continue

                # yfinance用に.Tを追加
                ticker = f"{code}.T"
                stocks[ticker] = name
                success_count += 1

            except Exception as e:
                error_count += 1
                continue  # エラー表示なしでスキップ

        st.info(f"✅ 処理完了: 成功={success_count}件, スキップ={error_count}件")

        if len(stocks) == 0:
            raise Exception("銘柄が取得できませんでした")

        st.success(f"✅ プライム市場の銘柄を{len(stocks)}件取得しました")
        return stocks

    except Exception as e:
        st.error(f"❌ プライム市場の銘柄リスト取得に失敗: {e}")
        st.info("💡 主要銘柄のリストを使用します")
        return None

def get_stock_list(market):
    """市場に応じた銘柄リストを取得"""
    if market == "日本株（東証プライム市場全銘柄）":
        # プライム市場全銘柄を取得
        premium_stocks = get_premium_market_stocks()
        if premium_stocks:
            return premium_stocks
        # 取得失敗時は主要銘柄にフォールバック
        market = "日本株（東証主要銘柄）"

    if market == "日本株（東証主要銘柄）":
        # 日本の主要銘柄（TOPIX100の主要銘柄）
        stocks = {
            # 自動車・輸送機器
            "7203.T": "トヨタ自動車",
            "7267.T": "本田技研工業",
            "7201.T": "日産自動車",
            "6902.T": "デンソー",

            # 電気機器
            "6758.T": "ソニーグループ",
            "6861.T": "キーエンス",
            "6501.T": "日立製作所",
            "6752.T": "パナソニック",
            "6702.T": "富士通",
            "6971.T": "京セラ",

            # 情報・通信
            "9984.T": "ソフトバンクグループ",
            "9432.T": "日本電信電話",
            "9433.T": "KDDI",
            "4689.T": "Zホールディングス",

            # 半導体・電子部品
            "8035.T": "東京エレクトロン",
            "6857.T": "アドバンテスト",
            "6723.T": "ルネサスエレクトロニクス",

            # 銀行・金融
            "8306.T": "三菱UFJフィナンシャル・グループ",
            "8316.T": "三井住友フィナンシャルグループ",
            "8411.T": "みずほフィナンシャルグループ",

            # 商社
            "8058.T": "三菱商事",
            "8001.T": "伊藤忠商事",
            "8031.T": "三井物産",
            "8053.T": "住友商事",
            "8002.T": "丸紅",

            # 医薬品
            "4502.T": "武田薬品工業",
            "4503.T": "アステラス製薬",
            "4568.T": "第一三共",
            "4519.T": "中外製薬",

            # 化学
            "4063.T": "信越化学工業",
            "4005.T": "住友化学",
            "4188.T": "三菱ケミカルグループ",

            # 小売・サービス
            "9983.T": "ファーストリテイリング",
            "3382.T": "セブン&アイ・ホールディングス",
            "8267.T": "イオン",
            "6098.T": "リクルートホールディングス",

            # ゲーム・エンタメ
            "7974.T": "任天堂",
            "9697.T": "カプコン",

            # 鉄道・運輸
            "9020.T": "東日本旅客鉄道",
            "9022.T": "東海旅客鉄道",

            # その他
            "2914.T": "日本たばこ産業",
            "5401.T": "日本製鉄",
            "4911.T": "資生堂",
            "9531.T": "東京ガス",
            "8031.T": "三井不動産",
        }
    else:  # 米国株
        stocks = {
            # テクノロジー
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "GOOGL": "Alphabet",
            "AMZN": "Amazon",
            "NVDA": "NVIDIA",
            "META": "Meta",
            "TSLA": "Tesla",
            "ADBE": "Adobe",
            "CRM": "Salesforce",
            "ORCL": "Oracle",
            "INTC": "Intel",
            "CSCO": "Cisco",
            "NFLX": "Netflix",
            "AMD": "AMD",

            # 金融
            "BRK-B": "Berkshire Hathaway",
            "JPM": "JPMorgan Chase",
            "BAC": "Bank of America",
            "WFC": "Wells Fargo",
            "V": "Visa",
            "MA": "Mastercard",
            "GS": "Goldman Sachs",
            "AXP": "American Express",

            # ヘルスケア
            "JNJ": "Johnson & Johnson",
            "UNH": "UnitedHealth",
            "PFE": "Pfizer",
            "ABBV": "AbbVie",
            "TMO": "Thermo Fisher",
            "MRK": "Merck",
            "LLY": "Eli Lilly",

            # 消費財
            "PG": "Procter & Gamble",
            "KO": "Coca-Cola",
            "PEP": "PepsiCo",
            "COST": "Costco",
            "WMT": "Walmart",
            "NKE": "Nike",
            "MCD": "McDonald's",

            # 産業・その他
            "HD": "Home Depot",
            "DIS": "Disney",
            "BA": "Boeing",
            "CAT": "Caterpillar",
            "GE": "General Electric",
            "XOM": "ExxonMobil",
            "CVX": "Chevron",
        }
    return stocks

def translate_financial_terms(df):
    """財務諸表の項目を日本語と英語の両方で表示"""
    # 主要な財務項目の日英対応辞書
    translations = {
        # 損益計算書
        'Total Revenue': '売上高 (Total Revenue)',
        'Cost Of Revenue': '売上原価 (Cost Of Revenue)',
        'Gross Profit': '売上総利益 (Gross Profit)',
        'Operating Expense': '営業費用 (Operating Expense)',
        'Operating Income': '営業利益 (Operating Income)',
        'Net Income': '当期純利益 (Net Income)',
        'EBITDA': 'EBITDA',
        'EBIT': 'EBIT',
        'Interest Income': '受取利息 (Interest Income)',
        'Interest Expense': '支払利息 (Interest Expense)',
        'Net Interest Income': '純金利収益 (Net Interest Income)',
        'Other Income Expense': 'その他損益 (Other Income Expense)',
        'Pretax Income': '税引前当期純利益 (Pretax Income)',
        'Tax Provision': '法人税等 (Tax Provision)',
        'Net Income From Continuing Operations': '継続事業からの純利益 (Net Income From Continuing Ops)',
        'Diluted EPS': '希薄化後EPS (Diluted EPS)',
        'Basic EPS': '基本的EPS (Basic EPS)',
        'Diluted Average Shares': '希薄化後平均株式数 (Diluted Average Shares)',
        'Basic Average Shares': '基本的平均株式数 (Basic Average Shares)',
        'Total Operating Income As Reported': '報告営業利益 (Total Operating Income As Reported)',
        'Total Expenses': '総費用 (Total Expenses)',
        'Net Income Common Stockholders': '普通株主に帰属する純利益 (Net Income Common Stockholders)',
        'Reconciled Depreciation': '減価償却費 (Reconciled Depreciation)',
        'Reconciled Cost Of Revenue': '調整後売上原価 (Reconciled Cost Of Revenue)',
        'Normalized Income': '正常化純利益 (Normalized Income)',
        'Tax Rate For Calcs': '計算用税率 (Tax Rate For Calcs)',
        'Tax Effect Of Unusual Items': '特別項目の税効果 (Tax Effect Of Unusual Items)',

        # 貸借対照表
        'Total Assets': '総資産 (Total Assets)',
        'Total Liabilities Net Minority Interest': '総負債 (Total Liabilities)',
        'Total Equity Gross Minority Interest': '純資産 (Total Equity)',
        'Stockholders Equity': '株主資本 (Stockholders Equity)',
        'Total Capitalization': '総資本 (Total Capitalization)',
        'Common Stock Equity': '普通株式資本 (Common Stock Equity)',
        'Capital Lease Obligations': 'キャピタルリース債務 (Capital Lease Obligations)',
        'Net Tangible Assets': '有形固定資産純額 (Net Tangible Assets)',
        'Working Capital': '運転資本 (Working Capital)',
        'Invested Capital': '投下資本 (Invested Capital)',
        'Tangible Book Value': '有形簿価 (Tangible Book Value)',
        'Total Debt': '総負債 (Total Debt)',
        'Net Debt': '純負債 (Net Debt)',
        'Share Issued': '発行済株式数 (Share Issued)',
        'Ordinary Shares Number': '普通株式数 (Ordinary Shares Number)',
        'Current Assets': '流動資産 (Current Assets)',
        'Current Liabilities': '流動負債 (Current Liabilities)',
        'Other Current Assets': 'その他流動資産 (Other Current Assets)',
        'Other Current Liabilities': 'その他流動負債 (Other Current Liabilities)',
        'Non Current Assets': '固定資産 (Non Current Assets)',
        'Non Current Liabilities': '固定負債 (Non Current Liabilities)',
        'Cash And Cash Equivalents': '現金及び現金同等物 (Cash And Cash Equivalents)',
        'Cash Cash Equivalents And Short Term Investments': '現金及び短期投資 (Cash, Cash Equivalents And Short Term Investments)',
        'Cash Financial': '金融機関の現金 (Cash Financial)',
        'Cash Equivalents': '現金同等物 (Cash Equivalents)',
        'Other Short Term Investments': 'その他短期投資 (Other Short Term Investments)',
        'Receivables': '売掛金 (Receivables)',
        'Accounts Receivable': '売掛金 (Accounts Receivable)',
        'Gross Accounts Receivable': '総売掛金 (Gross Accounts Receivable)',
        'Allowance For Doubtful Accounts Receivable': '貸倒引当金 (Allowance For Doubtful Accounts Receivable)',
        'Other Receivables': 'その他債権 (Other Receivables)',
        'Inventory': '棚卸資産 (Inventory)',
        'Finished Goods': '製品 (Finished Goods)',
        'Work In Process': '仕掛品 (Work In Process)',
        'Raw Materials': '原材料 (Raw Materials)',
        'Properties': '不動産 (Properties)',
        'Land And Improvements': '土地及び改良 (Land And Improvements)',
        'Buildings And Improvements': '建物及び改良 (Buildings And Improvements)',
        'Machinery Furniture Equipment': '機械設備 (Machinery Furniture Equipment)',
        'Leases': 'リース資産 (Leases)',
        'Accumulated Depreciation': '減価償却累計額 (Accumulated Depreciation)',
        'Goodwill And Other Intangible Assets': 'のれん及び無形資産 (Goodwill And Other Intangible Assets)',
        'Goodwill': 'のれん (Goodwill)',
        'Other Intangible Assets': 'その他無形資産 (Other Intangible Assets)',
        'Investments And Advances': '投資及び前払金 (Investments And Advances)',
        'Long Term Equity Investment': '長期株式投資 (Long Term Equity Investment)',
        'Other Non Current Assets': 'その他固定資産 (Other Non Current Assets)',
        'Payables And Accrued Expenses': '買掛金及び未払費用 (Payables And Accrued Expenses)',
        'Payables': '買掛金 (Payables)',
        'Accounts Payable': '買掛金 (Accounts Payable)',
        'Total Tax Payable': '未払税金 (Total Tax Payable)',
        'Income Tax Payable': '未払法人税 (Income Tax Payable)',
        'Dividends Payable': '未払配当金 (Dividends Payable)',
        'Accrued Interest Payable': '未払利息 (Accrued Interest Payable)',
        'Pensionand Other Post Retirement Benefit Plans Current': '年金及び退職給付負債(流動) (Pension and Other Post Retirement Benefit Plans Current)',
        'Current Debt': '短期借入金 (Current Debt)',
        'Current Debt And Capital Lease Obligation': '短期借入金及びリース債務 (Current Debt And Capital Lease Obligation)',
        'Current Deferred Liabilities': '繰延負債(流動) (Current Deferred Liabilities)',
        'Current Deferred Revenue': '繰延収益(流動) (Current Deferred Revenue)',
        'Other Current Borrowings': 'その他短期借入金 (Other Current Borrowings)',
        'Long Term Debt': '長期借入金 (Long Term Debt)',
        'Long Term Debt And Capital Lease Obligation': '長期借入金及びリース債務 (Long Term Debt And Capital Lease Obligation)',
        'Non Current Deferred Liabilities': '繰延負債(固定) (Non Current Deferred Liabilities)',
        'Non Current Deferred Taxes Liabilities': '繰延税金負債 (Non Current Deferred Taxes Liabilities)',
        'Non Current Deferred Revenue': '繰延収益(固定) (Non Current Deferred Revenue)',
        'Tradeand Other Payables Non Current': '長期買掛金 (Trade and Other Payables Non Current)',
        'Other Non Current Liabilities': 'その他固定負債 (Other Non Current Liabilities)',
        'Capital Stock': '資本金 (Capital Stock)',
        'Common Stock': '普通株式 (Common Stock)',
        'Retained Earnings': '利益剰余金 (Retained Earnings)',
        'Gains Losses Not Affecting Retained Earnings': 'その他包括利益累計額 (Gains Losses Not Affecting Retained Earnings)',
        'Other Equity Adjustments': 'その他資本調整 (Other Equity Adjustments)',
        'Treasury Stock': '自己株式 (Treasury Stock)',

        # キャッシュフロー計算書
        'Operating Cash Flow': '営業活動によるキャッシュフロー (Operating Cash Flow)',
        'Investing Cash Flow': '投資活動によるキャッシュフロー (Investing Cash Flow)',
        'Financing Cash Flow': '財務活動によるキャッシュフロー (Financing Cash Flow)',
        'End Cash Position': '期末現金残高 (End Cash Position)',
        'Income Tax Paid Supplemental Data': '法人税等の支払額 (Income Tax Paid Supplemental Data)',
        'Interest Paid Supplemental Data': '利息の支払額 (Interest Paid Supplemental Data)',
        'Capital Expenditure': '設備投資 (Capital Expenditure)',
        'Issuance Of Capital Stock': '株式の発行 (Issuance Of Capital Stock)',
        'Issuance Of Debt': '社債の発行 (Issuance Of Debt)',
        'Repayment Of Debt': '社債の償還 (Repayment Of Debt)',
        'Repurchase Of Capital Stock': '自己株式の取得 (Repurchase Of Capital Stock)',
        'Free Cash Flow': 'フリーキャッシュフロー (Free Cash Flow)',
        'Change In Working Capital': '運転資本の増減 (Change In Working Capital)',
        'Change In Receivables': '売掛金の増減 (Change In Receivables)',
        'Change In Inventory': '棚卸資産の増減 (Change In Inventory)',
        'Change In Payables And Accrued Expense': '買掛金及び未払費用の増減 (Change In Payables And Accrued Expense)',
        'Change In Payable': '買掛金の増減 (Change In Payable)',
        'Changes In Account Receivables': '売掛金の増減 (Changes In Account Receivables)',
        'Stock Based Compensation': '株式報酬 (Stock Based Compensation)',
        'Deferred Tax': '繰延税金 (Deferred Tax)',
        'Deferred Income Tax': '繰延法人税 (Deferred Income Tax)',
        'Depreciation Amortization Depletion': '減価償却費 (Depreciation Amortization Depletion)',
        'Depreciation And Amortization': '減価償却費 (Depreciation And Amortization)',
        'Depreciation': '減価償却費 (Depreciation)',
        'Amortization Of Securities': '有価証券償却 (Amortization Of Securities)',
        'Asset Impairment Charge': '資産減損損失 (Asset Impairment Charge)',
        'Provision For Doubtful Accounts': '貸倒引当金繰入 (Provision For Doubtful Accounts)',
        'Purchase Of Investment': '投資の取得 (Purchase Of Investment)',
        'Sale Of Investment': '投資の売却 (Sale Of Investment)',
        'Purchase Of Business': '事業の取得 (Purchase Of Business)',
        'Sale Of Business': '事業の売却 (Sale Of Business)',
        'Purchase Of PPE': '有形固定資産の取得 (Purchase Of PPE)',
        'Sale Of PPE': '有形固定資産の売却 (Sale Of PPE)',
        'Net PPE Purchase And Sale': '有形固定資産の取得及び売却(純額) (Net PPE Purchase And Sale)',
        'Net Investment Purchase And Sale': '投資の取得及び売却(純額) (Net Investment Purchase And Sale)',
        'Net Business Purchase And Sale': '事業の取得及び売却(純額) (Net Business Purchase And Sale)',
        'Common Stock Dividend Paid': '配当金の支払 (Common Stock Dividend Paid)',
        'Common Stock Issuance': '普通株式の発行 (Common Stock Issuance)',
        'Common Stock Payments': '普通株式の取得 (Common Stock Payments)',
        'Net Common Stock Issuance': '普通株式の発行及び取得(純額) (Net Common Stock Issuance)',
        'Long Term Debt Issuance': '長期借入 (Long Term Debt Issuance)',
        'Long Term Debt Payments': '長期借入金の返済 (Long Term Debt Payments)',
        'Net Long Term Debt Issuance': '長期借入及び返済(純額) (Net Long Term Debt Issuance)',
        'Short Term Debt Issuance': '短期借入 (Short Term Debt Issuance)',
        'Short Term Debt Payments': '短期借入金の返済 (Short Term Debt Payments)',
        'Net Short Term Debt Issuance': '短期借入及び返済(純額) (Net Short Term Debt Issuance)',
        'Net Issuance Payments Of Debt': '借入及び返済(純額) (Net Issuance Payments Of Debt)',
        'Beginning Cash Position': '期首現金残高 (Beginning Cash Position)',
        'Changes In Cash': '現金の増減 (Changes In Cash)',
        'Effect Of Exchange Rate Changes': '為替変動の影響 (Effect Of Exchange Rate Changes)',

        # その他よく出る項目
        'Selling General And Administration': '販売費及び一般管理費 (Selling General And Administration)',
        'Selling And Marketing Expense': '販売費 (Selling And Marketing Expense)',
        'General And Administrative Expense': '一般管理費 (General And Administrative Expense)',
        'Research And Development': '研究開発費 (Research And Development)',
        'Other Gand A': 'その他販管費 (Other G&A)',
        'Gross PPE': '有形固定資産総額 (Gross PPE)',
        'Net PPE': '有形固定資産純額 (Net PPE)',
        'Total Non Current Assets': '固定資産合計 (Total Non Current Assets)',
        'Total Current Assets': '流動資産合計 (Total Current Assets)',
        'Total Non Current Liabilities Net Minority Interest': '固定負債合計 (Total Non Current Liabilities)',
        'Total Current Liabilities': '流動負債合計 (Total Current Liabilities)',
        'Minority Interest': '少数株主持分 (Minority Interest)',
        'Preferred Stock': '優先株式 (Preferred Stock)',
        'Additional Paid In Capital': '資本剰余金 (Additional Paid In Capital)',
        'Other Comprehensive Income': 'その他包括利益 (Other Comprehensive Income)',
        'Accumulated Other Comprehensive Income': 'その他包括利益累計額 (Accumulated Other Comprehensive Income)',
        'Construction In Progress': '建設仮勘定 (Construction In Progress)',
        'Land': '土地 (Land)',
        'Buildings': '建物 (Buildings)',
        'Machinery': '機械装置 (Machinery)',
        'Vehicles': '車両運搬具 (Vehicles)',
        'Computer And Equipment': 'コンピュータ及び設備 (Computer And Equipment)',
        'Furniture And Fixtures': '器具備品 (Furniture And Fixtures)',
        'Line Of Credit': '与信枠 (Line Of Credit)',
        'Commercial Paper': 'コマーシャルペーパー (Commercial Paper)',
        'Long Term Capital Lease Obligation': '長期キャピタルリース債務 (Long Term Capital Lease Obligation)',
        'Current Capital Lease Obligation': '短期キャピタルリース債務 (Current Capital Lease Obligation)',
        'Notes Receivable': '受取手形 (Notes Receivable)',
        'Loans Receivable': '貸付金 (Loans Receivable)',
        'Prepaid Assets': '前払費用 (Prepaid Assets)',
        'Restricted Cash': '拘束性預金 (Restricted Cash)',
        'Securities And Investments': '有価証券及び投資 (Securities And Investments)',
        'Available For Sale Securities': '売却可能有価証券 (Available For Sale Securities)',
        'Held To Maturity Securities': '満期保有有価証券 (Held To Maturity Securities)',
        'Trading Securities': '売買目的有価証券 (Trading Securities)',
        'Financial Assets': '金融資産 (Financial Assets)',
        'Investments In Joint Ventures': '共同支配事業投資 (Investments In Joint Ventures)',
        'Investments In Associates': '関連会社投資 (Investments In Associates)',
        'Investments In Subsidiaries': '子会社投資 (Investments In Subsidiaries)',
        'Interest Receivable': '未収利息 (Interest Receivable)',
        'Employee Benefits': '従業員給付 (Employee Benefits)',
        'Pension Provisions': '年金引当金 (Pension Provisions)',
        'Restructuring And Mergern Acquisition': '事業再編及びM&A費用 (Restructuring And M&A)',
        'Impairment Of Capital Assets': '固定資産減損損失 (Impairment Of Capital Assets)',
        'Write Off': '償却 (Write Off)',
        'Gain Loss On Sale Of Security': '有価証券売却損益 (Gain Loss On Sale Of Security)',
        'Gain Loss On Sale Of PPE': '固定資産売却損益 (Gain Loss On Sale Of PPE)',
        'Earnings From Equity Interest': '持分法投資損益 (Earnings From Equity Interest)',
        'Gain On Sale Of Business': '事業売却益 (Gain On Sale Of Business)',
        'Loss On Sale Of Business': '事業売却損 (Loss On Sale Of Business)',
        'Other Special Charges': 'その他特別損失 (Other Special Charges)',
        'Other Non Operating Income Expenses': 'その他営業外損益 (Other Non Operating Income Expenses)',
        'Net Non Operating Interest Income Expense': '営業外純金利損益 (Net Non Operating Interest Income Expense)',
        'Interest Income Non Operating': '営業外受取利息 (Interest Income Non Operating)',
        'Interest Expense Non Operating': '営業外支払利息 (Interest Expense Non Operating)',
        'Net Investment Income': '投資純利益 (Net Investment Income)',
        'Investment Income': '投資収益 (Investment Income)',
        'Investment Expense': '投資費用 (Investment Expense)',
        'Rent Expense': '賃借料 (Rent Expense)',
        'Rent Income': '賃貸収入 (Rent Income)',
        'Gain Loss On Investment Securities': '投資有価証券評価損益 (Gain Loss On Investment Securities)',
        'Earnings Losses From Equity Interest Net Of Tax': '持分法投資損益(税引後) (Earnings Losses From Equity Interest Net Of Tax)',
        'Total Unusual Items': '特別項目合計 (Total Unusual Items)',
        'Total Unusual Items Excluding Goodwill': 'のれんを除く特別項目合計 (Total Unusual Items Excluding Goodwill)',
        'Net Income Including Noncontrolling Interests': '非支配持分を含む純利益 (Net Income Including Noncontrolling Interests)',
        'Net Income Continuous Operations': '継続事業純利益 (Net Income Continuous Operations)',
        'Minority Interests': '少数株主損益 (Minority Interests)',
        'Net Income Attributable To Common Shareholders': '普通株主に帰属する純利益 (Net Income Attributable To Common Shareholders)',

        # 追加の金融・費用関連項目
        'Total Other Finance Cost': 'その他金融費用合計 (Total Other Finance Cost)',
        'Other Finance Cost': 'その他金融費用 (Other Finance Cost)',
        'Finance Cost': '金融費用 (Finance Cost)',
        'Finance Income': '金融収益 (Finance Income)',
        'Net Finance Cost': '純金融費用 (Net Finance Cost)',
        'Foreign Exchange Gain Loss': '為替差損益 (Foreign Exchange Gain Loss)',
        'Foreign Exchange Loss': '為替差損 (Foreign Exchange Loss)',
        'Foreign Exchange Gain': '為替差益 (Foreign Exchange Gain)',
        'Insurance And Claims': '保険及び保険金請求 (Insurance And Claims)',
        'Salaries And Wages': '給与及び賃金 (Salaries And Wages)',
        'Payroll Expense': '人件費 (Payroll Expense)',
        'Legal And Professional Fees': '法務及び専門家報酬 (Legal And Professional Fees)',
        'Advertising Expense': '広告宣伝費 (Advertising Expense)',
        'Marketing Expense': '販促費 (Marketing Expense)',
        'Travel Expense': '旅費交通費 (Travel Expense)',
        'Communication Expense': '通信費 (Communication Expense)',
        'Utilities Expense': '水道光熱費 (Utilities Expense)',
        'Repairs And Maintenance': '修繕維持費 (Repairs And Maintenance)',
        'Office Expense': '事務費 (Office Expense)',
        'Supplies Expense': '消耗品費 (Supplies Expense)',
        'Insurance Expense': '保険料 (Insurance Expense)',
        'Taxes Excluding Income Tax': '租税公課 (Taxes Excluding Income Tax)',
        'Amortization': '償却費 (Amortization)',
        'Amortization Of Intangibles': '無形資産償却 (Amortization Of Intangibles)',
        'DD And A': '減価償却費及び償却費 (DD&A)',
        'Exploration And Development': '探鉱開発費 (Exploration And Development)',
        'Gain Loss On Disposal Of Assets': '資産処分損益 (Gain Loss On Disposal Of Assets)',
        'Gain On Disposal Of Assets': '資産処分益 (Gain On Disposal Of Assets)',
        'Loss On Disposal Of Assets': '資産処分損 (Loss On Disposal Of Assets)',
        'Restructuring Charges': '事業再編費用 (Restructuring Charges)',
        'Restructuring And Impairment': '事業再編及び減損 (Restructuring And Impairment)',
        'Merger And Acquisition': 'M&A費用 (Merger And Acquisition)',
        'Litigation Settlement': '訴訟和解金 (Litigation Settlement)',
        'Environmental Costs': '環境対策費 (Environmental Costs)',
        'Bad Debt Expense': '貸倒損失 (Bad Debt Expense)',
        'Warranty Expense': '製品保証費 (Warranty Expense)',
        'Royalty Expense': 'ロイヤリティ費用 (Royalty Expense)',
        'Royalty Income': 'ロイヤリティ収入 (Royalty Income)',
        'Commission Expense': '手数料費用 (Commission Expense)',
        'Commission Income': '手数料収入 (Commission Income)',
        'Lease Expense': 'リース費用 (Lease Expense)',
        'Lease Income': 'リース収入 (Lease Income)',
        'Dividend Income': '配当金収入 (Dividend Income)',
        'Dividend Expense': '配当金支払 (Dividend Expense)',
        'Preferred Dividends': '優先株式配当 (Preferred Dividends)',
        'Other Operating Income': 'その他営業収益 (Other Operating Income)',
        'Other Operating Expense': 'その他営業費用 (Other Operating Expense)',
        'Nonoperating Income': '営業外収益 (Nonoperating Income)',
        'Nonoperating Expense': '営業外費用 (Nonoperating Expense)',
        'Extraordinary Items': '特別損益 (Extraordinary Items)',
        'Extraordinary Income': '特別利益 (Extraordinary Income)',
        'Extraordinary Expense': '特別損失 (Extraordinary Expense)',
        'Discontinued Operations': '非継続事業 (Discontinued Operations)',
        'Income From Discontinued Operations': '非継続事業からの利益 (Income From Discontinued Operations)',
        'Loss From Discontinued Operations': '非継続事業からの損失 (Loss From Discontinued Operations)',
        'Accounting Change': '会計方針変更 (Accounting Change)',
        'Other Items': 'その他項目 (Other Items)',
        'Comprehensive Income': '包括利益 (Comprehensive Income)',
        'Total Comprehensive Income': '包括利益合計 (Total Comprehensive Income)',
        'Attributable To Parent': '親会社株主に帰属 (Attributable To Parent)',
        'Attributable To Noncontrolling Interest': '非支配株主に帰属 (Attributable To Noncontrolling Interest)',
    }

    # インデックスを翻訳
    if df is not None and not df.empty:
        df_copy = df.copy()
        new_index = []
        for idx in df_copy.index:
            if idx in translations:
                new_index.append(translations[idx])
            else:
                # 翻訳がない場合は元の名前をそのまま使用
                new_index.append(idx)
        df_copy.index = new_index
        return df_copy
    return df

def calculate_historical_dividend_yield(ticker_obj, dividends, hist_prices, years=5):
    """過去N年の配当利回りを計算（トレンド分析と特別配当検出付き）"""
    try:
        if dividends is None or len(dividends) == 0 or hist_prices is None or len(hist_prices) == 0:
            return None, None, None, None, None

        # タイムゾーン情報を削除（yfinanceのデータはUTC、datetime.now()はnaive）
        dividends = dividends.copy()
        hist_prices = hist_prices.copy()
        if hasattr(dividends.index, 'tz') and dividends.index.tz is not None:
            dividends.index = dividends.index.tz_localize(None)
        if hasattr(hist_prices.index, 'tz') and hist_prices.index.tz is not None:
            hist_prices.index = hist_prices.index.tz_localize(None)

        # 過去N年分のデータを取得
        cutoff_date = datetime.now() - timedelta(days=365 * years)
        recent_dividends = dividends[dividends.index >= cutoff_date]

        if len(recent_dividends) == 0:
            return None, None, None, None, None

        # 年次配当利回りを計算
        yearly_yields = []
        for year in range(years):
            year_start = datetime.now() - timedelta(days=365 * (year + 1))
            year_end = datetime.now() - timedelta(days=365 * year)

            # その年の配当合計
            year_divs = recent_dividends[(recent_dividends.index >= year_start) & (recent_dividends.index < year_end)]
            if len(year_divs) == 0:
                continue

            total_div = year_divs.sum()

            # その年の平均株価（年初の価格を使用）
            year_prices = hist_prices[(hist_prices.index >= year_start) & (hist_prices.index < year_end)]
            if len(year_prices) == 0:
                continue

            avg_price = year_prices['Close'].iloc[0] if len(year_prices) > 0 else None
            if avg_price and avg_price > 0:
                yield_pct = (total_div / avg_price) * 100
                yearly_yields.append(yield_pct)

        if len(yearly_yields) == 0:
            return None, None, None, None, None

        # データを新しい順から古い順に並べ替え（時系列分析用）
        yearly_yields.reverse()

        # 特別配当の検出と除外
        # IQR（四分位範囲）法で外れ値を検出
        if len(yearly_yields) >= 4:
            q1 = pd.Series(yearly_yields).quantile(0.25)
            q3 = pd.Series(yearly_yields).quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            # 外れ値（特別配当の可能性）を除外
            filtered_yields = [y for y in yearly_yields if lower_bound <= y <= upper_bound]
            has_special_dividend = len(filtered_yields) < len(yearly_yields)
        else:
            filtered_yields = yearly_yields
            has_special_dividend = False

        # フィルタ後のデータで再計算
        if len(filtered_yields) == 0:
            filtered_yields = yearly_yields  # 全て外れ値の場合は元データを使用

        # 平均配当利回り（特別配当除外後）
        avg_yield = sum(filtered_yields) / len(filtered_yields)

        # 配当の変動係数（CV = 標準偏差 / 平均）
        if len(filtered_yields) >= 2:
            std_dev = pd.Series(filtered_yields).std()
            cv = (std_dev / avg_yield) if avg_yield > 0 else float('inf')
        else:
            cv = 0

        # 配当トレンド分析（線形回帰の傾き）
        if len(filtered_yields) >= 3:
            # x = 年数（0, 1, 2, ...）、y = 配当利回り
            x = list(range(len(filtered_yields)))
            y = filtered_yields

            # 線形回帰: y = ax + b
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(xi ** 2 for xi in x)

            # 傾き a = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
            denominator = (n * sum_x2 - sum_x ** 2)
            if denominator != 0:
                slope = (n * sum_xy - sum_x * sum_y) / denominator
                dividend_trend = slope  # 正なら増配傾向、負なら減配傾向
            else:
                dividend_trend = 0
        else:
            dividend_trend = 0

        # 最新年の配当利回り
        current_yield = yearly_yields[-1] if len(yearly_yields) > 0 else None

        return avg_yield, cv, current_yield, dividend_trend, has_special_dividend

    except Exception as e:
        return None, None, None, None, None

def calculate_dividend_quality_score(avg_yield, cv, trend, has_special_div):
    """配当の質を総合的にスコアリング（0-100点）"""
    try:
        if avg_yield is None or cv is None or trend is None:
            return None

        score = 0

        # 1. 配当利回り（最大40点）
        if avg_yield >= 5.0:
            score += 40
        elif avg_yield >= 4.0:
            score += 35
        elif avg_yield >= 3.0:
            score += 30
        elif avg_yield >= 2.0:
            score += 20
        else:
            score += 10

        # 2. 安定性（最大30点）
        if cv <= 0.15:
            score += 30  # 非常に安定
        elif cv <= 0.25:
            score += 25  # 安定
        elif cv <= 0.35:
            score += 20  # やや安定
        elif cv <= 0.50:
            score += 10  # 中程度
        else:
            score += 0   # 不安定

        # 3. トレンド（最大30点）
        if trend > 0.3:
            score += 30  # 強い増配傾向
        elif trend > 0.15:
            score += 25  # 増配傾向
        elif trend > 0:
            score += 20  # 緩やかな増配
        elif trend > -0.15:
            score += 10  # 横ばい
        else:
            score += 0   # 減配傾向

        # 4. 特別配当ペナルティ（-10点）
        if has_special_div:
            score -= 10

        # スコアを0-100の範囲に収める
        score = max(0, min(100, score))

        return score

    except Exception:
        return None

def calculate_historical_per(ticker_obj, years=5):
    """過去N年のPERを計算"""
    try:
        # 過去の株価データを取得
        hist = ticker_obj.history(period=f"{years}y")
        if hist is None or len(hist) == 0:
            return None, None, None

        # 財務データを取得
        financials = ticker_obj.financials
        if financials is None or len(financials.columns) == 0:
            return None, None, None

        # 年次PERを計算
        yearly_pers = []

        for i in range(min(years, len(financials.columns))):
            try:
                # その年の純利益
                net_income = financials.loc['Net Income', financials.columns[i]]

                # その年の株価（年初）
                fin_date = financials.columns[i]
                closest_price = hist[hist.index >= fin_date]['Close'].iloc[0] if len(hist[hist.index >= fin_date]) > 0 else None

                if closest_price is None or net_income <= 0:
                    continue

                # 発行済株式数
                shares = ticker_obj.info.get('sharesOutstanding', None)
                if shares is None or shares <= 0:
                    continue

                # EPS = 純利益 / 発行済株式数
                eps = net_income / shares

                # PER = 株価 / EPS
                if eps > 0:
                    per = closest_price / eps
                    yearly_pers.append(per)

            except Exception:
                continue

        if len(yearly_pers) == 0:
            return None, None, None

        # 平均PER
        avg_per = sum(yearly_pers) / len(yearly_pers)

        # PERの変動係数
        if len(yearly_pers) >= 2:
            std_dev = pd.Series(yearly_pers).std()
            cv = (std_dev / avg_per) if avg_per > 0 else float('inf')
        else:
            cv = 0

        # 最新のPER
        current_per = yearly_pers[0] if len(yearly_pers) > 0 else None

        return avg_per, cv, current_per

    except Exception as e:
        return None, None, None

def screen_stocks(stocks, conditions):
    """条件に基づいて銘柄をスクリーニング"""
    results = []

    # デバッグ用統計
    debug_stats = {
        'total': 0,
        'no_dividend': 0,
        'low_dividend': 0,
        'high_cv': 0,
        'no_trend': 0,
        'failed_per': 0,
        'failed_pbr': 0,
        'failed_margin': 0,
        'passed': 0
    }

    progress_bar = st.progress(0)
    status_text = st.empty()

    total_stocks = len(stocks)
    for idx, (ticker, name) in enumerate(stocks.items()):
        try:
            status_text.text(f"分析中: {name} ({ticker}) - {idx+1}/{total_stocks}")
            progress_bar.progress((idx + 1) / total_stocks)

            stock = yf.Ticker(ticker)
            info = stock.info

            # 基本データ取得
            dividend_yield = info.get('dividendYield', 0)
            if dividend_yield and dividend_yield < 1:
                dividend_yield = dividend_yield * 100
            elif not dividend_yield:
                dividend_yield = 0

            per = info.get('trailingPE', 0) or 0
            pbr = info.get('priceToBook', 0) or 0
            profit_margin = info.get('profitMargins', 0) or 0
            if profit_margin < 1:
                profit_margin = profit_margin * 100

            revenue_growth_rate = info.get('revenueGrowth', 0) or 0
            if revenue_growth_rate < 1:
                revenue_growth_rate = revenue_growth_rate * 100

            # 配当履歴チェック
            dividends = stock.dividends
            dividend_increasing = False
            if len(dividends) >= 2:
                recent_div = dividends[-5:] if len(dividends) >= 5 else dividends
                dividend_increasing = all(recent_div.iloc[i] <= recent_div.iloc[i+1] for i in range(len(recent_div)-1))

            # 高度な配当分析
            hist_prices = stock.history(period="5y")
            avg_div_yield, div_cv, current_div_yield, div_trend, has_special_div = calculate_historical_dividend_yield(
                stock, dividends, hist_prices, years=conditions.get('dividend_years', 4)
            )

            # 配当クオリティスコア
            div_quality_score = calculate_dividend_quality_score(avg_div_yield, div_cv, div_trend, has_special_div)

            # 高度なPER分析
            avg_per, per_cv, current_per = calculate_historical_per(stock, years=conditions.get('per_years', 4))

            # 条件チェック
            passes = True

            # 基本的な配当利回り条件
            if conditions.get('use_basic_dividend', True):
                if dividend_yield < conditions.get('min_dividend_yield', 0):
                    passes = False

            # 高度な配当条件
            if conditions.get('use_advanced_dividend', False):
                # 過去N年平均配当利回り条件
                if conditions.get('min_avg_dividend_yield', None) is not None:
                    if avg_div_yield is None or avg_div_yield < conditions['min_avg_dividend_yield']:
                        passes = False

                # 配当の安定性条件（変動係数が小さい）
                if conditions.get('max_dividend_cv', None) is not None:
                    if div_cv is None or div_cv > conditions['max_dividend_cv']:
                        passes = False

                # 配当トレンド条件（増配傾向）
                if conditions.get('require_increasing_trend', False):
                    if div_trend is None or div_trend <= 0:
                        passes = False

                # 特別配当を除外
                if conditions.get('exclude_special_dividend', False):
                    if has_special_div:
                        passes = False

                # 配当クオリティスコア条件
                if conditions.get('min_dividend_quality_score', None) is not None:
                    if div_quality_score is None or div_quality_score < conditions['min_dividend_quality_score']:
                        passes = False

                # 減配だが過去平均が高い条件
                if conditions.get('declining_but_high_avg', False):
                    if current_div_yield is None or avg_div_yield is None:
                        passes = False
                    elif not (current_div_yield < avg_div_yield and avg_div_yield >= conditions.get('min_avg_dividend_yield', 4.0)):
                        passes = False

            # 高度なPER条件
            if conditions.get('use_advanced_per', False):
                # 過去N年平均PER条件
                if conditions.get('min_avg_per', None) is not None:
                    if avg_per is None or avg_per < conditions['min_avg_per']:
                        passes = False

                if conditions.get('max_avg_per', None) is not None:
                    if avg_per is None or avg_per > conditions['max_avg_per']:
                        passes = False

                # PERの安定性条件
                if conditions.get('max_per_cv', None) is not None:
                    if per_cv is None or per_cv > conditions['max_per_cv']:
                        passes = False

                # 現在PERが低いが過去平均は高い（バリュー株発掘）
                if conditions.get('low_current_high_avg_per', False):
                    if current_per is None or avg_per is None:
                        passes = False
                    elif not (current_per < avg_per * 0.8):  # 現在PERが過去平均の80%未満
                        passes = False

            # 基本的な条件
            if conditions.get('dividend_growth', False) and not dividend_increasing:
                passes = False

            if conditions.get('revenue_growth', False) and revenue_growth_rate <= 0:
                passes = False

            if profit_margin < conditions.get('min_profit_margin', 0):
                passes = False

            if conditions.get('use_basic_per', True):
                if per > conditions.get('max_per', 100) and per > 0:
                    passes = False

            if pbr > conditions.get('max_pbr', 100) and pbr > 0:
                passes = False

            if passes:
                result_row = {
                    '銘柄コード': ticker,
                    '銘柄名': name,
                    '配当利回り': f"{dividend_yield:.2f}%" if dividend_yield > 0 else "N/A",
                    'PER': f"{per:.2f}" if per > 0 else "N/A",
                    'PBR': f"{pbr:.2f}" if pbr > 0 else "N/A",
                    '利益率': f"{profit_margin:.2f}%",
                    '売上成長率': f"{revenue_growth_rate:.2f}%",
                }

                # 高度な配当情報を追加
                if conditions.get('use_advanced_dividend', False):
                    result_row['過去平均配当利回り'] = f"{avg_div_yield:.2f}%" if avg_div_yield else "N/A"
                    result_row['配当安定性(CV)'] = f"{div_cv:.2f}" if div_cv is not None else "N/A"

                    # トレンド表示
                    if div_trend is not None:
                        if div_trend > 0.3:
                            trend_str = f"↑↑ {div_trend:.2f}"
                        elif div_trend > 0:
                            trend_str = f"↑ {div_trend:.2f}"
                        elif div_trend > -0.15:
                            trend_str = f"→ {div_trend:.2f}"
                        else:
                            trend_str = f"↓ {div_trend:.2f}"
                        result_row['配当トレンド'] = trend_str
                    else:
                        result_row['配当トレンド'] = "N/A"

                    result_row['配当クオリティ'] = f"{div_quality_score:.0f}点" if div_quality_score else "N/A"
                    result_row['特別配当'] = "あり" if has_special_div else "なし"

                # 高度なPER情報を追加
                if conditions.get('use_advanced_per', False):
                    result_row['過去平均PER'] = f"{avg_per:.2f}" if avg_per else "N/A"
                    result_row['PER安定性'] = f"{per_cv:.2f}" if per_cv is not None else "N/A"

                results.append(result_row)

        except Exception as e:
            continue

    progress_bar.empty()
    status_text.empty()

    # スクリーニング統計を表示
    st.info(f"""
    📊 スクリーニング統計:
    - 対象銘柄数: {total_stocks}件
    - 合格銘柄数: {len(results)}件
    - 除外率: {((total_stocks - len(results)) / total_stocks * 100):.1f}%
    """)

    return pd.DataFrame(results)

# メインの分析実行
# スクリーニングから来た場合は自動実行
should_auto_run = (
    mode == "個別銘柄分析" and
    st.session_state.get('analyze_ticker') and
    st.session_state.get('analyze_ticker') == ticker and
    not st.session_state.get('auto_run_completed', False)
)

run_analysis = st.sidebar.button("分析実行") or should_auto_run

if mode == "個別銘柄分析" and run_analysis:
    # 自動実行の場合はフラグを設定
    if should_auto_run:
        st.session_state['auto_run_completed'] = True

    with st.spinner("データを取得中..."):
        hist, info, financials, balance_sheet, cashflow, dividends = get_stock_data(ticker, start_date, end_date)

        # 四半期データも取得
        stock = yf.Ticker(ticker)
        quarterly_financials = stock.quarterly_financials
        quarterly_balance_sheet = stock.quarterly_balance_sheet
        quarterly_cashflow = stock.quarterly_cashflow
    
    if hist is not None and not hist.empty:
        # 基本情報の表示
        st.header(f"{ticker} 基本情報")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            current_price = hist['Close'].iloc[-1]
            st.metric("現在の株価", f"{current_price:,.2f}円")

        with col2:
            company_name = info.get('longName', 'N/A')
            st.metric("会社名", company_name)

        with col3:
            market_cap = info.get('marketCap', 'N/A')
            if market_cap != 'N/A':
                st.metric("時価総額", f"{market_cap:,.0f}円")

        with col4:
            sector = info.get('sector', 'N/A')
            st.metric("セクター", sector)

        # 財務指標の計算と表示
        ratios = calculate_financial_ratios(info, financials, balance_sheet)

        # 配当情報セクション（最上部に配置）
        st.header("📊 配当情報")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            dividend_yield = ratios.get('配当利回り', 'N/A')
            if dividend_yield != 'N/A':
                st.metric("配当利回り", f"{dividend_yield:.2f}%", delta=None)
            else:
                st.metric("配当利回り", "N/A")

        with col2:
            dividend_rate = info.get('dividendRate', 'N/A')
            if dividend_rate != 'N/A':
                st.metric("年間配当金", f"{dividend_rate:.2f}円")
            else:
                st.metric("年間配当金", "N/A")

        with col3:
            payout_ratio = info.get('payoutRatio', 'N/A')
            if payout_ratio != 'N/A':
                st.metric("配当性向", f"{payout_ratio*100:.1f}%")
            else:
                st.metric("配当性向", "N/A")

        with col4:
            ex_dividend_date = info.get('exDividendDate', 'N/A')
            if ex_dividend_date != 'N/A':
                from datetime import datetime
                ex_date = datetime.fromtimestamp(ex_dividend_date).strftime('%Y-%m-%d')
                st.metric("権利落ち日", ex_date)
            else:
                st.metric("権利落ち日", "N/A")

        # 配当履歴チャート
        if dividends is not None and len(dividends) > 0:
            st.subheader("配当履歴")
            fig_div = go.Figure()
            fig_div.add_trace(go.Bar(x=dividends.index, y=dividends.values, name='配当金', marker_color='lightblue'))
            fig_div.update_layout(
                xaxis_title="年月",
                yaxis_title="配当金（円）",
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig_div, use_container_width=True)

        # 業績・財務指標セクション
        st.header("💰 業績・財務指標")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            per = ratios.get('PER', 'N/A')
            if per != 'N/A':
                st.metric("PER（株価収益率）", f"{per:.2f}倍")
            else:
                st.metric("PER（株価収益率）", "N/A")

        with col2:
            pbr = ratios.get('PBR', 'N/A')
            if pbr != 'N/A':
                st.metric("PBR（株価純資産倍率）", f"{pbr:.2f}倍")
            else:
                st.metric("PBR（株価純資産倍率）", "N/A")

        with col3:
            roe = info.get('returnOnEquity', 'N/A')
            if roe != 'N/A':
                st.metric("ROE（自己資本利益率）", f"{roe*100:.2f}%")
            else:
                st.metric("ROE（自己資本利益率）", "N/A")

        with col4:
            revenue_growth = ratios.get('売上高成長率', 'N/A')
            if revenue_growth != 'N/A':
                st.metric("売上高成長率", f"{revenue_growth:.2f}%")
            else:
                st.metric("売上高成長率", "N/A")

        with col5:
            profit_growth = ratios.get('利益成長率', 'N/A')
            if profit_growth != 'N/A':
                st.metric("利益成長率", f"{profit_growth:.2f}%")
            else:
                st.metric("利益成長率", "N/A")

        # 財務諸表の詳細表示
        st.header("📈 財務諸表")

        # 年次・四半期の選択
        financial_period = st.radio(
            "表示期間を選択",
            ["年次データ（Annual）", "四半期データ（Quarterly）"],
            horizontal=True,
            help="年次データは通常4年分、四半期データは通常4四半期～16四半期分のデータが表示されます"
        )

        # 選択に応じてデータを切り替え
        if financial_period == "年次データ（Annual）":
            display_financials = financials
            display_balance_sheet = balance_sheet
            display_cashflow = cashflow
            period_label = "年次"
        else:
            display_financials = quarterly_financials
            display_balance_sheet = quarterly_balance_sheet
            display_cashflow = quarterly_cashflow
            period_label = "四半期"

        tab1, tab2, tab3 = st.tabs(["損益計算書", "貸借対照表", "キャッシュフロー"])

        with tab1:
            st.subheader(f"損益計算書（Income Statement） - {period_label}")
            if display_financials is not None and not display_financials.empty:
                # データの期間情報を表示
                if len(display_financials.columns) > 0:
                    oldest_date = display_financials.columns[-1].strftime('%Y-%m-%d')
                    newest_date = display_financials.columns[0].strftime('%Y-%m-%d')
                    st.info(f"📅 データ期間: {oldest_date} ～ {newest_date} （{len(display_financials.columns)}期間）")

                # 日本円表示に変換
                financials_display = display_financials.copy()
                financials_display = financials_display / 1000000  # 百万円単位
                financials_display = financials_display.round(0)
                # 項目名を日本語と英語で表示
                financials_display = translate_financial_terms(financials_display)
                st.dataframe(financials_display, use_container_width=True)
                st.caption("単位：百万円")
            else:
                st.info("損益計算書のデータが取得できませんでした。")

        with tab2:
            st.subheader(f"貸借対照表（Balance Sheet） - {period_label}")
            if display_balance_sheet is not None and not display_balance_sheet.empty:
                # データの期間情報を表示
                if len(display_balance_sheet.columns) > 0:
                    oldest_date = display_balance_sheet.columns[-1].strftime('%Y-%m-%d')
                    newest_date = display_balance_sheet.columns[0].strftime('%Y-%m-%d')
                    st.info(f"📅 データ期間: {oldest_date} ～ {newest_date} （{len(display_balance_sheet.columns)}期間）")

                balance_sheet_display = display_balance_sheet.copy()
                balance_sheet_display = balance_sheet_display / 1000000  # 百万円単位
                balance_sheet_display = balance_sheet_display.round(0)
                # 項目名を日本語と英語で表示
                balance_sheet_display = translate_financial_terms(balance_sheet_display)
                st.dataframe(balance_sheet_display, use_container_width=True)
                st.caption("単位：百万円")
            else:
                st.info("貸借対照表のデータが取得できませんでした。")

        with tab3:
            st.subheader(f"キャッシュフロー計算書（Cash Flow） - {period_label}")
            if display_cashflow is not None and not display_cashflow.empty:
                # データの期間情報を表示
                if len(display_cashflow.columns) > 0:
                    oldest_date = display_cashflow.columns[-1].strftime('%Y-%m-%d')
                    newest_date = display_cashflow.columns[0].strftime('%Y-%m-%d')
                    st.info(f"📅 データ期間: {oldest_date} ～ {newest_date} （{len(display_cashflow.columns)}期間）")

                cashflow_display = display_cashflow.copy()
                cashflow_display = cashflow_display / 1000000  # 百万円単位
                cashflow_display = cashflow_display.round(0)
                # 項目名を日本語と英語で表示
                cashflow_display = translate_financial_terms(cashflow_display)
                st.dataframe(cashflow_display, use_container_width=True)
                st.caption("単位：百万円")
            else:
                st.info("キャッシュフロー計算書のデータが取得できませんでした。")

        # 株価チャート（シンプル版）
        st.header("📊 株価チャート")

        # シンプルな株価チャート（終値のみ）
        fig_price_simple = go.Figure()
        fig_price_simple.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='終値', line=dict(color='blue', width=2)))
        fig_price_simple.update_layout(
            xaxis_title="日付",
            yaxis_title="株価（円）",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig_price_simple, use_container_width=True)

        # テクニカル指標（折りたたみ式）
        with st.expander("📉 テクニカル指標を表示（オプション）", expanded=False):
            st.info("テクニカル分析が必要な場合はこちらをご確認ください")

            # テクニカル指標の計算
            # 単純移動平均
            hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
            hist['SMA_50'] = hist['Close'].rolling(window=50).mean()

            # ボリンジャーバンド
            hist['BB_upper'] = hist['Close'].rolling(window=20).mean() + hist['Close'].rolling(window=20).std() * 2
            hist['BB_middle'] = hist['Close'].rolling(window=20).mean()
            hist['BB_lower'] = hist['Close'].rolling(window=20).mean() - hist['Close'].rolling(window=20).std() * 2

            # RSI
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            hist['RSI'] = 100 - (100 / (1 + rs))

            # ローソク足チャート
            st.subheader("ローソク足チャート")
            fig_candlestick = go.Figure()
            fig_candlestick.add_trace(go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close'],
                name='ローソク足'
            ))
            fig_candlestick.add_trace(go.Scatter(x=hist.index, y=hist['SMA_20'], name='20日移動平均', line=dict(color='orange')))
            fig_candlestick.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], name='50日移動平均', line=dict(color='purple')))
            fig_candlestick.update_layout(
                xaxis_title="日付",
                yaxis_title="株価（円）",
                height=400,
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig_candlestick, use_container_width=True)

            # ボリンジャーバンド
            st.subheader("ボリンジャーバンド")
            fig_bb = go.Figure()
            fig_bb.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='終値', line=dict(color='blue')))
            fig_bb.add_trace(go.Scatter(x=hist.index, y=hist['BB_upper'], name='上限バンド', line=dict(color='red', dash='dash')))
            fig_bb.add_trace(go.Scatter(x=hist.index, y=hist['BB_middle'], name='中央線', line=dict(color='gray', dash='dot')))
            fig_bb.add_trace(go.Scatter(x=hist.index, y=hist['BB_lower'], name='下限バンド', line=dict(color='green', dash='dash')))
            fig_bb.update_layout(
                xaxis_title="日付",
                yaxis_title="株価（円）",
                height=300
            )
            st.plotly_chart(fig_bb, use_container_width=True)

            # RSIチャート
            st.subheader("RSI（相対力指数）")
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name='RSI', line=dict(color='blue')))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="買われすぎ")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="売られすぎ")
            fig_rsi.update_layout(
                xaxis_title="日付",
                yaxis_title="RSI",
                height=300
            )
            st.plotly_chart(fig_rsi, use_container_width=True)

        # 適時開示情報
        st.header("適時開示情報")
        # 日本株の場合、適時開示情報のリンクを表示
        if ticker.endswith('.T'):
            stock_code = ticker.replace('.T', '')

            # TDnet検索ページ
            tdnet_search_url = f"https://www.release.tdnet.info/inbs/I_search.html"
            st.markdown(f"[TDnet適時開示情報検索（銘柄コード: {stock_code}）]({tdnet_search_url})")

            # EDINET（金融商品取引法に基づく有価証券報告書等の開示書類）
            edinet_url = "https://disclosure2.edinet-fsa.go.jp/"
            st.markdown(f"[EDINET - 有価証券報告書等]({edinet_url})")

            # 日本取引所グループの銘柄情報
            jpx_url = f"https://www.jpx.co.jp/listing/stocks/new/index.html"
            st.markdown(f"[日本取引所グループ - 上場会社情報]({jpx_url})")

            # 会社の投資家情報ページへのリンク（infoから取得）
            ir_website = info.get('website', '')
            if ir_website:
                st.markdown(f"[企業公式ウェブサイト]({ir_website})")
        else:
            # 米国株などの場合、SECのEDGARへのリンク
            company_name = info.get('longName', ticker)
            sec_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=&dateb=&owner=exclude&count=40"
            st.markdown(f"[SEC EDGAR - {company_name} の開示情報]({sec_url})")

            ir_website = info.get('website', '')
            if ir_website:
                st.markdown(f"[企業公式ウェブサイト]({ir_website})")

        st.info("※ 適時開示情報は外部サイトで確認してください。TDnetでは銘柄コードで検索してください。")

    else:
        st.error("データを取得できませんでした。銘柄コードを確認してください。")

elif mode == "銘柄スクリーニング":
    st.header("🔍 銘柄スクリーニング")

    # データベース接続確認
    from database import DatabaseManager
    db_manager = DatabaseManager()

    st.info("""
    **スクリーニング方法の選択:**
    - **データベースから検索（推奨）**: 高速・事前に更新されたデータから検索
    - **リアルタイム検索**: yfinanceから最新データを取得（時間がかかります）
    """)

    use_database = st.checkbox("データベースから検索（推奨）", value=True)

    if use_database:
        # データベースからの高速スクリーニング
        st.info("データベース内のデータから検索します。左側のサイドバーで条件を設定してください。")

        if st.button("スクリーニング実行", type="primary"):
            # DBスクリーニング用の条件辞書を作成
            db_conditions = {
                'min_dividend_yield': min_dividend_yield if min_dividend_yield > 0 else None,
                'max_per': max_per if max_per < 50 else None,
                'max_pbr': max_pbr if max_pbr < 10 else None,
                'min_avg_dividend_yield': min_avg_dividend_yield if 'min_avg_dividend_yield' in locals() and min_avg_dividend_yield else None,
                'min_dividend_quality_score': min_dividend_quality_score if 'min_dividend_quality_score' in locals() and min_dividend_quality_score else None,
                'market': 'プライム' if market == "全銘柄" else None
            }

            with st.spinner("データベースから検索中..."):
                results = db_manager.get_screening_data(db_conditions)

            if results:
                # 結果をDataFrameに変換
                results_df = pd.DataFrame(results)

                # 列名を日本語に変換
                results_df = results_df.rename(columns={
                    'ticker': '銘柄コード',
                    'name': '銘柄名',
                    'sector': 'セクター',
                    'market': '市場',
                    'per': 'PER',
                    'pbr': 'PBR',
                    'roe': 'ROE',
                    'dividend_yield': '配当利回り(%)',
                    'avg_dividend_yield': '平均配当利回り(%)',
                    'dividend_cv': '配当変動係数',
                    'dividend_quality_score': '配当品質スコア'
                })

                # 結果をセッション状態に保存
                st.session_state['screening_results'] = results_df
                st.session_state['screening_conditions'] = db_conditions
                st.session_state['screening_mode'] = 'database'
            else:
                st.warning("データベースから結果が取得できませんでした。データ更新画面でデータを更新してください。")
                st.session_state['screening_results'] = pd.DataFrame()
    else:
        # 従来のリアルタイムスクリーニング
        st.info("yfinanceからリアルタイムでデータを取得します。左側のサイドバーで条件を設定してください。")

        if st.button("スクリーニング実行", type="primary"):
            # 条件を辞書にまとめる
            conditions = {
                # 基本条件
                'use_basic_dividend': use_basic_dividend if 'use_basic_dividend' in locals() else True,
                'min_dividend_yield': min_dividend_yield,
                'dividend_growth': dividend_growth,
                'revenue_growth': revenue_growth,
                'min_profit_margin': min_profit_margin,
                'use_basic_per': use_basic_per if 'use_basic_per' in locals() else True,
                'max_per': max_per,
                'max_pbr': max_pbr,
                # 高度な配当条件
                'use_advanced_dividend': use_advanced_dividend if 'use_advanced_dividend' in locals() else False,
                'dividend_years': dividend_years if 'dividend_years' in locals() else 4,
                'min_avg_dividend_yield': min_avg_dividend_yield if 'min_avg_dividend_yield' in locals() else None,
                'max_dividend_cv': max_dividend_cv if 'max_dividend_cv' in locals() else None,
                'declining_but_high_avg': declining_but_high_avg if 'declining_but_high_avg' in locals() else False,
                'require_increasing_trend': require_increasing_trend if 'require_increasing_trend' in locals() else False,
                'exclude_special_dividend': exclude_special_dividend if 'exclude_special_dividend' in locals() else False,
                'min_dividend_quality_score': min_dividend_quality_score if 'min_dividend_quality_score' in locals() else None,
                # 高度なPER条件
                'use_advanced_per': use_advanced_per if 'use_advanced_per' in locals() else False,
                'per_years': per_years if 'per_years' in locals() else 4,
                'min_avg_per': min_avg_per if 'min_avg_per' in locals() else None,
                'max_avg_per': max_avg_per if 'max_avg_per' in locals() else None,
                'max_per_cv': max_per_cv if 'max_per_cv' in locals() else None,
                'low_current_high_avg_per': low_current_high_avg_per if 'low_current_high_avg_per' in locals() else False,
            }

            # スクリーニング実行
            stocks = get_stock_list(market)

            with st.spinner("スクリーニング実行中..."):
                results_df = screen_stocks(stocks, conditions)

            # 結果をセッション状態に保存
            st.session_state['screening_results'] = results_df
            st.session_state['screening_conditions'] = conditions
            st.session_state['screening_mode'] = 'realtime'
            st.session_state['screening_market'] = market

    # スクリーニング結果が保存されている場合は表示
    if 'screening_results' in st.session_state and st.session_state['screening_results'] is not None:
        results_df = st.session_state['screening_results']
        conditions = st.session_state.get('screening_conditions', {})
        market = st.session_state.get('screening_market', market)

        # 設定条件の表示
        st.subheader("設定条件")
        col1, col2 = st.columns(2)

        with col1:
            st.write("**配当条件**")
            st.write(f"- 最低配当利回り: {conditions.get('min_dividend_yield', 'N/A')}%以上")
            if conditions.get('dividend_growth', False):
                st.write(f"- 配当増加傾向: 有効")

        with col2:
            st.write("**業績・バリュエーション**")
            st.write(f"- 最低利益率: {conditions.get('min_profit_margin', 'N/A')}%以上")
            if conditions.get('revenue_growth', False):
                st.write(f"- 売上高増加傾向: 有効")
            st.write(f"- 最大PER: {conditions.get('max_per', 'N/A')}倍以下")
            st.write(f"- 最大PBR: {conditions.get('max_pbr', 'N/A')}倍以下")

        st.write("---")

        # 結果表示
        st.subheader("スクリーニング結果")

        if len(results_df) > 0:
            st.success(f"条件に合致する銘柄: {len(results_df)}銘柄")

            # データテーブル表示
            st.dataframe(
                results_df,
                use_container_width=True,
                hide_index=True
            )

            # CSVダウンロードボタン
            csv = results_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="結果をCSVでダウンロード",
                data=csv,
                file_name=f"screening_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

            # 詳細分析用に銘柄選択
            st.subheader("詳細分析")
            st.write("結果から銘柄を選択して詳細分析できます")

            selected_ticker = st.selectbox(
                "詳細分析する銘柄を選択",
                options=results_df['銘柄コード'].tolist(),
                format_func=lambda x: f"{x} - {results_df[results_df['銘柄コード']==x]['銘柄名'].values[0]}"
            )

            st.write("")

            if st.button("📊 選択した銘柄の詳細分析を開く", key="detail_analysis_btn", type="primary", use_container_width=True):
                # セッション状態を更新
                st.session_state['analyze_ticker'] = selected_ticker
                st.session_state['switch_to_analysis'] = True
                st.session_state['auto_run_completed'] = False
                st.session_state['current_mode'] = "個別銘柄分析"
                st.session_state['last_ticker'] = None
                # ページを再読み込み
                st.rerun()
        else:
            st.warning("条件に合致する銘柄が見つかりませんでした。条件を緩和してみてください。")

else:
    st.info("左側のサイドバーで分析モードを選択してください。")
    st.write("**個別銘柄分析**: 特定の銘柄を詳細に分析")
    st.write("**銘柄スクリーニング**: 条件に基づいて複数の銘柄を検索")
    st.write("")
    st.write("使用例:")
    st.write("- トヨタ自動車: 7203.T")
    st.write("- ソニーグループ: 6758.T")
    st.write("- Apple: AAPL")
    st.write("- Microsoft: MSFT")