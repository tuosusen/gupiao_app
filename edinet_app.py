"""
EDINET財務分析アプリ - エントリーポイント
新しいアーキテクチャ版
"""

import streamlit as st
from ui.pages.edinet_page import EDINETPage

if __name__ == "__main__":
    st.set_page_config(
        page_title="EDINET財務分析",
        page_icon="📊",
        layout="wide"
    )
    
    EDINETPage.show()
