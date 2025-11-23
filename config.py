"""
アプリケーション設定
データベース接続設定とアプリケーション全体の設定を管理
"""

import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DatabaseConfig:
    """データベース接続設定"""
    host: str = os.getenv('MYSQL_HOST', 'localhost')
    port: int = int(os.getenv('MYSQL_PORT', '3306'))
    user: str = os.getenv('MYSQL_USER', 'root')
    password: str = os.getenv('MYSQL_PASSWORD', '')
    database: str = os.getenv('MYSQL_DATABASE', 'stock_analysis')
    charset: str = 'utf8mb4'
    collation: str = 'utf8mb4_unicode_ci'

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'charset': self.charset,
            'collation': self.collation
        }


@dataclass
class AppConfig:
    """アプリケーション設定"""
    page_title: str = "株価分析アプリ"
    page_icon: str = "📈"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"

    # スクリーニング設定
    default_market: str = "プライム"
    max_results: int = 100

    # データ更新設定
    batch_size: int = 10
    max_workers: int = 5


# 設定インスタンス（シングルトン）
DB_CONFIG = DatabaseConfig()
APP_CONFIG = AppConfig()
