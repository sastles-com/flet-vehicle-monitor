#!/usr/bin/env python3
"""
Vehicle Monitor Application - Modern Framework Version
車両監視システム - モダンフレームワーク版
"""

import sys
from typing import Optional

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QSizePolicy
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
    
    def _setup_config_content(self):
        """CONFIG専用コンテンツ設定"""
        # 既存のConfigSidebarを統合（完全に表示）
        self.config_sidebar = ConfigSidebar(self.app_state)
        
        # マージンを調整してConfigSidebarを最大表示
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.addWidget(self.config_sidebar)
    
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
        self._auto_show_vehicle_dialog()
    
    def _setup_edit_content(self):
        """EDIT専用コンテンツ設定"""
        from PySide6.QtWidgets import QLabel, QPushButton, QGroupBox
        
        # Vehicle設定グループ
        vehicle_group = QGroupBox("車両設定")
        vehicle_layout = QVBoxLayout()
        
        # 車両ファイル情報表示
        self.vehicle_info_label = QLabel("車両: 未読み込み")
        self.vehicle_info_label.setStyleSheet(f"""
            QLabel {{
                color: {StyleBuilder.get_color('dark', 'on_surface_secondary')};
                font-size: 12px;
                padding: 5px;
            }}
        """)
        vehicle_layout.addWidget(self.vehicle_info_label)
        
        # Load Vehicleボタン
        self.load_vehicle_btn = QPushButton("Load Vehicle")
        self.load_vehicle_btn.setStyleSheet(StyleBuilder.create_button_style(
            bg_color=StyleBuilder.get_color('secondary', 600)
        ))
        self.load_vehicle_btn.clicked.connect(self._on_load_vehicle_clicked)
        vehicle_layout.addWidget(self.load_vehicle_btn)
        
        vehicle_group.setLayout(vehicle_layout)
        self.content_layout.addWidget(vehicle_group)
        
        # 画像取得グループ
        image_group = QGroupBox("画像取得")
        image_layout = QVBoxLayout()
        
        # 画像取得ボタン
        self.fetch_btn = QPushButton("RestAPIから画像取得")
        self.fetch_btn.setStyleSheet(StyleBuilder.create_button_style())
        self.fetch_btn.clicked.connect(self._on_fetch_image_clicked)
        image_layout.addWidget(self.fetch_btn)
        
        image_group.setLayout(image_layout)
        self.content_layout.addWidget(image_group)
        
        # ストレッチ
        self.content_layout.addStretch()
    
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
            
            # 車両名をUIに反映
            vehicle_name = self.vehicle_data.get("name", "Unknown")
            self.vehicle_info_label.setText(f"車両: {vehicle_name}")
            
            print(f"Vehicle loaded successfully: {vehicle_name}")
            
            # RestAPIで画像を取得
            self._fetch_full_image()
            
        except Exception as e:
            print(f"Error loading vehicle file: {e}")
            self.vehicle_info_label.setText("車両: 読み込みエラー")
    
    def _on_load_vehicle_clicked(self):
        """Load Vehicleボタンクリック時の処理"""
        self._open_vehicle_file_dialog()
    
    def _on_fetch_image_clicked(self):
        """RestAPIから画像取得ボタンクリック時の処理"""
        self._fetch_full_image()
    
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
        self._load_dummy_image()
    
    def _setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 画像表示用ラベル
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(f"""
            QLabel {{
                background-color: {StyleBuilder.get_color('dark', 'surface_2')};
                border: 2px solid {StyleBuilder.get_color('dark', 'border')};
                border-radius: 8px;
            }}
        """)
        self.image_label.setScaledContents(True)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.image_label)
        
        # 既存のConfigViewも隠して保持（MQTT接続機能用）
        self.config_view = ConfigView(self.app_state)
        self.config_view.hide()
    
    def _load_dummy_image(self):
        """初期状態は何も表示しない（空状態）"""
        self._set_initial_empty_state()
    
    def _set_initial_empty_state(self):
        """初期状態の空画面設定"""
        self.image_label.setText("設定ファイルを読み込んでください\n\n「Config.json読み込み」ボタンから\nベンチ設定を選択してください")
        self.image_label.setStyleSheet(f"""
            QLabel {{
                background-color: {StyleBuilder.get_color('dark', 'surface_1')};
                border: 2px solid {StyleBuilder.get_color('dark', 'border')};
                border-radius: 8px;
                color: {StyleBuilder.get_color('dark', 'on_surface_secondary')};
                font-size: 16px;
                padding: 40px;
            }}
        """)
    
    def update_mqtt_image(self, image_data: str):
        """MQTT画像データを受信して表示"""
        from PySide6.QtGui import QPixmap
        import base64
        
        print(f"=== update_mqtt_image called with data length: {len(image_data)} ===")
        print(f"=== Image data preview: {image_data[:100]}... ===")
        
        try:
            # Base64デコード
            image_bytes = base64.b64decode(image_data)
            print(f"=== Base64 decoded successfully, binary size: {len(image_bytes)} bytes ===")
            
            # QPixmapに変換
            pixmap = QPixmap()
            if pixmap.loadFromData(image_bytes):
                # 画像を最大サイズでアスペクト比を保って表示
                self.image_label.setPixmap(pixmap)
                self.image_label.setText("")
                print(f"=== SUCCESS: MQTT画像を表示しました (サイズ: {len(image_bytes)} bytes) ===")
                print(f"=== Pixmap size: {pixmap.size().width()}x{pixmap.size().height()} ===")
            else:
                print("=== ERROR: MQTT画像のQPixmapへの変換に失敗しました ===")
                self._set_placeholder_text()
                
        except Exception as e:
            print(f"=== EXCEPTION: MQTT画像表示エラー: {e} ===")
            import traceback
            traceback.print_exc()
            self._set_placeholder_text()
    
    def _set_placeholder_text(self):
        """プレースホルダーテキスト設定"""
        self.image_label.setText("画像プレビュー\n（data/image.jpg が見つかりません）")
        self.image_label.setStyleSheet(f"""
            QLabel {{
                background-color: {StyleBuilder.get_color('dark', 'surface_2')};
                border: 2px solid {StyleBuilder.get_color('dark', 'border')};
                border-radius: 8px;
                color: {StyleBuilder.get_color('dark', 'on_surface_secondary')};
                font-size: 18px;
            }}
        """)
    
    def get_config_view(self):
        """ConfigViewインスタンスを取得（外部アクセス用）"""
        return self.config_view


class ModernEditMainView(QWidget):
    """EDIT用モダンメインビュー"""
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        
        # 画像表示関連
        self.current_image = None
        self.image_label = None
        self.vehicle_data = None
        
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
        self.image_label.setScaledContents(False)
        
        # 初期プレースホルダー設定
        self._set_placeholder_image()
        
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
    
    def _set_placeholder_image(self):
        """プレースホルダー画像を設定"""
        try:
            # 固定サイズでプレースホルダー画像を作成
            placeholder = QPixmap(800, 600)
            placeholder.fill(QColor('#2D2D30'))
            
            # 中央にテキストを描画
            painter = QPainter(placeholder)
            painter.setPen(QColor('#FFFFFF'))
            painter.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
            painter.drawText(placeholder.rect(), Qt.AlignmentFlag.AlignCenter, "EDIT画面")
            
            # サブテキスト
            painter.setFont(QFont("Segoe UI", 18))
            painter.setPen(QColor('#B0B0B0'))
            text_rect = placeholder.rect()
            text_rect.setTop(text_rect.center().y() + 40)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "vehicle.json読み込み後\n画像が表示されます")
            painter.end()
            
            # プレースホルダー画像を設定
            self.image_label.setPixmap(placeholder)
            self.image_label.setText("")
            
        except Exception as e:
            print(f"Placeholder image creation error: {e}")
            # フォールバック: テキストのみ表示
            self.image_label.setText("EDIT画面\nvehicle.json読み込み後\n画像が表示されます")
    
    def load_vehicle_json(self, vehicle_data: dict):
        """vehicle.jsonデータを読み込み"""
        self.vehicle_data = vehicle_data
        vehicle_name = vehicle_data.get("name", "Unknown")
        print(f"EDIT main view: Vehicle data loaded for {vehicle_name}")
    
    def load_full_image(self, image_data: bytes):
        """RestAPIから取得した画像を表示"""
        try:
            print(f"EDIT main view: Loading full image ({len(image_data)} bytes)")
            
            # バイナリデータをQPixmapに変換
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                # 画像ラベルのサイズに合わせてスケーリング
                label_geometry = self.image_label.geometry()
                available_width = max(label_geometry.width() - 20, 200)
                available_height = max(label_geometry.height() - 20, 150)
                
                if available_width > 100 and available_height > 100:
                    scaled_pixmap = pixmap.scaled(
                        available_width, available_height,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                else:
                    # 固定サイズでスケーリング
                    scaled_pixmap = pixmap.scaled(
                        800, 600,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                
                self.image_label.setText("")
                print("EDIT main view: Full image displayed successfully")
            else:
                print("EDIT main view: Failed to load image from data")
                
        except Exception as e:
            print(f"EDIT main view: Image loading error: {e}")


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
        self.mode_components[AppMode.CONFIG]['sidebar'] = ConfigModernSidebar(self.app_state)
        self.mode_components[AppMode.CONFIG]['main_view'] = ModernConfigMainView(self.app_state)
        
        # EDIT 
        edit_sidebar = EditModernSidebar(self.app_state)
        edit_sidebar.set_main_application(self)
        self.mode_components[AppMode.EDIT]['sidebar'] = edit_sidebar
        self.mode_components[AppMode.EDIT]['main_view'] = ModernEditMainView(self.app_state)
        
        # MONITOR
        self.mode_components[AppMode.MONITOR]['sidebar'] = MonitorModernSidebar(self.app_state)
        monitor_main_view = ModernMonitorMainView(self.app_state)
        self.mode_components[AppMode.MONITOR]['main_view'] = monitor_main_view
        
        # MQTTサービスとMONITORビューを接続
        self.mqtt_service.image_received.connect(monitor_main_view.update_image)
        print("MQTT service connected to MONITOR main view for image updates")
    
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
            
            # 5. 500msec待機
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
        
        else:
            print(f">>> 現在のモードは{self.app_state.current_mode}なので画像表示をスキップします <<<")


def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    # アプリケーション作成
    window = VehicleMonitorModernApplication()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()