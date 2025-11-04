import requests
import pandas as pd
import zipfile
import io
import json
from datetime import datetime, timedelta
import streamlit as st

class EDINETAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.edinet-fsa.go.jp/api/v2"
        
    def get_documents_list(self, date, doc_type=2):
        """
        書類一覧を取得
        type=1: メタデータのみ
        type=2: 提出書類一覧及びメタデータ
        """
        url = f"{self.base_url}/documents.json"
        params = {
            'date': date,
            'type': doc_type,
            'Subscription-Key': self.api_key
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('metadata', {}).get('status') == '200':
                    return result
                else:
                    st.error(f"API応答エラー: {result.get('metadata', {}).get('message', '不明なエラー')}")
                    return None
            else:
                st.error(f"書類一覧取得エラー: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.Timeout:
            st.error("リクエストがタイムアウトしました")
            return None
        except Exception as e:
            st.error(f"書類一覧取得エラー: {str(e)}")
            return None
    
    def get_document(self, doc_id, doc_type=1):
        """
        書類を取得
        type=1: 提出本文書及び監査報告書(XBRL含む)
        type=5: CSV形式
        """
        url = f"{self.base_url}/documents/{doc_id}"
        params = {
            'type': doc_type,
            'Subscription-Key': self.api_key
        }

        try:
            response = requests.get(url, params=params, timeout=60)
            if response.status_code == 200:
                return response.content
            else:
                st.error(f"書類取得エラー (docID: {doc_id}): {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            st.error(f"書類取得タイムアウト (docID: {doc_id})")
            return None
        except Exception as e:
            st.error(f"書類取得エラー (docID: {doc_id}): {str(e)}")
            return None
    
    def extract_xbrl_data(self, zip_content):
        """
        ZIPファイルからXBRLデータを抽出
        """
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
                # XBRLファイルを探す
                for file_name in zip_file.namelist():
                    if file_name.endswith('.xbrl') or 'XBRL' in file_name:
                        with zip_file.open(file_name) as xbrl_file:
                            return xbrl_file.read()
                return None
        except Exception as e:
            st.error(f"ZIP解凍エラー: {e}")
            return None
    
    def extract_csv_data(self, zip_content):
        """
        ZIPファイルからCSVデータを抽出
        """
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
                csv_data = {}
                for file_name in zip_file.namelist():
                    if file_name.endswith('.csv'):
                        with zip_file.open(file_name) as csv_file:
                            df = pd.read_csv(csv_file, encoding='cp932')
                            csv_data[file_name] = df
                return csv_data
        except Exception as e:
            st.error(f"CSV抽出エラー: {e}")
            return None

def get_financial_statements(edinet_api, company_code, years=5):
    """
    企業の財務諸表を取得
    """
    financial_data = {}

    st.info(f"企業コード: {company_code} のデータを検索中...")

    # 過去数年分のデータを取得
    for year_offset in range(years):
        target_date = (datetime.now() - timedelta(days=365*year_offset)).strftime('%Y-%m-%d')
        st.write(f"検索日付: {target_date}")

        # 書類一覧を取得
        documents = edinet_api.get_documents_list(target_date)
        if not documents:
            st.warning(f"{target_date} の書類一覧を取得できませんでした")
            continue

        st.write(f"取得した書類数: {len(documents.get('results', []))}")

        # 対象企業の書類をフィルタリング
        company_docs = []
        for doc in documents.get('results', []):
            sec_code = (doc.get('secCode') or '').replace(' ', '')
            edinet_code = doc.get('edinetCode') or ''
            target_code = company_code.replace('.T', '').replace(' ', '')

            if (sec_code == target_code or edinet_code == target_code):
                # 有価証券報告書や四半期報告書を対象
                doc_type = doc.get('docTypeCode')
                if doc_type in ['120', '130', '140', '150']:  # 有価証券報告書、四半期報告書など
                    company_docs.append(doc)
                    st.write(f"✓ マッチング: {doc.get('filerName')} ({doc_type})")

        if not company_docs:
            st.warning(f"{target_date} に該当する書類が見つかりませんでした")

        # 各書類のデータを取得
        for doc in company_docs:
            doc_id = doc.get('docID')
            st.write(f"書類ID {doc_id} を取得中...")
            doc_content = edinet_api.get_document(doc_id, doc_type=5)  # CSV形式で取得

            if doc_content:
                csv_data = edinet_api.extract_csv_data(doc_content)
                if csv_data:
                    period = doc.get('periodEnd', 'Unknown')
                    financial_data[period] = csv_data
                    st.success(f"期間 {period} のデータを取得しました")
                else:
                    st.warning(f"書類ID {doc_id} のCSVデータを抽出できませんでした")
            else:
                st.warning(f"書類ID {doc_id} のコンテンツを取得できませんでした")

    if not financial_data:
        st.error(f"企業コード {company_code} の財務データが見つかりませんでした。以下を確認してください:")
        st.write("- 企業コードが正しいか（証券コードまたはEDINETコード）")
        st.write("- 指定期間内に有価証券報告書が提出されているか")
        st.write("- APIキーが有効か")

    return financial_data

def extract_revenue_data(data):
    """
    売上高データを抽出
    """
    try:
        # CSVファイルから売上高データを検索
        for df in data.values():
            if '売上高' in df.columns:
                return df['売上高'].values
        return None
    except Exception as e:
        st.error(f"売上高データ抽出エラー: {e}")
        return None

def calculate_financial_ratios(financial_data):
    """
    財務指標を計算
    """
    ratios = {}
    
    try:
        for period, data in financial_data.items():
            period_ratios = {}
            
            # 売上高成長率の計算（前年比）
            # 利益成長率の計算
            # PER, PBRなどの計算
            
            # 例: 売上高の取得と成長率計算
            revenue_data = extract_revenue_data(data)
            if revenue_data and len(revenue_data) > 1:
                current_revenue = revenue_data[-1]
                previous_revenue = revenue_data[-2]
                growth_rate = ((current_revenue - previous_revenue) / previous_revenue) * 100
                period_ratios['売上高成長率'] = growth_rate
            
            ratios[period] = period_ratios
            
    except Exception as e:
        st.error(f"財務指標計算エラー: {e}")
    
    return ratios

# Streamlitアプリの実装
def main():
    st.title("EDINET APIを使用した財務分析アプリ")
    
    # APIキーの入力
    api_key = st.sidebar.text_input("EDINET APIキー", type="password")
    
    if not api_key:
        st.info("EDINET APIキーを入力してください")
        st.write("APIキーの取得方法:")
        st.write("1. https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1 にアクセス")
        st.write("2. アカウントを作成し、APIキーを発行")
        return
    
    edinet_api = EDINETAPI(api_key)
    
    # 企業コード入力
    company_code = st.text_input("企業コード（例: 7203 または 7203.T）", "7203")
    company_code = company_code.replace('.T', '')  # .Tを除去
    
    years = st.slider("分析年数", 1, 10, 5)
    
    if st.button("財務データ取得"):
        with st.spinner("財務データを取得中..."):
            financial_data = get_financial_statements(edinet_api, company_code, years)
            
            if financial_data:
                st.success(f"{len(financial_data)}期分の財務データを取得しました")
                
                # 財務指標の計算
                ratios = calculate_financial_ratios(financial_data)
                
                # 結果の表示
                display_financial_analysis(financial_data, ratios)
            else:
                st.error("財務データを取得できませんでした")

def display_financial_analysis(financial_data, ratios):
    """
    財務分析結果を表示
    """
    st.header("財務分析結果")
    
    # 財務指標テーブル
    if ratios:
        ratios_df = pd.DataFrame(ratios).T
        st.subheader("財務指標")
        st.dataframe(ratios_df)
        
        # グラフ表示
        st.subheader("推移グラフ")
        
        # 売上高成長率の推移
        if '売上高成長率' in ratios_df.columns:
            st.line_chart(ratios_df['売上高成長率'])
    
    # 詳細データの表示
    st.subheader("詳細財務データ")
    for period, data in financial_data.items():
        with st.expander(f"期間: {period}"):
            for file_name, df in data.items():
                st.write(f"ファイル: {file_name}")
                st.dataframe(df.head())

if __name__ == "__main__":
    main()