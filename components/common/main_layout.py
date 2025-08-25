#!/usr/bin/env python3
"""
Main Layout Manager
メインレイアウト管理クラス
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QStackedWidget, QDockWidget, QStatusBar, QToolBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from models.app_state import AppState
from models.app_mode import AppMode
from typing import Optional, Dict, Any


class MainLayout(QMainWindow):
    """メインレイアウト管理"""
    
    # シグナル定義
    mode_changed = Signal(object)  # モード変更時
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.main_widget = self
        
        # 現在のコンポーネント
        self.current_sidebar: Optional[QDockWidget] = None
        self.current_main_view: Optional[QWidget] = None
        
        # メインコンテンツスタック
        self.content_stack = QStackedWidget()
        
        self._setup_ui()
        self._setup_window()
    
    def _setup_ui(self):
        """UI初期化"""
        # 中央ウィジェットとしてスタックを設定
        self.setCentralWidget(self.content_stack)
        
        # ステータスバー作成
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - CONFIG Mode")
        
        # ツールバー作成
        self._create_toolbar()
    
    def _setup_window(self):
        """ウィンドウ設定"""
        self.setWindowTitle(self.app_state.get_header_title())
        self.resize(1200, 800)
        
        # ダークテーマ適用
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QDockWidget {
                background-color: #3c3c3c;
                border: 1px solid #555;
            }
            QDockWidget::title {
                background-color: #444;
                padding: 5px;
                border-bottom: 1px solid #555;
            }
            QStatusBar {
                background-color: #333;
                color: #fff;
                border-top: 1px solid #555;
            }
            QToolBar {
                background-color: #444;
                border: none;
                spacing: 5px;
            }
        """)
    
    def _create_toolbar(self):
        """ツールバー作成"""
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # モード切替ボタン
        self.config_action = QAction("CONFIG", self)
        self.config_action.triggered.connect(lambda: self.switch_to_mode(AppMode.CONFIG))
        toolbar.addAction(self.config_action)
        
        self.edit_action = QAction("EDIT", self)
        self.edit_action.triggered.connect(lambda: self.switch_to_mode(AppMode.EDIT))
        toolbar.addAction(self.edit_action)
        
        self.monitor_action = QAction("MONITOR", self)
        self.monitor_action.triggered.connect(lambda: self.switch_to_mode(AppMode.MONITOR))
        toolbar.addAction(self.monitor_action)
        
        toolbar.addSeparator()
        
        # サイドバートグル
        self.sidebar_action = QAction("サイドバー", self)
        self.sidebar_action.setCheckable(True)
        self.sidebar_action.setChecked(self.app_state.sidebar_expanded)
        self.sidebar_action.triggered.connect(self._toggle_sidebar)
        toolbar.addAction(self.sidebar_action)
        
        # 現在のモードをハイライト
        self._update_toolbar_state()
    
    def _update_toolbar_state(self):
        """ツールバー状態更新"""
        # 全てのアクションを無効化してから現在のモードを有効化
        actions = [self.config_action, self.edit_action, self.monitor_action]
        for action in actions:
            action.setEnabled(True)
            action.setStyleSheet("")
        
        # 現在のモードをハイライト
        if self.app_state.current_mode == AppMode.CONFIG:
            self.config_action.setStyleSheet("background-color: #2196F3; color: white; padding: 5px;")
        elif self.app_state.current_mode == AppMode.EDIT:
            self.edit_action.setStyleSheet("background-color: #FF9800; color: white; padding: 5px;")
        elif self.app_state.current_mode == AppMode.MONITOR:
            self.monitor_action.setStyleSheet("background-color: #F44336; color: white; padding: 5px;")
    
    def _toggle_sidebar(self, checked: bool):
        """サイドバートグル"""
        self.app_state.sidebar_expanded = checked
        
        if self.current_sidebar:
            if checked:
                self.current_sidebar.show()
            else:
                self.current_sidebar.hide()
    
    def switch_to_mode(self, mode: AppMode):
        """モード切替"""
        old_mode = self.app_state.current_mode
        self.app_state.current_mode = mode
        
        # ウィンドウタイトル更新
        self.setWindowTitle(self.app_state.get_header_title())
        
        # ステータスバー更新
        self.status_bar.showMessage(f"Mode: {mode.value}")
        
        # ツールバー状態更新
        self._update_toolbar_state()
        
        # シグナル発出
        self.mode_changed.emit(mode)
        
        print(f"Mode switched: {old_mode} -> {mode}")
    
    def set_sidebar(self, sidebar_widget: QWidget, title: str = "Sidebar"):
        """サイドバー設定"""
        # 既存のサイドバーを削除
        if self.current_sidebar:
            self.removeDockWidget(self.current_sidebar)
        
        # 新しいサイドバーをドックウィジェットとして追加
        dock = QDockWidget(title, self)
        dock.setWidget(sidebar_widget)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetClosable)
        
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self.current_sidebar = dock
        
        # 表示状態を同期
        if self.app_state.sidebar_expanded:
            dock.show()
        else:
            dock.hide()
    
    def set_main_view(self, view_widget: QWidget):
        """メインビュー設定"""
        # スタックに追加
        if self.current_main_view:
            self.content_stack.removeWidget(self.current_main_view)
        
        self.content_stack.addWidget(view_widget)
        self.content_stack.setCurrentWidget(view_widget)
        self.current_main_view = view_widget
    
    def get_current_mode(self) -> AppMode:
        """現在のモード取得"""
        return self.app_state.current_mode