#!/usr/bin/env python3
"""
Design System and Style Guide
統一デザインシステムとスタイルガイド
"""

from typing import Dict, Any
from PySide6.QtGui import QFont


class DesignTokens:
    """デザイントークン - 色、フォント、サイズの統一定義"""
    
    # === Color Palette ===
    COLORS = {
        # Primary Colors (ダークモード適応)
        'primary': {
            50: '#E8EAF6',   
            100: '#C5CAE9',
            200: '#9FA8DA', 
            300: '#7986CB',
            400: '#5C6BC0',
            500: '#3F51B5',  # ベース
            600: '#3949AB',
            700: '#303F9F',
            800: '#283593',
            900: '#1A237E'   
        },
        
        # Secondary Colors (控えめなアクセント)
        'secondary': {
            50: '#F3E5F5',
            100: '#E1BEE7', 
            200: '#CE93D8',
            300: '#BA68C8',
            400: '#AB47BC',
            500: '#9C27B0',  # ベース
            600: '#8E24AA',
            700: '#7B1FA2',
            800: '#6A1B9A',
            900: '#4A148C'
        },
        
        # Neutral Colors (グレースケール)
        'neutral': {
            50: '#FAFAFA',
            100: '#F5F5F5',
            200: '#EEEEEE',
            300: '#E0E0E0',
            400: '#BDBDBD',
            500: '#9E9E9E',
            600: '#757575',
            700: '#616161',
            800: '#424242',
            900: '#212121'
        },
        
        # Dark Theme Colors (典型的なダークモード)
        'dark': {
            'surface': '#1E1E1E',      # 背景色
            'surface_1': '#2D2D30',    # 少し明るい背景
            'surface_2': '#3C3C3C',    # さらに明るい背景
            'surface_3': '#4A4A4A',    # 最も明るい背景
            'on_surface': '#FFFFFF',   # テキスト色
            'on_surface_secondary': '#B0B0B0',  # セカンダリテキスト
            'on_surface_disabled': '#6D6D6D',   # 無効テキスト
            'border': '#484848',       # ボーダー色
            'border_light': '#5A5A5A', # 明るいボーダー
            'shadow': 'rgba(0,0,0,0.3)'  # 影
        },
        
        # Semantic Colors (ダークモード適応)
        'semantic': {
            'success': '#4CAF50',      # 成功
            'warning': '#FFA726',      # 警告
            'error': '#EF5350',        # エラー
            'info': '#42A5F5'          # 情報
        }
    }
    
    # === Typography ===
    FONTS = {
        'primary': 'Segoe UI',  # Windows標準
        'monospace': 'Consolas',
        'fallback': ['Arial', 'sans-serif']
    }
    
    FONT_SIZES = {
        'xs': 10,
        'sm': 12,
        'base': 14,
        'lg': 16,
        'xl': 18,
        'xxl': 20,
        'xxxl': 24,
        'display': 32,
        'hero': 48
    }
    
    FONT_WEIGHTS = {
        'normal': 400,
        'medium': 500,
        'bold': 700
    }
    
    # === Spacing ===
    SPACING = {
        'xs': 4,
        'sm': 8,
        'base': 16,
        'lg': 24,
        'xl': 32,
        'xxl': 48,
        'xxxl': 64
    }
    
    # === Border Radius ===
    RADIUS = {
        'xs': 2,
        'sm': 4,
        'base': 8,
        'lg': 12,
        'xl': 16,
        'full': 9999
    }
    
    # === Elevation (Shadow) ===
    ELEVATION = {
        1: 'rgba(0,0,0,0.1) 0px 1px 3px',
        2: 'rgba(0,0,0,0.1) 0px 1px 6px',
        3: 'rgba(0,0,0,0.1) 0px 2px 12px',
        4: 'rgba(0,0,0,0.15) 0px 4px 16px',
        5: 'rgba(0,0,0,0.2) 0px 8px 24px'
    }


class StyleBuilder:
    """スタイル構築ヘルパークラス"""
    
    @staticmethod
    def get_color(category: str, variant: Any = 500) -> str:
        """色を取得"""
        colors = DesignTokens.COLORS.get(category, {})
        if isinstance(colors, dict):
            return colors.get(variant, colors.get(500, '#000000'))
        return colors
    
    @staticmethod
    def get_font(size: str = 'base', weight: str = 'normal') -> QFont:
        """フォントを取得"""
        font = QFont(DesignTokens.FONTS['primary'])
        font.setPointSize(DesignTokens.FONT_SIZES.get(size, 14))
        font.setWeight(DesignTokens.FONT_WEIGHTS.get(weight, 400))
        return font
    
    @staticmethod
    def create_button_style(
        bg_color: str = None,
        text_color: str = 'white',
        border_radius: str = 'base',
        padding: str = 'base',
        hover_bg: str = None,
        disabled_bg: str = None
    ) -> str:
        """ボタンスタイルを生成"""
        bg = bg_color or StyleBuilder.get_color('primary')
        hover = hover_bg or StyleBuilder.get_color('primary', 600)
        disabled = disabled_bg or StyleBuilder.get_color('neutral', 300)
        
        radius = DesignTokens.RADIUS.get(border_radius, 8)
        pad = DesignTokens.SPACING.get(padding, 16)
        
        return f"""
        QPushButton {{
            background-color: {bg};
            color: {text_color};
            border: none;
            border-radius: {radius}px;
            padding: {pad//2}px {pad}px;
            font-weight: 500;
            font-size: 14px;
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
        QPushButton:pressed {{
            background-color: {StyleBuilder.get_color('primary', 700)};
        }}
        QPushButton:disabled {{
            background-color: {disabled};
            color: {StyleBuilder.get_color('neutral', 500)};
        }}
        """
    
    @staticmethod
    def create_card_style(
        bg_color: str = None,
        border_color: str = None,
        border_radius: str = 'base',
        elevation: int = 1
    ) -> str:
        """カードスタイルを生成"""
        bg = bg_color or StyleBuilder.get_color('dark', 'surface_1')
        border = border_color or StyleBuilder.get_color('dark', 'border')
        radius = DesignTokens.RADIUS.get(border_radius, 8)
        shadow = DesignTokens.ELEVATION.get(elevation, '')
        
        return f"""
        QWidget {{
            background-color: {bg};
            border: 1px solid {border};
            border-radius: {radius}px;
            box-shadow: {shadow};
        }}
        """


class ComponentStyles:
    """コンポーネント別スタイル定義"""
    
    @staticmethod
    def header() -> str:
        """ヘッダースタイル"""
        return f"""
        QWidget {{
            background-color: {StyleBuilder.get_color('dark', 'surface_1')};
            border-bottom: 1px solid {StyleBuilder.get_color('dark', 'border')};
            min-height: 80px;
            max-height: 80px;
        }}
        
        QLabel {{
            color: {StyleBuilder.get_color('dark', 'on_surface')};
            font-weight: 700;
            font-size: 24px;
            background: transparent;
            border: none;
        }}
        
        QPushButton {{
            background-color: {StyleBuilder.get_color('primary', 600)};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
            font-size: 13px;
            min-width: 80px;
            min-height: 32px;
        }}
        
        QPushButton:hover {{
            background-color: {StyleBuilder.get_color('primary', 500)};
        }}
        
        QPushButton:pressed {{
            background-color: {StyleBuilder.get_color('primary', 700)};
        }}
        """
    
    @staticmethod
    def footer() -> str:
        """フッタースタイル"""
        return f"""
        QWidget {{
            background-color: {StyleBuilder.get_color('dark', 'surface_1')};
            border-top: 1px solid {StyleBuilder.get_color('dark', 'border')};
            min-height: 50px;
            max-height: 50px;
        }}
        
        QLabel {{
            color: {StyleBuilder.get_color('dark', 'on_surface_secondary')};
            font-size: 14px;
            background: transparent;
            border: none;
        }}
        """
    
    @staticmethod
    def sidebar() -> str:
        """サイドバースタイル"""
        return f"""
        QWidget {{
            background-color: {StyleBuilder.get_color('dark', 'surface')};
            border-right: 1px solid {StyleBuilder.get_color('dark', 'border')};
            min-width: 320px;
            max-width: 380px;
            color: {StyleBuilder.get_color('dark', 'on_surface')};
        }}
        
        QLabel {{
            color: {StyleBuilder.get_color('dark', 'on_surface')};
            font-size: 14px;
        }}
        
        QGroupBox {{
            background-color: {StyleBuilder.get_color('dark', 'surface_1')};
            border: 1px solid {StyleBuilder.get_color('dark', 'border')};
            border-radius: 6px;
            font-weight: 600;
            font-size: 14px;
            color: {StyleBuilder.get_color('dark', 'on_surface')};
            margin-top: 12px;
            padding-top: 10px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 0 10px 0 10px;
        }}
        
        QLineEdit {{
            background-color: {StyleBuilder.get_color('dark', 'surface_2')};
            border: 1px solid {StyleBuilder.get_color('dark', 'border')};
            border-radius: 4px;
            padding: 8px;
            font-size: 14px;
            color: {StyleBuilder.get_color('dark', 'on_surface')};
            min-height: 20px;
        }}
        
        QLineEdit:focus {{
            border-color: {StyleBuilder.get_color('primary', 500)};
        }}
        
        QPushButton {{
            background-color: {StyleBuilder.get_color('primary', 600)};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 10px 16px;
            font-size: 14px;
            font-weight: 500;
            min-height: 32px;
        }}
        
        QPushButton:hover {{
            background-color: {StyleBuilder.get_color('primary', 500)};
        }}
        
        QPushButton:pressed {{
            background-color: {StyleBuilder.get_color('primary', 700)};
        }}
        """
    
    @staticmethod
    def main_content() -> str:
        """メインコンテンツエリアスタイル"""
        return f"""
        QWidget {{
            background-color: {StyleBuilder.get_color('dark', 'surface')};
            color: {StyleBuilder.get_color('dark', 'on_surface')};
        }}
        """


# モード別カラーテーマ
MODE_THEMES = {
    'CONFIG': {
        'primary': StyleBuilder.get_color('primary', 600),
        'accent': StyleBuilder.get_color('primary', 400),
        'text': '#FFFFFF'
    },
    'EDIT': {
        'primary': StyleBuilder.get_color('secondary', 600),
        'accent': StyleBuilder.get_color('secondary', 400), 
        'text': '#FFFFFF'
    },
    'MONITOR': {
        'primary': StyleBuilder.get_color('semantic', 'error'),
        'accent': '#FF6B6B',
        'text': '#FFFFFF'
    }
}