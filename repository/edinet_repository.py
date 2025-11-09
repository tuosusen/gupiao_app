"""
EDINET API リポジトリ
金融庁のEDINET APIから財務データを取得
"""

import requests
import pandas as pd
import zipfile
import io
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import re


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
                xbrl_files = []

                # すべてのXBRLファイルを収集
                for file_name in zip_file.namelist():
                    if file_name.endswith('.xbrl'):
                        xbrl_files.append(file_name)

                if not xbrl_files:
                    return None

                # 財務データを含む可能性が高いXBRLファイルを優先
                # 1. PublicDoc内のファイル（財務諸表データ）
                # 2. ファイルサイズが大きいもの
                priority_files = []
                for xbrl_file in xbrl_files:
                    # ヘッダーファイル、監査報告書を除外
                    if 'header' in xbrl_file.lower() or 'audit' in xbrl_file.lower():
                        continue
                    # PublicDoc内のファイルを優先
                    if 'PublicDoc' in xbrl_file or 'public' in xbrl_file.lower():
                        priority_files.insert(0, xbrl_file)
                    else:
                        priority_files.append(xbrl_file)

                # 優先順位の高いファイルから試す
                target_files = priority_files if priority_files else xbrl_files

                # サイズ順にソート（大きいファイルほど財務データを含む可能性が高い）
                file_sizes = []
                for file_name in target_files:
                    file_info = zip_file.getinfo(file_name)
                    file_sizes.append((file_name, file_info.file_size))

                file_sizes.sort(key=lambda x: x[1], reverse=True)

                # 最大のXBRLファイルを返す
                if file_sizes:
                    largest_file = file_sizes[0][0]
                    print(f"        💡 {len(xbrl_files)}個のXBRLファイル中、最大のファイルを選択: {largest_file} ({file_sizes[0][1]} bytes)")
                    with zip_file.open(largest_file) as xbrl_file:
                        return xbrl_file.read()

                return None
        except Exception as e:
            print(f"XBRL抽出エラー: {e}")
            return None

    def parse_xbrl_to_dataframe(self, xbrl_content: bytes) -> Optional[Dict[str, pd.DataFrame]]:
        """
        XBRLデータをパースして財務データをDataFrameに変換

        Args:
            xbrl_content: XBRLファイルのバイナリデータ

        Returns:
            {カテゴリ名: DataFrame} の辞書、またはNone
        """
        try:
            # XMLをパース
            root = ET.fromstring(xbrl_content)

            # 財務データを抽出
            financial_data = {
                '損益計算書': [],
                '貸借対照表': [],
                '包括利益計算書': [],
                'キャッシュフロー計算書': []
            }

            # デバッグ: 最初の50個のタグをサンプル表示
            tag_samples = []
            elem_count = 0

            # XBRLの要素を探索
            for elem in root.iter():
                tag_name = elem.tag
                # 名前空間を除去してタグ名を取得
                if '}' in tag_name:
                    tag_name = tag_name.split('}')[1]

                # デバッグ用サンプル収集（最初の50個のみ）
                if elem_count < 50 and elem.text and elem.text.strip():
                    tag_samples.append(f"{tag_name}: {elem.text.strip()[:50]}")
                    elem_count += 1

                # 財務指標のパターンマッチング
                value = elem.text
                if value and value.strip():
                    # 売上高関連
                    if re.search(r'(売上高|NetSales|Revenue)', tag_name, re.IGNORECASE):
                        financial_data['損益計算書'].append({
                            '項目': '売上高',
                            'タグ': tag_name,
                            '値': value,
                            'コンテキスト': elem.get('contextRef', ''),
                            '単位': elem.get('unitRef', '')
                        })

                    # 営業利益関連
                    elif re.search(r'(営業利益|OperatingIncome|OperatingProfit)', tag_name, re.IGNORECASE):
                        financial_data['損益計算書'].append({
                            '項目': '営業利益',
                            'タグ': tag_name,
                            '値': value,
                            'コンテキスト': elem.get('contextRef', ''),
                            '単位': elem.get('unitRef', '')
                        })

                    # 当期純利益関連
                    elif re.search(r'(当期純利益|NetIncome|ProfitLoss)', tag_name, re.IGNORECASE):
                        financial_data['損益計算書'].append({
                            '項目': '当期純利益',
                            'タグ': tag_name,
                            '値': value,
                            'コンテキスト': elem.get('contextRef', ''),
                            '単位': elem.get('unitRef', '')
                        })

                    # 総資産関連
                    elif re.search(r'(総資産|TotalAssets|Assets)', tag_name, re.IGNORECASE):
                        financial_data['貸借対照表'].append({
                            '項目': '総資産',
                            'タグ': tag_name,
                            '値': value,
                            'コンテキスト': elem.get('contextRef', ''),
                            '単位': elem.get('unitRef', '')
                        })

                    # 純資産関連
                    elif re.search(r'(純資産|NetAssets|Equity)', tag_name, re.IGNORECASE):
                        financial_data['貸借対照表'].append({
                            '項目': '純資産',
                            'タグ': tag_name,
                            '値': value,
                            'コンテキスト': elem.get('contextRef', ''),
                            '単位': elem.get('unitRef', '')
                        })

                    # 営業キャッシュフロー関連
                    elif re.search(r'(営業.*キャッシュ|OperatingCashFlow|CashFlowsFromOperating)', tag_name, re.IGNORECASE):
                        financial_data['キャッシュフロー計算書'].append({
                            '項目': '営業活動によるキャッシュフロー',
                            'タグ': tag_name,
                            '値': value,
                            'コンテキスト': elem.get('contextRef', ''),
                            '単位': elem.get('unitRef', '')
                        })

            # デバッグ: サンプルタグを表示
            if tag_samples:
                print(f"        📋 XBRLタグサンプル（最初の{len(tag_samples)}個）:")
                for i, sample in enumerate(tag_samples[:10], 1):
                    print(f"          {i}. {sample}")

            # DataFrameに変換
            result = {}
            for category, items in financial_data.items():
                if items:
                    df = pd.DataFrame(items)
                    result[category] = df

            # デバッグ: マッチしたタグがない場合の追加情報
            if not result:
                print(f"        ⚠️ 財務指標のパターンにマッチするタグが見つかりませんでした")
                print(f"        💡 XBRLファイルに {elem_count} 個の要素がありますが、パターンにマッチしませんでした")

            return result if result else None

        except Exception as e:
            print(f"XBRL解析エラー: {e}")
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
        # doc_typesがNoneの場合はすべての書類種類を許可（リストとして渡されない）
        # 空リストの場合はデフォルト値を使用
        if doc_types is not None and len(doc_types) == 0:
            doc_types = ['120', '140']  # 有価証券報告書、四半期報告書

        financial_data = {}
        company_code = company_code.replace('.T', '').replace(' ', '')

        # 各年について、過去N日分の書類を検索
        # 毎日チェック（書類提出日を確実にカバー）
        # 注: API制限を考慮して最大180日間に制限
        end_date = datetime.now()
        max_days = min(365 * years, 180)  # 最大180日間
        start_date = end_date - timedelta(days=max_days)

        # デバッグ情報用の変数
        total_checked_dates = 0
        dates_with_docs = 0
        matching_docs_count = 0
        sample_sec_codes = []  # サンプル証券コードを収集

        # 毎日チェック（書類提出日を確実にカバー）
        current_date = end_date
        while current_date >= start_date:
            date_str = current_date.strftime('%Y-%m-%d')
            total_checked_dates += 1

            documents = self.get_documents_list(date_str)
            if not documents:
                current_date -= timedelta(days=1)
                continue

            dates_with_docs += 1

            # 対象企業の書類をフィルタリング
            company_docs = []
            for idx, doc in enumerate(documents.get('results', [])):
                sec_code = (doc.get('secCode') or '').replace(' ', '')
                edinet_code = doc.get('edinetCode') or ''
                filer_name = doc.get('filerName', '')

                # サンプル証券コードを収集（最初の10件のみ）
                if len(sample_sec_codes) < 10 and sec_code:
                    sample_sec_codes.append(f"{filer_name[:20]}... | {sec_code}")

                # デバッグ: 企業コードが一致する書類を詳細ログ出力
                if company_code in sec_code or (filer_name and company_code in filer_name):
                    doc_type_for_debug = doc.get('docTypeCode')
                    print(f"  候補発見: {filer_name} | 証券コード: '{sec_code}' | EDINETコード: {edinet_code} | 書類種類: {doc_type_for_debug}")

                if (sec_code.startswith(company_code) or edinet_code == company_code):
                    doc_type = doc.get('docTypeCode')
                    print(f"    → 企業コード一致チェック: sec_code='{sec_code}', doc_type='{doc_type}', 期待される書類種類={doc_types}")
                    # doc_typesがNoneの場合はすべての書類を受け入れる
                    if doc_types is None or doc_type in doc_types:
                        company_docs.append(doc)
                        matching_docs_count += 1
                        print(f"    ✓ マッチ成功: {filer_name} | 書類種類: {doc_type}")
                    else:
                        print(f"    ✗ 書類種類不一致: doc_type='{doc_type}' not in {doc_types}")

            # 各書類のデータを取得
            for doc in company_docs:
                doc_id = doc.get('docID')
                doc_type_code = doc.get('docTypeCode')
                filer_name_for_dl = doc.get('filerName', '')

                print(f"      → 書類ダウンロード試行: {doc_id} | 種類: {doc_type_code}")
                doc_content = self.get_document(doc_id, doc_type=1)  # XBRL形式に変更

                if doc_content:
                    print(f"        ✓ ダウンロード成功 ({len(doc_content)} bytes)")

                    # XBRLデータを抽出
                    xbrl_content = self.extract_xbrl_data(doc_content)
                    if xbrl_content:
                        print(f"        ✓ XBRL抽出成功 ({len(xbrl_content)} bytes)")

                        # XBRLをパースしてDataFrameに変換
                        parsed_data = self.parse_xbrl_to_dataframe(xbrl_content)
                        if parsed_data:
                            period = doc.get('periodEnd', 'Unknown')
                            financial_data[period] = parsed_data
                            print(f"        ✓ XBRL解析成功: {len(parsed_data)} カテゴリ")
                            for category, df in parsed_data.items():
                                print(f"          - {category}: {len(df)} 項目")
                        else:
                            print(f"        ✗ XBRL解析失敗: 財務データを抽出できませんでした")
                    else:
                        print(f"        ✗ XBRL抽出失敗: ZIPにXBRLファイルなし")
                else:
                    print(f"        ✗ ダウンロード失敗またはデータなし")

            current_date -= timedelta(days=1)

        # デバッグ情報を含めて返す（一時的）
        print(f"\n===== デバッグ情報 =====")
        print(f"検索対象企業コード: '{company_code}'")
        print(f"チェックした日付数: {total_checked_dates}")
        print(f"書類があった日付数: {dates_with_docs}")
        print(f"マッチした書類数: {matching_docs_count}")
        if sample_sec_codes:
            print(f"\nサンプル証券コード（最初の10件）:")
            for sample in sample_sec_codes[:10]:
                print(f"  {sample}")
        print(f"====================\n")

        return financial_data
