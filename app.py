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
    QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QFont


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
        self.setWindowTitle("Vehicle Monitor Application")
        
        # データ格納用
        self.config_data: Optional[ConfigData] = None
        self.vehicle_data: Optional[VehicleData] = None
        
        # UI初期化
        self.setup_ui()
        
        # 起動時最大化
        self.showMaximized()
    
    def setup_ui(self):
        """UI初期化"""
        # 中央ウィジェットとしてタブウィジェットを設定
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # 3つのタブを作成
        self.setup_config_tab()
        self.setup_edit_tab()
        self.setup_monitor_tab()
        
        # デフォルトでCONFIGタブを選択
        self.tab_widget.setCurrentIndex(0)
    
    def setup_config_tab(self):
        """CONFIGタブセットアップ"""
        config_widget = QWidget()
        layout = QVBoxLayout()
        
        # タイトル
        title = QLabel("CONFIG - システム設定")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Config読み込みボタン
        load_config_btn = QPushButton("Config.json読み込み")
        load_config_btn.clicked.connect(self.load_config_json)
        layout.addWidget(load_config_btn)
        
        # 設定表示エリア
        self.config_display = QTextEdit()
        self.config_display.setReadOnly(True)
        layout.addWidget(self.config_display)
        
        config_widget.setLayout(layout)
        self.tab_widget.addTab(config_widget, "CONFIG")
    
    def setup_edit_tab(self):
        """EDITタブセットアップ"""
        edit_widget = QWidget()
        layout = QVBoxLayout()
        
        # タイトル
        title = QLabel("EDIT - Vehicle設定編集")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Vehicle読み込みボタン
        load_vehicle_btn = QPushButton("Vehicle.json読み込み")
        load_vehicle_btn.clicked.connect(self.load_vehicle_json)
        layout.addWidget(load_vehicle_btn)
        
        # Vehicle表示エリア
        self.vehicle_display = QTextEdit()
        self.vehicle_display.setReadOnly(True)
        layout.addWidget(self.vehicle_display)
        
        edit_widget.setLayout(layout)
        self.tab_widget.addTab(edit_widget, "EDIT")
    
    def setup_monitor_tab(self):
        """MONITORタブセットアップ"""
        monitor_widget = QWidget()
        layout = QVBoxLayout()
        
        # タイトル
        title = QLabel("MONITOR - リアルタイム監視")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # ステータス表示
        status_label = QLabel("監視モード準備中...")
        layout.addWidget(status_label)
        
        monitor_widget.setLayout(layout)
        self.tab_widget.addTab(monitor_widget, "MONITOR")
    
    def load_config_json(self, file_path: str = None) -> Optional[ConfigData]:
        """config.json読み込み"""
        if file_path is None:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Config.json読み込み", "./data/", "JSON Files (*.json)"
            )
        
        if not file_path:
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # ConfigDataインスタンス作成
            self.config_data = ConfigData(
                mqtt_host=config_dict["mqtt"]["host"],
                mqtt_port=config_dict["mqtt"]["port"],
                mqtt_ws_port=config_dict["mqtt"]["wsPort"],
                rest_api_host=config_dict["RestAPI"]["host"],
                rest_api_port=config_dict["RestAPI"]["port"],
                camera_width=config_dict["camera"]["width"],
                camera_height=config_dict["camera"]["height"],
                camera_scale=config_dict["camera"]["scale"],
                camera_focus_length=config_dict["camera"]["focus_length"],
                camera_exposure=config_dict["camera"]["exposure"],
                camera_analogue_gain=config_dict["camera"]["AnalogueGain"],
                frame=config_dict["frame"],
                bench=config_dict["bench"],
                path=config_dict["path"]
            )
            
            # UI更新
            self.update_config_display()
            
            return self.config_data
            
        except Exception as e:
            QMessageBox.warning(self, "読み込みエラー", f"Config.json読み込み失敗:\n{str(e)}")
            return None
    
    def load_vehicle_json(self, file_path: str = None) -> Optional[VehicleData]:
        """vehicle.json読み込み"""
        if file_path is None:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Vehicle.json読み込み", "./data/", "JSON Files (*.json)"
            )
        
        if not file_path:
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                vehicle_dict = json.load(f)
            
            # VehicleDataインスタンス作成（簡略化）
            self.vehicle_data = VehicleData(
                name=vehicle_dict["name"],
                path=vehicle_dict["path"],
                threshold=vehicle_dict["threshold"],
                gray=vehicle_dict["gray"],
                offset=vehicle_dict["offset"],
                icon=[],  # 詳細パース実装は後段階
                meter=[],
                ocr=[]
            )
            
            # UI更新
            self.update_vehicle_display()
            
            return self.vehicle_data
            
        except Exception as e:
            QMessageBox.warning(self, "読み込みエラー", f"Vehicle.json読み込み失敗:\n{str(e)}")
            return None
    
    def update_config_display(self):
        """Config表示更新"""
        if self.config_data:
            display_text = f"""
MQTT設定:
  Host: {self.config_data.mqtt_host}
  Port: {self.config_data.mqtt_port}
  WS Port: {self.config_data.mqtt_ws_port}

RestAPI設定:
  Host: {self.config_data.rest_api_host}
  Port: {self.config_data.rest_api_port}

カメラ設定:
  解像度: {self.config_data.camera_width} x {self.config_data.camera_height}
  スケール: {self.config_data.camera_scale}
  
ベンチ名: {self.config_data.bench}
            """
            self.config_display.setPlainText(display_text.strip())
    
    def update_vehicle_display(self):
        """Vehicle表示更新"""
        if self.vehicle_data:
            display_text = f"""
車両名: {self.vehicle_data.name}
テンプレートパス: {self.vehicle_data.path}
閾値: {self.vehicle_data.threshold}
グレースケール: {self.vehicle_data.gray}
オフセット: {self.vehicle_data.offset}

Icon数: {len(self.vehicle_data.icon)}
Meter数: {len(self.vehicle_data.meter)}  
OCR数: {len(self.vehicle_data.ocr)}
            """
            self.vehicle_display.setPlainText(display_text.strip())


def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    # アプリケーション作成
    window = VehicleMonitorApplication()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()