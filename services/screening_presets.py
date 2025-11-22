"""
スクリーニングプリセット定義
利回り重視投資家向けのプリセット条件
"""

from typing import Dict, Any, List


class ScreeningPresets:
    """スクリーニングプリセットの定義と管理"""

    PRESETS: Dict[str, Dict[str, Any]] = {
        "高配当・安定配当": {
            "icon": "💰",
            "description": "配当利回り4%以上、配当が安定している銘柄",
            "target_user": "安定した配当収入を求める投資家",
            "conditions": {
                "min_dividend_yield": 4.0,
                "max_dividend_cv": 0.3,
                "min_quality_score": 60,
                "use_db": True,
            },
            "display_columns": [
                "銘柄コード", "銘柄名", "現在配当利回り", "平均配当利回り",
                "配当変動係数", "配当品質スコア", "リスクレベル"
            ]
        },
        "配当貴族候補": {
            "icon": "👑",
            "description": "長期連続増配が見込まれる優良銘柄",
            "target_user": "配当成長を重視する長期投資家",
            "conditions": {
                "min_avg_yield": 3.0,
                "dividend_trend": "増加",
                "min_quality_score": 70,
                "max_per": 15,
                "use_db": True,
            },
            "display_columns": [
                "銘柄コード", "銘柄名", "現在配当利回り", "平均配当利回り",
                "トレンド", "配当品質スコア", "PER"
            ]
        },
        "バリュー高配当": {
            "icon": "📊",
            "description": "割安かつ高配当な銘柄",
            "target_user": "バリュー投資 + 高配当を求める投資家",
            "conditions": {
                "min_dividend_yield": 3.5,
                "max_per": 12,
                "max_pbr": 1.0,
                "min_quality_score": 50,
                "use_db": True,
            },
            "display_columns": [
                "銘柄コード", "銘柄名", "現在配当利回り", "PER", "PBR",
                "配当品質スコア", "時価総額"
            ]
        },
        "超高配当": {
            "icon": "🚀",
            "description": "配当利回り5%以上（リスク高めの可能性あり）",
            "target_user": "高利回りを最優先する投資家（リスク許容度高）",
            "conditions": {
                "min_dividend_yield": 5.0,
                "min_quality_score": 40,
                "use_db": True,
            },
            "display_columns": [
                "銘柄コード", "銘柄名", "現在配当利回り", "平均配当利回り",
                "リスクレベル", "配当品質スコア", "自己資本比率"
            ]
        },
        "安定成長配当": {
            "icon": "🌱",
            "description": "配当成長と安定性のバランスが取れた銘柄",
            "target_user": "バランス重視の長期投資家",
            "conditions": {
                "min_dividend_yield": 2.5,
                "dividend_trend": "増加",
                "max_dividend_cv": 0.25,
                "min_quality_score": 65,
                "use_db": True,
            },
            "display_columns": [
                "銘柄コード", "銘柄名", "現在配当利回り", "平均配当利回り",
                "トレンド", "配当変動係数", "配当品質スコア"
            ]
        },
        "低リスク配当株": {
            "icon": "🛡️",
            "description": "財務健全性が高く、低リスクな配当株",
            "target_user": "リスクを最小限に抑えたい保守的な投資家",
            "conditions": {
                "min_dividend_yield": 2.0,
                "min_quality_score": 60,
                "min_equity_ratio": 40,
                "min_current_ratio": 150,
                "use_db": True,
            },
            "display_columns": [
                "銘柄コード", "銘柄名", "現在配当利回り", "リスクレベル",
                "自己資本比率", "流動比率", "配当品質スコア"
            ]
        }
    }

    @classmethod
    def get_preset_names(cls) -> List[str]:
        """プリセット名のリストを取得"""
        return list(cls.PRESETS.keys())

    @classmethod
    def get_preset(cls, name: str) -> Dict[str, Any]:
        """指定されたプリセットを取得"""
        return cls.PRESETS.get(name)

    @classmethod
    def get_preset_with_icon(cls, name: str) -> str:
        """アイコン付きプリセット名を取得"""
        preset = cls.PRESETS.get(name)
        if preset:
            return f"{preset['icon']} {name}"
        return name

    @classmethod
    def apply_preset_conditions(cls, preset_name: str, base_conditions: Dict) -> Dict:
        """
        プリセット条件を基本条件に適用

        Args:
            preset_name: プリセット名
            base_conditions: 基本条件の辞書

        Returns:
            プリセット条件が適用された辞書
        """
        preset = cls.get_preset(preset_name)
        if not preset:
            return base_conditions

        # プリセット条件をマージ
        merged = base_conditions.copy()
        merged.update(preset["conditions"])

        return merged

    @classmethod
    def get_display_columns(cls, preset_name: str) -> List[str]:
        """プリセットの推奨表示列を取得"""
        preset = cls.get_preset(preset_name)
        if preset and "display_columns" in preset:
            return preset["display_columns"]
        return []

    @classmethod
    def format_preset_info(cls, preset_name: str) -> str:
        """
        プリセット情報をフォーマットして表示用文字列を生成

        Args:
            preset_name: プリセット名

        Returns:
            フォーマットされた情報文字列
        """
        preset = cls.get_preset(preset_name)
        if not preset:
            return ""

        info_parts = [
            f"**{preset['icon']} {preset_name}**",
            f"📝 {preset['description']}",
            f"👤 対象: {preset['target_user']}",
            "",
            "**条件:**"
        ]

        # 条件を読みやすく表示
        conditions = preset["conditions"]
        condition_labels = {
            "min_dividend_yield": "最低配当利回り",
            "max_dividend_cv": "最大配当変動係数",
            "min_quality_score": "最低品質スコア",
            "min_avg_yield": "最低平均利回り",
            "dividend_trend": "配当トレンド",
            "max_per": "最大PER",
            "max_pbr": "最大PBR",
            "min_equity_ratio": "最低自己資本比率",
            "min_current_ratio": "最低流動比率",
        }

        for key, value in conditions.items():
            if key == "use_db":
                continue
            label = condition_labels.get(key, key)
            if isinstance(value, float):
                if "利回り" in label or "比率" in label:
                    info_parts.append(f"- {label}: {value}% 以上")
                else:
                    info_parts.append(f"- {label}: {value}")
            elif isinstance(value, int):
                info_parts.append(f"- {label}: {value} 以上")
            else:
                info_parts.append(f"- {label}: {value}")

        return "\n".join(info_parts)


def get_risk_color_and_badge(risk_level: str) -> tuple:
    """
    リスクレベルに応じた色とバッジを返す

    Args:
        risk_level: リスクレベル

    Returns:
        (color, badge) のタプル
    """
    risk_mapping = {
        "低リスク": ("green", "✅ 安全"),
        "中リスク": ("orange", "⚠️ 注意"),
        "高リスク": ("red", "🔴 警戒"),
        "非常に高リスク": ("darkred", "❌ 危険"),
        "不明": ("gray", "❓ 不明")
    }
    return risk_mapping.get(risk_level, ("gray", "❓ 不明"))


def get_yield_indicator(yield_value: float) -> str:
    """
    配当利回りに応じたインジケーターを返す

    Args:
        yield_value: 配当利回り（%）

    Returns:
        インジケーター文字列
    """
    if yield_value >= 5.0:
        return "🟢"  # 非常に高い
    elif yield_value >= 3.5:
        return "🟡"  # 高い
    elif yield_value >= 2.0:
        return "🟠"  # 普通
    else:
        return "⚪"  # 低い


def get_score_color(score: int) -> str:
    """
    スコアに応じた色を返す

    Args:
        score: 品質スコア（0-100）

    Returns:
        色名
    """
    if score >= 70:
        return "green"
    elif score >= 50:
        return "orange"
    else:
        return "red"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    パーセンテージを見やすくフォーマット

    Args:
        value: 数値
        decimals: 小数点以下の桁数

    Returns:
        フォーマットされた文字列
    """
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"


def format_large_number(value: float) -> str:
    """
    大きな数値を読みやすくフォーマット（億円単位）

    Args:
        value: 数値

    Returns:
        フォーマットされた文字列
    """
    if value is None:
        return "N/A"
    if value >= 10000:
        return f"{value/10000:.1f}兆円"
    else:
        return f"{value:.0f}億円"
