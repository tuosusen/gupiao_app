"""
EDINET API リポジトリ
金融庁のEDINET APIから財務データを取得
"""

import requests
import pandas as pd
import zipfile
import io
from datetime import datetime, timedelta
from typing import Optional, Dict, List


class EDINETRepository:
    """EDINET APIを使用したデータ取得"""
    
    def __init__(self, api_key: str):
        """
        初期化
        
        Args:
            api_key: EDINET APIキー
        """
        self.api_key = api_key
        self.base_url = "https://api.edinet-fsa.go.jp/api/v2"
    
    def get_documents_list(self, date: str, doc_type: int = 2) -> Optional[Dict]:
        """
        書類一覧を取得
        
        Args:
            date: 日付（YYYY-MM-DD形式）
            doc_type: 1=メタデータのみ, 2=提出書類一覧及びメタデータ
            
        Returns:
            書類一覧の辞書、またはNone
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
                    return None
            else:
                return None
        except Exception:
            return None
    
    def get_document(self, doc_id: str, doc_type: int = 1) -> Optional[bytes]:
        """
        書類を取得
        
        Args:
            doc_id: 書類ID
            doc_type: 1=提出本文書及び監査報告書(XBRL含む), 5=CSV形式
            
        Returns:
            書類コンテンツ（bytes）、またはNone
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
                return None
        except Exception:
            return None
    
    def extract_xbrl_data(self, zip_content: bytes) -> Optional[bytes]:
        """
        ZIPファイルからXBRLデータを抽出
        
        Args:
            zip_content: ZIPファイルのバイナリデータ
            
        Returns:
            XBRLデータ、またはNone
        """
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
                for file_name in zip_file.namelist():
                    if file_name.endswith('.xbrl') or 'XBRL' in file_name:
                        with zip_file.open(file_name) as xbrl_file:
                            return xbrl_file.read()
                return None
        except Exception:
            return None
    
    def extract_csv_data(self, zip_content: bytes) -> Optional[Dict[str, pd.DataFrame]]:
        """
        ZIPファイルからCSVデータを抽出
        
        Args:
            zip_content: ZIPファイルのバイナリデータ
            
        Returns:
            {ファイル名: DataFrame} の辞書、またはNone
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
        except Exception:
            return None
    
    def get_financial_statements(self, company_code: str, years: int = 5, 
                                 doc_types: List[str] = None) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        企業の財務諸表を取得
        
        Args:
            company_code: 企業コード（証券コードまたはEDINETコード）
            years: 取得する年数
            doc_types: 書類種類コードのリスト（例: ['120', '140']）
            
        Returns:
            {期間: {ファイル名: DataFrame}} の辞書
        """
        if doc_types is None:
            doc_types = ['120', '140']  # 有価証券報告書、四半期報告書
        
        financial_data = {}
        company_code = company_code.replace('.T', '').replace(' ', '')

        for year_offset in range(years):
            target_date = (datetime.now() - timedelta(days=365*year_offset)).strftime('%Y-%m-%d')
            
            documents = self.get_documents_list(target_date)
            if not documents:
                continue

            # 対象企業の書類をフィルタリング
            company_docs = []
            for doc in documents.get('results', []):
                sec_code = (doc.get('secCode') or '').replace(' ', '')
                edinet_code = doc.get('edinetCode') or ''

                if (sec_code.startswith(company_code) or edinet_code == company_code):
                    doc_type = doc.get('docTypeCode')
                    if doc_type in doc_types:
                        company_docs.append(doc)

            # 各書類のデータを取得
            for doc in company_docs:
                doc_id = doc.get('docID')
                doc_content = self.get_document(doc_id, doc_type=5)  # CSV形式

                if doc_content:
                    csv_data = self.extract_csv_data(doc_content)
                    if csv_data:
                        period = doc.get('periodEnd', 'Unknown')
                        financial_data[period] = csv_data

        return financial_data
