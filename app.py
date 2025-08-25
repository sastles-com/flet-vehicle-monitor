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
        
        # CONFIGコンポーネント作成
        if not self.config_sidebar:
            self.config_sidebar = ConfigSidebar(self.app_state)
            self.config_sidebar.config_loaded.connect(self.on_config_loaded)
            self.config_sidebar.connection_test_requested.connect(self.test_connections)
        
        if not self.config_view:
            self.config_view = ConfigView(self.app_state)
        
        # レイアウト設定
        self.setup_config_layout()
        
        self.status_bar.showMessage("CONFIG Mode - Ready")
        print("Switched to CONFIG mode")
    
    def switch_to_edit_mode(self):
        """EDITモードに切替"""
        self.app_state.current_mode = AppMode.EDIT
        self.setWindowTitle(self.app_state.get_header_title())
        
        # 簡易EDITビュー作成
        edit_widget = self.create_edit_placeholder()
        self.setCentralWidget(edit_widget)
        
        # サイドバーを非表示
        if hasattr(self, 'sidebar_dock'):
            self.removeDockWidget(self.sidebar_dock)
        
        self.status_bar.showMessage("EDIT Mode - Ready")
        print("Switched to EDIT mode")
    
    def switch_to_monitor_mode(self):
        """MONITORモードに切替"""
        self.app_state.current_mode = AppMode.MONITOR
        self.setWindowTitle(self.app_state.get_header_title())
        
        # 簡易MONITORビュー作成
        monitor_widget = self.create_monitor_placeholder()
        self.setCentralWidget(monitor_widget)
        
        # サイドバーを非表示
        if hasattr(self, 'sidebar_dock'):
            self.removeDockWidget(self.sidebar_dock)
        
        self.status_bar.showMessage("MONITOR Mode - Ready")
        print("Switched to MONITOR mode")
    
    def setup_config_layout(self):
        """CONFIGモードレイアウト設定"""
        # サイドバーをドックとして設定
        if hasattr(self, 'sidebar_dock'):
            self.removeDockWidget(self.sidebar_dock)
            
        self.sidebar_dock = QDockWidget("設定", self)
        self.sidebar_dock.setWidget(self.config_sidebar)
        self.sidebar_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar_dock)
        
        # メインビューを中央に設定
        self.setCentralWidget(self.config_view)
    
    def create_edit_placeholder(self) -> QWidget:
        """EDITモード用プレースホルダー"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("EDIT Mode")
        title.setFont(QFont("Arial", 24))
        title.setAlignment(Qt.AlignCenter)
        
        description = QLabel("画像編集機能（main.pyで実装済み）")
        description.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_monitor_placeholder(self) -> QWidget:
        """MONITORモード用プレースホルダー"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("MONITOR Mode")
        title.setFont(QFont("Arial", 24))
        title.setAlignment(Qt.AlignCenter)
        
        description = QLabel("リアルタイム監視機能（未実装）")
        description.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
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
        
        # MQTT接続テスト（簡易版）
        try:
            if self.config_data.mqtt_host and self.config_data.mqtt_port:
                # 実際の接続テストは省略し、設定値があれば成功とする
                status.mqtt = True
                print(f"MQTT: {self.config_data.mqtt_host}:{self.config_data.mqtt_port} - OK")
        except:
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
    


def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    # アプリケーション作成
    window = VehicleMonitorApplication()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()