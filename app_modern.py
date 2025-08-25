#!/usr/bin/env python3
"""
Vehicle Monitor Application - Modern Framework Version
車両監視システム - モダンフレームワーク版
"""

import sys
from typing import Optional

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import QTimer, Qt

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
        self._setup_edit_content()
    
    def _setup_edit_content(self):
        """EDIT専用コンテンツ設定"""
        from PySide6.QtWidgets import QLabel, QPushButton, QGroupBox
        
        # Vehicle設定グループ
        vehicle_group = QGroupBox("車両設定")
        vehicle_layout = QVBoxLayout()
        
        load_vehicle_btn = QPushButton("Load Vehicle")
        load_vehicle_btn.setStyleSheet(StyleBuilder.create_button_style(
            bg_color=StyleBuilder.get_color('secondary', 600)
        ))
        vehicle_layout.addWidget(load_vehicle_btn)
        
        vehicle_group.setLayout(vehicle_layout)
        self.content_layout.addWidget(vehicle_group)
        
        # 画像取得グループ
        image_group = QGroupBox("画像取得")
        image_layout = QVBoxLayout()
        
        fetch_btn = QPushButton("RestAPIから画像取得")
        fetch_btn.setStyleSheet(StyleBuilder.create_button_style())
        image_layout.addWidget(fetch_btn)
        
        image_group.setLayout(image_layout)
        self.content_layout.addWidget(image_group)
        
        # ストレッチ
        self.content_layout.addStretch()


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
        self._setup_ui()
    
    def _setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 空のメイン画面


class ModernMonitorMainView(QWidget):
    """MONITOR用モダンメインビュー"""
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self._setup_ui()
    
    def _setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 空のメイン画面


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
        self.mode_components[AppMode.EDIT]['sidebar'] = EditModernSidebar(self.app_state)
        self.mode_components[AppMode.EDIT]['main_view'] = ModernEditMainView(self.app_state)
        
        # MONITOR
        self.mode_components[AppMode.MONITOR]['sidebar'] = MonitorModernSidebar(self.app_state)
        self.mode_components[AppMode.MONITOR]['main_view'] = ModernMonitorMainView(self.app_state)
    
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
        print(f"Switching to {new_mode.value} mode")
        
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
        
        # ヘッダー更新
        self.framework.header.update_mode(new_mode)
        
        print(f"Switched to {new_mode.value} mode successfully")
    
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
        
        # CONFIGモードの場合、メイン画面に画像を表示
        if self.app_state.current_mode == AppMode.CONFIG:
            print(">>> CONFIGモードです - メイン画面に表示します <<<")
            config_main_view = self.mode_components[AppMode.CONFIG]['main_view']
            print(f">>> Config main view: {config_main_view} <<<")
            
            if hasattr(config_main_view, 'update_mqtt_image'):
                print(">>> update_mqtt_image メソッドを呼び出します <<<")
                config_main_view.update_mqtt_image(image_data)
            else:
                print(">>> ERROR: update_mqtt_image メソッドが見つかりません <<<")
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