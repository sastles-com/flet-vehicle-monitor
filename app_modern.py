#!/usr/bin/env python3
"""
Vehicle Monitor Application - Modern Framework Version
車両監視システム - モダンフレームワーク版
"""

import sys
from typing import Optional
import os

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QSizePolicy,
                               QGraphicsView, QGraphicsScene, QPushButton, QHBoxLayout, QGroupBox,
                               QCheckBox, QTreeWidget, QTreeWidgetItem, QGraphicsRectItem, QGraphicsEllipseItem,
                               QGraphicsTextItem)
from PySide6.QtCore import QTimer, Qt, QRectF, QPointF
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush
from typing import List, Dict, Tuple
from enum import Enum

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


def _get_default_desktop_dir() -> str:
    """Resolve Desktop base dir from env/Windows, fallback to ~/Desktop."""
    env_dir = os.environ.get("DEFAULT_DIR")
    if env_dir:
        return env_dir
    # Try Windows Known Folder
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(260)
        CSIDL_DESKTOPDIRECTORY = 0x10
        if ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOPDIRECTORY, None, 0, buf) == 0:
            return buf.value
    except Exception:
        pass
    return os.path.join(os.path.expanduser("~"), "Desktop")


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
            default_vehicle_folder = os.path.join(_get_default_desktop_dir(), "Vehicles")
            
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
        self.default_vehicle_folder = os.path.join(_get_default_desktop_dir(), "Vehicles")
        
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
        
        # パーツ選択のための初期状態ラベル
        self.parts_info_label = QLabel("⏳ 車を選択すると編集できます")
        self.parts_info_label.setStyleSheet(f"""
            QLabel {{
                color: {DesignTokens.COLORS['dark']['text_secondary']};
                font-size: 13px;
                padding: 8px 12px;
                background-color: {DesignTokens.COLORS['dark']['surface_1']};
                border-radius: 6px;
                text-align: center;
            }}
        """)
        step2_layout.addWidget(self.parts_info_label)
        
        # パーツ表示カテゴリ別チェックボックス（初期は非表示）
        self.category_group = QGroupBox("表示カテゴリ")
        self.category_group.setStyleSheet(f"""
            QGroupBox {{
                color: {DesignTokens.COLORS['dark']['text_primary']};
                border: 1px solid {DesignTokens.COLORS['dark']['border']};
                border-radius: 6px;
                margin-top: 8px;
                font-size: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }}
        """)
        self.category_group.hide()  # 初期は非表示
        
        category_layout = QVBoxLayout()
        
        self.icon_checkbox = QCheckBox("🔴 Icon (矩形)")
        self.icon_checkbox.setChecked(True)
        self.icon_checkbox.stateChanged.connect(lambda: self._toggle_category_visibility('icon'))
        
        self.meter_checkbox = QCheckBox("🔵 Meter (円形)")
        self.meter_checkbox.setChecked(True)
        self.meter_checkbox.stateChanged.connect(lambda: self._toggle_category_visibility('meter'))
        
        self.ocr_checkbox = QCheckBox("🟠 OCR (矩形)")
        self.ocr_checkbox.setChecked(True)
        self.ocr_checkbox.stateChanged.connect(lambda: self._toggle_category_visibility('ocr'))
        
        category_layout.addWidget(self.icon_checkbox)
        category_layout.addWidget(self.meter_checkbox)
        category_layout.addWidget(self.ocr_checkbox)
        self.category_group.setLayout(category_layout)
        
        step2_layout.addWidget(self.category_group)
        
        # パーツリストツリー（初期は非表示）
        self.parts_tree_label = QLabel("パーツリスト:")
        self.parts_tree_label.setStyleSheet(f"""
            QLabel {{
                color: {DesignTokens.COLORS['dark']['text_primary']};
                font-size: 12px;
                font-weight: 600;
                margin-top: 8px;
            }}
        """)
        self.parts_tree_label.hide()  # 初期は非表示
        
        from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
        self.parts_tree = QTreeWidget()
        self.parts_tree.setHeaderLabels(["名前", "カテゴリ", "タイプ"])
        self.parts_tree.itemClicked.connect(self._on_tree_item_clicked)
        self.parts_tree.setMaximumHeight(200)
        self.parts_tree.setStyleSheet(f"""
            QTreeWidget {{
                color: {DesignTokens.COLORS['dark']['text_primary']};
                background-color: {DesignTokens.COLORS['dark']['surface_1']};
                border: 1px solid {DesignTokens.COLORS['dark']['border']};
                border-radius: 4px;
                selection-background-color: {DesignTokens.COLORS['dark']['primary']};
            }}
        """)
        self.parts_tree.hide()  # 初期は非表示
        
        step2_layout.addWidget(self.parts_tree_label)
        step2_layout.addWidget(self.parts_tree)
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
            print(f"=== VEHICLE FILE LOADING START ===")
            print(f"Loading vehicle file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                self.vehicle_data = json.load(f)
            
            # ファイルパスを記憶
            self.current_vehicle_file_path = file_path
            
            # デバッグ: データ構造を確認
            print(f"Vehicle data loaded: {self.vehicle_data.keys()}")
            print(f"Icons: {len(self.vehicle_data.get('icon', []))}")
            print(f"Meters: {len(self.vehicle_data.get('meter', []))}")
            print(f"OCRs: {len(self.vehicle_data.get('ocr', []))}")
            
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
            
            # MainViewにvehicle.jsonデータを渡す
            print("=== SENDING DATA TO MAIN VIEW ===")
            self._send_vehicle_data_to_main_view()
            
            # RestAPIで画像を取得
            self._fetch_full_image()
            
            print(f"=== VEHICLE FILE LOADING COMPLETE ===")
            
            # 将来的にはここでステップ2のボタンを有効化する予定
            
        except Exception as e:
            print(f"Error loading vehicle file: {e}")
            self.vehicle_info_label.setText("車両: 読み込みエラー")
    
    def _send_vehicle_data_to_main_view(self):
        """vehicle.jsonデータをMainViewに送信"""
        if not self.vehicle_data:
            print("No vehicle data to send")
            return
            
        try:
            # 親のVehicleMonitorApplicationインスタンスを取得
            app_instance = self.parent()
            while app_instance and not hasattr(app_instance, 'mode_components'):
                app_instance = app_instance.parent()
            
            if app_instance and hasattr(app_instance, 'mode_components'):
                # EDITモードのMainViewを取得
                edit_components = app_instance.mode_components.get(AppMode.EDIT, {})
                main_view = edit_components.get('main_view')
                
                if main_view and hasattr(main_view, 'load_vehicle_json'):
                    print("Sending vehicle data to EditModernMainView")
                    main_view.load_vehicle_json(self.vehicle_data)
                    
                    # サイドバーのパーツリストも更新
                    self._update_sidebar_parts_list()
                else:
                    print("EditModernMainView not found or load_vehicle_json method missing")
            else:
                print("VehicleMonitorApplication instance not found")
                
        except Exception as e:
            print(f"Error sending vehicle data to main view: {e}")
    
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
    
    def _update_sidebar_parts_list(self):
        """サイドバーのパーツリストを更新"""
        if not self.vehicle_data:
            return
            
        # パーツ情報ラベルを更新
        vehicle_name = self.vehicle_data.get("name", "Unknown")
        icon_count = len(self.vehicle_data.get('icon', []))
        meter_count = len(self.vehicle_data.get('meter', []))
        ocr_count = len(self.vehicle_data.get('ocr', []))
        
        self.parts_info_label.setText(f"✅ {vehicle_name}: {icon_count + meter_count + ocr_count}個のパーツ")
        
        # パーツ選択要素を表示
        self.category_group.show()
        self.parts_tree_label.show()
        self.parts_tree.show()
        
        # パーツリストツリーを更新
        from PySide6.QtWidgets import QTreeWidgetItem
        from PySide6.QtCore import Qt
        
        self.parts_tree.clear()
        
        # カテゴリ別にグループ化
        icon_parent = QTreeWidgetItem(["Icon", "", ""])
        meter_parent = QTreeWidgetItem(["Meter", "", ""])
        ocr_parent = QTreeWidgetItem(["OCR", "", ""])
        
        # Iconアイテムを追加
        for i, icon in enumerate(self.vehicle_data.get('icon', [])):
            item = QTreeWidgetItem([
                icon.get('name', f'Icon {i+1}'),
                'Icon',
                icon.get('type', 'bool')
            ])
            item.setData(0, Qt.UserRole, {'category': 'icon', 'index': i, 'data': icon})
            icon_parent.addChild(item)
        
        # Meterアイテムを追加
        for i, meter in enumerate(self.vehicle_data.get('meter', [])):
            item = QTreeWidgetItem([
                meter.get('name', f'Meter {i+1}'),
                'Meter',
                meter.get('type', 'float')
            ])
            item.setData(0, Qt.UserRole, {'category': 'meter', 'index': i, 'data': meter})
            meter_parent.addChild(item)
        
        # OCRアイテムを追加
        for i, ocr in enumerate(self.vehicle_data.get('ocr', [])):
            item = QTreeWidgetItem([
                ocr.get('name', f'OCR {i+1}'),
                'OCR',
                ocr.get('type', 'int')
            ])
            item.setData(0, Qt.UserRole, {'category': 'ocr', 'index': i, 'data': ocr})
            ocr_parent.addChild(item)
        
        # カテゴリをツリーに追加（子要素があるもののみ）
        if icon_parent.childCount() > 0:
            self.parts_tree.addTopLevelItem(icon_parent)
            icon_parent.setExpanded(True)
        
        if meter_parent.childCount() > 0:
            self.parts_tree.addTopLevelItem(meter_parent)
            meter_parent.setExpanded(True)
        
        if ocr_parent.childCount() > 0:
            self.parts_tree.addTopLevelItem(ocr_parent)
            ocr_parent.setExpanded(True)
            
        print(f"Sidebar parts list updated: {icon_count} icons, {meter_count} meters, {ocr_count} ocrs")
    
    def _on_tree_item_clicked(self, item, column):
        """ツリーアイテムクリック時の処理"""
        try:
            item_data = item.data(0, Qt.UserRole)
            if not item_data:
                print("No item data found")
                return
                
            category = item_data.get('category')
            index = item_data.get('index')
            data = item_data.get('data')
            
            print(f"Tree item clicked: {category} #{index} - {data.get('name', 'Unknown')}")
            
            # メインビューに選択されたパーツをハイライトするよう通知
            self._highlight_part_in_main_view(category, index)
            
        except Exception as e:
            print(f"Error handling tree item click: {e}")
    
    def _highlight_part_in_main_view(self, category, index):
        """メインビューで指定されたパーツをハイライト"""
        try:
            # 親のVehicleMonitorApplicationインスタンスを取得
            app_instance = self.parent()
            while app_instance and not hasattr(app_instance, 'mode_components'):
                app_instance = app_instance.parent()
            
            if app_instance and hasattr(app_instance, 'mode_components'):
                edit_components = app_instance.mode_components.get(AppMode.EDIT, {})
                main_view = edit_components.get('main_view')
                
                if main_view and hasattr(main_view, '_highlight_part'):
                    main_view._highlight_part(category, index)
                else:
                    print("MainView highlight method not found")
            else:
                print("VehicleMonitorApplication instance not found")
                    
        except Exception as e:
            print(f"Error highlighting part in main view: {e}")
    
    def _toggle_category_visibility(self, category):
        """カテゴリ表示の切り替え"""
        try:
            # 親のVehicleMonitorApplicationインスタンスを取得
            app_instance = self.parent()
            while app_instance and not hasattr(app_instance, 'mode_components'):
                app_instance = app_instance.parent()
            
            if app_instance and hasattr(app_instance, 'mode_components'):
                edit_components = app_instance.mode_components.get(AppMode.EDIT, {})
                main_view = edit_components.get('main_view')
                
                if main_view and hasattr(main_view, '_toggle_category_visibility'):
                    is_checked = getattr(self, f'{category}_checkbox').isChecked()
                    main_view._toggle_category_visibility(category, is_checked)
                    print(f"Category {category} visibility toggled: {is_checked}")
                else:
                    print("MainView toggle method not found")
            else:
                print("VehicleMonitorApplication instance not found")
                    
        except Exception as e:
            print(f"Error toggling category visibility: {e}")


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
        
        # 図形選択管理（main.py準拠）
        self.selected_shape = None
        self._vehicle_shapes: List[ResizableGraphicsItem] = []
        
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
        """マウスボタンが押された時の処理（main.py完全準拠）"""
        from PySide6.QtCore import Qt
        
        if event.button() == Qt.MouseButton.RightButton:
            # 右クリック開始 - パン移動モード
            self._right_mouse_pressed = True
            self._last_pan_point = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)  # 掴んでいる状態のカーソル
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton:
            # 左クリック処理 - 制御点選択システム（main.py準拠）
            click_pos = self.mapToScene(event.position().toPoint())
            
            # 制御点選択を試行
            if not self.select_nearest_control_point(click_pos):
                # 制御点以外をクリックした場合 - 全ての選択を解除
                if self.selected_shape:
                    self.selected_shape.set_selected(False)
                    self.selected_shape = None
                    print("All selections cleared")
            
            # 標準のマウス処理も実行（重要）
            super().mousePressEvent(event)
        else:
            # その他のボタンは標準処理
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
    
    def select_nearest_control_point(self, click_pos):
        """クリック位置に最も近い制御点を選択（main.pyから完全移植）"""
        import math
        
        min_distance = float('inf')
        nearest_shape = None
        
        for shape in self._vehicle_shapes:
            if shape.center_control_point and shape.visible:
                # 制御点の中心位置を計算
                control_rect = shape.center_control_point.rect()
                control_pos = shape.center_control_point.pos()
                center_x = control_pos.x() + control_rect.width() / 2
                center_y = control_pos.y() + control_rect.height() / 2
                
                # クリック位置からの距離を計算
                distance = math.sqrt((click_pos.x() - center_x)**2 + (click_pos.y() - center_y)**2)
                
                # 制御点の半径内にある場合のみ対象とする（選択可能範囲）
                control_radius = max(control_rect.width(), control_rect.height()) / 2 + 10  # +10px余裕
                
                if distance <= control_radius and distance < min_distance:
                    min_distance = distance
                    nearest_shape = shape
        
        # 最も近いパーツがあれば選択
        if nearest_shape:
            # 既存の選択をクリア
            if self.selected_shape and self.selected_shape != nearest_shape:
                self.selected_shape.set_selected(False)
            
            # 新しいパーツを選択
            self.selected_shape = nearest_shape
            nearest_shape.set_selected(True)
            
            print(f"Selected shape: {nearest_shape.category.value} at distance {min_distance:.1f}px")
            return True
        
        return False
    
    def resizeEvent(self, event):
        """ウィンドウリサイズ時の処理"""
        super().resizeEvent(event)
        # 原寸表示モードではリサイズ時の自動調整を行わない


# ===== 高度パーツ描画システム (main.pyから移植) =====

class CenterControlPointHover:
    """重心制御点のホバー効果ハンドラ（main.pyから完全移植）"""
    
    def __init__(self, control_point_item, parent_shape):
        self.control_point_item = control_point_item
        self.parent_shape = parent_shape
        # サイズは動的に計算（移動時に追従するため）
    
    def get_current_sizes(self):
        """現在の選択状態に応じたサイズを取得"""
        original_size = 28 if self.parent_shape.is_selected else 24
        hover_size = original_size + 6
        return original_size, hover_size
    
    def hoverEnterEvent(self, event):
        """ホバー開始時の処理（制御点を大きく、色変更）"""
        # 動的サイズ取得
        original_size, hover_size = self.get_current_sizes()
        
        # 現在の中心位置を保持してサイズのみ変更
        current_rect = self.control_point_item.rect()
        current_pos = self.control_point_item.pos()
        
        # 現在の中心位置を計算（絶対座標）
        center_x = current_pos.x() + current_rect.center().x()
        center_y = current_pos.y() + current_rect.center().y()
        
        # 新しい位置を計算（中心を保持）
        new_pos_x = center_x - hover_size / 2
        new_pos_y = center_y - hover_size / 2
        
        # 位置とサイズを更新
        self.control_point_item.setPos(new_pos_x, new_pos_y)
        self.control_point_item.setRect(0, 0, hover_size, hover_size)
        
        # 色を明るく（選択可能を示す）
        if self.parent_shape.is_selected:
            # 選択時: カテゴリ色をより明るく
            hover_color = self.parent_shape.get_category_color().lighter(150)
        else:
            # 未選択時: カテゴリ色で表示
            hover_color = self.parent_shape.get_category_color().lighter(120)
        self.control_point_item.setBrush(QBrush(hover_color))
        self.control_point_item.setPen(QPen(QColor(0, 0, 0), 3))
        
        # デフォルトのホバー処理
        from PySide6.QtWidgets import QGraphicsEllipseItem
        QGraphicsEllipseItem.hoverEnterEvent(self.control_point_item, event)
    
    def hoverLeaveEvent(self, event):
        """ホバー終了時の処理（元のサイズ、色に戻す）"""
        # 動的サイズ取得
        original_size, hover_size = self.get_current_sizes()
        
        # 現在の中心位置を保持して元のサイズに戻す
        current_rect = self.control_point_item.rect()
        current_pos = self.control_point_item.pos()
        
        # 現在の中心位置を計算（絶対座標）
        center_x = current_pos.x() + current_rect.center().x()
        center_y = current_pos.y() + current_rect.center().y()
        
        # 元のサイズでの新しい位置を計算（中心を保持）
        new_pos_x = center_x - original_size / 2
        new_pos_y = center_y - original_size / 2
        
        # 位置とサイズを更新
        self.control_point_item.setPos(new_pos_x, new_pos_y)
        self.control_point_item.setRect(0, 0, original_size, original_size)
        
        # 色を元に戻す（選択状態に応じて）
        if self.parent_shape.is_selected:
            # 選択時: カテゴリ色
            original_color = self.parent_shape.get_category_color()
        else:
            # 未選択時: 白色
            original_color = QColor(255, 255, 255)
        self.control_point_item.setBrush(QBrush(original_color))
        self.control_point_item.setPen(QPen(QColor(0, 0, 0), 3))
        
        # デフォルトのホバー処理
        from PySide6.QtWidgets import QGraphicsEllipseItem
        QGraphicsEllipseItem.hoverLeaveEvent(self.control_point_item, event)


class CenterControlPointHandler:
    """重心制御点のマウスイベントハンドラー"""
    
    def __init__(self, control_point_item, parent_shape):
        self.control_point_item = control_point_item
        self.parent_shape = parent_shape
        self.is_dragging = False
        self.last_pos = None
    
    def mousePressEvent(self, event):
        """制御点クリック時の処理 - main.py準拠"""
        from PySide6.QtCore import Qt
        if event.button() == Qt.LeftButton:
            # 親図形を選択状態に設定
            if hasattr(self.parent_shape, 'set_selected'):
                # 他の全ての図形の選択を解除
                self._clear_all_selections()
                
                # 現在の図形を選択
                self.parent_shape.set_selected(True)
                
                # Canvas側のselected_shapeも更新
                if hasattr(self.parent_shape, 'main_view') and self.parent_shape.main_view:
                    main_view = self.parent_shape.main_view
                    if hasattr(main_view, 'image_canvas'):
                        main_view.image_canvas.selected_shape = self.parent_shape
                        
                print(f"Selected {self.parent_shape.category.value} via control point click")
            
            # ドラッグ開始準備
            self.is_dragging = True
            self.last_pos = event.scenePos()
            
            print("Center control point pressed - ready to drag")
            
            # main.py式のイベント処理: 制御点自体にイベントを渡す
            from PySide6.QtWidgets import QGraphicsEllipseItem
            QGraphicsEllipseItem.mousePressEvent(self.control_point_item, event)
    
    def mouseMoveEvent(self, event):
        """制御点ドラッグ時の処理 - main.py完全準拠"""
        if self.is_dragging and self.last_pos:
            # 移動量を計算
            current_pos = event.scenePos()
            delta_x = current_pos.x() - self.last_pos.x()
            delta_y = current_pos.y() - self.last_pos.y()
            
            # main.py準拠：先に制御点を移動
            from PySide6.QtWidgets import QGraphicsEllipseItem
            QGraphicsEllipseItem.mouseMoveEvent(self.control_point_item, event)
            
            # その後で関連アイテムを同期移動
            self.parent_shape.move_associated_items(delta_x, delta_y)
            
            self.last_pos = current_pos
            
            print(f"Shape moved by ({delta_x:.1f}, {delta_y:.1f}) - main.py style")
    
    def mouseReleaseEvent(self, event):
        """制御点ドラッグ終了時の処理"""
        from PySide6.QtCore import Qt
        if event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.last_pos = None
            
            # 移動後の位置を元座標に反映
            self.update_original_coordinates()
            
            # ハンドルを再作成して正しい位置に配置
            self.parent_shape.create_handles()
            
            print("Center control point drag completed")
            event.accept()
        
        # main.py式のイベント処理: 制御点自体にイベントを渡す
        from PySide6.QtWidgets import QGraphicsEllipseItem
        QGraphicsEllipseItem.mouseReleaseEvent(self.control_point_item, event)
    
    def update_original_coordinates(self):
        """移動後の位置を元座標に反映"""
        item = self.parent_shape.get_item()
        current_pos = item.pos()
        
        # 現在のスケールで割って元座標を更新
        scale = self.parent_shape.scene_scale
        self.parent_shape.original_x = current_pos.x() / scale
        self.parent_shape.original_y = current_pos.y() / scale
        
        print(f"Updated original coordinates: ({self.parent_shape.original_x:.1f}, {self.parent_shape.original_y:.1f})")
    
    def _clear_all_selections(self):
        """全ての図形の選択を解除"""
        # main_view経由でCanvasの_vehicle_shapesにアクセス
        if hasattr(self.parent_shape, 'main_view') and self.parent_shape.main_view:
            main_view = self.parent_shape.main_view
            if hasattr(main_view, 'image_canvas') and hasattr(main_view.image_canvas, '_vehicle_shapes'):
                for shape in main_view.image_canvas._vehicle_shapes:
                    if hasattr(shape, 'set_selected'):
                        shape.set_selected(False)
                # Canvas側のselected_shapeも更新
                main_view.image_canvas.selected_shape = None
                print("Cleared all selections via Canvas reference")
                return
        
        print("Warning: Could not clear selections - Canvas reference not found")


class ResizeHandler:
    """リサイズハンドルのドラッグハンドラー（main.pyから移植）"""
    
    def __init__(self, handle_item, parent_shape, handle_type):
        self.handle_item = handle_item
        self.parent_shape = parent_shape
        self.handle_type = handle_type
        self.is_dragging = False
        self.start_pos = None
        self.start_rect = None
        self.start_item_pos = None
    
    def mousePressEvent(self, event):
        """リサイズハンドルクリック時の処理"""
        from PySide6.QtCore import Qt
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.start_pos = event.scenePos()
            
            # 現在の図形の位置とサイズを記録
            item = self.parent_shape.get_item()
            self.start_rect = item.boundingRect()
            self.start_item_pos = item.pos()
            
            event.accept()
    
    def mouseMoveEvent(self, event):
        """リサイズハンドルドラッグ時の処理"""
        if self.is_dragging and self.start_pos:
            current_pos = event.scenePos()
            delta_x = current_pos.x() - self.start_pos.x()
            delta_y = current_pos.y() - self.start_pos.y()
            
            # ハンドルタイプに応じてリサイズ処理
            self.resize_shape(delta_x, delta_y)
    
    def mouseReleaseEvent(self, event):
        """リサイズハンドルドラッグ終了時の処理"""
        from PySide6.QtCore import Qt
        if event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.start_pos = None
            
            # リサイズ後の座標を元座標に反映
            self.update_original_size()
            
            # ハンドルを再作成して正しい位置に配置
            self.parent_shape.create_handles()
            
            # circumferenceポイントも更新
            if hasattr(self.parent_shape, 'update_circumference_display'):
                self.parent_shape.update_circumference_display()
            
            event.accept()
    
    def resize_shape(self, delta_x: float, delta_y: float):
        """ハンドルタイプに応じた図形リサイズ"""
        item = self.parent_shape.get_item()
        
        # 円形の場合は正円を維持する特別処理
        if hasattr(self.parent_shape, 'shape_type') and self.parent_shape.shape_type == ShapeType.CIRCLE:
            self.resize_circle(delta_x, delta_y)
            return
        
        # 新しい位置とサイズを計算（矩形・バー用）
        new_x = self.start_item_pos.x()
        new_y = self.start_item_pos.y()
        new_width = self.start_rect.width()
        new_height = self.start_rect.height()
        
        # ハンドルタイプ別のリサイズロジック
        if self.handle_type == "top_left":
            new_x += delta_x
            new_y += delta_y
            new_width -= delta_x
            new_height -= delta_y
        elif self.handle_type == "top_center":
            new_y += delta_y
            new_height -= delta_y
        elif self.handle_type == "top_right":
            new_y += delta_y
            new_width += delta_x
            new_height -= delta_y
        elif self.handle_type == "middle_right":
            new_width += delta_x
        elif self.handle_type == "bottom_right":
            new_width += delta_x
            new_height += delta_y
        elif self.handle_type == "bottom_center":
            new_height += delta_y
        elif self.handle_type == "bottom_left":
            new_x += delta_x
            new_width -= delta_x
            new_height += delta_y
        elif self.handle_type == "middle_left":
            new_x += delta_x
            new_width -= delta_x
        
        # 最小サイズ制限
        min_size = 20
        if new_width < min_size:
            if self.handle_type in ["top_left", "bottom_left", "middle_left"]:
                new_x = new_x + new_width - min_size
            new_width = min_size
        if new_height < min_size:
            if self.handle_type in ["top_left", "top_center", "top_right"]:
                new_y = new_y + new_height - min_size
            new_height = min_size
        
        # 図形の位置とサイズを更新
        item.setPos(new_x, new_y)
        item.setRect(0, 0, new_width, new_height)
        
        # 制御点とパーツ名も更新
        self.parent_shape.update_center_control_point()
        self.parent_shape.update_name_display()
    
    def update_original_size(self):
        """リサイズ後のサイズを元座標に反映"""
        item = self.parent_shape.get_item()
        rect = item.boundingRect()
        pos = item.pos()
        
        # 現在のスケールで割って元座標を更新
        scale = self.parent_shape.scene_scale
        self.parent_shape.original_x = pos.x() / scale
        self.parent_shape.original_y = pos.y() / scale
        self.parent_shape.original_width = rect.width() / scale
        self.parent_shape.original_height = rect.height() / scale
        
        print(f"Updated original size: ({self.parent_shape.original_width:.1f} x {self.parent_shape.original_height:.1f})")
    
    def resize_circle(self, delta_x: float, delta_y: float):
        """円形専用リサイズ（正円を維持）"""
        item = self.parent_shape.get_item()
        
        # 半径の変更量を計算（右ハンドルは+、左ハンドルは-）
        if self.handle_type == "middle_right":
            radius_delta = delta_x
        elif self.handle_type == "middle_left":
            radius_delta = -delta_x
        else:
            return
        
        # 新しい半径を計算（最小半径20px）
        old_radius = self.start_rect.width() / 2
        new_radius = max(20, old_radius + radius_delta)
        
        # 新しいサイズ（正円なのでwidth=height）
        new_size = new_radius * 2
        
        # 中心を維持するため、新しい位置を計算
        old_center_x = self.start_item_pos.x() + self.start_rect.width() / 2
        old_center_y = self.start_item_pos.y() + self.start_rect.height() / 2
        
        new_x = old_center_x - new_radius
        new_y = old_center_y - new_radius
        
        # 図形の位置とサイズを更新（正円）
        item.setPos(new_x, new_y)
        item.setRect(0, 0, new_size, new_size)
        
        # 制御点とパーツ名も更新
        self.parent_shape.update_center_control_point()
        self.parent_shape.update_name_display()
        
        print(f"Circle resized: radius={new_radius:.1f}px")


class ShapeCategory(Enum):
    """図形のカテゴリ"""
    ICON = "icon"
    METER = "meter"
    OCR = "ocr"
    CUSTOM = "custom"

class ShapeType(Enum):
    """図形の種類"""
    BOX = "box"
    CIRCLE = "circle"
    BAR = "bar"

class CircumferencePoint:
    """円周上のポイント（meter用）"""
    def __init__(self, position: Dict, value: float):
        self.position = position  # {"x": float, "y": float}
        self.value = value


class ResizableGraphicsItem:
    """リサイズ可能な図形の基底クラス（main.pyから完全移植）"""
    
    def __init__(self, x: float, y: float, width: float, height: float, 
                 scene_scale: float = 1.0, category: ShapeCategory = ShapeCategory.CUSTOM, 
                 main_view=None):
        # 基本プロパティ
        self.category = category
        self.scene_scale = scene_scale
        self.is_selected = False
        self.visible = True
        self.main_view = main_view  # ModernEditMainViewの参照
        
        # 元座標（vehicle.jsonでの座標）
        self.original_x = x
        self.original_y = y
        self.original_width = width
        self.original_height = height
        
        # ドラッグ・リサイズ用ハンドル
        self.handles: List[QGraphicsRectItem] = []
        self.handle_size = 16  # main.pyと同じサイズ
        
        # パーツ名表示用テキストアイテム
        self.name_text_item = None
        # 重心制御点
        self.center_control_point = None
        
    def get_item(self):
        """継承クラスで実装: 実際のQGraphicsItemを返す"""
        raise NotImplementedError("Subclass must implement get_item method")
    
    def get_original_coords(self, scale: float = None) -> Tuple[float, float, float, float]:
        """元画像の座標系での位置を返す"""
        return (self.original_x, self.original_y, self.original_width, self.original_height)
    
    def update_position_for_scale(self, scale: float):
        """スケール変更時の位置更新"""
        self.scene_scale = scale
        # 表示位置を実座標からスケールされた位置に更新
        display_x = self.original_x * scale
        display_y = self.original_y * scale
        self.get_item().setPos(display_x, display_y)
        
        # パーツ名と制御点も更新
        self.update_center_control_point()
        self.update_name_display()
    
    def set_visible(self, visible: bool):
        """図形の表示/非表示を切り替え"""
        self.visible = visible
        self.get_item().setVisible(visible)
        
        # 制御点も連動
        if self.center_control_point:
            self.center_control_point.setVisible(visible and self.is_selected)
        
        # パーツ名も連動
        if self.name_text_item:
            self.name_text_item.setVisible(visible)
    
    def set_selected(self, selected: bool):
        """選択状態を設定"""
        self.is_selected = selected
        
        # 選択状態に応じて描画を更新
        self.update_display()
        self.update_center_control_point()
        
        # リサイズハンドル表示制御
        self.create_handles()
    
    def get_category_color(self) -> QColor:
        """カテゴリ別の色を取得"""
        category_colors = {
            ShapeCategory.ICON: QColor(255, 100, 100),    # 赤系
            ShapeCategory.METER: QColor(100, 255, 100),   # 緑系
            ShapeCategory.OCR: QColor(100, 100, 255),     # 青系
            ShapeCategory.CUSTOM: QColor(255, 255, 255),  # 白
        }
        return category_colors.get(self.category, QColor(255, 255, 255))
    
    def update_display(self):
        """選択状態に応じて表示を更新"""
        item = self.get_item()
        if self.is_selected:
            # 選択時: カテゴリ色で強調表示
            pen_color = self.get_category_color()
        else:
            # 未選択時: 白色で表示
            pen_color = QColor(255, 255, 255)
        
        # 統一方針：塗りなし、太線（線幅3px）
        item.setBrush(QBrush(Qt.NoBrush))  # 塗りなし
        item.setPen(QPen(pen_color, 3))     # 太線
    
    def create_handles(self):
        """リサイズハンドルを作成（選択時のみ表示）"""
        # 既存のハンドルを削除
        for handle in self.handles:
            if handle.scene():
                handle.scene().removeItem(handle)
        self.handles.clear()
        
        # 未選択時は変形ハンドルを表示しない
        if not self.is_selected:
            return
        
        # 継承クラスで具体的なハンドル作成を実装
        self._create_specific_handles()
    
    def _create_specific_handles(self):
        """継承クラスで実装: 図形固有のハンドル作成"""
        pass
    
    def move_associated_items(self, delta_x: float, delta_y: float):
        """関連アイテムを同期移動（main.py準拠の実装）"""
        # ドラッグ競合防止のフラグ設定
        if not hasattr(self, '_is_moving'):
            self._is_moving = False
        
        if self._is_moving:
            return  # 既に移動中の場合は処理をスキップ
        
        self._is_moving = True
        
        try:
            # メイン図形を移動
            item = self.get_item()
            current_pos = item.pos()
            new_pos = QPointF(current_pos.x() + delta_x, current_pos.y() + delta_y)
            item.setPos(new_pos)
            
            # 制御点は既にQGraphicsEllipseItem.mouseMoveEvent()で移動済みなので除外
            
            # パーツ名を移動
            if self.name_text_item:
                name_pos = self.name_text_item.pos()
                self.name_text_item.setPos(name_pos.x() + delta_x, name_pos.y() + delta_y)
            
            # リサイズハンドルを移動
            for handle in self.handles:
                handle_pos = handle.pos()
                handle.setPos(handle_pos.x() + delta_x, handle_pos.y() + delta_y)
            
            # circumferenceポイントも移動（meter用）
            if hasattr(self, 'circumference_items') and self.circumference_items:
                for circ_item in self.circumference_items:
                    circ_pos = circ_item.pos()
                    circ_item.setPos(circ_pos.x() + delta_x, circ_pos.y() + delta_y)
            
            print(f"move_associated_items: moved associated items by ({delta_x:.1f}, {delta_y:.1f})")
            
        finally:
            # フラグを必ずリセット
            self._is_moving = False
    
    def update_center_control_point(self):
        """重心位置制御点を更新"""
        if not self.get_item().scene():
            return
            
        # 既存の制御点を削除
        if self.center_control_point:
            self.get_item().scene().removeItem(self.center_control_point)
            self.center_control_point = None
        
        # 常に重心位置に制御点を表示
        item = self.get_item()
        rect = item.boundingRect()
        pos = item.pos()
        
        # 重心位置を計算
        center_x = pos.x() + rect.center().x()
        center_y = pos.y() + rect.center().y()
        
        # 制御点（選択状態に応じてサイズと色を変更）を作成
        if self.is_selected:
            # 選択時: より大きく、カテゴリ色で表示
            control_point_size = 28
            control_color = self.get_category_color()
        else:
            # 未選択時: 通常サイズ、白色で表示
            control_point_size = 24
            control_color = QColor(255, 255, 255)
            
        self.center_control_point = QGraphicsEllipseItem(
            center_x - control_point_size/2,
            center_y - control_point_size/2,
            control_point_size,
            control_point_size
        )
        
        # 制御点のスタイル設定（main.py完全準拠）
        self.center_control_point.setBrush(QBrush(control_color))
        self.center_control_point.setPen(QPen(QColor(0, 0, 0), 3))  # main.pyと同じ太さ
        
        # ホバー時のスタイル変更用のフラグ設定（main.py準拠）
        self.center_control_point.setAcceptHoverEvents(True)
        
        # ホバーイベントハンドラを設定（main.py準拠）
        hover_handler = CenterControlPointHover(self.center_control_point, self)
        self.center_control_point.hoverEnterEvent = hover_handler.hoverEnterEvent
        self.center_control_point.hoverLeaveEvent = hover_handler.hoverLeaveEvent
        
        # 制御点を確実に最前面に設定（main.pyと同じ値）
        self.center_control_point.setZValue(2000)
        
        # ドラッグ可能に設定（選択は無効化：Canvas側で処理）
        from PySide6.QtWidgets import QGraphicsItem
        self.center_control_point.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.center_control_point.setFlag(QGraphicsItem.ItemIsSelectable, False)
        
        # シーンに追加
        self.get_item().scene().addItem(self.center_control_point)
        
        # 制御点のドラッグイベントをカスタムクラスで置き換え（main.py準拠）
        control_point_handler = CenterControlPointHandler(self.center_control_point, self)
        # ドラッグ処理を有効化（選択は既にCanvas側で処理済み）
        self.center_control_point.mousePressEvent = control_point_handler.mousePressEvent
        self.center_control_point.mouseMoveEvent = control_point_handler.mouseMoveEvent
        self.center_control_point.mouseReleaseEvent = control_point_handler.mouseReleaseEvent
        
        # 表示制御
        self.center_control_point.setVisible(self.visible)
    
    def create_name_text(self, name: str):
        """パーツ名テキストを作成"""
        if not self.get_item().scene():
            return
            
        # 既存のテキストを削除
        if self.name_text_item:
            self.get_item().scene().removeItem(self.name_text_item)
            self.name_text_item = None
        
        # テキストアイテム作成
        self.name_text_item = QGraphicsTextItem(name)
        
        # フォント設定
        font = QFont("Arial", 12, QFont.Bold)
        self.name_text_item.setFont(font)
        self.name_text_item.setDefaultTextColor(QColor(255, 255, 0))  # 黄色
        
        # 位置設定（図形の上部）
        self.update_name_display()
        
        # シーンに追加
        self.get_item().scene().addItem(self.name_text_item)
    
    def update_name_display(self):
        """パーツ名表示位置を更新"""
        if not self.name_text_item:
            return
            
        item = self.get_item()
        rect = item.boundingRect()
        pos = item.pos()
        
        # 図形の上部中央に配置
        text_x = pos.x() + rect.center().x() - self.name_text_item.boundingRect().width() / 2
        text_y = pos.y() - self.name_text_item.boundingRect().height() - 5
        
        self.name_text_item.setPos(text_x, text_y)


class ResizableRectItem(ResizableGraphicsItem):
    """リサイズ可能な矩形（icon/ocr用）"""
    
    def __init__(self, x: float, y: float, width: float, height: float,
                 scene_scale: float = 1.0, category: ShapeCategory = ShapeCategory.CUSTOM,
                 is_original_coords: bool = False, main_view=None):
        super().__init__(x, y, width, height, scene_scale, category, main_view)
        
        self.shape_type = ShapeType.BOX
        
        # 座標変換
        if is_original_coords:
            display_x = x
            display_y = y
            display_width = width
            display_height = height
        else:
            display_x = x * scene_scale
            display_y = y * scene_scale
            display_width = width * scene_scale
            display_height = height * scene_scale
        
        # 矩形アイテム作成
        self.rect_item = QGraphicsRectItem(0, 0, display_width, display_height)
        self.rect_item.setPos(display_x, display_y)
        
        # 初期表示設定
        self.update_display()
    
    def get_item(self) -> QGraphicsRectItem:
        return self.rect_item
    
    def _create_specific_handles(self):
        """矩形用8方向ハンドル作成"""
        item = self.get_item()
        rect = item.boundingRect()
        pos = item.pos()
        
        # 8つのハンドル位置
        handle_types = [
            "top_left", "top_center", "top_right", "middle_right",
            "bottom_right", "bottom_center", "bottom_left", "middle_left"
        ]
        
        positions = [
            (pos.x() + rect.left(), pos.y() + rect.top()),        # 左上
            (pos.x() + rect.center().x(), pos.y() + rect.top()),  # 上中央
            (pos.x() + rect.right(), pos.y() + rect.top()),       # 右上
            (pos.x() + rect.right(), pos.y() + rect.center().y()),# 右中央
            (pos.x() + rect.right(), pos.y() + rect.bottom()),    # 右下
            (pos.x() + rect.center().x(), pos.y() + rect.bottom()),# 下中央
            (pos.x() + rect.left(), pos.y() + rect.bottom()),     # 左下
            (pos.x() + rect.left(), pos.y() + rect.center().y())  # 左中央
        ]
        
        for i, (handle_type, (hx, hy)) in enumerate(zip(handle_types, positions)):
            handle = QGraphicsRectItem(
                hx - self.handle_size/2, 
                hy - self.handle_size/2, 
                self.handle_size, 
                self.handle_size
            )
            handle.setBrush(QBrush(QColor(255, 255, 255)))  # 白色（main.pyと同じ）
            handle.setPen(QPen(QColor(0, 0, 0), 1))       # 黒枠
            handle.setZValue(1001)  # 制御点より前面
            
            # ドラッグ可能に設定
            handle.setFlag(handle.GraphicsItemFlag.ItemIsMovable, True)
            handle.setAcceptHoverEvents(True)
            
            # ハンドルタイプをデータとして保存
            handle.setData(0, handle_type)
            
            # リサイズハンドラーを設定
            resize_handler = ResizeHandler(handle, self, handle_type)
            handle.mousePressEvent = resize_handler.mousePressEvent
            handle.mouseMoveEvent = resize_handler.mouseMoveEvent
            handle.mouseReleaseEvent = resize_handler.mouseReleaseEvent
            
            self.handles.append(handle)
            self.get_item().scene().addItem(handle)


class ResizableEllipseItem(ResizableGraphicsItem):
    """リサイズ可能な円（meter用、circumferenceポイント付き）"""
    
    def __init__(self, x: float, y: float, width: float, height: float,
                 scene_scale: float = 1.0, category: ShapeCategory = ShapeCategory.CUSTOM,
                 is_original_coords: bool = False, circumference_points: List[CircumferencePoint] = None,
                 main_view=None):
        super().__init__(x, y, width, height, scene_scale, category, main_view)
        
        self.shape_type = ShapeType.CIRCLE
        self.circumference_points = circumference_points or []
        self.circumference_items = []  # 表示用アイテム
        
        # 座標変換
        if is_original_coords:
            display_x = x
            display_y = y
            display_width = width
            display_height = height
        else:
            display_x = x * scene_scale
            display_y = y * scene_scale
            display_width = width * scene_scale
            display_height = height * scene_scale
        
        # 円形アイテム作成
        self.ellipse_item = QGraphicsEllipseItem(0, 0, display_width, display_height)
        self.ellipse_item.setPos(display_x, display_y)
        
        # 初期表示設定
        self.update_display()
    
    def get_item(self) -> QGraphicsEllipseItem:
        return self.ellipse_item
    
    def update_circumference_display(self):
        """circumferenceポイントの表示を更新（選択時のみ）"""
        # 既存の表示を削除
        for item in self.circumference_items:
            if item.scene():
                item.scene().removeItem(item)
        self.circumference_items.clear()
        
        if not self.ellipse_item.scene():
            return
        
        # 選択されていない場合は表示しない（デバッグ用に一時的にコメントアウト）
        # if not self.is_selected:
        #     return
        
        print(f"DEBUG EllipseItem: update_circumference_display called, is_selected={self.is_selected}, points={len(self.circumference_points)}")
        
        # 円の中心と半径を計算
        rect = self.ellipse_item.boundingRect()
        pos = self.ellipse_item.pos()
        center_x = pos.x() + rect.width() / 2
        center_y = pos.y() + rect.height() / 2
        radius = rect.width() / 2  # 正円なので幅から半径を計算
        
        import math
        
        # circumferenceポイントをvalue順にソート
        sorted_points = sorted(self.circumference_points, key=lambda p: p.value)
        
        print(f"Circle center: ({center_x:.2f}, {center_y:.2f}), radius: {radius:.2f}")
        print(f"Circumference points: {len(sorted_points)}")
        
        # 各circumferenceポイントを現在の円の中心・半径に基づいて配置
        for i, point in enumerate(sorted_points):
            try:
                # 元の位置から角度を計算
                original_x = point.position.get('x', 0)
                original_y = point.position.get('y', 0)
                
                # vehicle.jsonの元座標系での円の中心を計算
                original_center_x = self.original_x + self.original_width / 2
                original_center_y = self.original_y + self.original_height / 2
                
                # 元座標系での角度を計算
                dx = original_x - original_center_x
                dy = original_y - original_center_y
                angle = math.atan2(dy, dx)
                
                # 現在の半径で円周上に配置
                point_x = center_x + radius * math.cos(angle)
                point_y = center_y + radius * math.sin(angle)
                
                # ポイントサイズ（valueによって変化）
                if point.value == 0 or point.value == 1:
                    # 開始点と終了点は大きく、赤色
                    point_size = 16
                    point_color = QColor(255, 100, 100)
                else:
                    # 中間点は通常サイズ、青色
                    point_size = 12
                    point_color = QColor(100, 150, 255)
                
                # circumferenceポイントアイテム作成
                point_item = QGraphicsEllipseItem(
                    point_x - point_size/2,
                    point_y - point_size/2,
                    point_size,
                    point_size
                )
                
                # スタイル設定
                point_item.setBrush(QBrush(point_color))
                point_item.setPen(QPen(QColor(255, 255, 255), 2))  # 白枠
                point_item.setZValue(1002)  # ハンドルより前面
                
                # シーンに追加
                self.ellipse_item.scene().addItem(point_item)
                self.circumference_items.append(point_item)
                
                # valueテキストを表示
                value_text = QGraphicsTextItem(f"{point.value:.2f}")
                value_text.setDefaultTextColor(QColor(255, 255, 0))  # 黄色で見やすく
                value_text.setFont(QFont("Arial", 14, QFont.Bold))   # 14pxに拡大
                
                # 背景色（黒い背景で見やすく）
                bg_rect = QGraphicsRectItem(value_text.boundingRect(), value_text)
                bg_rect.setBrush(QBrush(QColor(0, 0, 0, 180)))  # 半透明の黒
                bg_rect.setPen(QPen(QColor(255, 255, 255, 100), 1))  # 薄い白枠
                bg_rect.setZValue(-1)  # テキストより後ろ
                
                # テキスト位置（ポイントの近く）
                text_rect = value_text.boundingRect()
                value_text.setPos(
                    point_x + point_size/2 + 5,
                    point_y - text_rect.height()/2
                )
                value_text.setZValue(1003)  # 最前面
                
                # シーンに追加
                self.ellipse_item.scene().addItem(value_text)
                self.circumference_items.append(value_text)
                
                print(f"  Point {i}: value={point.value:.2f}, pos=({point_x:.1f}, {point_y:.1f})")
                
            except Exception as e:
                print(f"Error displaying circumference point {i}: {e}")
    
    def set_selected(self, selected: bool):
        """選択状態を設定（circumferenceポイント表示更新）"""
        super().set_selected(selected)
        # circumferenceポイント表示を更新
        self.update_circumference_display()
    
    def _create_specific_handles(self):
        """円形用2方向ハンドル作成（半径変更用）"""
        item = self.get_item()
        rect = item.boundingRect()
        pos = item.pos()
        
        # 円形: 左右の2つのハンドルのみ（半径変更用）
        positions = [
            (pos.x() + rect.right(), pos.y() + rect.center().y()),  # 右中央
            (pos.x() + rect.left(), pos.y() + rect.center().y()),   # 左中央
        ]
        handle_types = ["middle_right", "middle_left"]
        
        for i, (hx, hy) in enumerate(positions):
            handle = QGraphicsRectItem(
                hx - self.handle_size/2, 
                hy - self.handle_size/2, 
                self.handle_size, 
                self.handle_size
            )
            handle.setBrush(QBrush(QColor(255, 255, 255)))  # 白色
            handle.setPen(QPen(QColor(0, 0, 0), 1))       # 黒枠
            handle.setZValue(1001)  # 制御点より前面
            
            # ドラッグ可能に設定
            handle.setFlag(handle.GraphicsItemFlag.ItemIsMovable, True)
            handle.setAcceptHoverEvents(True)
            
            # リサイズハンドラーを設定
            resize_handler = ResizeHandler(handle, self, handle_types[i])
            handle.mousePressEvent = resize_handler.mousePressEvent
            handle.mouseMoveEvent = resize_handler.mouseMoveEvent
            handle.mouseReleaseEvent = resize_handler.mouseReleaseEvent
            
            self.handles.append(handle)
            self.get_item().scene().addItem(handle)


class BarShapeItem(ResizableGraphicsItem):
    """バーグラフタイプの図形（水平または垂直バー、meter用）"""
    
    def __init__(self, x: float, y: float, width: float, height: float,
                 scene_scale: float = 1.0, category: ShapeCategory = ShapeCategory.METER,
                 is_original_coords: bool = False, circumference_points: List[CircumferencePoint] = None,
                 main_view=None):
        super().__init__(x, y, width, height, scene_scale, category, main_view)
        
        self.shape_type = ShapeType.BAR
        self.circumference_points = circumference_points or []
        self.circumference_items = []  # 表示用アイテム
        self.orientation = "horizontal"  # "horizontal" or "vertical"
        
        # 座標変換
        if is_original_coords:
            display_x = x
            display_y = y
            display_width = width
            display_height = height
        else:
            display_x = x * scene_scale
            display_y = y * scene_scale
            display_width = width * scene_scale
            display_height = height * scene_scale
        
        # 矩形ベースのバー作成
        self.rect_item = QGraphicsRectItem(0, 0, display_width, display_height)
        self.rect_item.setPos(display_x, display_y)
        
        # バー形状の特別な設定
        self.create_bar_shape(display_width, display_height)
        
        # 初期表示設定
        self.update_display()
    
    def get_item(self) -> QGraphicsRectItem:
        return self.rect_item
    
    def create_bar_shape(self, width: float, height: float):
        """バー形状を作成（方向判定と分割線）"""
        # アスペクト比によるorientation自動判定
        aspect_ratio = width / height if height > 0 else 1.0
        self.orientation = "horizontal" if aspect_ratio > 1.0 else "vertical"
    
    def update_circumference_display(self):
        """circumferenceポイントの表示を更新（バー用、直線上配置）"""
        # 既存の表示を削除
        for item in self.circumference_items:
            if item.scene():
                item.scene().removeItem(item)
        self.circumference_items.clear()
        
        if not self.rect_item.scene():
            return
        
        # 選択されていない場合は表示しない（デバッグ用に一時的にコメントアウト）
        # if not self.is_selected:
        #     return
        
        print(f"DEBUG BarItem: update_circumference_display called, is_selected={self.is_selected}, points={len(self.circumference_points)}")
        
        # バーの位置とサイズを取得
        rect = self.rect_item.boundingRect()
        pos = self.rect_item.pos()
        
        # circumferenceポイントをvalue順にソート
        sorted_points = sorted(self.circumference_points, key=lambda p: p.value)
        
        print(f"Bar rect: ({pos.x():.2f}, {pos.y():.2f}), size: {rect.width():.2f} x {rect.height():.2f}")
        print(f"Bar circumference points: {len(sorted_points)}")
        
        # 各circumferenceポイントを直線上に配置
        for i, point in enumerate(sorted_points):
            try:
                # value値に基づいて直線上の位置を計算
                value = point.value
                
                if self.orientation == "horizontal":
                    # 水平バー: 左から右へvalue値で位置決定
                    point_x = pos.x() + rect.width() * value
                    point_y = pos.y() + rect.height() / 2
                else:
                    # 垂直バー: 下から上へvalue値で位置決定
                    point_x = pos.x() + rect.width() / 2
                    point_y = pos.y() + rect.height() * (1.0 - value)  # 反転（上が高い値）
                
                # ポイントサイズ（valueによって変化）
                if point.value == 0 or point.value == 1:
                    # 開始点と終了点は大きく、赤色
                    point_size = 16
                    point_color = QColor(255, 100, 100)
                else:
                    # 中間点は通常サイズ、緑色（バー用）
                    point_size = 12
                    point_color = QColor(100, 255, 100)
                
                # circumferenceポイントアイテム作成
                point_item = QGraphicsEllipseItem(
                    point_x - point_size/2,
                    point_y - point_size/2,
                    point_size,
                    point_size
                )
                
                # スタイル設定
                point_item.setBrush(QBrush(point_color))
                point_item.setPen(QPen(QColor(255, 255, 255), 2))  # 白枠
                point_item.setZValue(1002)  # ハンドルより前面
                
                # シーンに追加
                self.rect_item.scene().addItem(point_item)
                self.circumference_items.append(point_item)
                
                # valueテキストを表示
                value_text = QGraphicsTextItem(f"{point.value:.2f}")
                value_text.setDefaultTextColor(QColor(255, 255, 0))  # 黄色で見やすく
                value_text.setFont(QFont("Arial", 14, QFont.Bold))   # 14pxに拡大
                
                # 背景色（黒い背景で見やすく）
                bg_rect = QGraphicsRectItem(value_text.boundingRect(), value_text)
                bg_rect.setBrush(QBrush(QColor(0, 0, 0, 180)))  # 半透明の黒
                bg_rect.setPen(QPen(QColor(255, 255, 255, 100), 1))  # 薄い白枠
                bg_rect.setZValue(-1)  # テキストより後ろ
                
                # テキスト位置（ポイントの近く）
                text_rect = value_text.boundingRect()
                if self.orientation == "horizontal":
                    value_text.setPos(
                        point_x - text_rect.width()/2,
                        point_y + point_size/2 + 5
                    )
                else:
                    value_text.setPos(
                        point_x + point_size/2 + 5,
                        point_y - text_rect.height()/2
                    )
                value_text.setZValue(1003)  # 最前面
                
                # シーンに追加
                self.rect_item.scene().addItem(value_text)
                self.circumference_items.append(value_text)
                
                print(f"  Bar Point {i}: value={point.value:.2f}, pos=({point_x:.1f}, {point_y:.1f})")
                
            except Exception as e:
                print(f"Error displaying bar circumference point {i}: {e}")
    
    def set_selected(self, selected: bool):
        """選択状態を設定（circumferenceポイント表示更新）"""
        super().set_selected(selected)
        # circumferenceポイント表示を更新
        self.update_circumference_display()
    
    def _create_specific_handles(self):
        """バー用ハンドル作成（矩形と同じ8方向）"""
        # 矩形と同じハンドル作成ロジック
        item = self.get_item()
        rect = item.boundingRect()
        pos = item.pos()
        
        # 8つのハンドル位置
        handle_types = [
            "top_left", "top_center", "top_right", "middle_right",
            "bottom_right", "bottom_center", "bottom_left", "middle_left"
        ]
        
        positions = [
            (pos.x() + rect.left(), pos.y() + rect.top()),        # 左上
            (pos.x() + rect.center().x(), pos.y() + rect.top()),  # 上中央
            (pos.x() + rect.right(), pos.y() + rect.top()),       # 右上
            (pos.x() + rect.right(), pos.y() + rect.center().y()),# 右中央
            (pos.x() + rect.right(), pos.y() + rect.bottom()),    # 右下
            (pos.x() + rect.center().x(), pos.y() + rect.bottom()),# 下中央
            (pos.x() + rect.left(), pos.y() + rect.bottom()),     # 左下
            (pos.x() + rect.left(), pos.y() + rect.center().y())  # 左中央
        ]
        
        for i, (hx, hy) in enumerate(positions):
            handle = QGraphicsRectItem(
                hx - self.handle_size/2, 
                hy - self.handle_size/2, 
                self.handle_size, 
                self.handle_size
            )
            handle.setBrush(QBrush(QColor(255, 255, 255)))  # 白色
            handle.setPen(QPen(QColor(0, 0, 0), 1))       # 黒枠
            handle.setZValue(1001)  # 制御点より前面
            
            # ドラッグ可能に設定
            handle.setFlag(handle.GraphicsItemFlag.ItemIsMovable, True)
            handle.setAcceptHoverEvents(True)
            
            # リサイズハンドラーを設定
            resize_handler = ResizeHandler(handle, self, handle_types[i])
            handle.mousePressEvent = resize_handler.mousePressEvent
            handle.mouseMoveEvent = resize_handler.mouseMoveEvent
            handle.mouseReleaseEvent = resize_handler.mouseReleaseEvent
            
            self.handles.append(handle)
            self.get_item().scene().addItem(handle)


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
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)
        
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
        
        self.main_layout.addLayout(toolbar_layout)
        
        # フルサイズ画像キャンバス
        self.image_canvas = ModernEditImageCanvas()
        self.image_canvas.setMinimumSize(800, 600)
        self.image_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 初期プレースホルダー表示
        self._show_placeholder()
        
        # 画像キャンバスを直接追加（パーツパネルは左サイドバーに移動）
        self.main_layout.addWidget(self.image_canvas)
    
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
        print(f"=== EDIT MAIN VIEW: VEHICLE JSON LOAD START ===")
        self.vehicle_data = vehicle_data
        vehicle_name = vehicle_data.get("name", "Unknown")
        print(f"EDIT main view: Vehicle data loaded for {vehicle_name}")
        
        # パーツ選択はサイドバーで行う（右側パネル廃止）
        
        # 図形をキャンバスに表示
        print("=== Displaying vehicle shapes on canvas ===")
        self._display_vehicle_shapes()
        
        print(f"Vehicle JSON loaded: {len(vehicle_data.get('icon', []))} icons, "
              f"{len(vehicle_data.get('meter', []))} meters, "
              f"{len(vehicle_data.get('ocr', []))} ocrs")
        print(f"=== EDIT MAIN VIEW: VEHICLE JSON LOAD COMPLETE ===")
    
    def _create_parts_selection_panel(self):
        """パーツ選択パネルを作成"""
        if hasattr(self, '_parts_panel'):
            return  # 既に作成済み
            
        # パーツ選択パネル
        self._parts_panel = QGroupBox("Vehicle Parts")
        # StyleSheetは後で追加
        # self._parts_panel.setStyleSheet(ComponentStyles.sidebar())
        
        panel_layout = QVBoxLayout()
        
        # カテゴリ別チェックボックス
        category_group = QGroupBox("カテゴリ表示")
        category_layout = QVBoxLayout()
        
        self._icon_checkbox = QCheckBox("Icon (矩形)")
        self._icon_checkbox.setChecked(True)
        self._icon_checkbox.stateChanged.connect(lambda: self._toggle_category_visibility('icon'))
        
        self._meter_checkbox = QCheckBox("Meter (円形)")
        self._meter_checkbox.setChecked(True)
        self._meter_checkbox.stateChanged.connect(lambda: self._toggle_category_visibility('meter'))
        
        self._ocr_checkbox = QCheckBox("OCR (矩形)")
        self._ocr_checkbox.setChecked(True)
        self._ocr_checkbox.stateChanged.connect(lambda: self._toggle_category_visibility('ocr'))
        
        category_layout.addWidget(self._icon_checkbox)
        category_layout.addWidget(self._meter_checkbox)
        category_layout.addWidget(self._ocr_checkbox)
        category_group.setLayout(category_layout)
        
        # パーツリストツリー
        self._parts_tree = QTreeWidget()
        self._parts_tree.setHeaderLabels(["名前", "カテゴリ", "タイプ"])
        self._parts_tree.itemClicked.connect(self._on_tree_item_clicked)
        self._parts_tree.setMaximumHeight(300)
        
        panel_layout.addWidget(category_group)
        panel_layout.addWidget(QLabel("パーツリスト:"))
        panel_layout.addWidget(self._parts_tree)
        panel_layout.addStretch()
        
        self._parts_panel.setLayout(panel_layout)
        
        # パーツパネルを右側に追加（コンテンツレイアウトに1の比率で）
        self.content_layout.addWidget(self._parts_panel, 1)
    
    def _update_parts_list(self):
        """パーツリストを更新"""
        if not hasattr(self, '_parts_tree') or not self.vehicle_data:
            return
            
        self._parts_tree.clear()
        
        # カテゴリ別にグループ化
        categories = {
            'icon': QTreeWidgetItem(["Icons", "", ""]),
            'meter': QTreeWidgetItem(["Meters", "", ""]),
            'ocr': QTreeWidgetItem(["OCR", "", ""])
        }
        
        # Iconパーツを追加
        for i, icon in enumerate(self.vehicle_data.get('icon', [])):
            item = QTreeWidgetItem([
                icon.get('name', f'Icon {i+1}'),
                'Icon',
                icon.get('shape', 'box')
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'icon', 'data': icon, 'index': i})
            categories['icon'].addChild(item)
        
        # Meterパーツを追加
        for i, meter in enumerate(self.vehicle_data.get('meter', [])):
            item = QTreeWidgetItem([
                meter.get('name', f'Meter {i+1}'),
                'Meter',
                meter.get('shape', 'circle')
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'meter', 'data': meter, 'index': i})
            categories['meter'].addChild(item)
        
        # OCRパーツを追加
        for i, ocr in enumerate(self.vehicle_data.get('ocr', [])):
            item = QTreeWidgetItem([
                ocr.get('name', f'OCR {i+1}'),
                'OCR',
                ocr.get('shape', 'box')
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'ocr', 'data': ocr, 'index': i})
            categories['ocr'].addChild(item)
        
        # カテゴリをツリーに追加
        for category, parent in categories.items():
            if parent.childCount() > 0:
                self._parts_tree.addTopLevelItem(parent)
                parent.setExpanded(True)
    
    def _toggle_category_visibility(self, category: str):
        """カテゴリの表示/非表示を切り替え"""
        checkbox_map = {
            'icon': self._icon_checkbox,
            'meter': self._meter_checkbox,
            'ocr': self._ocr_checkbox
        }
        
        checkbox = checkbox_map.get(category)
        if checkbox:
            visible = checkbox.isChecked()
            self._set_shapes_visibility(category, visible)
            print(f"Toggle {category} visibility: {visible}")
    
    def _set_shapes_visibility(self, category: str, visible: bool):
        """指定カテゴリの図形の表示/非表示を設定"""
        if not hasattr(self, '_vehicle_shapes'):
            return
            
        for shape in self._vehicle_shapes:
            shape_data = shape.data(0)
            if shape_data and shape_data.get('type') == category:
                shape.setVisible(visible)
    
    def _on_tree_item_clicked(self, item, column):
        """ツリーアイテムがクリックされた時の処理"""
        part_data = item.data(0, Qt.ItemDataRole.UserRole)
        if part_data:
            part_type = part_data['type']
            data = part_data['data']
            index = part_data['index']
            
            print(f"Selected {part_type} part: {data.get('name', f'{part_type} {index+1}')}")
            
            # キャンバス上で対応する図形をハイライト
            self._highlight_shape(part_type, index)
            
            # 図形位置にビューをセンタリング
            self._center_view_on_shape(part_type, index)
    
    def _highlight_shape(self, part_type: str, index: int):
        """指定された図形をハイライト"""
        if not hasattr(self, '_vehicle_shapes'):
            return
            
        # 全ての図形のハイライトを解除
        for shape in self._vehicle_shapes:
            self._set_shape_highlight(shape, False)
        
        # 指定された図形をハイライト
        for shape in self._vehicle_shapes:
            shape_data = shape.data(0)
            if shape_data and shape_data.get('type') == part_type and shape_data.get('index') == index:
                self._set_shape_highlight(shape, True)
                break
    
    def _set_shape_highlight(self, shape, highlighted: bool):
        """図形のハイライト状態を設定"""
        from PySide6.QtGui import QPen
        from PySide6.QtCore import Qt
        
        if highlighted:
            # ハイライト時は太い黄色の枠線
            pen = QPen(QColor(255, 255, 0), 5, Qt.PenStyle.DashLine)
        else:
            # 通常時は元の色と太さに戻す
            shape_data = shape.data(0)
            if shape_data:
                shape_type = shape_data.get('type')
                if shape_type == 'icon':
                    pen = QPen(QColor(0, 255, 0), 3)
                elif shape_type == 'meter':
                    pen = QPen(QColor(0, 0, 255), 3) if shape_data['data'].get('shape') != 'bar' else QPen(QColor(255, 165, 0), 3)
                elif shape_type == 'ocr':
                    pen = QPen(QColor(255, 0, 0), 3)
                else:
                    pen = QPen(QColor(128, 128, 128), 3)
            else:
                pen = QPen(QColor(128, 128, 128), 3)
        
        shape.setPen(pen)
    
    def _center_view_on_shape(self, part_type: str, index: int):
        """指定された図形の位置にビューをセンタリング"""
        if not hasattr(self, '_vehicle_shapes'):
            return
            
        for shape in self._vehicle_shapes:
            shape_data = shape.data(0)
            if shape_data and shape_data.get('type') == part_type and shape_data.get('index') == index:
                # 図形の中心位置を計算
                rect = shape.boundingRect()
                center = rect.center()
                
                # ビューを図形の中心にセンタリング
                if self.image_canvas and hasattr(self.image_canvas, 'graphics_view'):
                    self.image_canvas.graphics_view.centerOn(center)
                
                print(f"View centered on {part_type} {index+1}")
                break
    
    def _display_vehicle_shapes(self):
        """vehicle.jsonの図形をキャンバスに表示（新ResizableGraphicsItemシステム使用）"""
        if not self.image_canvas or not self.vehicle_data:
            return
            
        # 既存の図形をクリア（もしあれば）
        self._clear_vehicle_shapes()
        
        # 図形を格納するリスト（ResizableGraphicsItemオブジェクト）
        self._vehicle_shapes = []
        
        # 現在のスケール取得（フルサイズ表示は1.0）
        scene_scale = 1.0
        
        # アイコン（矩形）を追加
        for i, icon in enumerate(self.vehicle_data.get('icon', [])):
            try:
                shape_item = self._create_resizable_icon_shape(icon, i, scene_scale)
                if shape_item:
                    # QGraphicsItemをシーンに追加
                    self.image_canvas.scene.addItem(shape_item.get_item())
                    self._vehicle_shapes.append(shape_item)
                    
                    # パーツ名と制御点を作成
                    shape_item.create_name_text(icon.get('name', f'Icon {i+1}'))
                    shape_item.update_center_control_point()
                    
                    print(f"Resizable Icon shape added: {icon.get('name', f'Icon {i+1}')}")
            except Exception as e:
                print(f"Error creating resizable icon shape {i}: {e}")
        
        # メーター（円形・バー）を追加
        for i, meter in enumerate(self.vehicle_data.get('meter', [])):
            try:
                shape_item = self._create_resizable_meter_shape(meter, i, scene_scale)
                if shape_item:
                    # QGraphicsItemをシーンに追加
                    self.image_canvas.scene.addItem(shape_item.get_item())
                    self._vehicle_shapes.append(shape_item)
                    
                    # パーツ名と制御点を作成
                    shape_item.create_name_text(meter.get('name', f'Meter {i+1}'))
                    shape_item.update_center_control_point()
                    
                    # circumferenceポイントを初期表示（main.pyと同じ処理順序）
                    if hasattr(shape_item, 'update_circumference_display'):
                        shape_item.update_circumference_display()
                    
                    print(f"Resizable Meter shape added: {meter.get('name', f'Meter {i+1}')}")
            except Exception as e:
                print(f"Error creating resizable meter shape {i}: {e}")
        
        # OCR（矩形）を追加
        for i, ocr in enumerate(self.vehicle_data.get('ocr', [])):
            try:
                shape_item = self._create_resizable_ocr_shape(ocr, i, scene_scale)
                if shape_item:
                    # QGraphicsItemをシーンに追加
                    self.image_canvas.scene.addItem(shape_item.get_item())
                    self._vehicle_shapes.append(shape_item)
                    
                    # パーツ名と制御点を作成
                    shape_item.create_name_text(ocr.get('name', f'OCR {i+1}'))
                    shape_item.update_center_control_point()
                    
                    print(f"Resizable OCR shape added: {ocr.get('name', f'OCR {i+1}')}")
            except Exception as e:
                print(f"Error creating resizable OCR shape {i}: {e}")
        
        print(f"Resizable Vehicle shapes displayed: {len(self._vehicle_shapes)} shapes")
    
    def _clear_vehicle_shapes(self):
        """既存の図形をクリア（新ResizableGraphicsItemシステム対応）"""
        if hasattr(self, '_vehicle_shapes'):
            for shape in self._vehicle_shapes:
                try:
                    # ResizableGraphicsItemオブジェクトの場合
                    if hasattr(shape, 'get_item'):
                        graphics_item = shape.get_item()
                        if graphics_item.scene():
                            graphics_item.scene().removeItem(graphics_item)
                        
                        # 制御点も削除
                        if shape.center_control_point and shape.center_control_point.scene():
                            shape.center_control_point.scene().removeItem(shape.center_control_point)
                        
                        # パーツ名テキストも削除
                        if shape.name_text_item and shape.name_text_item.scene():
                            shape.name_text_item.scene().removeItem(shape.name_text_item)
                        
                        # ハンドルも削除
                        for handle in shape.handles:
                            if handle.scene():
                                handle.scene().removeItem(handle)
                        
                        # circumferenceアイテムも削除
                        if hasattr(shape, 'circumference_items'):
                            for circ_item in shape.circumference_items:
                                if circ_item.scene():
                                    circ_item.scene().removeItem(circ_item)
                    
                    # 旧システム対応（QGraphicsItemの場合）
                    elif hasattr(shape, 'scene') and shape.scene():
                        shape.scene().removeItem(shape)
                except:
                    pass
            self._vehicle_shapes.clear()
    
    def _create_resizable_icon_shape(self, icon_data: dict, index: int, scene_scale: float):
        """ResizableGraphicsItemシステム用Icon形状作成"""
        try:
            top_left = icon_data.get('top_left', {})
            bottom_right = icon_data.get('bottom_right', {})
            
            x = top_left.get('x', 0)
            y = top_left.get('y', 0)
            w = bottom_right.get('x', 0) - x
            h = bottom_right.get('y', 0) - y
            
            # ResizableRectItemを作成（icon用）
            shape_item = ResizableRectItem(
                x, y, w, h,
                scene_scale=scene_scale,
                category=ShapeCategory.ICON,
                is_original_coords=True,  # vehicle.jsonの座標は元座標
                main_view=self  # ModernEditMainViewの参照を渡す
            )
            
            return shape_item
            
        except Exception as e:
            print(f"Error creating resizable icon shape: {e}")
            return None
    
    def _create_resizable_meter_shape(self, meter_data: dict, index: int, scene_scale: float):
        """ResizableGraphicsItemシステム用Meter形状作成"""
        try:
            shape_type = meter_data.get('shape', 'circle')
            
            # circumferenceポイント変換
            circumference_points = []
            for cp_data in meter_data.get('circumference', []):
                cp = CircumferencePoint(
                    position=cp_data.get('position', {}),
                    value=cp_data.get('value', 0.0)
                )
                circumference_points.append(cp)
            
            if shape_type == 'circle':
                # 円形メーター
                center = meter_data.get('center', {})
                radius = meter_data.get('radius', 100)
                
                x = center.get('x', 0) - radius
                y = center.get('y', 0) - radius
                w = h = radius * 2
                
                shape_item = ResizableEllipseItem(
                    x, y, w, h,
                    scene_scale=scene_scale,
                    category=ShapeCategory.METER,
                    is_original_coords=True,
                    circumference_points=circumference_points,
                    main_view=self
                )
                
            elif shape_type == 'bar':
                # バー形状メーター
                center = meter_data.get('center', {})
                radius = meter_data.get('radius', 50)  # バーの場合は半分の長さ
                
                # バーのサイズを仮設定（実際はcircumferenceポイントから決定）
                x = center.get('x', 0) - radius
                y = center.get('y', 0) - 25
                w = radius * 2
                h = 50
                
                shape_item = BarShapeItem(
                    x, y, w, h,
                    scene_scale=scene_scale,
                    category=ShapeCategory.METER,
                    is_original_coords=True,
                    circumference_points=circumference_points,
                    main_view=self
                )
                
            else:
                print(f"Unknown meter shape type: {shape_type}")
                return None
            
            return shape_item
            
        except Exception as e:
            print(f"Error creating resizable meter shape: {e}")
            return None
    
    def _create_resizable_ocr_shape(self, ocr_data: dict, index: int, scene_scale: float):
        """ResizableGraphicsItemシステム用OCR形状作成"""
        try:
            top_left = ocr_data.get('top_left', {})
            bottom_right = ocr_data.get('bottom_right', {})
            
            x = top_left.get('x', 0)
            y = top_left.get('y', 0)
            w = bottom_right.get('x', 0) - x
            h = bottom_right.get('y', 0) - y
            
            # ResizableRectItemを作成（ocr用）
            shape_item = ResizableRectItem(
                x, y, w, h,
                scene_scale=scene_scale,
                category=ShapeCategory.OCR,
                is_original_coords=True,  # vehicle.jsonの座標は元座標
                main_view=self
            )
            
            return shape_item
            
        except Exception as e:
            print(f"Error creating resizable OCR shape: {e}")
            return None
    
    def _create_icon_shape(self, icon_data: dict, index: int):
        """Icon形状を作成"""
        from PySide6.QtWidgets import QGraphicsRectItem
        from PySide6.QtGui import QPen, QBrush
        from PySide6.QtCore import Qt
        
        try:
            top_left = icon_data.get('top_left', {})
            bottom_right = icon_data.get('bottom_right', {})
            
            x = top_left.get('x', 0)
            y = top_left.get('y', 0)
            w = bottom_right.get('x', 0) - x
            h = bottom_right.get('y', 0) - y
            
            # 矩形アイテム作成
            rect_item = QGraphicsRectItem(x, y, w, h)
            
            # スタイル設定（緑色の枠線、半透明の塗りつぶし）
            pen = QPen(QColor(0, 255, 0), 3)  # 緑色の枠線
            brush = QBrush(QColor(0, 255, 0, 50))  # 半透明の緑色
            rect_item.setPen(pen)
            rect_item.setBrush(brush)
            
            # データを保存
            rect_item.setData(0, {'type': 'icon', 'data': icon_data, 'index': index})
            
            return rect_item
            
        except Exception as e:
            print(f"Error creating icon shape: {e}")
            return None
    
    def _create_meter_shape(self, meter_data: dict, index: int):
        """Meter形状を作成"""
        from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsRectItem
        from PySide6.QtGui import QPen, QBrush
        from PySide6.QtCore import Qt
        
        try:
            center = meter_data.get('center', {})
            radius = meter_data.get('radius', 50)
            shape_type = meter_data.get('shape', 'circle')
            
            x = center.get('x', 0) - radius
            y = center.get('y', 0) - radius
            w = radius * 2
            h = radius * 2
            
            if shape_type == 'bar':
                # バー形状（矩形）
                shape_item = QGraphicsRectItem(x, y, w, h)
                pen = QPen(QColor(255, 165, 0), 3)  # オレンジ色の枠線
                brush = QBrush(QColor(255, 165, 0, 50))  # 半透明のオレンジ色
            else:
                # 円形
                shape_item = QGraphicsEllipseItem(x, y, w, h)
                pen = QPen(QColor(0, 0, 255), 3)  # 青色の枠線
                brush = QBrush(QColor(0, 0, 255, 50))  # 半透明の青色
            
            shape_item.setPen(pen)
            shape_item.setBrush(brush)
            
            # データを保存
            shape_item.setData(0, {'type': 'meter', 'data': meter_data, 'index': index})
            
            return shape_item
            
        except Exception as e:
            print(f"Error creating meter shape: {e}")
            return None
    
    def _create_ocr_shape(self, ocr_data: dict, index: int):
        """OCR形状を作成"""
        from PySide6.QtWidgets import QGraphicsRectItem
        from PySide6.QtGui import QPen, QBrush
        from PySide6.QtCore import Qt
        
        try:
            top_left = ocr_data.get('top_left', {})
            bottom_right = ocr_data.get('bottom_right', {})
            
            x = top_left.get('x', 0)
            y = top_left.get('y', 0)
            w = bottom_right.get('x', 0) - x
            h = bottom_right.get('y', 0) - y
            
            # 矩形アイテム作成
            rect_item = QGraphicsRectItem(x, y, w, h)
            
            # スタイル設定（赤色の枠線、半透明の塗りつぶし）
            pen = QPen(QColor(255, 0, 0), 3)  # 赤色の枠線
            brush = QBrush(QColor(255, 0, 0, 50))  # 半透明の赤色
            rect_item.setPen(pen)
            rect_item.setBrush(brush)
            
            # データを保存
            rect_item.setData(0, {'type': 'ocr', 'data': ocr_data, 'index': index})
            
            return rect_item
            
        except Exception as e:
            print(f"Error creating OCR shape: {e}")
            return None
    
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
    
    def _highlight_part(self, category, index):
        """指定されたパーツをハイライト（ResizableGraphicsItemシステム対応）"""
        try:
            if not hasattr(self, '_vehicle_shapes') or not self._vehicle_shapes:
                print("No vehicle shapes to highlight")
                return
                
            # すべてのハイライトを解除（選択状態をリセット）
            self._clear_all_highlights()
            
            # 指定されたパーツをハイライト（選択状態に設定）
            shape_index = self._get_shape_index_by_category(category, index)
            if 0 <= shape_index < len(self._vehicle_shapes):
                shape_item = self._vehicle_shapes[shape_index]
                if shape_item and hasattr(shape_item, 'set_selected'):
                    # ResizableGraphicsItemの選択状態を設定
                    shape_item.set_selected(True)
                    
                    # パーツの中心に画面をフォーカス
                    self._center_view_on_part(category, index)
                    
                    print(f"Selected {category} #{index} (ResizableGraphicsItem)")
            
        except Exception as e:
            print(f"Error highlighting part: {e}")
    
    def _clear_all_highlights(self):
        """すべてのハイライトを解除（ResizableGraphicsItemシステム対応）"""
        try:
            if not hasattr(self, '_vehicle_shapes') or not self._vehicle_shapes:
                return
                
            for i, shape_item in enumerate(self._vehicle_shapes):
                if shape_item and hasattr(shape_item, 'set_selected'):
                    # ResizableGraphicsItemの選択状態を解除
                    shape_item.set_selected(False)
                elif shape_item:
                    # 旧システム対応（QGraphicsItemの場合）
                    original_pen = self._get_original_pen_for_shape_index(i)
                    shape_item.setPen(original_pen)
                    
        except Exception as e:
            print(f"Error clearing highlights: {e}")
    
    def _get_original_pen_for_shape_index(self, shape_index):
        """図形インデックスから元のペンを取得"""
        from PySide6.QtGui import QPen, QColor
        
        if not self.vehicle_data:
            return QPen(QColor(128, 128, 128), 2)  # デフォルト色
            
        # インデックスからカテゴリを判定
        current_index = 0
        icon_count = len(self.vehicle_data.get('icon', []))
        meter_count = len(self.vehicle_data.get('meter', []))
        
        if shape_index < current_index + icon_count:
            return QPen(QColor(0, 255, 0), 2)  # 緑 - Icon
        current_index += icon_count
        
        if shape_index < current_index + meter_count:
            return QPen(QColor(0, 150, 255), 2)  # 青 - Meter
        
        return QPen(QColor(255, 100, 0), 2)  # オレンジ - OCR
    
    def _get_shape_index_by_category(self, category, part_index):
        """カテゴリとパーツインデックスから図形配列のインデックスを取得"""
        if not self.vehicle_data:
            return -1
            
        current_index = 0
        
        # Icon
        if category == 'icon':
            return current_index + part_index
        current_index += len(self.vehicle_data.get('icon', []))
        
        # Meter  
        if category == 'meter':
            return current_index + part_index
        current_index += len(self.vehicle_data.get('meter', []))
        
        # OCR
        if category == 'ocr':
            return current_index + part_index
            
        return -1
    
    def _center_view_on_part(self, category, index):
        """指定されたパーツにビューをセンタリング"""
        try:
            if not self.vehicle_data or not self.image_canvas:
                return
                
            # パーツの中心座標を計算
            center_x, center_y = None, None
            
            if category == 'icon':
                icons = self.vehicle_data.get('icon', [])
                if 0 <= index < len(icons):
                    icon = icons[index]
                    top_left = icon.get('top_left', {})
                    bottom_right = icon.get('bottom_right', {})
                    center_x = (top_left.get('x', 0) + bottom_right.get('x', 0)) / 2
                    center_y = (top_left.get('y', 0) + bottom_right.get('y', 0)) / 2
            elif category == 'meter':
                meters = self.vehicle_data.get('meter', [])
                if 0 <= index < len(meters):
                    meter = meters[index]
                    center = meter.get('center', {})
                    center_x = center.get('x', 0)
                    center_y = center.get('y', 0)
            elif category == 'ocr':
                ocrs = self.vehicle_data.get('ocr', [])
                if 0 <= index < len(ocrs):
                    ocr = ocrs[index]
                    top_left = ocr.get('top_left', {})
                    bottom_right = ocr.get('bottom_right', {})
                    center_x = (top_left.get('x', 0) + bottom_right.get('x', 0)) / 2
                    center_y = (top_left.get('y', 0) + bottom_right.get('y', 0)) / 2
            
            if center_x is not None and center_y is not None:
                self.image_canvas.centerOn(center_x, center_y)
                print(f"Centered view on {category} #{index} at ({center_x}, {center_y})")
                
        except Exception as e:
            print(f"Error centering view on part: {e}")
    
    def _toggle_category_visibility(self, category, visible):
        """カテゴリの表示切り替え（ResizableGraphicsItemシステム対応）"""
        try:
            if not hasattr(self, '_vehicle_shapes') or not self._vehicle_shapes:
                return
                
            # カテゴリ別にResizableGraphicsItemの表示/非表示を切り替え
            for shape_item in self._vehicle_shapes:
                if hasattr(shape_item, 'category') and hasattr(shape_item, 'set_visible'):
                    # ResizableGraphicsItemの場合
                    if (category == 'icon' and shape_item.category == ShapeCategory.ICON) or \
                       (category == 'meter' and shape_item.category == ShapeCategory.METER) or \
                       (category == 'ocr' and shape_item.category == ShapeCategory.OCR):
                        shape_item.set_visible(visible)
                elif shape_item:
                    # 旧システム対応（QGraphicsItemの場合）
                    current_index = 0
                    
                    if category == 'icon':
                        icon_count = len(self.vehicle_data.get('icon', [])) if self.vehicle_data else 0
                        for i in range(current_index, current_index + icon_count):
                            if i < len(self._vehicle_shapes) and self._vehicle_shapes[i]:
                                self._vehicle_shapes[i].setVisible(visible)
                        break
                    current_index += len(self.vehicle_data.get('icon', [])) if self.vehicle_data else 0
                    
                    if category == 'meter':
                        meter_count = len(self.vehicle_data.get('meter', [])) if self.vehicle_data else 0
                        for i in range(current_index, current_index + meter_count):
                            if i < len(self._vehicle_shapes) and self._vehicle_shapes[i]:
                                self._vehicle_shapes[i].setVisible(visible)
                        break
                    current_index += len(self.vehicle_data.get('meter', [])) if self.vehicle_data else 0
                    
                    if category == 'ocr':
                        ocr_count = len(self.vehicle_data.get('ocr', [])) if self.vehicle_data else 0
                        for i in range(current_index, current_index + ocr_count):
                            if i < len(self._vehicle_shapes) and self._vehicle_shapes[i]:
                                self._vehicle_shapes[i].setVisible(visible)
                        break
            
            print(f"{category.capitalize()} visibility set to {visible} (ResizableGraphicsItem)")
                
        except Exception as e:
            print(f"Error toggling category visibility: {e}")


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
        
        # MQTTメッセージを初期状態でミュート（デバッグ用）
        self.set_mqtt_muted(True)
        
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
            
            # ローカルファイルパス（リポジトリ相対）
            file_path = os.path.join(os.getcwd(), "data", "full_image.jpg")
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
        # MQTTメッセージがミュートされている場合はスキップ
        if getattr(self, '_mqtt_muted', False):
            return
            
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
    
    def set_mqtt_muted(self, muted: bool):
        """MQTTメッセージのミュート状態を設定"""
        self._mqtt_muted = muted
        if muted:
            print("=== MQTTメッセージをミュートしました ===")
        else:
            print("=== MQTTメッセージミュートを解除しました ===")
    
    def toggle_mqtt_muted(self):
        """MQTTメッセージミュート状態を切り替え"""
        current_state = getattr(self, '_mqtt_muted', False)
        self.set_mqtt_muted(not current_state)
    
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
