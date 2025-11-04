
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta

# Streamlitアプリの設定 - ページ設定を最初に
st.set_page_config(
    page_title="株価分析アプリ",
    layout="wide",
    initial_sidebar_state="expanded"  # サイドバーを初期表示
)

st.title("株価分析ダッシュボード")

# サイドバーにモード選択を追加
st.sidebar.header("モード選択")

# デバッグ情報をサイドバーに常に表示
st.sidebar.write("---")
st.sidebar.write("**🔍 現在の状態**")
st.sidebar.write(f"switch_to_analysis: {st.session_state.get('switch_to_analysis', False)}")
st.sidebar.write(f"current_mode: {st.session_state.get('current_mode', 'N/A')}")
st.sidebar.write(f"analyze_ticker: {st.session_state.get('analyze_ticker', 'N/A')}")
st.sidebar.write("---")

# スクリーニングから詳細分析に切り替える場合
if 'current_mode' not in st.session_state:
    st.session_state['current_mode'] = "個別銘柄分析"

# 強制的に個別銘柄分析モードに切り替え
if st.session_state.get('switch_to_analysis', False):
    st.sidebar.warning("⚠️ モード切替が要求されました！")
    st.session_state['current_mode'] = "個別銘柄分析"
    st.session_state['switch_to_analysis'] = False
    # モード切替直後にフラグをクリア
    mode = "個別銘柄分析"
    st.sidebar.success(f"✅ 個別銘柄分析モードに切り替えました")
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

    # デバッグ情報（開発時のみ表示）
    if st.sidebar.checkbox("デバッグ情報を表示", value=False):
        st.sidebar.write("**セッション状態:**")
        st.sidebar.write(f"- analyze_ticker: {st.session_state.get('analyze_ticker')}")
        st.sidebar.write(f"- current_mode: {st.session_state.get('current_mode')}")
        st.sidebar.write(f"- auto_run_completed: {st.session_state.get('auto_run_completed')}")
        st.sidebar.write(f"- last_ticker: {st.session_state.get('last_ticker')}")

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

    # 配当利回り
    st.sidebar.subheader("配当条件")
    min_dividend_yield = st.sidebar.number_input("最低配当利回り (%)", min_value=0.0, max_value=20.0, value=2.0, step=0.5)
    dividend_growth = st.sidebar.checkbox("配当増加傾向", value=False)

    # 業績条件
    st.sidebar.subheader("業績条件")
    revenue_growth = st.sidebar.checkbox("売上高増加傾向", value=False)
    min_profit_margin = st.sidebar.number_input("最低利益率 (%)", min_value=0.0, max_value=100.0, value=5.0, step=1.0)

    # バリュエーション
    st.sidebar.subheader("バリュエーション")
    max_per = st.sidebar.number_input("最大PER", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
    max_pbr = st.sidebar.number_input("最大PBR", min_value=0.0, max_value=10.0, value=2.0, step=0.1)

    # 対象市場
    st.sidebar.subheader("対象市場")
    market = st.sidebar.selectbox("市場を選択", ["日本株（東証主要銘柄）", "米国株（S&P500）"])

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
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
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

def get_stock_list(market):
    """市場に応じた銘柄リストを取得"""
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

def screen_stocks(stocks, conditions):
    """条件に基づいて銘柄をスクリーニング"""
    results = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    total_stocks = len(stocks)
    for idx, (ticker, name) in enumerate(stocks.items()):
        try:
            status_text.text(f"分析中: {name} ({ticker}) - {idx+1}/{total_stocks}")
            progress_bar.progress((idx + 1) / total_stocks)

            stock = yf.Ticker(ticker)
            info = stock.info

            # データ取得
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

            # 条件チェック
            passes = True

            if dividend_yield < conditions['min_dividend_yield']:
                passes = False

            if conditions['dividend_growth'] and not dividend_increasing:
                passes = False

            if conditions['revenue_growth'] and revenue_growth_rate <= 0:
                passes = False

            if profit_margin < conditions['min_profit_margin']:
                passes = False

            if per > conditions['max_per'] and per > 0:
                passes = False

            if pbr > conditions['max_pbr'] and pbr > 0:
                passes = False

            if passes:
                results.append({
                    '銘柄コード': ticker,
                    '銘柄名': name,
                    '配当利回り': f"{dividend_yield:.2f}%",
                    'PER': f"{per:.2f}" if per > 0 else "N/A",
                    'PBR': f"{pbr:.2f}" if pbr > 0 else "N/A",
                    '利益率': f"{profit_margin:.2f}%",
                    '売上成長率': f"{revenue_growth_rate:.2f}%",
                })

        except Exception as e:
            continue

    progress_bar.empty()
    status_text.empty()

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

        tab1, tab2, tab3 = st.tabs(["損益計算書", "貸借対照表", "キャッシュフロー"])

        with tab1:
            st.subheader("損益計算書（Income Statement）")
            if financials is not None and not financials.empty:
                # 日本円表示に変換
                financials_display = financials.copy()
                financials_display = financials_display / 1000000  # 百万円単位
                financials_display = financials_display.round(0)
                st.dataframe(financials_display, use_container_width=True)
                st.caption("単位：百万円")
            else:
                st.info("損益計算書のデータが取得できませんでした。")

        with tab2:
            st.subheader("貸借対照表（Balance Sheet）")
            if balance_sheet is not None and not balance_sheet.empty:
                balance_sheet_display = balance_sheet.copy()
                balance_sheet_display = balance_sheet_display / 1000000  # 百万円単位
                balance_sheet_display = balance_sheet_display.round(0)
                st.dataframe(balance_sheet_display, use_container_width=True)
                st.caption("単位：百万円")
            else:
                st.info("貸借対照表のデータが取得できませんでした。")

        with tab3:
            st.subheader("キャッシュフロー計算書（Cash Flow）")
            if cashflow is not None and not cashflow.empty:
                cashflow_display = cashflow.copy()
                cashflow_display = cashflow_display / 1000000  # 百万円単位
                cashflow_display = cashflow_display.round(0)
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

    st.info("設定した条件に基づいて銘柄をスクリーニングします。左側のサイドバーで条件を設定してください。")

    if st.button("スクリーニング実行", type="primary"):
        # 条件を辞書にまとめる
        conditions = {
            'min_dividend_yield': min_dividend_yield,
            'dividend_growth': dividend_growth,
            'revenue_growth': revenue_growth,
            'min_profit_margin': min_profit_margin,
            'max_per': max_per,
            'max_pbr': max_pbr,
        }

        # スクリーニング実行
        stocks = get_stock_list(market)

        with st.spinner("スクリーニング実行中..."):
            results_df = screen_stocks(stocks, conditions)

        # 結果をセッション状態に保存
        st.session_state['screening_results'] = results_df
        st.session_state['screening_conditions'] = conditions
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

            # デバッグ情報を常に表示
            st.write("---")
            st.write("### 🔍 デバッグ情報")
            st.write(f"**現在のモード**: {st.session_state.get('current_mode', 'N/A')}")
            st.write(f"**analyze_ticker**: {st.session_state.get('analyze_ticker', 'N/A')}")
            st.write(f"**switch_to_analysis**: {st.session_state.get('switch_to_analysis', False)}")
            st.write(f"**auto_run_completed**: {st.session_state.get('auto_run_completed', False)}")
            st.write(f"**選択された銘柄**: {selected_ticker}")
            st.write("---")

            if st.button("📊 選択した銘柄の詳細分析を開く", key="detail_analysis_btn", type="primary", use_container_width=True):
                # セッション状態を更新
                st.session_state['analyze_ticker'] = selected_ticker
                st.session_state['switch_to_analysis'] = True
                st.session_state['auto_run_completed'] = False
                st.session_state['current_mode'] = "個別銘柄分析"
                st.session_state['last_ticker'] = None

                # 更新後の状態を表示
                st.success(f"✅ セッション状態を更新しました: {selected_ticker}")
                st.write("更新後のセッション状態:")
                st.write("- analyze_ticker:", st.session_state['analyze_ticker'])
                st.write("- switch_to_analysis:", st.session_state['switch_to_analysis'])
                st.write("- current_mode:", st.session_state['current_mode'])
                st.write("ページを再読み込みします...")

                # ページを再読み込み
                st.rerun()

            st.info("💡 ボタンが機能しない場合: サイドバーで「個別銘柄分析」を手動で選択し、銘柄コード欄に上記の銘柄コードを入力してください")
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