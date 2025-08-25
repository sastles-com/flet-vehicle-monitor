#!/usr/bin/env python3
"""
Unified Framework Components
統一フレームワークコンポーネント - Header, Footer, Sidebar
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPainter, QLinearGradient, QColor, QPalette

from .design_system import StyleBuilder, ComponentStyles, MODE_THEMES, DesignTokens
from models.app_state import AppState, ConnectionStatus
from models.app_mode import AppMode
from typing import Callable, Optional, Dict, Any


class ModernHeader(QWidget):
    """モダンなヘッダーコンポーネント"""
    
    mode_changed = Signal(AppMode)
    menu_toggled = Signal()
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.current_mode = app_state.current_mode
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """UI構築"""
        # 固定高さを削除し、動的サイズ設定
        self.setMinimumHeight(60)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        layout = QHBoxLayout(self)
        # マージンを画面サイズに応じて動的設定（後でresizeEventで調整）
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(20)
        
        # 統一レイアウト: メニューボタン + 左ボタンエリア + タイトル + 右ボタンエリア
        
        # 左側: メニューボタン
        self.menu_btn = QPushButton("☰")
        self.menu_btn.setFixedSize(36, 36)
        self.menu_btn.clicked.connect(self.menu_toggled.emit)
        layout.addWidget(self.menu_btn)
        
        # 左ボタンエリア（EDITモードに戻るボタン）
        left_button_layout = QHBoxLayout()
        left_button_layout.setContentsMargins(0, 0, 0, 0)
        
        if self.current_mode == AppMode.MONITOR:
            self.edit_return_btn = QPushButton("EDITモードに戻る")
            self.edit_return_btn.setMinimumSize(120, 32)
            self.edit_return_btn.clicked.connect(lambda: self.mode_changed.emit(AppMode.EDIT))
            left_button_layout.addWidget(self.edit_return_btn)
        else:
            # 他のモードでは空のスペース
            left_button_layout.addStretch()
        
        self.left_button_widget = QWidget()
        self.left_button_widget.setLayout(left_button_layout)
        self.left_button_widget.setFixedWidth(150)  # 固定幅でバランス調整
        layout.addWidget(self.left_button_widget)
        
        # 中央: タイトルエリア
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(self.title_label)
        
        self.breadcrumb_label = QLabel()
        self.breadcrumb_label.setAlignment(Qt.AlignCenter)
        self.breadcrumb_label.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.7);")
        title_layout.addWidget(self.breadcrumb_label)
        
        title_widget = QWidget()
        title_widget.setLayout(title_layout)
        layout.addWidget(title_widget, 1)  # 拡張してセンタリング
        
        # 右側: START/STOPボタンエリア
        self.action_layout = QHBoxLayout()
        self.action_layout.setSpacing(12)
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        self._create_action_buttons()
        
        action_widget = QWidget()
        action_widget.setLayout(self.action_layout)
        action_widget.setFixedWidth(150)  # 固定幅でバランス調整
        layout.addWidget(action_widget)
        
        self._update_content()
    
    def _create_action_buttons(self):
        """アクションボタン作成"""
        self.action_buttons = {}
        
        # モード別ボタン
        if self.current_mode == AppMode.CONFIG:
            self.action_buttons['edit'] = self._create_mode_button("EDIT", AppMode.EDIT)
        elif self.current_mode == AppMode.EDIT:
            self.action_buttons['config'] = self._create_mode_button("CONFIG", AppMode.CONFIG)
            self.action_buttons['monitor'] = self._create_mode_button("MONITOR", AppMode.MONITOR)
        else:  # MONITOR
            # EDITボタンは左側に配置済みなので、右側にはSTART/STOPのみ
            self.action_buttons['start_stop'] = self._create_start_stop_button()
        
        # ボタンを追加
        for button in self.action_buttons.values():
            self.action_layout.addWidget(button)
    
    def _create_mode_button(self, text: str, target_mode: AppMode) -> QPushButton:
        """モード切替ボタン作成"""
        button = QPushButton(text)
        
        # 固定サイズを削除し、動的サイズ設定
        header_height = max(60, self.height())  # 最小60px
        button_height = int(header_height * 0.45)  # ヘッダー高さの45%
        button_width = max(80, int(button_height * 2.5))  # 高さの2.5倍の幅
        
        button.setMinimumSize(button_width, button_height)
        button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        
        # EDITボタンを特に強調
        if text == "EDIT":
            font_size = max(14, int(button_height * 0.5))
            button.setStyleSheet(f"""
                QPushButton {{
                    font-size: {font_size}px;
                    font-weight: bold;
                    background-color: {StyleBuilder.get_color('secondary', 600)};
                    color: white;
                    border: 2px solid {StyleBuilder.get_color('secondary', 400)};
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: {StyleBuilder.get_color('secondary', 500)};
                    border-color: {StyleBuilder.get_color('secondary', 300)};
                }}
            """)
        else:
            font_size = max(12, int(button_height * 0.4))
            button.setStyleSheet(f"""
                QPushButton {{
                    font-size: {font_size}px;
                    font-weight: 500;
                }}
            """)
        
        button.clicked.connect(lambda: self.mode_changed.emit(target_mode))
        return button
    
    def _create_start_stop_button(self) -> QPushButton:
        """START/STOPボタン作成"""
        self.start_stop_button = QPushButton("START")
        self.start_stop_button.setMinimumSize(80, 36)
        self.start_stop_button.setCheckable(True)  # トグルボタンとして動作
        self.start_stop_button.clicked.connect(self._on_start_stop_clicked)
        
        # 初期スタイル（START状態）
        self._update_start_stop_style(False)
        
        return self.start_stop_button
    
    def _on_start_stop_clicked(self):
        """START/STOPボタンクリック時の処理"""
        is_monitoring = self.start_stop_button.isChecked()
        
        # ボタンテキストと色を切り替え
        if is_monitoring:
            self.start_stop_button.setText("STOP")
        else:
            self.start_stop_button.setText("START")
        
        self._update_start_stop_style(is_monitoring)
        
        print(f"Monitor status changed: {'STOP (monitoring)' if is_monitoring else 'START (stopped)'}")
        
        # TODO: MQTT制御メッセージ送信の実装
    
    def _update_start_stop_style(self, is_monitoring: bool):
        """START/STOPボタンのスタイルを更新"""
        if is_monitoring:
            # STOP状態（赤いボタン）
            self.start_stop_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {DesignTokens.COLORS['red'][600]};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {DesignTokens.COLORS['red'][700]};
                }}
                QPushButton:pressed {{
                    background-color: {DesignTokens.COLORS['red'][800]};
                }}
            """)
        else:
            # START状態（デフォルト色）
            self.start_stop_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {DesignTokens.COLORS['primary'][600]};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {DesignTokens.COLORS['primary'][500]};
                }}
                QPushButton:pressed {{
                    background-color: {DesignTokens.COLORS['primary'][700]};
                }}
            """)
    
    def _apply_styles(self):
        """スタイル適用"""
        self.setStyleSheet(ComponentStyles.header())
        
        # モード別カラーテーマ適用
        theme = MODE_THEMES.get(self.current_mode.value, MODE_THEMES['CONFIG'])
        
        # メニューボタンのスタイル
        self.menu_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {StyleBuilder.get_color('dark', 'surface_2')};
                color: {StyleBuilder.get_color('dark', 'on_surface')};
                border: 1px solid {StyleBuilder.get_color('dark', 'border')};
                border-radius: 4px;
                font-size: 16px;
                font-weight: normal;
            }}
            QPushButton:hover {{
                background-color: {StyleBuilder.get_color('dark', 'surface_3')};
                border-color: {StyleBuilder.get_color('dark', 'border_light')};
            }}
        """)
    
    def _update_content(self):
        """コンテンツ更新"""
        # タイトル更新
        self.title_label.setText(self.app_state.get_header_title())
        
        # ブレッドクラム更新
        mode_desc = {
            AppMode.CONFIG: "システム設定と接続管理",
            AppMode.EDIT: "車両検出領域の編集",
            AppMode.MONITOR: "リアルタイム監視"
        }
        self.breadcrumb_label.setText(mode_desc.get(self.current_mode, ""))
    
    def update_mode(self, new_mode: AppMode):
        """モード更新"""
        self.current_mode = new_mode
        self.app_state.current_mode = new_mode
        
        # 左右のボタンエリアを再構築
        self._update_button_areas()
        
        # アクションボタンを再作成
        self._clear_action_buttons()
        self._create_action_buttons()
        
        # コンテンツ更新
        self._update_content()
        self._apply_styles()
    
    def _update_button_areas(self):
        """左右のボタンエリアを更新"""
        # 左ボタンエリアを更新
        if hasattr(self, 'left_button_widget'):
            # 既存の左ボタンエリアをクリア
            left_button_layout = self.left_button_widget.layout()
            while left_button_layout.count():
                child = left_button_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # EDITモードに戻るボタンを再作成
            if self.current_mode == AppMode.MONITOR:
                self.edit_return_btn = QPushButton("EDITモードに戻る")
                self.edit_return_btn.setMinimumSize(120, 32)
                self.edit_return_btn.clicked.connect(lambda: self.mode_changed.emit(AppMode.EDIT))
                left_button_layout.addWidget(self.edit_return_btn)
            else:
                left_button_layout.addStretch()
        
        # 右ボタンエリア（アクションボタン）はすでに_create_action_buttonsで処理される
    
    def _clear_action_buttons(self):
        """アクションボタンをクリア"""
        for button in self.action_buttons.values():
            self.action_layout.removeWidget(button)
            button.deleteLater()
        self.action_buttons.clear()


class ModernFooter(QWidget):
    """モダンなフッターコンポーネント"""
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """UI構築"""
        # 固定高さを削除し、動的サイズ設定
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 6, 20, 6)  # マージンを動的に調整
        layout.setAlignment(Qt.AlignVCenter)
        
        # 左側: システム情報
        left_layout = QHBoxLayout()
        
        self.debug_label = QLabel(self.app_state.debug_info)
        self.fps_label = QLabel(f"FPS: {self.app_state.frame_rate:.1f}")
        
        left_layout.addWidget(self.debug_label)
        left_layout.addSpacing(20)
        left_layout.addWidget(self.fps_label)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        layout.addWidget(left_widget)
        
        # 右側: 接続状態
        self.status_layout = QHBoxLayout()
        self.status_indicators = {}
        self._create_status_indicators()
        
        status_widget = QWidget()
        status_widget.setLayout(self.status_layout)
        layout.addWidget(status_widget)
    
    def _create_status_indicators(self):
        """接続状態インジケータ作成"""
        services = ['MQTT', 'REST', 'ROS2']
        status = self.app_state.connection_status
        
        for service in services:
            indicator = ConnectionIndicator(service)
            connected = getattr(status, service.lower().replace('rest', 'restapi'), False)
            indicator.update_status(connected)
            
            self.status_indicators[service] = indicator
            self.status_layout.addWidget(indicator)
            
            if service != services[-1]:
                self.status_layout.addSpacing(8)
    
    def _apply_styles(self):
        """スタイル適用"""
        self.setStyleSheet(ComponentStyles.footer())
    
    def update_debug_info(self, info: str):
        """デバッグ情報更新"""
        self.debug_label.setText(info)
    
    def update_fps(self, fps: float):
        """FPS更新"""
        self.fps_label.setText(f"FPS: {fps:.1f}")
    
    def update_connection_status(self, status: ConnectionStatus):
        """接続状態更新"""
        status_map = {
            'MQTT': status.mqtt,
            'REST': status.restapi,
            'ROS2': status.ros2
        }
        
        for service, connected in status_map.items():
            if service in self.status_indicators:
                self.status_indicators[service].update_status(connected)


class ConnectionIndicator(QWidget):
    """接続状態インジケータ"""
    
    def __init__(self, service_name: str, parent=None):
        super().__init__(parent)
        self.service_name = service_name
        self.connected = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI構築"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignCenter)
        
        # 動的サイズ設定
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        
        self.status_dot = QLabel("●")
        self.status_dot.setMinimumSize(12, 12)  # 最小サイズのみ指定
        
        self.service_label = QLabel(self.service_name)
        
        layout.addWidget(self.status_dot)
        layout.addWidget(self.service_label)
        
        self._update_style()
    
    def update_status(self, connected: bool):
        """接続状態更新"""
        self.connected = connected
        self._update_style()
    
    def _update_style(self):
        """スタイル更新"""
        if self.connected:
            bg_color = StyleBuilder.get_color('semantic', 'success')
            dot_color = '#4CAF50'
            text_color = 'white'
        else:
            bg_color = StyleBuilder.get_color('dark', 'surface_2')
            dot_color = StyleBuilder.get_color('dark', 'on_surface_disabled')
            text_color = StyleBuilder.get_color('dark', 'on_surface_secondary')
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 4px;
                padding: 2px 6px;
                border: 1px solid {StyleBuilder.get_color('dark', 'border')};
                min-height: 18px;
            }}
        """)
        
        self.status_dot.setStyleSheet(f"color: {dot_color}; font-size: 10px;")
        self.service_label.setStyleSheet(f"color: {text_color}; font-size: 11px; font-weight: 400;")


class ModernSidebar(QWidget):
    """モダンなサイドバーコンポーネント"""
    
    def __init__(self, app_state: AppState, width: int = 320, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.width = width
        self.expanded = True
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """UI構築"""
        self.setFixedWidth(self.width)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # サイドバーヘッダー
        header_label = QLabel(f"{self.app_state.current_mode.value} 設定")
        header_label.setStyleSheet(f"""
            font-size: 18px; 
            font-weight: bold; 
            color: {StyleBuilder.get_color('dark', 'on_surface')};
            margin-bottom: 8px;
        """)
        layout.addWidget(header_label)
        
        # 区切り線
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"color: {StyleBuilder.get_color('dark', 'border')};")
        layout.addWidget(separator)
        
        # コンテンツエリア（サブクラスで実装）
        self.content_layout = QVBoxLayout()
        self.content_widget = QWidget()
        self.content_widget.setLayout(self.content_layout)
        layout.addWidget(self.content_widget, 1)
    
    def _apply_styles(self):
        """スタイル適用"""
        self.setStyleSheet(ComponentStyles.sidebar())
    
    def toggle_visibility(self):
        """表示切替"""
        self.expanded = not self.expanded
        self.setVisible(self.expanded)


class AppFramework(QWidget):
    """アプリケーションフレームワーク - Header + Content + Footer"""
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        
        # コンポーネント
        self.header = None
        self.footer = None
        self.sidebar = None
        self.main_content = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI構築"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ヘッダー
        self.header = ModernHeader(self.app_state)
        self.header.mode_changed.connect(self._on_mode_changed)
        self.header.menu_toggled.connect(self._on_menu_toggled)
        main_layout.addWidget(self.header)
        
        # コンテンツエリア (サイドバー + メインコンテンツ)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # サイドバー（後で追加）
        # content_layout.addWidget(self.sidebar)
        
        # メインコンテンツエリア
        self.content_container = QWidget()
        self.content_container.setStyleSheet(ComponentStyles.main_content())
        content_layout.addWidget(self.content_container, 1)
        
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget, 1)
        
        # フッター
        self.footer = ModernFooter(self.app_state)
        main_layout.addWidget(self.footer)
    
    def set_sidebar(self, sidebar: ModernSidebar):
        """サイドバー設定"""
        if self.sidebar:
            self.sidebar.setParent(None)
        
        self.sidebar = sidebar
        # コンテンツレイアウトの先頭に挿入
        content_layout = self.content_container.parent().layout()
        content_layout.insertWidget(0, sidebar)
    
    def set_main_content(self, content: QWidget):
        """メインコンテンツ設定"""
        print(f"=== set_main_content called with {type(content).__name__} ===")
        
        if self.main_content:
            print(f"=== Removing existing main_content: {type(self.main_content).__name__} ===")
            self.main_content.setParent(None)
        
        self.main_content = content
        
        # 既存レイアウトをチェック（レイアウト再作成を回避）
        existing_layout = self.content_container.layout()
        if not existing_layout:
            print("=== Creating new layout for content_container ===")
            layout = QVBoxLayout(self.content_container)
            layout.setContentsMargins(0, 0, 0, 0)
        else:
            print("=== Using existing layout, clearing widgets ===")
            layout = existing_layout
            # 既存ウィジェットのみクリア（レイアウトは保持）
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().setParent(None)
        
        layout.addWidget(content)
        print(f"=== Main content set successfully: {type(content).__name__} ===")
        print(f"=== Content container layout items: {layout.count()} ===")
        
        # コンテンツの表示状態を確認
        print(f"=== Content visible: {content.isVisible()} ===")
        print(f"=== Content enabled: {content.isEnabled()} ===")
        print(f"=== Container visible: {self.content_container.isVisible()} ===")
    
    def _on_mode_changed(self, new_mode: AppMode):
        """モード変更イベント"""
        self.app_state.current_mode = new_mode
        self.header.update_mode(new_mode)
        # TODO: サイドバーとメインコンテンツの更新
    
    def _on_menu_toggled(self):
        """メニュー切替イベント"""
        if self.sidebar:
            self.sidebar.toggle_visibility()
    
    def set_sidebar_visible(self, visible: bool):
        """サイドバーの表示/非表示を設定"""
        if self.sidebar:
            self.sidebar.setVisible(visible)
            self.sidebar.expanded = visible