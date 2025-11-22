import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import json

def display_api_guide():
    st.header("EDINET APIキー取得ガイド")
    
    st.subheader("ステップ1: アカウント作成")
    st.write("""
    1. [EDINET API 認証ページ](https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1)にアクセス
    2. 「今すぐサインアップ」をクリック
    3. メールアドレスを入力し「確認コードを送信」
    4. 届いた確認コードを入力
    5. パスワードを設定（12文字以上、大文字・小文字・数字・記号のうち3種類以上）
    6. 多要素認証を設定（SMSまたは音声通話）
    """)
    
    st.subheader("ステップ2: APIキー発行")
    st.write("""
    1. 多要素認証後にAPIキー発行画面が表示
    2. 必須項目を入力：
       - 所属（会社名）
       - 氏名
       - 電話番号（ハイフンなし）
    3. 「連絡先登録」をクリック
    4. 表示されたAPIキーを必ず保存
    """)
    
    st.subheader("ステップ3: APIキーの使用方法")
    st.code("""
# 環境変数として設定（推奨）
import os
API_KEY = os.getenv('EDINET_API_KEY')

# 直接設定（テスト用のみ）
API_KEY = "あなたのAPIキー"
    """, language='python')

# 簡易版EDINET APIクライアント
class SimpleEDINETClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.edinet-fsa.go.jp/api/v2"
    
    def test_connection(self):
        """API接続テスト"""
        test_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        url = f"{self.base_url}/documents.json"
        params = {
            'date': test_date,
            'type': 1,  # メタデータのみ
            'Subscription-Key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return True, "接続成功"
            else:
                return False, f"接続エラー: {response.status_code}"
        except Exception as e:
            return False, f"接続エラー: {e}"

def main():
    st.title("EDINET財務データ分析アプリ")
    
    # APIキー取得ガイドを表示
    display_api_guide()
    
    st.divider()
    
    # APIキー入力
    st.subheader("APIキー設定")
    api_key = st.text_input("EDINET APIキー", type="password", 
                           placeholder="ここに取得したAPIキーを入力")
    
    if api_key:
        client = SimpleEDINETClient(api_key)
        success, message = client.test_connection()
        
        if success:
            st.success("✅ " + message)
            st.session_state.api_key = api_key
            show_analysis_interface(api_key)
        else:
            st.error("❌ " + message)
            st.info("APIキーが正しいか確認してください")

def show_analysis_interface(api_key):
    """分析インターフェースを表示"""
    st.header("企業財務分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        company_code = st.text_input("企業コード", "7203", 
                                   help="例: 7203（トヨタ）, 6758（ソニー）")
        start_date = st.date_input("開始日", 
                                 datetime.now() - timedelta(days=365*3))
    
    with col2:
        doc_type = st.selectbox("書類種別", 
                              ["有価証券報告書", "四半期報告書", "全て"])
        end_date = st.date_input("終了日", datetime.now())
    
    if st.button("財務データ取得", type="primary"):
        with st.spinner("データ取得中..."):
            # 簡易的なデータ取得デモ
            demo_financial_data = get_demo_financial_data()
            display_financial_analysis(demo_financial_data)

def get_demo_financial_data():
    """デモ用の財務データ（実際のAPI実装時は置き換え）"""
    periods = ['2024-Q2', '2024-Q1', '2023-Q4', '2023-Q3']
    
    data = {
        'period': periods,
        '売上高（百万円）': [1250000, 1150000, 2450000, 2350000],
        '営業利益（百万円）': [150000, 135000, 280000, 260000],
        '純利益（百万円）': [120000, 110000, 220000, 205000],
        '純資産（百万円）': [4500000, 4400000, 4300000, 4200000],
        '総資産（百万円）': [7500000, 7400000, 7300000, 7200000]
    }
    
    return pd.DataFrame(data)

def display_financial_analysis(df):
    """財務分析結果を表示"""
    st.subheader("財務データ概要")
    st.dataframe(df, use_container_width=True)
    
    # 売上高と利益の推移
    st.subheader("売上高と利益の推移")
    col1, col2 = st.columns(2)
    
    with col1:
        st.line_chart(df.set_index('period')['売上高（百万円）'])
    
    with col2:
        st.area_chart(df.set_index('period')[['営業利益（百万円）', '純利益（百万円）']])
    
    # 財務指標の計算
    st.subheader("財務指標")
    df['売上高営業利益率(%)'] = (df['営業利益（百万円）'] / df['売上高（百万円）']) * 100
    df['自己資本比率(%)'] = (df['純資産（百万円）'] / df['総資産（百万円）']) * 100
    
    st.dataframe(df[['period', '売上高営業利益率(%)', '自己資本比率(%)']])

if __name__ == "__main__":
    main()