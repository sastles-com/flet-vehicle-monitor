#!/usr/bin/env python3
"""
Vehicle Monitor Application - Modern Framework Version
車両監視システム - モダンフレームワーク版
"""

import sys
from typing import Optional

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QSizePolicy,
                               QGraphicsView, QGraphicsScene, QPushButton, QHBoxLayout, QGroupBox)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont

# データモデル
from models.app_state import AppState
from models.app_mode import AppMode
from models.config_manager import ConfigManager

# 新しいフレームワーク
from components.common.framework import AppFramework, ModernSidebar
from components.common.design_system import StyleBuilder, DesignTokens

# 各モード専用コンポーネント
from components.config.config_sidebar import ConfigSidebar
from components.config.config_view import ConfigView

# サービス
from services.mqtt_service import MQTTService


class ConfigModernSidebar(ModernSidebar):
    """CONFIG用モダンサイドバー"""
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(app_state, width=350, parent=parent)
        self.config_sidebar = None
        self._setup_config_content()
        
        # CONFIGモード用の自動初期化
        self._auto_show_config_dialog()
    
    def _setup_config_content(self):
        """CONFIG専用コンテンツ設定"""
        # 既存のConfigSidebarを統合（完全に表示）
        self.config_sidebar = ConfigSidebar(self.app_state)
        
        # マージンを調整してConfigSidebarを最大表示
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.addWidget(self.config_sidebar)
    
    def _auto_show_config_dialog(self):
        """CONFIGモード起動時にconfig.jsonファイルダイアログを自動表示"""
        def delayed_open():
            import time
            time.sleep(0.5)  # UI初期化完了を待つ
            QTimer.singleShot(100, self._open_config_file_dialog)
        
        import threading
        threading.Thread(target=delayed_open, daemon=True).start()
    
    def _open_config_file_dialog(self):
        """configファイルダイアログを開く"""
        from PySide6.QtWidgets import QFileDialog
        import os
        
        try:
            default_config_folder = "./data"
            
            print(f"CONFIG起動時: 設定選択のため、ファイルダイアログを自動表示します")
            print(f"Opening config file dialog with default folder: {default_config_folder}")
            
            # デフォルトフォルダが存在しない場合は作成を試行
            if not os.path.exists(default_config_folder):
                try:
                    os.makedirs(default_config_folder, exist_ok=True)
                    print(f"Created default folder: {default_config_folder}")
                except Exception as e:
                    print(f"Could not create default folder: {e}")
                    default_config_folder = "."
            
            print("設定ファイル読み込みダイアログを開きます...")
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select config.json to start configuration",
                default_config_folder,
                "JSON files (*.json)"
            )
            
            if file_path:
                self._load_config_file(file_path)
            else:
                print("No config file selected")
                
        except Exception as e:
            print(f"Error opening config file dialog: {e}")
    
    def _load_config_file(self, file_path: str):
        """config.jsonファイルを読み込み"""
        try:
            # ConfigSidebarの機能を使用して設定読み込み
            if self.config_sidebar:
                print(f"Loading config file via ConfigSidebar: {file_path}")
                # ConfigSidebarのload_config_from_fileメソッドを呼び出し（もしあれば）
                # または直接ファイルを読み込む
                self._load_config_directly(file_path)
            
        except Exception as e:
            print(f"Error loading config file: {e}")
    
    def _load_config_directly(self, file_path: str):
        """config.jsonを直接読み込み"""
        try:
            import json
            print(f"Loading config file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            print(f"Config loaded: {config_data}")
            
            # ConfigSidebarにデータを適用
            if self.config_sidebar and hasattr(self.config_sidebar, 'load_config_data'):
                self.config_sidebar.load_config_data(config_data)
            
            # config.json読み込み後、vehicle.jsonダイアログを表示
            self._show_vehicle_dialog_after_config()
            
        except Exception as e:
            print(f"Error loading config file directly: {e}")
    
    def _show_vehicle_dialog_after_config(self):
        """config.json読み込み後にvehicle.jsonダイアログを表示"""
        def delayed_vehicle_dialog():
            import time
            time.sleep(1.0)  # config読み込み完了を少し待つ
            QTimer.singleShot(200, self._open_vehicle_file_dialog)
        
        import threading
        threading.Thread(target=delayed_vehicle_dialog, daemon=True).start()
    
    def _open_vehicle_file_dialog(self):
        """vehicleファイルダイアログを開く"""
        from PySide6.QtWidgets import QFileDialog
        import os
        
        try:
            default_vehicle_folder = r"C:\Users\table0\Desktop\Vehicles"
            
            print(f"CONFIG起動時: vehicle.json選択ダイアログを自動表示します")
            print(f"Opening vehicle file dialog with default folder: {default_vehicle_folder}")
            
            # デフォルトフォルダが存在しない場合は作成を試行
            if not os.path.exists(default_vehicle_folder):
                try:
                    os.makedirs(default_vehicle_folder, exist_ok=True)
                    print(f"Created default vehicle folder: {default_vehicle_folder}")
                except Exception as e:
                    print(f"Could not create default vehicle folder: {e}")
                    default_vehicle_folder = "."
            
            print("vehicle.json読み込みダイアログを開きます...")
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select vehicle.json for configuration",
                default_vehicle_folder,
                "JSON files (*.json)"
            )
            
            if file_path:
                self._load_vehicle_file(file_path)
            else:
                print("No vehicle file selected for CONFIG mode")
                
        except Exception as e:
            print(f"Error opening vehicle file dialog in CONFIG mode: {e}")
    
    def _load_vehicle_file(self, file_path: str):
        """vehicle.jsonファイルを読み込み"""
        try:
            import json
            print(f"CONFIG mode: Loading vehicle file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                vehicle_data = json.load(f)
            
            # 車両名を取得
            vehicle_name = vehicle_data.get("name", "Unknown")
            print(f"CONFIG mode: Vehicle loaded successfully: {vehicle_name}")
            
            # 必要に応じて、ConfigSidebarに車両データを適用
            # （ConfigSidebarに車両情報表示機能があれば追加）
            
        except Exception as e:
            print(f"Error loading vehicle file in CONFIG mode: {e}")
    
    def get_config_sidebar(self):
        """ConfigSidebarインスタンスを取得（外部アクセス用）"""
        return self.config_sidebar


class EditModernSidebar(ModernSidebar):
    """EDIT用モダンサイドバー"""
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(app_state, width=300, parent=parent)
        
        # ファイル選択用
        self.current_vehicle_file_path = None
        self.default_vehicle_folder = r"C:\Users\table0\Desktop\Vehicles"
        
        # 設定データ保存
        self.config_data = None
        self.vehicle_data = None
        
        self._setup_edit_content()
        self._auto_load_config()
        # _auto_show_vehicle_dialog() をコメントアウト（CONFIG→EDIT遷移時に_auto_open_vehicle_dialog()を使用）
        # self._auto_show_vehicle_dialog()
    
    def _setup_edit_content(self):
        """EDIT専用コンテンツ設定（ユーザーフレンドリー版）"""
        from PySide6.QtWidgets import QLabel, QPushButton, QGroupBox, QVBoxLayout, QHBoxLayout
        
        # ステップガイド
        guide_label = QLabel("📝 車のダッシュボード編集")
        guide_label.setStyleSheet(f"""
            QLabel {{
                color: {DesignTokens.COLORS['dark']['text_primary']};
                font-size: 18px;
                font-weight: 600;
                padding: 16px 8px 8px 8px;
            }}
        """)
        self.content_layout.addWidget(guide_label)
        
        # ステップ1: 車の設定ファイル
        step1_group = QGroupBox("ステップ1: 車の種類を選ぶ")
        step1_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: {DesignTokens.COLORS['dark']['text_primary']};
                border: 2px solid {DesignTokens.COLORS['dark']['border']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: {DesignTokens.COLORS['dark']['primary']};
            }}
        """)
        step1_layout = QVBoxLayout()
        
        # 現在の車両情報表示
        self.vehicle_info_label = QLabel("🚗 まだ車が選択されていません")
        self.vehicle_info_label.setStyleSheet(f"""
            QLabel {{
                color: {DesignTokens.COLORS['dark']['text_secondary']};
                font-size: 13px;
                padding: 8px 12px;
                background-color: {DesignTokens.COLORS['dark']['surface_1']};
                border-radius: 6px;
                border-left: 3px solid {DesignTokens.COLORS['dark']['warning']};
            }}
        """)
        step1_layout.addWidget(self.vehicle_info_label)
        
        # 車選択ボタン
        self.load_vehicle_btn = QPushButton("🔍 車の種類を選ぶ")
        self.load_vehicle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DesignTokens.COLORS['dark']['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {DesignTokens.COLORS['dark']['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {DesignTokens.COLORS['dark']['primary_pressed']};
            }}
        """)
        self.load_vehicle_btn.clicked.connect(self._on_load_vehicle_clicked)
        step1_layout.addWidget(self.load_vehicle_btn)
        
        step1_group.setLayout(step1_layout)
        self.content_layout.addWidget(step1_group)
        
        # ステップ2: 編集モード（将来用）
        step2_group = QGroupBox("ステップ2: 編集する項目を選ぶ")
        step2_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: {DesignTokens.COLORS['dark']['text_secondary']};
                border: 2px solid {DesignTokens.COLORS['dark']['border_secondary']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: {DesignTokens.COLORS['dark']['text_secondary']};
            }}
        """)
        step2_layout = QVBoxLayout()
        
        # 編集項目説明
        edit_info_label = QLabel("⏳ 車を選択すると編集できます")
        edit_info_label.setStyleSheet(f"""
            QLabel {{
                color: {DesignTokens.COLORS['dark']['text_secondary']};
                font-size: 13px;
                padding: 8px 12px;
                background-color: {DesignTokens.COLORS['dark']['surface_1']};
                border-radius: 6px;
                text-align: center;
            }}
        """)
        step2_layout.addWidget(edit_info_label)
        
        # 将来の編集ボタン（現在は無効化）
        edit_buttons_layout = QVBoxLayout()
        
        meter_btn = QPushButton("🌡️ メーターの位置を決める")
        meter_btn.setEnabled(False)
        meter_btn.setStyleSheet(self._get_disabled_button_style())
        edit_buttons_layout.addWidget(meter_btn)
        
        icon_btn = QPushButton("⚠️ アイコンの位置を決める")
        icon_btn.setEnabled(False) 
        icon_btn.setStyleSheet(self._get_disabled_button_style())
        edit_buttons_layout.addWidget(icon_btn)
        
        text_btn = QPushButton("📝 文字の位置を決める")
        text_btn.setEnabled(False)
        text_btn.setStyleSheet(self._get_disabled_button_style())
        edit_buttons_layout.addWidget(text_btn)
        
        step2_layout.addLayout(edit_buttons_layout)
        step2_group.setLayout(step2_layout)
        self.content_layout.addWidget(step2_group)
        
        # ヒント表示
        hint_label = QLabel("💡 ヒント: 最初に「車の種類を選ぶ」ボタンを押してください")
        hint_label.setStyleSheet(f"""
            QLabel {{
                color: {DesignTokens.COLORS['dark']['text_secondary']};
                font-size: 12px;
                padding: 12px;
                background-color: {DesignTokens.COLORS['dark']['surface_1']};
                border-radius: 6px;
                border-left: 3px solid {DesignTokens.COLORS['dark']['info']};
            }}
        """)
        self.content_layout.addWidget(hint_label)
        
        # ストレッチ
        self.content_layout.addStretch()
    
    def _get_disabled_button_style(self):
        """無効化されたボタンのスタイル"""
        return f"""
            QPushButton {{
                background-color: {DesignTokens.COLORS['dark']['surface_1']};
                color: {DesignTokens.COLORS['dark']['text_disabled']};
                border: 1px solid {DesignTokens.COLORS['dark']['border_secondary']};
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
                margin: 2px 0;
            }}
        """
    
    def _auto_load_config(self):
        """config.jsonを自動読み込み"""
        import os
        import json
        
        config_paths = ["./data/config.json", "../data/config.json"]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self.config_data = json.load(f)
                    
                    print(f"EDIT mode: Auto-loaded config from {config_path}")
                    return
                    
                except Exception as e:
                    print(f"Auto-load config error from {config_path}: {e}")
                    continue
        
        print("EDIT mode: No config.json found")
        self.config_data = None
    
    def _auto_show_vehicle_dialog(self):
        """EDITモード開始時にvehicle.jsonファイルダイアログを自動表示"""
        def delayed_open():
            import time
            time.sleep(0.5)  # UI初期化完了を待つ
            QTimer.singleShot(100, self._open_vehicle_file_dialog)
        
        import threading
        threading.Thread(target=delayed_open, daemon=True).start()
    
    def _auto_open_vehicle_dialog(self):
        """外部から呼び出し可能なvehicle.jsonダイアログ自動開放（CONFIG→EDIT遷移後用）"""
        print("=== _auto_open_vehicle_dialog called from CONFIG→EDIT transition ===")
        def delayed_open():
            import time
            time.sleep(0.5)  # サイドバー展開完了を待つ
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._open_vehicle_file_dialog)
        
        import threading
        threading.Thread(target=delayed_open, daemon=True).start()
    
    def _open_vehicle_file_dialog(self):
        """vehicleファイルダイアログを開く"""
        from PySide6.QtWidgets import QFileDialog
        import os
        
        try:
            print(f"Opening vehicle file dialog with default folder: {self.default_vehicle_folder}")
            
            # デフォルトフォルダが存在しない場合は作成を試行
            if not os.path.exists(self.default_vehicle_folder):
                try:
                    os.makedirs(self.default_vehicle_folder, exist_ok=True)
                    print(f"Created default folder: {self.default_vehicle_folder}")
                except Exception as e:
                    print(f"Could not create default folder: {e}")
                    self.default_vehicle_folder = "."
            
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select vehicle.json to start editing",
                self.default_vehicle_folder,
                "JSON files (*.json)"
            )
            
            if file_path:
                self._load_vehicle_file(file_path)
            else:
                print("No vehicle file selected")
                
        except Exception as e:
            print(f"Error opening vehicle file dialog: {e}")
    
    def _load_vehicle_file(self, file_path: str):
        """vehicle.jsonファイルを読み込み"""
        try:
            import json
            print(f"Loading vehicle file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                self.vehicle_data = json.load(f)
            
            # ファイルパスを記憶
            self.current_vehicle_file_path = file_path
            
            # 車両名をUIに反映（ユーザーフレンドリー表示）
            vehicle_name = self.vehicle_data.get("name", "Unknown")
            self.vehicle_info_label.setText(f"🚗 選択中の車: {vehicle_name}")
            self.vehicle_info_label.setStyleSheet(f"""
                QLabel {{
                    color: {DesignTokens.COLORS['dark']['text_primary']};
                    font-size: 13px;
                    font-weight: 600;
                    padding: 8px 12px;
                    background-color: {DesignTokens.COLORS['dark']['success']};
                    border-radius: 6px;
                    border-left: 3px solid {DesignTokens.COLORS['dark']['success_border']};
                }}
            """)
            
            print(f"Vehicle loaded successfully: {vehicle_name}")
            
            # RestAPIで画像を取得
            self._fetch_full_image()
            
            # 将来的にはここでステップ2のボタンを有効化する予定
            
        except Exception as e:
            print(f"Error loading vehicle file: {e}")
            self.vehicle_info_label.setText("車両: 読み込みエラー")
    
    def _on_load_vehicle_clicked(self):
        """Load Vehicleボタンクリック時の処理"""
        self._open_vehicle_file_dialog()
    
    def _fetch_full_image(self):
        """RestAPIでfull_imageを取得"""
        if not self.config_data:
            print("No config data available for RestAPI")
            return
        
        restapi_config = self.config_data.get("RestAPI", {})
        if not restapi_config.get("host") or not restapi_config.get("port"):
            print("RestAPI config incomplete")
            return
        
        def fetch_in_background():
            try:
                import requests
                host = restapi_config.get("host")
                port = restapi_config.get("port")
                url = f"http://{host}:{port}/full_image"
                
                print(f"Fetching full_image from {url}")
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print("Full image loaded successfully from RestAPI")
                    
                    # EDITメインビューに画像を送信
                    QTimer.singleShot(0, lambda: self._notify_image_loaded(response.content))
                    
                else:
                    print(f"RestAPI error: {response.status_code}")
                    
            except Exception as e:
                print(f"Error fetching full_image: {e}")
        
        # バックグラウンドで取得
        import threading
        threading.Thread(target=fetch_in_background, daemon=True).start()
    
    def _notify_image_loaded(self, image_data: bytes):
        """画像読み込み完了をメインビューに通知"""
        try:
            # 親アプリケーションを取得してEDITメインビューにアクセス
            if hasattr(self.app_state, 'main_application'):
                main_app = self.app_state.main_application
                if main_app and hasattr(main_app, 'mode_components'):
                    from models.app_mode import AppMode
                    edit_main_view = main_app.mode_components.get(AppMode.EDIT, {}).get('main_view')
                    if edit_main_view and hasattr(edit_main_view, 'load_full_image'):
                        edit_main_view.load_full_image(image_data)
                        return
            
            print("Could not find EDIT main view to send image data")
            
        except Exception as e:
            print(f"Error notifying image loaded: {e}")
    
    def set_main_application(self, main_app):
        """メインアプリケーションの参照を設定"""
        self.app_state.main_application = main_app


class MonitorModernSidebar(ModernSidebar):
    """MONITOR用モダンサイドバー"""
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(app_state, width=280, parent=parent)
        self._setup_monitor_content()
    
    def _setup_monitor_content(self):
        """MONITOR専用コンテンツ設定"""
        from PySide6.QtWidgets import QLabel, QPushButton, QGroupBox, QVBoxLayout
        
        # 監視制御グループ
        control_group = QGroupBox("監視制御")
        control_layout = QVBoxLayout()
        
        # START/STOPボタン
        self.start_stop_btn = QPushButton("START")
        self.start_stop_btn.setStyleSheet(StyleBuilder.create_button_style(
            bg_color=StyleBuilder.get_color('semantic', 'success')
        ))
        control_layout.addWidget(self.start_stop_btn)
        
        control_group.setLayout(control_layout)
        self.content_layout.addWidget(control_group)
        
        # 統計情報グループ
        stats_group = QGroupBox("統計情報")
        stats_layout = QVBoxLayout()
        
        self.fps_label = QLabel("FPS: 0.0")
        self.frame_count_label = QLabel("Frame Count: 0")
        
        stats_layout.addWidget(self.fps_label)
        stats_layout.addWidget(self.frame_count_label)
        
        stats_group.setLayout(stats_layout)
        self.content_layout.addWidget(stats_group)
        
        # ストレッチ
        self.content_layout.addStretch()


class ModernConfigMainView(QWidget):
    """CONFIG用モダンメインビュー"""
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.config_view = None
        self.image_label = None
        self._setup_ui()
    
    def _setup_ui(self):
        """UI設定（MONITORモードと統一）"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)
        
        # 画像表示エリア（MONITORと同様の構造）
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # setScaledContentsをFalseに変更（手動スケーリング使用）
        self.image_label.setScaledContents(False)
        
        # 初期プレースホルダー画像を設定
        self._create_placeholder_image()
        
        # フレーム・ボーダーを設定（MONITORと統一）
        self.image_label.setStyleSheet(f"""
            QLabel {{
                background-color: {DesignTokens.COLORS['dark']['surface_1']};
                border: 2px solid {DesignTokens.COLORS['dark']['border']};
                border-radius: 12px;
                padding: 8px;
            }}
        """)
        
        layout.addWidget(self.image_label)
        
        # 既存のConfigViewも隠して保持（MQTT接続機能用）
        self.config_view = ConfigView(self.app_state)
        self.config_view.hide()
    
    def _create_placeholder_image(self):
        """プレースホルダー画像を作成（MONITORモードと統一）"""
        try:
            print(f"=== Creating CONFIG placeholder image ===")
            print(f"=== Widget hierarchy: {type(self).__name__} -> {type(self.image_label).__name__} ===")
            
            # 固定サイズでプレースホルダー画像を作成
            placeholder = QPixmap(800, 600)
            placeholder.fill(QColor('#2D2D30'))  # 統一されたダークグレー
            
            # 中央にテキストを描画
            painter = QPainter(placeholder)
            painter.setPen(QColor('#FFFFFF'))
            painter.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
            painter.drawText(placeholder.rect(), Qt.AlignmentFlag.AlignCenter, "CONFIG画面")
            
            # サブテキスト
            painter.setFont(QFont("Segoe UI", 16))
            painter.setPen(QColor('#B0B0B0'))
            text_rect = placeholder.rect()
            text_rect.setTop(text_rect.center().y() + 50)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "設定ファイルを読み込んでください")
            
            # 詳細テキスト
            painter.setFont(QFont("Segoe UI", 14))
            painter.setPen(QColor('#909090'))
            detail_rect = placeholder.rect()
            detail_rect.setTop(text_rect.bottom() + 20)
            painter.drawText(detail_rect, Qt.AlignmentFlag.AlignCenter, "サイドバーから「Config.json読み込み」ボタンを使用")
            painter.end()
            
            # プレースホルダー画像を設定
            self.image_label.setPixmap(placeholder)
            self.image_label.setText("")  # テキストをクリア
            
            print(f"=== CONFIG placeholder image created and set ===")
            print(f"=== Placeholder pixmap size: {placeholder.size().width()}x{placeholder.size().height()} ===")
            
        except Exception as e:
            print(f"=== ERROR: CONFIG placeholder image creation error: {e} ===")
            import traceback
            traceback.print_exc()
            # フォールバック: テキストのみ表示
            self.image_label.setText("CONFIG画面\n設定ファイルを読み込んでください")
            self.image_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {DesignTokens.COLORS['dark']['surface_1']};
                    border: 2px solid {DesignTokens.COLORS['dark']['border']};
                    border-radius: 12px;
                    color: #FFFFFF;
                    font-size: 18px;
                    padding: 40px;
                }}
            """)
    
    def update_mqtt_image(self, image_data: str):
        """MQTT画像データを受信して表示（MONITORと統一された手動スケーリング）"""
        from PySide6.QtGui import QPixmap
        import base64
        
        print(f"=== CONFIG update_mqtt_image called with data length: {len(image_data)} ===")
        print(f"=== Image data preview: {image_data[:100]}... ===")
        
        try:
            # Base64デコード
            image_bytes = base64.b64decode(image_data)
            print(f"=== Base64 decoded successfully, binary size: {len(image_bytes)} bytes ===")
            
            # QPixmapに変換
            original_pixmap = QPixmap()
            if original_pixmap.loadFromData(image_bytes):
                print(f"=== Original pixmap size: {original_pixmap.size().width()}x{original_pixmap.size().height()} ===")
                print(f"=== Label geometry: {self.image_label.geometry()} ===")
                
                # ラベルの利用可能サイズを取得（padding考慮）
                label_size = self.image_label.size()
                available_width = label_size.width() - 20  # padding分を引く
                available_height = label_size.height() - 20
                print(f"=== Available display size: {available_width}x{available_height} ===")
                
                # アスペクト比を保って最適サイズを計算
                scaled_pixmap = original_pixmap.scaled(
                    available_width, available_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                print(f"=== Scaled to: {scaled_pixmap.size().width()}x{scaled_pixmap.size().height()} ===")
                
                # スケーリングされた画像を設定
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.setText("")
                print(f"=== SUCCESS: CONFIG画像を表示しました (サイズ: {len(image_bytes)} bytes) ===")
            else:
                print("=== ERROR: CONFIG画像のQPixmapへの変換に失敗しました ===")
                self._create_error_placeholder()
                
        except Exception as e:
            print(f"=== EXCEPTION: CONFIG画像表示エラー: {e} ===")
            import traceback
            traceback.print_exc()
            self._create_error_placeholder()
    
    def _create_error_placeholder(self):
        """エラー時のプレースホルダー画像作成"""
        try:
            placeholder = QPixmap(800, 600)
            placeholder.fill(QColor('#2D2D30'))
            
            painter = QPainter(placeholder)
            painter.setPen(QColor('#FF5722'))  # エラー色（オレンジレッド）
            painter.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
            painter.drawText(placeholder.rect(), Qt.AlignmentFlag.AlignCenter, "画像読み込みエラー")
            
            painter.setFont(QFont("Segoe UI", 14))
            painter.setPen(QColor('#B0B0B0'))
            text_rect = placeholder.rect()
            text_rect.setTop(text_rect.center().y() + 40)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "MQTT画像データの処理に失敗しました")
            painter.end()
            
            self.image_label.setPixmap(placeholder)
            self.image_label.setText("")
            
        except Exception as e:
            print(f"Error placeholder creation failed: {e}")
            # 最終フォールバック
            self.image_label.setText("CONFIG画面\n画像読み込みエラー")
            self.image_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {DesignTokens.COLORS['dark']['surface_1']};
                    border: 2px solid {DesignTokens.COLORS['dark']['border']};
                    border-radius: 12px;
                    color: #FF5722;
                    font-size: 18px;
                    padding: 40px;
                }}
            """)
    
    def get_config_view(self):
        """ConfigViewインスタンスを取得（外部アクセス用）"""
        return self.config_view


class ModernEditImageCanvas(QGraphicsView):
    """フルサイズ画像編集用キャンバス（main.pyのImageCanvasをベース）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # 画像関連
        self.image_item = None
        self.original_pixmap = None
        self.current_scale = 1.0  # フルサイズ表示では常に1.0
        
        # フルサイズ画像サイズ（config.jsonから設定）
        self.full_image_width = 2304  # デフォルト値
        self.full_image_height = 1296  # デフォルト値
        
        # 右クリックパン移動用の変数
        self._right_mouse_pressed = False
        self._last_pan_point = None
        
        # 原寸表示用ビュー設定
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        # スクロールバーを必要時表示（原寸表示のため）
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # モダンデザイン適用
        self.setStyleSheet(f"""
            QGraphicsView {{
                background-color: {DesignTokens.COLORS['dark']['surface_2']};
                border: 2px solid {DesignTokens.COLORS['dark']['border']};
                border-radius: 12px;
            }}
            QScrollBar:vertical {{
                background: {DesignTokens.COLORS['dark']['surface_1']};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {DesignTokens.COLORS['dark']['text_secondary']};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar:horizontal {{
                background: {DesignTokens.COLORS['dark']['surface_1']};
                height: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background: {DesignTokens.COLORS['dark']['text_secondary']};
                border-radius: 6px;
                min-width: 20px;
            }}
        """)
    
    def set_full_image_size(self, width: int, height: int):
        """フルサイズ画像サイズを設定"""
        self.full_image_width = width
        self.full_image_height = height
        print(f"Full image size set to: {width}x{height}")
        
    def load_image_from_data(self, image_data: bytes):
        """バイナリデータから画像を読み込んで原寸表示"""
        try:
            print(f"ModernEditImageCanvas: Loading image from data ({len(image_data)} bytes)")
            
            # バイナリデータをQPixmapに変換
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                self.original_pixmap = pixmap
                
                # 既存の画像アイテムを削除
                if self.image_item:
                    self.scene.removeItem(self.image_item)
                    
                # 新しい画像アイテムを追加
                self.image_item = self.scene.addPixmap(self.original_pixmap)
                # 画像を最背景に設定
                self.image_item.setZValue(-1000)
                
                # 原寸表示（スケール1.0固定）
                self.display_at_original_size()
                
                print(f"ModernEditImageCanvas: Image loaded successfully (size: {pixmap.width()}x{pixmap.height()})")
                return True
            else:
                print("ModernEditImageCanvas: Failed to create pixmap from data")
                return False
                
        except Exception as e:
            print(f"ModernEditImageCanvas: Error loading image: {e}")
            return False
    
    def load_image_from_file(self, file_path: str):
        """ファイルパスから画像を読み込んで原寸表示"""
        try:
            print(f"ModernEditImageCanvas: Loading image from file: {file_path}")
            
            self.original_pixmap = QPixmap(file_path)
            if self.original_pixmap.isNull():
                print("ModernEditImageCanvas: Failed to load image file")
                return False
                
            # 既存の画像アイテムを削除
            if self.image_item:
                self.scene.removeItem(self.image_item)
                
            # 新しい画像アイテムを追加
            self.image_item = self.scene.addPixmap(self.original_pixmap)
            # 画像を最背景に設定
            self.image_item.setZValue(-1000)
            
            # 原寸表示（スケール1.0固定）
            self.display_at_original_size()
            
            print(f"ModernEditImageCanvas: Image loaded successfully from file")
            return True
            
        except Exception as e:
            print(f"ModernEditImageCanvas: Error loading image from file: {e}")
            return False
        
    def display_at_original_size(self):
        """画像を原寸（1:1）で表示"""
        if not self.original_pixmap:
            return
            
        # 原寸表示（スケール1.0固定）
        new_scale = 1.0
        
        # ビューのトランスフォームをリセットして1.0スケール適用
        self.resetTransform()
        self.scale(new_scale, new_scale)
        
        self.current_scale = new_scale
        
        # シーンのサイズを画像サイズに合わせる
        if self.image_item:
            self.scene.setSceneRect(self.image_item.boundingRect())
            
        print("ModernEditImageCanvas: Displaying at original size (1:1)")
    
    def fit_image_to_view(self):
        """画像をビューに収まるようにスケーリング"""
        if not self.original_pixmap:
            return
            
        # ビューサイズを取得
        view_rect = self.viewport().rect()
        image_rect = self.original_pixmap.rect()
        
        # アスペクト比を保持してスケール計算
        scale_x = view_rect.width() / image_rect.width()
        scale_y = view_rect.height() / image_rect.height()
        scale = min(scale_x, scale_y) * 0.9  # 少し余白を残す
        
        # スケール適用
        self.resetTransform()
        self.scale(scale, scale)
        self.current_scale = scale
        
        print(f"ModernEditImageCanvas: Fit to view with scale: {scale}")
    
    def get_current_scale(self) -> float:
        """現在のスケールを取得"""
        return self.current_scale
    
    def wheelEvent(self, event):
        """マウスホイールによるスクロール"""
        try:
            from PySide6.QtCore import Qt
            
            # ホイールの回転量を取得
            delta = event.angleDelta().y()
            scroll_amount = 30  # スクロール量（ピクセル）
            
            # Ctrlキーが押されている場合は水平スクロール
            if event.modifiers() & Qt.ControlModifier:
                # 水平スクロール
                h_scrollbar = self.horizontalScrollBar()
                if delta > 0:
                    h_scrollbar.setValue(h_scrollbar.value() - scroll_amount)
                else:
                    h_scrollbar.setValue(h_scrollbar.value() + scroll_amount)
            else:
                # 通常の縦スクロール
                v_scrollbar = self.verticalScrollBar()
                if delta > 0:
                    # 上にスクロール
                    v_scrollbar.setValue(v_scrollbar.value() - scroll_amount)
                else:
                    # 下にスクロール
                    v_scrollbar.setValue(v_scrollbar.value() + scroll_amount)
            
            # イベントを受け入れる
            event.accept()
            
        except Exception as e:
            print(f"ModernEditImageCanvas: Wheel event error: {e}")
            # エラー時は標準の処理にフォールバック
            super().wheelEvent(event)
    
    def mousePressEvent(self, event):
        """マウスボタンが押された時の処理"""
        from PySide6.QtCore import Qt
        
        if event.button() == Qt.MouseButton.RightButton:
            # 右クリック開始 - パン移動モード
            self._right_mouse_pressed = True
            self._last_pan_point = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)  # 掴んでいる状態のカーソル
            event.accept()
        else:
            # 左クリックなど他のボタンは標準処理
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """マウス移動時の処理"""
        from PySide6.QtCore import Qt
        
        if self._right_mouse_pressed and self._last_pan_point:
            # 右クリックドラッグによるパン移動
            delta = event.pos() - self._last_pan_point
            self._last_pan_point = event.pos()
            
            # スクロールバーを移動してパン効果を実現
            h_scrollbar = self.horizontalScrollBar()
            v_scrollbar = self.verticalScrollBar()
            
            h_scrollbar.setValue(h_scrollbar.value() - delta.x())
            v_scrollbar.setValue(v_scrollbar.value() - delta.y())
            
            event.accept()
        else:
            # 右クリック以外は標準処理
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """マウスボタンが離された時の処理"""
        from PySide6.QtCore import Qt
        
        if event.button() == Qt.MouseButton.RightButton:
            # 右クリック終了 - パン移動モード解除
            self._right_mouse_pressed = False
            self._last_pan_point = None
            self.setCursor(Qt.CursorShape.ArrowCursor)  # 通常のカーソルに戻す
            event.accept()
        else:
            # 左クリックなど他のボタンは標準処理
            super().mouseReleaseEvent(event)
    
    def resizeEvent(self, event):
        """ウィンドウリサイズ時の処理"""
        super().resizeEvent(event)
        # 原寸表示モードではリサイズ時の自動調整を行わない


class ModernEditMainView(QWidget):
    """EDIT用モダンメインビュー（フルサイズ画像表示対応）"""
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        
        # 画像表示関連
        self.image_canvas = None
        self.vehicle_data = None
        self._priority_image_loaded = False  # RestAPI優先画像ロード済みフラグ
        self._mqtt_paused = False  # MQTT画像処理一時停止フラグ
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # ツールバー（将来の機能拡張用）
        toolbar_layout = QHBoxLayout()
        
        # 現在の表示モード表示
        mode_label = QLabel("フルサイズ編集モード")
        mode_label.setStyleSheet(f"""
            QLabel {{
                color: {DesignTokens.COLORS['dark']['text_primary']};
                font-size: 14px;
                font-weight: 600;
                padding: 8px 12px;
                background-color: {DesignTokens.COLORS['dark']['surface_1']};
                border-radius: 6px;
            }}
        """)
        toolbar_layout.addWidget(mode_label)
        
        toolbar_layout.addStretch()
        
        # 表示切り替えボタン（将来用）
        fit_button = QPushButton("画面に合わせる")
        fit_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {DesignTokens.COLORS['dark']['surface_1']};
                color: {DesignTokens.COLORS['dark']['text_primary']};
                border: 1px solid {DesignTokens.COLORS['dark']['border']};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {DesignTokens.COLORS['dark']['surface_2']};
            }}
        """)
        fit_button.clicked.connect(self._fit_image_to_view)
        toolbar_layout.addWidget(fit_button)
        
        original_button = QPushButton("原寸表示")
        original_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {DesignTokens.COLORS['dark']['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {DesignTokens.COLORS['dark']['primary_hover']};
            }}
        """)
        original_button.clicked.connect(self._display_at_original_size)
        toolbar_layout.addWidget(original_button)
        
        layout.addLayout(toolbar_layout)
        
        # フルサイズ画像キャンバス
        self.image_canvas = ModernEditImageCanvas()
        self.image_canvas.setMinimumSize(800, 600)
        self.image_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 初期プレースホルダー表示
        self._show_placeholder()
        
        layout.addWidget(self.image_canvas)
    
    def _show_placeholder(self):
        """プレースホルダー表示を設定"""
        try:
            # シーンをクリアしてプレースホルダー画像を作成
            self.image_canvas.scene.clear()
            
            # プレースホルダー画像を作成
            placeholder = QPixmap(1200, 800)
            placeholder.fill(QColor(DesignTokens.COLORS['dark']['surface_1']))
            
            # 中央にテキストを描画
            painter = QPainter(placeholder)
            painter.setPen(QColor(DesignTokens.COLORS['dark']['text_primary']))
            painter.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
            painter.drawText(placeholder.rect(), Qt.AlignmentFlag.AlignCenter, "フルサイズ編集モード")
            
            # サブテキスト
            painter.setFont(QFont("Segoe UI", 20))
            painter.setPen(QColor(DesignTokens.COLORS['dark']['text_secondary']))
            text_rect = placeholder.rect()
            text_rect.setTop(text_rect.center().y() + 60)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, 
                           "CONFIG→EDIT遷移で画像を自動取得\nvehicle.json読み込みで編集可能")
            painter.end()
            
            # プレースホルダー画像をシーンに追加
            placeholder_item = self.image_canvas.scene.addPixmap(placeholder)
            placeholder_item.setZValue(-1000)
            
            # シーンサイズを調整
            self.image_canvas.scene.setSceneRect(placeholder.rect())
            
        except Exception as e:
            print(f"Placeholder creation error: {e}")
    
    def _fit_image_to_view(self):
        """画像をビューに収まるように表示"""
        if self.image_canvas:
            self.image_canvas.fit_image_to_view()
    
    def _display_at_original_size(self):
        """画像を原寸（1:1）で表示"""
        if self.image_canvas:
            self.image_canvas.display_at_original_size()
    
    def load_vehicle_json(self, vehicle_data: dict):
        """vehicle.jsonデータを読み込み"""
        self.vehicle_data = vehicle_data
        vehicle_name = vehicle_data.get("name", "Unknown")
        print(f"EDIT main view: Vehicle data loaded for {vehicle_name}")
        # TODO: 将来的にvehicle.jsonの図形データを表示
    
    def load_full_image(self, image_data: bytes):
        """RestAPIまたはMQTTから取得した画像を表示（フルサイズ対応）"""
        try:
            print(f"EDIT main view: Loading full image ({len(image_data)} bytes)")
            
            # ImageCanvasにフルサイズ画像をロード
            if self.image_canvas.load_image_from_data(image_data):
                print("EDIT main view: Full-size image loaded successfully")
                return True
            else:
                print("EDIT main view: Failed to load full-size image")
                return False
                
        except Exception as e:
            print(f"EDIT main view: Image loading error: {e}")
            return False
    
    def update_mqtt_image(self, image_data: bytes):
        """MQTTから受信した画像を表示 - RestAPI優先画像がロード済み、またはMQTT一時停止の場合はスキップ"""
        # MQTT一時停止中の場合、MQTT画像を無視
        if self._mqtt_paused:
            print("EDIT main view: Skipping MQTT image - MQTT paused for RestAPI priority loading")
            return True
            
        # RestAPI優先画像がロード済みの場合、MQTT画像を無視
        if self._priority_image_loaded:
            print("EDIT main view: Skipping MQTT image - RestAPI priority image already loaded")
            return True
            
        print("EDIT main view: Processing MQTT image (no priority image loaded yet)")
        return self.load_full_image(image_data)
    
    def load_priority_image(self, image_data: bytes):
        """RestAPI優先画像をロード（MQTT より優先）"""
        try:
            print(f"EDIT main view: Loading RestAPI priority image ({len(image_data)} bytes)")
            
            # ImageCanvasに優先画像をロード
            if self.image_canvas and self.image_canvas.load_image_from_data(image_data):
                self._priority_image_loaded = True  # 優先画像ロード完了フラグ設定
                print("EDIT main view: RestAPI priority image loaded successfully - MQTT updates disabled")
                return True
            else:
                print("EDIT main view: Failed to load RestAPI priority image")
                return False
                
        except Exception as e:
            print(f"EDIT main view: Error loading RestAPI priority image - {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def pause_mqtt_updates(self):
        """MQTT画像更新を一時停止"""
        self._mqtt_paused = True
        print("EDIT main view: MQTT image updates paused for RestAPI priority loading")
    
    def resume_mqtt_updates(self):
        """MQTT画像更新を再開"""
        self._mqtt_paused = False
        print("EDIT main view: MQTT image updates resumed")
    
    def set_full_image_size(self, width: int, height: int):
        """フルサイズ画像サイズを設定（config.jsonから）"""
        if self.image_canvas:
            self.image_canvas.set_full_image_size(width, height)


class ModernMonitorMainView(QWidget):
    """MONITOR用モダンメインビュー"""
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        
        # 画像表示関連
        self.current_image = None
        self.image_label = None
        self.image_count = 0
        self.last_image_time = ""
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)
        
        # 画像表示エリア
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # setScaledContentsをFalseに変更（手動スケーリング使用）
        self.image_label.setScaledContents(False)
        
        # 初期プレースホルダー画像を設定
        self._create_placeholder_image()
        
        # フレーム・ボーダーを設定
        self.image_label.setStyleSheet(f"""
            QLabel {{
                background-color: {DesignTokens.COLORS['dark']['surface_1']};
                border: 2px solid {DesignTokens.COLORS['dark']['border']};
                border-radius: 12px;
                padding: 8px;
            }}
        """)
        
        layout.addWidget(self.image_label)
    
    def _create_placeholder_image(self):
        """プレースホルダー画像を作成"""
        try:
            print(f"=== Creating placeholder image ===")
            print(f"=== Widget hierarchy: {type(self).__name__} -> {type(self.image_label).__name__} ===")
            print(f"=== Image label size: {self.image_label.size().width()}x{self.image_label.size().height()} ===")
            print(f"=== Image label geometry: {self.image_label.geometry()} ===")
            print(f"=== Image label visible: {self.image_label.isVisible()} ===")
            print(f"=== Image label enabled: {self.image_label.isEnabled()} ===")
            print(f"=== Parent visible: {self.isVisible()} ===")
            
            # 固定サイズでプレースホルダー画像を作成
            placeholder = QPixmap(800, 600)
            placeholder.fill(QColor('#2D2D30'))  # 直接色指定で確実に設定
            
            # 中央にテキストを描画
            painter = QPainter(placeholder)
            painter.setPen(QColor('#FFFFFF'))
            painter.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
            painter.drawText(placeholder.rect(), Qt.AlignmentFlag.AlignCenter, "MONITOR画面")
            
            # サブテキスト
            painter.setFont(QFont("Segoe UI", 18))
            painter.setPen(QColor('#B0B0B0'))
            text_rect = placeholder.rect()
            text_rect.setTop(text_rect.center().y() + 40)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "画像待機中...")
            painter.end()
            
            # プレースホルダー画像を設定
            self.image_label.setPixmap(placeholder)
            self.image_label.setText("")  # テキストをクリア
            
            print(f"=== Placeholder image created and set ===")
            print(f"=== Placeholder pixmap size: {placeholder.size().width()}x{placeholder.size().height()} ===")
            print(f"=== Has pixmap after set: {not self.image_label.pixmap().isNull() if self.image_label.pixmap() else False} ===")
            
            # 強制更新とredraw
            self.image_label.update()
            self.image_label.repaint()
            
        except Exception as e:
            print(f"=== ERROR: Placeholder image creation error: {e} ===")
            import traceback
            traceback.print_exc()
            # フォールバック: テキストのみ表示
            self.image_label.setText("MONITOR画面\n画像待機中...")
            self.image_label.setStyleSheet(f"""
                QLabel {{
                    background-color: #2D2D30;
                    color: #FFFFFF;
                    font-size: 18px;
                    font-weight: bold;
                    border: 2px solid #484848;
                    border-radius: 12px;
                    padding: 20px;
                }}
            """)
    
    def update_image(self, image_base64: str):
        """画像を更新（MQTT受信時に呼び出し）"""
        try:
            print(f"=== MONITOR update_image called with data length: {len(image_base64) if image_base64 else 0} ===")
            
            if not image_base64:
                return
            
            # 画像統計を更新
            self.image_count += 1
            from datetime import datetime
            self.last_image_time = datetime.now().strftime("%H:%M:%S")
            
            # Base64デコード
            import base64
            image_bytes = base64.b64decode(image_base64)
            print(f"=== Base64 decoded successfully, binary size: {len(image_bytes)} bytes ===")
            
            # QPixmapに変換
            pixmap = QPixmap()
            if pixmap.loadFromData(image_bytes):
                print(f"=== Original pixmap size: {pixmap.size().width()}x{pixmap.size().height()} ===")
                
                # ラベルの利用可能サイズを取得（パディングとボーダーを除く）
                label_geometry = self.image_label.geometry()
                available_width = max(label_geometry.width() - 20, 200)  # パディング+ボーダー分を除く
                available_height = max(label_geometry.height() - 20, 150)
                
                print(f"=== Label geometry: {label_geometry} ===")
                print(f"=== Available display size: {available_width}x{available_height} ===")
                
                # アスペクト比を保持して適切にスケーリング
                if available_width > 100 and available_height > 100:
                    scaled_pixmap = pixmap.scaled(
                        available_width, available_height,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    print(f"=== Scaled to: {scaled_pixmap.size().width()}x{scaled_pixmap.size().height()} ===")
                    self.image_label.setPixmap(scaled_pixmap)
                else:
                    # サイズが無効な場合、固定サイズでスケーリング
                    scaled_pixmap = pixmap.scaled(
                        800, 600,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    print(f"=== Fixed scale to: {scaled_pixmap.size().width()}x{scaled_pixmap.size().height()} ===")
                    self.image_label.setPixmap(scaled_pixmap)
                
                # プレースホルダーテキストをクリア
                self.image_label.setText("")
                self.current_image = image_base64
                
                print(f"=== SUCCESS: Monitor image displayed (size: {len(image_bytes)} bytes) ===")
                print(f"Monitor image updated: {self.image_count} frames at {self.last_image_time}")
                
                # ウィジェット状態の詳細を確認
                print(f"=== Label visible: {self.image_label.isVisible()} ===")
                print(f"=== Label enabled: {self.image_label.isEnabled()} ===")
                print(f"=== Has pixmap: {not self.image_label.pixmap().isNull() if self.image_label.pixmap() else False} ===")
                
                # UI更新を強制実行
                self.image_label.update()
                self.image_label.repaint()
                
                # 親ウィジェットの更新
                parent = self.image_label.parent()
                while parent:
                    parent.update()
                    parent = parent.parent()
                    
            else:
                print("=== ERROR: Failed to load image from base64 data ===")
                
        except Exception as e:
            print(f"=== EXCEPTION: Monitor image update error: {e} ===")
            import traceback
            traceback.print_exc()
    
    def get_image_stats(self) -> dict:
        """画像統計を取得"""
        return {
            "count": self.image_count,
            "last_update": self.last_image_time
        }
    
    def reset_stats(self):
        """統計をリセット"""
        self.image_count = 0
        self.last_image_time = ""


class VehicleMonitorModernApplication(QMainWindow):
    """車両監視システム - モダンフレームワーク版"""
    
    def __init__(self):
        super().__init__()
        
        # 状態管理
        self.app_state = AppState()
        self.config_manager = ConfigManager()
        
        # フレームワーク
        self.framework = None
        
        # モード別コンポーネント
        self.mode_components = {
            AppMode.CONFIG: {'sidebar': None, 'main_view': None},
            AppMode.EDIT: {'sidebar': None, 'main_view': None},
            AppMode.MONITOR: {'sidebar': None, 'main_view': None}
        }
        
        # MQTT関連
        self.mqtt_service = MQTTService()
        
        self._setup_application()
        self._create_components()
        self._setup_framework()
        
        # 初期モードをCONFIGに設定
        self._switch_to_mode(AppMode.CONFIG)
        
        # ConfigSidebarのシグナル接続
        self._setup_config_connections()
        
        # サイドバーのフィールドを空状態に初期化
        self._clear_config_sidebar_fields()
        
        # MQTTサービスの設定
        self._setup_mqtt_service()
        
        # CONFIG起動時のファイルダイアログ自動表示（設定は空状態で開始）
        self._auto_show_config_dialog()
        
        # 初期化完了フラグ
        self._initialized = True
    
    def _setup_application(self):
        """アプリケーション設定"""
        self.setWindowTitle(self.app_state.get_header_title())
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # ダークテーマ適用
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {StyleBuilder.get_color('dark', 'surface')};
                color: {StyleBuilder.get_color('dark', 'on_surface')};
            }}
        """)
    
    def _create_components(self):
        """各モードのコンポーネント作成"""
        # CONFIG
        config_sidebar = ConfigModernSidebar(self.app_state)
        config_main_view = ModernConfigMainView(self.app_state)
        self.mode_components[AppMode.CONFIG]['sidebar'] = config_sidebar
        self.mode_components[AppMode.CONFIG]['main_view'] = config_main_view
        
        # EDIT 
        edit_sidebar = EditModernSidebar(self.app_state)
        edit_sidebar.set_main_application(self)
        self.mode_components[AppMode.EDIT]['sidebar'] = edit_sidebar
        self.mode_components[AppMode.EDIT]['main_view'] = ModernEditMainView(self.app_state)
        
        # MONITOR
        self.mode_components[AppMode.MONITOR]['sidebar'] = MonitorModernSidebar(self.app_state)
        monitor_main_view = ModernMonitorMainView(self.app_state)
        self.mode_components[AppMode.MONITOR]['main_view'] = monitor_main_view
        
        # MQTTサービスとビューを接続
        self.mqtt_service.image_received.connect(monitor_main_view.update_image)
        self.mqtt_service.image_received.connect(config_main_view.update_mqtt_image)
        print("MQTT service connected to MONITOR and CONFIG main views for image updates")
    
    def _setup_framework(self):
        """フレームワーク設定"""
        self.framework = AppFramework(self.app_state)
        self.setCentralWidget(self.framework)
        
        # フレームワークのイベント接続
        self.framework.header.mode_changed.connect(self._switch_to_mode)
        
        # フッターの更新タイマー
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(1000)  # 1秒ごと
    
    def _switch_to_mode(self, new_mode: AppMode):
        """モード切替"""
        old_mode = self.app_state.current_mode
        print(f"*** _switch_to_mode called ***")
        print(f"*** Target mode: {new_mode.value} ***")
        print(f"*** Current app_state.current_mode: {old_mode.value} ***")
        print(f"*** Header current_mode: {self.framework.header.current_mode.value} ***")
        print(f"*** Are they equal? {old_mode == new_mode} ***")
        
        # 同じモードへの遷移は何もしない（初期化時を除く）
        if old_mode == new_mode and hasattr(self, '_initialized'):
            print(f"Already in {new_mode.value} mode, no action needed")
            return
        
        # CONFIG→EDIT遷移時の特別処理
        if old_mode == AppMode.CONFIG and new_mode == AppMode.EDIT:
            print("CONFIG→EDIT transition detected, calling _handle_config_to_edit_transition")
            if not self._handle_config_to_edit_transition():
                print("CONFIG→EDIT transition cancelled")
                return
            print("CONFIG→EDIT transition completed successfully")
            
            # EDITモード遷移直後にMQTT画像処理を一時停止
            edit_components = self.mode_components.get(AppMode.EDIT, {})
            edit_main_view = edit_components.get('main_view')
            if edit_main_view and hasattr(edit_main_view, 'pause_mqtt_updates'):
                edit_main_view.pause_mqtt_updates()
        
        # EDIT→他モード遷移時のMQTT画像処理再開
        if old_mode == AppMode.EDIT and new_mode != AppMode.EDIT:
            print(f"EDIT→{new_mode.value} transition: MQTT image processing will resume")
            # 注意: 実際のMQTT再開は新しいモードでの_on_mqtt_image_received内で自動的に処理される
        
        # 状態更新
        self.app_state.current_mode = new_mode
        self.setWindowTitle(self.app_state.get_header_title())
        
        # コンポーネント取得
        components = self.mode_components[new_mode]
        sidebar = components['sidebar']
        main_view = components['main_view']
        
        # フレームワークに設定
        self.framework.set_sidebar(sidebar)
        self.framework.set_main_content(main_view)
        
        # モード別のサイドバー表示状態を設定
        if new_mode == AppMode.MONITOR:
            # MONITORモードではサイドバーをデフォルトで非表示
            self.app_state.sidebar_expanded = False
            self.framework.set_sidebar_visible(False)
            print("MONITOR mode: Sidebar set to collapsed by default")
        elif new_mode == AppMode.CONFIG:
            # CONFIGモードではサイドバーをデフォルトで表示
            self.app_state.sidebar_expanded = True
            self.framework.set_sidebar_visible(True)
            print("CONFIG mode: Sidebar set to expanded by default")
        elif new_mode == AppMode.EDIT:
            # EDITモードではサイドバーをデフォルトで表示
            self.app_state.sidebar_expanded = True
            self.framework.set_sidebar_visible(True)
            print("EDIT mode: Sidebar set to expanded by default")
        
        # ヘッダー更新
        self.framework.header.update_mode(new_mode)
        
        print(f"Switched to {new_mode.value} mode successfully")
    
    def _handle_config_to_edit_transition(self) -> bool:
        """CONFIG→EDIT遷移時の特別処理"""
        try:
            print("=== CONFIG→EDIT遷移処理開始 ===")
            
            # 1. 遷移条件チェック
            if not self._can_transition_to_edit():
                print("遷移条件を満たしていません")
                return False
            
            # 2. 現在の設定を取得
            config_data = self._get_current_config_data()
            if not config_data:
                print("設定データが取得できませんでした")
                return False
            
            # 3. 設定をファイルに保存
            self._save_temp_config(config_data)
            
            # 4. MQTT設定送信
            self._publish_config_to_mqtt(config_data)
            
            # 5. EDITモードでRestAPI画像取得を準備（遅延実行で）
            self._prepare_edit_mode_initialization()
            
            # 6. 500msec待機
            import time
            print("500msec待機中...")
            time.sleep(0.5)
            
            print("=== CONFIG→EDIT遷移処理完了 ===")
            return True
            
        except Exception as e:
            print(f"CONFIG→EDIT遷移処理エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _can_transition_to_edit(self) -> bool:
        """EDIT遷移可能かチェック"""
        # 設定データが存在するかチェック
        config_data = self._get_current_config_data()
        if not config_data:
            print("設定データが存在しません")
            return False
        
        # RestAPI接続状態をチェック（簡易実装：設定があれば OK とする）
        restapi_config = config_data.get("RestAPI", {})
        if not restapi_config.get("host") or not restapi_config.get("port"):
            print("RestAPI設定が不完全です")
            return False
        
        print("EDIT遷移条件を満たしています")
        return True
    
    def _get_current_config_data(self) -> dict:
        """現在の設定データを取得"""
        try:
            config_sidebar = self.mode_components[AppMode.CONFIG]['sidebar']
            if hasattr(config_sidebar, 'get_config_sidebar'):
                actual_sidebar = config_sidebar.get_config_sidebar()
                if actual_sidebar and hasattr(actual_sidebar, 'get_current_config'):
                    config_data = actual_sidebar.get_current_config()
                    print(f"設定データ取得成功: {list(config_data.keys()) if config_data else 'None'}")
                    return config_data
            
            print("設定データの取得に失敗しました")
            return None
            
        except Exception as e:
            print(f"設定データ取得エラー: {e}")
            return None
    
    def _save_temp_config(self, config_data: dict):
        """設定を一時ファイルに保存"""
        try:
            import os
            import json
            
            # ./data ディレクトリを作成
            os.makedirs("./data", exist_ok=True)
            
            # config.json に保存
            config_path = "./data/config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"設定を保存しました: {config_path}")
            
        except Exception as e:
            print(f"設定保存エラー: {e}")
            raise
    
    def _publish_config_to_mqtt(self, config_data: dict):
        """MQTT 'config' トピックに設定を送信"""
        try:
            print(f"=== _publish_config_to_mqtt called ===")
            print(f"MQTT service available: {self.mqtt_service is not None}")
            
            if not self.mqtt_service or not hasattr(self.mqtt_service, 'is_connected'):
                print("MQTTサービスが利用できません")
                return
            
            print(f"MQTT connected: {self.mqtt_service.is_connected()}")
            if not self.mqtt_service.is_connected():
                print("MQTT接続が確立されていません")
                return
            
            # JSON文字列に変換
            import json
            config_json = json.dumps(config_data, ensure_ascii=False, separators=(',', ':'))
            print(f"Config JSON prepared: {len(config_json)} chars")
            print(f"Config JSON preview: {config_json[:200]}...")
            
            # 'config' トピックに送信
            print("Calling mqtt_service.publish...")
            success = self.mqtt_service.publish("config", config_json, qos=1, retain=True)
            
            print(f"Publish result: {success}")
            if success:
                print("MQTT 'config' トピックに設定を送信しました")
            else:
                print("MQTT設定送信に失敗しました")
                
        except Exception as e:
            print(f"MQTT設定送信エラー: {e}")
            import traceback
            traceback.print_exc()
            # エラーでも処理は続行する
    
    def _prepare_edit_mode_initialization(self):
        """EDITモード初期化の準備（遅延実行）"""
        print("=== EDITモード初期化準備 ===")
        
        # QTimerを使用してEDITモード切り替え完了後に初期化を実行
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, self._initialize_edit_mode_after_switch)  # 1秒後に実行
    
    def _initialize_edit_mode_after_switch(self):
        """EDITモード切り替え完了後の初期化処理"""
        try:
            print("=== EDITモード後初期化開始 ===")
            
            # 1. ローカルファイルからフルサイズ画像を読み込み（RestAPI代替）
            print("=== CONFIG→EDIT: ローカルフルサイズ画像読み込み開始 ===")
            self._load_local_full_image()
            
            # 2. RestAPIからfull_imageを取得してaaa.jpgとして保存
            print("=== CONFIG→EDIT: RestAPI画像保存開始 ===")
            self._fetch_and_save_restapi_image()
            
            # 3. EDITサイドバーでvehicle.jsonダイアログを自動で開く
            edit_components = self.mode_components.get(AppMode.EDIT, {})
            edit_sidebar = edit_components.get('sidebar')
            
            if edit_sidebar and hasattr(edit_sidebar, '_auto_open_vehicle_dialog'):
                print("EditModernSidebarでvehicle.jsonダイアログを自動で開きます")
                edit_sidebar._auto_open_vehicle_dialog()
            else:
                print("EditModernSidebarに自動ダイアログ機能が見つかりません")
                
            print("=== EDITモード後初期化完了 ===")
            
        except Exception as e:
            print(f"EDITモード後初期化エラー: {e}")
            import traceback
            traceback.print_exc()
            
    def _load_local_full_image(self):
        """ローカルファイルからフルサイズ画像を読み込んでEDITモードに表示"""
        try:
            import os
            from PySide6.QtGui import QPixmap
            
            # ローカルファイルパス
            file_path = r"C:\Users\table0\vm\image_editor\data\full_image.jpg"
            print(f"CONFIG→EDIT ローカル: 画像ファイル読み込み開始 - {file_path}")
            
            # ファイル存在確認
            if not os.path.exists(file_path):
                print(f"CONFIG→EDIT ローカル: ファイルが存在しません - {file_path}")
                return False
            
            # main.py式の直接ファイル読み込み
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                print("CONFIG→EDIT ローカル: 画像ファイルの読み込みに失敗しました")
                return False
            
            print(f"CONFIG→EDIT ローカル: 画像読み込み成功 (size: {pixmap.width()}x{pixmap.height()})")
            
            # EDITメイン画面のImageCanvasに直接設定
            edit_components = self.mode_components.get(AppMode.EDIT, {})
            edit_main_view = edit_components.get('main_view')
            
            if edit_main_view and hasattr(edit_main_view, 'image_canvas') and edit_main_view.image_canvas:
                canvas = edit_main_view.image_canvas
                print("CONFIG→EDIT ローカル: ImageCanvasに画像を設定中...")
                
                # main.py式の直接Canvas操作
                canvas.original_pixmap = pixmap
                
                # 既存の画像アイテムを削除（プレースホルダー含む）
                if canvas.image_item:
                    canvas.scene.removeItem(canvas.image_item)
                    print("CONFIG→EDIT ローカル: 既存の画像アイテムを削除")
                
                # シーンをクリアしてプレースホルダーを完全削除
                canvas.scene.clear()
                print("CONFIG→EDIT ローカル: シーンをクリア（プレースホルダー削除）")
                
                # 新しい画像アイテムを追加
                canvas.image_item = canvas.scene.addPixmap(pixmap)
                canvas.image_item.setZValue(-1000)  # 最背景に設定
                
                # 原寸表示（1:1スケール）
                canvas.display_at_original_size()
                
                print(f"CONFIG→EDIT ローカル: フルサイズ画像表示完了 ({pixmap.width()}x{pixmap.height()})")
                return True
            else:
                print("CONFIG→EDIT ローカル: ImageCanvas未初期化 - 表示に失敗")
                return False
                
        except Exception as e:
            print(f"CONFIG→EDIT ローカル: 画像読み込みエラー: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _fetch_and_save_restapi_image(self):
        """RestAPIからfull_imageを取得してaaa.jpgとして保存"""
        try:
            import os
            import requests
            from pathlib import Path
            
            # 現在のconfig設定を取得
            config_data = self._get_current_config_data()
            if not config_data:
                print("RestAPI画像保存: config.jsonが読み込まれていません")
                return False
            
            restapi_config = config_data.get("RestAPI", {})
            if not restapi_config.get("host") or not restapi_config.get("port"):
                print("RestAPI画像保存: RestAPI設定が不完全です")
                return False
            
            host = restapi_config.get("host")
            port = restapi_config.get("port")
            url = f"http://{host}:{port}/full_image"
            
            print(f"RestAPI画像保存: フルサイズ画像取得開始 - {url}")
            print(f"RestAPI画像保存: 接続先: {host}:{port}")
            
            # RestAPIからフルサイズ画像を取得
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                image_data = response.content
                print(f"RestAPI画像保存: 画像取得成功 ({len(image_data)} bytes)")
                
                # aaa.jpgとして保存（現在のディレクトリ）
                save_path = "aaa.jpg"
                
                try:
                    with open(save_path, 'wb') as f:
                        f.write(image_data)
                    
                    print(f"RestAPI画像保存: ファイル保存完了 - {save_path}")
                    print(f"RestAPI画像保存: 保存サイズ: {len(image_data)} bytes")
                    
                    # ファイルサイズ確認
                    if os.path.exists(save_path):
                        file_size = os.path.getsize(save_path)
                        print(f"RestAPI画像保存: 保存確認成功 - ファイルサイズ: {file_size} bytes")
                        return True
                    else:
                        print("RestAPI画像保存: ファイル保存の確認に失敗")
                        return False
                        
                except Exception as e:
                    print(f"RestAPI画像保存: ファイル書き込みエラー - {e}")
                    return False
                    
            else:
                print(f"RestAPI画像保存: HTTPエラー - Status Code: {response.status_code}")
                print(f"RestAPI画像保存: Response: {response.text[:200]}")
                return False
                
        except requests.exceptions.ConnectTimeout:
            print(f"RestAPI画像保存: 接続タイムアウト - {host}:{port} に接続できません")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"RestAPI画像保存: 接続エラー - {e}")
            return False
        except Exception as e:
            print(f"RestAPI画像保存: 予期しないエラー: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _update_status(self):
        """ステータス情報更新"""
        # FPS更新（シミュレーション）
        import random
        if self.app_state.current_mode == AppMode.MONITOR:
            fps = random.uniform(28.0, 32.0)
        else:
            fps = 0.0
        
        self.app_state.frame_rate = fps
        self.framework.footer.update_fps(fps)
        
        # デバッグ情報更新
        debug_info = f"{self.app_state.current_mode.value} Mode - Ready"
        self.framework.footer.update_debug_info(debug_info)
    
    def _setup_config_connections(self):
        """CONFIG関連の接続設定"""
        # ConfigSidebarのシグナル接続
        config_sidebar = self.mode_components[AppMode.CONFIG]['sidebar']
        if hasattr(config_sidebar, 'get_config_sidebar'):
            actual_sidebar = config_sidebar.get_config_sidebar()
            if actual_sidebar:
                actual_sidebar.config_loaded.connect(self._on_config_loaded)
    
    def _on_config_loaded(self, config_data):
        """設定読み込み時の処理"""
        print(f"Config loaded: {config_data}")
        
        # カメラ設定からフルサイズ画像サイズを取得してEDITモードに設定
        camera_config = config_data.get("camera", {})
        if camera_config:
            width = camera_config.get("width", 2304)
            height = camera_config.get("height", 1296)
            print(f"フルサイズ画像サイズを設定: {width}x{height}")
            
            # EDITモードのメイン画面に画像サイズを設定
            edit_components = self.mode_components.get(AppMode.EDIT, {})
            edit_main_view = edit_components.get('main_view')
            if edit_main_view and hasattr(edit_main_view, 'set_full_image_size'):
                edit_main_view.set_full_image_size(width, height)
                print("EDITモードにフルサイズ画像サイズを設定しました")
        
        # MQTT設定を取得して自動接続
        mqtt_config = config_data.get("mqtt", {})
        if mqtt_config:
            print(f"MQTT設定を検出しました: {mqtt_config}")
            
            # MQTTサービスに設定を適用して自動接続
            self.mqtt_service.set_config(mqtt_config)
            self.mqtt_service.connect_async()
            print("MQTT自動接続を開始しました")
        else:
            print("MQTT設定が見つかりません")
    
    def _auto_show_config_dialog(self):
        """CONFIG起動時のファイルダイアログ自動表示"""
        if self.app_state.current_mode == AppMode.CONFIG:
            try:
                print("CONFIG起動時: 設定選択のため、ファイルダイアログを自動表示します")
                
                # QTimerを使って少し遅延してからダイアログを表示
                # （ウィンドウが完全に表示されてからダイアログを開く）
                QTimer.singleShot(500, self._trigger_config_load_dialog)
                
            except Exception as e:
                print(f"ファイルダイアログ自動表示エラー: {e}")
    
    def _trigger_config_load_dialog(self):
        """設定ファイル読み込みダイアログをトリガー"""
        try:
            config_sidebar = self.mode_components[AppMode.CONFIG]['sidebar']
            if hasattr(config_sidebar, 'get_config_sidebar'):
                actual_sidebar = config_sidebar.get_config_sidebar()
                if actual_sidebar and hasattr(actual_sidebar, '_load_config_file'):
                    print("設定ファイル読み込みダイアログを開きます...")
                    actual_sidebar._load_config_file()
                else:
                    print("ConfigSidebarの_load_config_fileメソッドが見つかりません")
            else:
                print("ConfigSidebarが見つかりません")
        except Exception as e:
            print(f"設定ファイルダイアログトリガーエラー: {e}")
    
    def _clear_config_sidebar_fields(self):
        """ConfigSidebarのフィールドを空状態にクリア"""
        try:
            config_sidebar = self.mode_components[AppMode.CONFIG]['sidebar']
            if hasattr(config_sidebar, 'get_config_sidebar'):
                actual_sidebar = config_sidebar.get_config_sidebar()
                if actual_sidebar and hasattr(actual_sidebar, 'clear_all_fields'):
                    actual_sidebar.clear_all_fields()
                    print("ConfigSidebarフィールドを空状態にクリアしました")
        except Exception as e:
            print(f"ConfigSidebarフィールドクリアエラー: {e}")
    
    def _setup_mqtt_service(self):
        """MQTTサービスの初期化と接続"""
        # MQTTシグナルの接続
        self.mqtt_service.connected.connect(self._on_mqtt_connected)
        self.mqtt_service.disconnected.connect(self._on_mqtt_disconnected)
        self.mqtt_service.image_received.connect(self._on_mqtt_image_received)
        
        # MQTTモード設定
        self.mqtt_service.set_mode("CONFIG")
    
    def _on_mqtt_connected(self, success: bool):
        """MQTT接続状態変更時の処理"""
        print(f"MQTT接続状態: {success}")
        
        # app_stateの接続状態を更新
        self.app_state.connection_status.mqtt = success
        
        # フッターの接続状態を更新
        self.framework.footer.update_connection_status(self.app_state.connection_status)
    
    def _on_mqtt_disconnected(self):
        """MQTT切断時の処理"""
        print("MQTTが切断されました")
        
        # app_stateの接続状態を更新
        self.app_state.connection_status.mqtt = False
        
        # フッターの接続状態を更新
        self.framework.footer.update_connection_status(self.app_state.connection_status)
    
    def _on_mqtt_image_received(self, image_data: str):
        """MQTT画像受信時の処理"""
        print(f">>> MQTT画像を受信しました (データ長: {len(image_data)}) <<<")
        print(f">>> 現在のモード: {self.app_state.current_mode} <<<")
        
        # CONFIGモードとMONITORモードで画像を表示
        if self.app_state.current_mode == AppMode.CONFIG:
            print(">>> CONFIGモードです - メイン画面に表示します <<<")
            config_main_view = self.mode_components[AppMode.CONFIG]['main_view']
            print(f">>> Config main view: {config_main_view} <<<")
            
            if hasattr(config_main_view, 'update_mqtt_image'):
                print(">>> update_mqtt_image メソッドを呼び出します <<<")
                config_main_view.update_mqtt_image(image_data)
            else:
                print(">>> ERROR: update_mqtt_image メソッドが見つかりません <<<")
        
        elif self.app_state.current_mode == AppMode.MONITOR:
            print(">>> MONITORモードです - メイン画面に表示します <<<")
            monitor_main_view = self.mode_components[AppMode.MONITOR]['main_view']
            print(f">>> Monitor main view: {monitor_main_view} <<<")
            
            if hasattr(monitor_main_view, 'update_image'):
                print(">>> update_image メソッドを呼び出します <<<")
                monitor_main_view.update_image(image_data)
            else:
                print(">>> ERROR: update_image メソッドが見つかりません <<<")
        
        elif self.app_state.current_mode == AppMode.EDIT:
            print(">>> EDITモードです - MQTT画像を完全にスキップします <<<")
            print(">>> EDIT mode: MQTT preview images are disabled for static editing <<<")
            return  # EDITモードでは一切のMQTT画像処理を行わない
        
        else:
            print(f">>> 現在のモードは{self.app_state.current_mode}なので画像表示をスキップします <<<")
    
    def _fetch_full_image_from_restapi(self):
        """CONFIG→EDIT遷移時にRestAPIから/full_imageを自動取得"""
        try:
            # 現在のconfig設定を取得
            config_data = self._get_current_config_data()
            if not config_data:
                print("CONFIG→EDIT: config.jsonが読み込まれていないため、RestAPI取得をスキップします")
                return
            
            restapi_config = config_data.get("RestAPI", {})
            if not restapi_config.get("host") or not restapi_config.get("port"):
                print("CONFIG→EDIT: RestAPI設定が不完全なため、画像取得をスキップします")
                return
            
            def fetch_in_background():
                try:
                    import requests
                    host = restapi_config.get("host")
                    port = restapi_config.get("port")
                    url = f"http://{host}:{port}/full_image"
                    
                    print(f"CONFIG→EDIT: RestAPIから画像取得中... {url}")
                    print(f"CONFIG→EDIT: 接続先: {host}:{port}")
                    
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        # JPEG画像データを取得（RestAPIはJPEG形式で返す）
                        image_data = response.content
                        print(f"CONFIG→EDIT: RestAPIから画像取得成功 ({len(image_data)} bytes)")
                        
                        # EDITメイン画面に画像を設定（メインスレッドで実行）
                        from PySide6.QtCore import QTimer
                        QTimer.singleShot(0, lambda: self._display_full_image_in_edit_mode(image_data))
                        
                    else:
                        print(f"CONFIG→EDIT: RestAPIエラー - Status Code: {response.status_code}")
                        print(f"CONFIG→EDIT: Response: {response.text[:200]}")
                        print("CONFIG→EDIT: RestAPI取得失敗 - MQTTからの画像を使用します")
                        
                except requests.exceptions.ConnectTimeout:
                    print(f"CONFIG→EDIT: RestAPI接続タイムアウト - {host}:{port} に接続できません")
                    print("CONFIG→EDIT: Raspiが起動していない、またはネットワーク接続を確認してください")
                except requests.exceptions.ConnectionError as e:
                    print(f"CONFIG→EDIT: RestAPI接続エラー - {e}")
                    print("CONFIG→EDIT: Raspi側のサーバーが起動していない可能性があります")
                except Exception as e:
                    print(f"CONFIG→EDIT: RestAPI取得エラー: {e}")
                    print(f"CONFIG→EDIT: エラー詳細: {type(e).__name__}")
                    import traceback
                    traceback.print_exc()
            
            # バックグラウンドで実行
            import threading
            threading.Thread(target=fetch_in_background, daemon=True).start()
            
        except Exception as e:
            print(f"CONFIG→EDIT: RestAPI取得処理の初期化エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _fetch_full_image_from_restapi_priority(self):
        """CONFIG→EDIT遷移時の優先RestAPI取得（MQTT画像より優先）"""
        try:
            # 現在のconfig設定を取得
            config_data = self._get_current_config_data()
            if not config_data:
                print("CONFIG→EDIT優先: config.jsonが読み込まれていないため、RestAPI取得をスキップします")
                return
            
            restapi_config = config_data.get("RestAPI", {})
            if not restapi_config.get("host") or not restapi_config.get("port"):
                print("CONFIG→EDIT優先: RestAPI設定が不完全なため、画像取得をスキップします")
                return
            
            def fetch_with_priority():
                try:
                    import requests
                    host = restapi_config.get("host")
                    port = restapi_config.get("port")
                    url = f"http://{host}:{port}/full_image"
                    
                    print(f"CONFIG→EDIT優先: RestAPIフルサイズ画像取得中... {url}")
                    print(f"CONFIG→EDIT優先: 接続先: {host}:{port}")
                    
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        # JPEG画像データを取得（RestAPIはJPEG形式で返す）
                        image_data = response.content
                        print(f"CONFIG→EDIT優先: RestAPIフルサイズ画像取得成功 ({len(image_data)} bytes)")
                        
                        # main.py式の直接的な画像表示（メインスレッドで実行）
                        from PySide6.QtCore import QTimer
                        from PySide6.QtGui import QPixmap
                        
                        def display_direct():
                            try:
                                # main.pyと同じパターンでpixmapを作成・検証
                                pixmap = QPixmap()
                                if pixmap.loadFromData(image_data):
                                    print(f"CONFIG→EDIT優先: Pixmap作成成功 (size: {pixmap.width()}x{pixmap.height()})")
                                    
                                    # EDITメイン画面のImageCanvasに直接設定
                                    edit_components = self.mode_components.get(AppMode.EDIT, {})
                                    edit_main_view = edit_components.get('main_view')
                                    
                                    if edit_main_view and hasattr(edit_main_view, 'image_canvas') and edit_main_view.image_canvas:
                                        canvas = edit_main_view.image_canvas
                                        
                                        # main.py式の直接Canvas操作
                                        canvas.original_pixmap = pixmap
                                        
                                        # 既存の画像アイテムを削除
                                        if canvas.image_item:
                                            canvas.scene.removeItem(canvas.image_item)
                                        
                                        # 新しい画像アイテムを追加
                                        canvas.image_item = canvas.scene.addPixmap(pixmap)
                                        canvas.image_item.setZValue(-1000)
                                        
                                        # 原寸表示
                                        canvas.display_at_original_size()
                                        
                                        print(f"CONFIG→EDIT優先: フルサイズ画像表示完了 ({pixmap.width()}x{pixmap.height()})")
                                    else:
                                        print("CONFIG→EDIT優先: ImageCanvas未初期化 - fallbackを試行")
                                        # fallback: 従来の方式
                                        self._display_full_image_in_edit_mode_priority(image_data)
                                else:
                                    print("CONFIG→EDIT優先: Pixmap作成失敗 - 画像データが無効")
                                    
                            except Exception as e:
                                print(f"CONFIG→EDIT優先: 直接表示エラー: {e}")
                                # fallback: 従来の方式
                                self._display_full_image_in_edit_mode_priority(image_data)
                        
                        QTimer.singleShot(0, display_direct)
                        
                    else:
                        print(f"CONFIG→EDIT優先: RestAPIエラー - Status Code: {response.status_code}")
                        print(f"CONFIG→EDIT優先: Response: {response.text[:200]}")
                        
                except requests.exceptions.ConnectTimeout:
                    print(f"CONFIG→EDIT優先: RestAPI接続タイムアウト - {host}:{port} に接続できません")
                except requests.exceptions.ConnectionError as e:
                    print(f"CONFIG→EDIT優先: RestAPI接続エラー - {e}")
                except Exception as e:
                    print(f"CONFIG→EDIT優先: RestAPI取得エラー: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 即座に実行（バックグラウンド）
            import threading
            threading.Thread(target=fetch_with_priority, daemon=True).start()
            
        except Exception as e:
            print(f"CONFIG→EDIT優先: RestAPI取得処理の初期化エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _display_full_image_in_edit_mode(self, image_data: bytes):
        """EDITモードのメイン画面に画像を表示"""
        try:
            print("CONFIG→EDIT: EDITモードのメイン画面に画像を表示します")
            
            # EDITメイン画面コンポーネントを取得
            edit_components = self.mode_components.get(AppMode.EDIT, {})
            edit_main_view = edit_components.get('main_view')
            
            if edit_main_view and hasattr(edit_main_view, 'load_full_image'):
                print("CONFIG→EDIT: load_full_imageメソッドを呼び出します")
                edit_main_view.load_full_image(image_data)
            else:
                print("CONFIG→EDIT: EDITメイン画面にload_full_imageメソッドが見つかりません")
                
        except Exception as e:
            print(f"CONFIG→EDIT: 画像表示エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _display_full_image_in_edit_mode_priority(self, image_data: bytes):
        """EDITモードのメイン画面に優先画像を表示（MQTT上書きを防ぐ）"""
        try:
            print("CONFIG→EDIT優先: EDITモードのメイン画面にフルサイズ画像を表示します")
            
            # EDITメイン画面コンポーネントを取得
            edit_components = self.mode_components.get(AppMode.EDIT, {})
            edit_main_view = edit_components.get('main_view')
            
            if edit_main_view and hasattr(edit_main_view, 'load_priority_image'):
                print("CONFIG→EDIT優先: load_priority_imageメソッドを呼び出します（MQTT無効化）")
                result = edit_main_view.load_priority_image(image_data)
                if result:
                    print(f"CONFIG→EDIT優先: フルサイズ画像表示成功 ({len(image_data)} bytes)")
                    
                    # RestAPI優先画像ロード完了後、MQTT更新再開（優先フラグにより実際はスキップされる）
                    if hasattr(edit_main_view, 'resume_mqtt_updates'):
                        edit_main_view.resume_mqtt_updates()
                    
                    # 画像情報をログ出力
                    from PySide6.QtGui import QPixmap
                    temp_pixmap = QPixmap()
                    if temp_pixmap.loadFromData(image_data):
                        print(f"CONFIG→EDIT優先: 実際の画像サイズ: {temp_pixmap.width()}x{temp_pixmap.height()}")
                else:
                    print("CONFIG→EDIT優先: 画像表示に失敗しました")
            else:
                print("CONFIG→EDIT優先: EDITメイン画面にload_priority_imageメソッドが見つかりません")
                # fallback: 通常のload_full_imageメソッドを試行
                if edit_main_view and hasattr(edit_main_view, 'load_full_image'):
                    print("CONFIG→EDIT優先: fallback - load_full_imageメソッドを使用")
                    edit_main_view.load_full_image(image_data)
                
        except Exception as e:
            print(f"CONFIG→EDIT優先: 画像表示エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def closeEvent(self, event):
        """アプリケーション終了時のクリーンアップ"""
        try:
            print("=== Application closing, cleaning up MQTT connections ===")
            
            # MQTT接続を切断
            if hasattr(self, 'mqtt_service') and self.mqtt_service:
                print("=== Disconnecting MQTT service ===")
                self.mqtt_service.disconnect()
            
            # その他のクリーンアップ処理があれば追加
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            # 親クラスのcloseEventを呼び出す
            super().closeEvent(event)
            print("=== Application closed successfully ===")


def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    # アプリケーション作成
    window = VehicleMonitorModernApplication()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()