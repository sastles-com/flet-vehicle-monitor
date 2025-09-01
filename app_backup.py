#!/usr/bin/env python3
"""
Vehicle Monitor Application (app.py)
車両監視システムメインアプリケーション

3つのタブ構成（CONFIG/EDIT/MONITOR）を提供する
"""

import sys
import json
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox,
    QTextEdit, QSplitter, QDockWidget
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QFont

# アプリケーション状態管理をインポート
from models.app_state import AppState, ConnectionStatus
from models.app_mode import AppMode
from models.config_manager import ConfigManager
from components.config.config_sidebar import ConfigSidebar
from components.config.config_view import ConfigView


# データクラス定義
@dataclass
class Position:
    """座標データ"""
    x: float
    y: float


@dataclass
class ConfigData:
    """config.json用データクラス"""
    mqtt_host: str
    mqtt_port: str
    mqtt_ws_port: str
    rest_api_host: str
    rest_api_port: str
    camera_width: int
    camera_height: int
    camera_scale: float
    camera_focus_length: str
    camera_exposure: int
    camera_analogue_gain: int
    frame: int
    bench: str
    path: str


@dataclass
class CircumferencePoint:
    """円周上の点データクラス"""
    position: Position
    value: float


@dataclass
class IconData:
    """アイコン（矩形）データクラス"""
    name: str
    path: str
    type: str
    shape: str
    top_left: Position
    bottom_right: Position


@dataclass
class MeterData:
    """メーター（円形）データクラス"""
    name: str
    path: str
    type: str
    shape: str
    center: Position
    radius: float
    ratio: float
    circumference: List[CircumferencePoint]


@dataclass
class OCRData:
    """OCR（矩形）データクラス"""
    name: str
    type: str
    shape: str
    top_left: Position
    bottom_right: Position


@dataclass
class VehicleData:
    """vehicle.json用データクラス"""
    name: str
    path: str
    threshold: float
    gray: bool
    offset: int
    icon: List[IconData]
    meter: List[MeterData]
    ocr: List[OCRData]


class VehicleMonitorApplication(QMainWindow):
    """車両監視システムメインアプリケーション"""
    
    def __init__(self):
        super().__init__()
        
        # アプリケーション状態管理
        self.app_state = AppState()
        self.config_manager = ConfigManager()
        
        self.setWindowTitle(self.app_state.get_header_title())
        
        # データ格納用
        self.config_data: Optional[ConfigData] = None
        self.vehicle_data: Optional[VehicleData] = None
        
        # MQTT関連
        self.mqtt_client = None
        
        # CONFIGコンポーネント
        self.config_sidebar: Optional[ConfigSidebar] = None
        self.config_view: Optional[ConfigView] = None
        
        # UI初期化
        self.setup_ui()
        
        # 起動時最大化
        self.showMaximized()
        
        # 初期モード設定（CONFIG）
        self.switch_to_config_mode()
    
    def setup_ui(self):
        """UI初期化"""
        # タブウィジェットは使用せず、モード切替による単一画面に変更
        # （vehicle_monitorアプリ参考）
        
        # ツールバー作成
        toolbar = self.addToolBar("Main")
        
        # モード切替ボタン
        config_action = toolbar.addAction("CONFIG")
        config_action.triggered.connect(self.switch_to_config_mode)
        
        edit_action = toolbar.addAction("EDIT")
        edit_action.triggered.connect(self.switch_to_edit_mode)
        
        monitor_action = toolbar.addAction("MONITOR") 
        monitor_action.triggered.connect(self.switch_to_monitor_mode)
        
        # ステータスバー作成
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - CONFIG Mode")
    
    # モード切替メソッド
    def switch_to_config_mode(self):
        """CONFIGモードに切替"""
        self.app_state.current_mode = AppMode.CONFIG
        self.setWindowTitle(self.app_state.get_header_title())
        
        # CONFIGコンポーネント作成（常に新しく作成）
        self.config_sidebar = ConfigSidebar(self.app_state)
        self.config_sidebar.config_loaded.connect(self.on_config_loaded)
        self.config_sidebar.connection_test_requested.connect(self.test_connections)
        
        self.config_view = ConfigView(self.app_state)
        
        # レイアウト設定
        self.setup_config_layout()
        
        self.status_bar.showMessage("CONFIG Mode - Ready")
        print("Switched to CONFIG mode")
    
    def switch_to_edit_mode(self):
        """EDITモードに切替"""
        self.app_state.current_mode = AppMode.EDIT
        self.setWindowTitle(self.app_state.get_header_title())
        
        # 簡易EDITビュー作成（同じHeader-Footer構成）
        edit_widget = self.create_edit_placeholder()
        self.setCentralWidget(edit_widget)
        
        self.status_bar.showMessage("EDIT Mode - Ready")
        print("Switched to EDIT mode")
    
    def switch_to_monitor_mode(self):
        """MONITORモードに切替"""
        self.app_state.current_mode = AppMode.MONITOR
        self.setWindowTitle(self.app_state.get_header_title())
        
        # 簡易MONITORビュー作成（同じHeader-Footer構成）
        monitor_widget = self.create_monitor_placeholder()
        self.setCentralWidget(monitor_widget)
        
        self.status_bar.showMessage("MONITOR Mode - Ready")
        print("Switched to MONITOR mode")
    
    def setup_config_layout(self):
        """CONFIGモードレイアウト設定（Header-Content-Footer構成）"""
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
        
        # メインウィジェット作成
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ヘッダー作成
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # コンテンツエリア作成（サイドバー + メインビュー）
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # サイドバーを追加
        content_layout.addWidget(self.config_sidebar)
        
        # メインビューを追加
        content_layout.addWidget(self.config_view, 1)  # 拡張可能
        
        main_layout.addWidget(content_widget, 1)  # 拡張可能
        
        # フッター作成
        footer_widget = self.create_footer()
        main_layout.addWidget(footer_widget)
        
        # メインウィジェットを設定
        self.setCentralWidget(main_widget)
    
    def create_header(self) -> QWidget:
        """ヘッダーウィジェットを作成"""
        from PySide6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QFrame
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
        
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #1a237e; color: white;")  # indigo_900相当
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        
        # 左側: メニューボタン
        menu_btn = QPushButton("☰")
        menu_btn.setFixedSize(50, 50)
        menu_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                color: white; 
                font-size: 24px; 
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.2); }
        """)
        
        # 中央: タイトル
        title_label = QLabel(self.app_state.get_header_title())
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffeb3b;")  # yellow_400相当
        title_label.setAlignment(Qt.AlignCenter)
        
        # 右側: モード遷移ボタン
        mode_btn = QPushButton("EDIT モードへ")
        mode_btn.setFixedSize(160, 50)
        mode_btn.setStyleSheet("""
            QPushButton {
                background-color: #f57c00; 
                color: white; 
                font-size: 14px; 
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #ff9800; }
        """)
        mode_btn.clicked.connect(lambda: self.switch_to_edit_mode())
        
        layout.addWidget(menu_btn)
        layout.addStretch()
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(mode_btn)
        
        return header
    
    def create_footer(self) -> QWidget:
        """フッターウィジェットを作成"""
        from PySide6.QtWidgets import QHBoxLayout, QLabel
        from PySide6.QtCore import Qt
        
        footer = QWidget()
        footer.setFixedHeight(60)
        footer.setStyleSheet("background-color: #00695c; color: white;")  # teal_900相当
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(30, 10, 30, 10)
        
        # 左側: デバッグ情報とFPS
        debug_label = QLabel(f"{self.app_state.debug_info}")
        debug_label.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 14px;")
        
        fps_label = QLabel(f"FPS: {self.app_state.frame_rate:.1f}")
        fps_label.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 14px;")
        
        # 右側: 接続状態インジケータ
        mqtt_indicator = self.create_connection_indicator("MQTT", self.app_state.connection_status.mqtt)
        rest_indicator = self.create_connection_indicator("REST", self.app_state.connection_status.restapi)
        ros2_indicator = self.create_connection_indicator("ROS2", self.app_state.connection_status.ros2)
        
        layout.addWidget(debug_label)
        layout.addSpacing(20)
        layout.addWidget(fps_label)
        layout.addStretch()
        layout.addWidget(mqtt_indicator)
        layout.addSpacing(5)
        layout.addWidget(rest_indicator)
        layout.addSpacing(5)
        layout.addWidget(ros2_indicator)
        
        return footer
    
    def create_connection_indicator(self, label: str, connected: bool) -> QWidget:
        """接続状態インジケータを作成"""
        from PySide6.QtWidgets import QHBoxLayout, QLabel
        
        indicator = QWidget()
        layout = QHBoxLayout(indicator)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        
        # 接続状態に応じた色
        if connected:
            bg_color = "#2e7d32"  # green_800
            icon_text = "●"  # 塗りつぶし円
            icon_color = "#4caf50"  # green_500
        else:
            bg_color = "#c62828"  # red_800
            icon_text = "○"  # 中抜き円
            icon_color = "#f44336"  # red_500
        
        indicator.setStyleSheet(f"background-color: {bg_color}; border-radius: 6px;")
        
        # アイコン
        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet(f"color: {icon_color}; font-size: 16px;")
        
        # テキスト
        text_label = QLabel(label)
        text_label.setStyleSheet("color: white; font-size: 12px;")
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        
        return indicator
    
    def create_edit_placeholder(self) -> QWidget:
        """EDITモード用プレースホルダー（Header-Footer構成）"""
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
        
        # メインウィジェット作成
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ヘッダー作成（EDITモード用）
        header_widget = self.create_edit_header()
        main_layout.addWidget(header_widget)
        
        # コンテンツエリア
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #2e2e2e;")  # ダークグレー
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("EDIT Mode")
        title.setStyleSheet("color: #ff9800; font-size: 32px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        
        description = QLabel("画像編集機能（main.pyで実装済み）\n矩形・円形図形の編集とvehicle.json管理")
        description.setStyleSheet("color: #e0e0e0; font-size: 16px;")
        description.setAlignment(Qt.AlignCenter)
        
        content_layout.addStretch()
        content_layout.addWidget(title)
        content_layout.addSpacing(20)
        content_layout.addWidget(description)
        content_layout.addStretch()
        
        main_layout.addWidget(content_widget, 1)
        
        # フッター作成
        footer_widget = self.create_footer()
        main_layout.addWidget(footer_widget)
        
        return main_widget
    
    def create_monitor_placeholder(self) -> QWidget:
        """MONITORモード用プレースホルダー（Header-Footer構成）"""
        from PySide6.QtWidgets import QVBoxLayout
        
        # メインウィジェット作成
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ヘッダー作成（MONITORモード用）
        header_widget = self.create_monitor_header()
        main_layout.addWidget(header_widget)
        
        # コンテンツエリア
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #1e1e1e;")  # より暗いグレー
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("MONITOR Mode")
        title.setStyleSheet("color: #f44336; font-size: 32px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        
        description = QLabel("リアルタイム監視機能\nMQTTストリーミングとSTART/STOP制御")
        description.setStyleSheet("color: #e0e0e0; font-size: 16px;")
        description.setAlignment(Qt.AlignCenter)
        
        content_layout.addStretch()
        content_layout.addWidget(title)
        content_layout.addSpacing(20)
        content_layout.addWidget(description)
        content_layout.addStretch()
        
        main_layout.addWidget(content_widget, 1)
        
        # フッター作成
        footer_widget = self.create_footer()
        main_layout.addWidget(footer_widget)
        
        return main_widget
    
    def create_edit_header(self) -> QWidget:
        """EDITモード用ヘッダー"""
        from PySide6.QtWidgets import QHBoxLayout, QPushButton, QLabel
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
        
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #1a237e; color: white;")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        
        # 左側: CONFIGボタン（戻る）
        back_btn = QPushButton("CONFIG")
        back_btn.setFixedSize(120, 50)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2; 
                color: white; 
                font-size: 14px; 
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #2196f3; }
        """)
        back_btn.clicked.connect(lambda: self.switch_to_config_mode())
        
        # 中央: タイトル
        title_label = QLabel(self.app_state.get_header_title())
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffeb3b;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # 右側: MONITORボタン
        monitor_btn = QPushButton("MONITOR モードへ")
        monitor_btn.setFixedSize(180, 50)
        monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f; 
                color: white; 
                font-size: 14px; 
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #f44336; }
        """)
        monitor_btn.clicked.connect(lambda: self.switch_to_monitor_mode())
        
        layout.addWidget(back_btn)
        layout.addStretch()
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(monitor_btn)
        
        return header
    
    def create_monitor_header(self) -> QWidget:
        """MONITORモード用ヘッダー"""
        from PySide6.QtWidgets import QHBoxLayout, QPushButton, QLabel
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
        
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #1a237e; color: white;")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        
        # 左側: EDITボタン（戻る）
        back_btn = QPushButton("EDIT")
        back_btn.setFixedSize(120, 50)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2; 
                color: white; 
                font-size: 14px; 
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #2196f3; }
        """)
        back_btn.clicked.connect(lambda: self.switch_to_edit_mode())
        
        # 中央: タイトル
        title_label = QLabel(self.app_state.get_header_title())
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffeb3b;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # 右側: START/STOPボタン
        start_stop_btn = QPushButton("START")
        start_stop_btn.setFixedSize(120, 50)
        start_stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #388e3c; 
                color: white; 
                font-size: 14px; 
                font-weight: bold;
                border: 2px solid #4caf50;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #4caf50; }
        """)
        
        layout.addWidget(back_btn)
        layout.addStretch()
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(start_stop_btn)
        
        return header
    
    def on_config_loaded(self, config_data: dict):
        """設定読み込み完了時の処理"""
        try:
            # ConfigDataに変換
            self.config_data = ConfigData(
                mqtt_host=config_data.get("mqtt", {}).get("host", ""),
                mqtt_port=config_data.get("mqtt", {}).get("port", ""),
                mqtt_ws_port=config_data.get("mqtt", {}).get("wsPort", ""),
                rest_api_host=config_data.get("RestAPI", {}).get("host", ""),
                rest_api_port=config_data.get("RestAPI", {}).get("port", ""),
                camera_width=config_data.get("camera", {}).get("width", 2304),
                camera_height=config_data.get("camera", {}).get("height", 1296),
                camera_scale=config_data.get("camera", {}).get("scale", 0.125),
                camera_focus_length=config_data.get("camera", {}).get("focus_length", "10.12768268585205"),
                camera_exposure=config_data.get("camera", {}).get("exposure", 60000),
                camera_analogue_gain=config_data.get("camera", {}).get("AnalogueGain", 1),
                frame=config_data.get("frame", 0),
                bench=config_data.get("bench", ""),
                path=config_data.get("path", "./config")
            )
            
            # アプリケーション状態更新
            self.app_state.bench_name = self.config_data.bench
            self.setWindowTitle(self.app_state.get_header_title())
            
            # ConfigViewに設定情報表示
            self.config_view.show_config_info(config_data)
            
            print(f"Config loaded: {self.config_data.bench}")
            
        except Exception as e:
            print(f"Config load error: {e}")
    
    def test_connections(self):
        """接続テスト実行"""
        if not self.config_data:
            print("No config data available for connection test")
            return
            
        print("Testing connections...")
        
        # 接続状態をリセット
        status = ConnectionStatus()
        
        # MQTT接続テスト（実際の接続）
        if self.config_data.mqtt_host and self.config_data.mqtt_port:
            try:
                self._setup_mqtt_connection()
                status.mqtt = True
                print(f"MQTT: {self.config_data.mqtt_host}:{self.config_data.mqtt_port} - OK")
            except Exception as e:
                status.mqtt = False
                print(f"MQTT connection failed: {e}")
        else:
            status.mqtt = False
            
        # RestAPI接続テスト
        try:
            if self.config_data.rest_api_host and self.config_data.rest_api_port:
                import requests
                url = f"http://{self.config_data.rest_api_host}:{self.config_data.rest_api_port}/"
                response = requests.get(url, timeout=3)
                status.restapi = response.status_code == 200
                print(f"RestAPI: {url} - {'OK' if status.restapi else 'Failed'}")
        except Exception as e:
            status.restapi = False
            print(f"RestAPI connection failed: {e}")
        
        # ROS2は常に成功とする（簡易版）
        status.ros2 = True
        print("ROS2: OK (simulated)")
        
        # 接続状態をConfigViewに反映
        self.config_view.update_connection_status(status)
        self.app_state.connection_status = status
        
        print("Connection test completed")
    
    def _setup_mqtt_connection(self):
        """MQTT接続セットアップ"""
        try:
            import paho.mqtt.client as mqtt
            
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    print("MQTT connected successfully")
                    # 画像トピックを購読
                    client.subscribe("image")
                    print("Subscribed to 'image' topic")
                else:
                    print(f"MQTT connection failed with code {rc}")
            
            def on_message(client, userdata, msg):
                try:
                    # メッセージをデコードして画像データとして処理
                    message_str = msg.payload.decode('utf-8')
                    import json
                    
                    # JSONとして解析
                    message_data = json.loads(message_str)
                    
                    if "image" in message_data and message_data["image"]:
                        print(f"Received image data: {len(message_data['image'])} characters")
                        # ConfigViewに画像を渡す（メインスレッドで実行）
                        from PySide6.QtCore import QMetaObject, Qt
                        QMetaObject.invokeMethod(
                            self.config_view, 
                            "update_image", 
                            Qt.QueuedConnection,
                            message_data["image"]
                        )
                except Exception as e:
                    print(f"MQTT message processing error: {e}")
            
            def on_disconnect(client, userdata, rc):
                print("MQTT disconnected")
            
            # MQTTクライアント作成
            if hasattr(self, 'mqtt_client') and self.mqtt_client:
                self.mqtt_client.disconnect()
                self.mqtt_client.loop_stop()
            
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = on_connect
            self.mqtt_client.on_message = on_message
            self.mqtt_client.on_disconnect = on_disconnect
            
            # 接続実行
            host = self.config_data.mqtt_host
            port = int(self.config_data.mqtt_port)
            
            print(f"Connecting to MQTT broker: {host}:{port}")
            self.mqtt_client.connect(host, port, 60)
            self.mqtt_client.loop_start()
            
        except ImportError:
            print("paho-mqtt library not installed. Please install with: pip install paho-mqtt")
            raise
        except Exception as e:
            print(f"MQTT setup error: {e}")
            raise


def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    # アプリケーション作成
    window = VehicleMonitorApplication()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()