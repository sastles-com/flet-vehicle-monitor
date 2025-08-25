#!/usr/bin/env python3
"""
CONFIG Mode Sidebar Component
CONFIGモード用サイドバーコンポーネント
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QGroupBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from models.app_state import AppState
from typing import Dict, Any, Optional


class ConfigSidebar(QWidget):
    """CONFIG用サイドバー"""
    
    # シグナル定義
    config_loaded = Signal(dict)  # 設定読み込み完了時
    connection_test_requested = Signal()  # 接続テスト要求時
    
    def __init__(self, app_state: AppState, width: int = 320, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.width = width
        
        # フォームフィールド辞書
        self.config_form_fields = {}
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """UI初期化"""
        self.setFixedWidth(self.width)
        
        # メインレイアウト
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # タイトル
        title_label = QLabel("CONFIG - 設定管理")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # 設定読み込みセクション
        load_group = self._create_load_section()
        main_layout.addWidget(load_group)
        
        # 設定フォーム
        form_group = self._create_config_form()
        main_layout.addWidget(form_group)
        
        # 接続テストボタン
        test_button = QPushButton("接続テスト実行")
        test_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        test_button.clicked.connect(self.connection_test_requested.emit)
        main_layout.addWidget(test_button)
        
        # スペーサー
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def _create_load_section(self) -> QGroupBox:
        """設定読み込みセクション作成"""
        group = QGroupBox("設定読み込み")
        layout = QVBoxLayout()
        
        load_button = QPushButton("Config.json読み込み")
        load_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        load_button.clicked.connect(self._load_config_file)
        layout.addWidget(load_button)
        
        group.setLayout(layout)
        return group
    
    def _create_config_form(self) -> QGroupBox:
        """設定フォーム作成"""
        group = QGroupBox("設定詳細")
        form_layout = QFormLayout()
        
        # MQTT設定
        mqtt_label = QLabel("MQTT設定")
        mqtt_label.setStyleSheet("font-weight: bold; color: #666;")
        form_layout.addRow(mqtt_label)
        
        self.config_form_fields['mqtt_host'] = QLineEdit()
        self.config_form_fields['mqtt_port'] = QLineEdit()
        self.config_form_fields['mqtt_wsport'] = QLineEdit()
        
        form_layout.addRow("MQTT Host:", self.config_form_fields['mqtt_host'])
        form_layout.addRow("MQTT Port:", self.config_form_fields['mqtt_port'])
        form_layout.addRow("WebSocket Port:", self.config_form_fields['mqtt_wsport'])
        
        # 区切り線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        form_layout.addRow(line)
        
        # RestAPI設定
        rest_label = QLabel("RestAPI設定")
        rest_label.setStyleSheet("font-weight: bold; color: #666;")
        form_layout.addRow(rest_label)
        
        self.config_form_fields['restapi_host'] = QLineEdit()
        self.config_form_fields['restapi_port'] = QLineEdit()
        
        form_layout.addRow("REST Host:", self.config_form_fields['restapi_host'])
        form_layout.addRow("REST Port:", self.config_form_fields['restapi_port'])
        
        # 区切り線
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        form_layout.addRow(line2)
        
        # その他設定
        other_label = QLabel("その他")
        other_label.setStyleSheet("font-weight: bold; color: #666;")
        form_layout.addRow(other_label)
        
        self.config_form_fields['bench_name'] = QLineEdit()
        form_layout.addRow("ベンチ名:", self.config_form_fields['bench_name'])
        
        group.setLayout(form_layout)
        return group
    
    def _connect_signals(self):
        """シグナル接続"""
        # フィールド値変更時の処理
        for field in self.config_form_fields.values():
            field.textChanged.connect(self._on_field_changed)
    
    def _load_config_file(self):
        """設定ファイル読み込み"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Config.json読み込み",
            "./data/",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                from models.config_manager import ConfigManager
                config_manager = ConfigManager()
                config_data = config_manager.load_config_from_file(file_path)
                
                # フォームに読み込み
                self.load_config_data(config_data)
                
                # シグナル発出
                self.config_loaded.emit(config_data)
                
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "読み込みエラー", f"設定ファイルの読み込みに失敗しました:\n{str(e)}")
    
    def _on_field_changed(self):
        """フィールド値変更時の処理"""
        # ベンチ名が変更された場合、アプリケーション状態を更新
        bench_name = self.config_form_fields['bench_name'].text()
        if bench_name != self.app_state.bench_name:
            self.app_state.bench_name = bench_name
    
    def load_config_data(self, config_data: Dict[str, Any]):
        """設定データをフォームに読み込み"""
        try:
            # MQTT設定
            if "mqtt" in config_data:
                mqtt_config = config_data["mqtt"]
                self.set_field_value('mqtt_host', mqtt_config.get('host', ''))
                self.set_field_value('mqtt_port', mqtt_config.get('port', ''))
                self.set_field_value('mqtt_wsport', mqtt_config.get('wsPort', ''))
            
            # RestAPI設定
            if "RestAPI" in config_data:
                rest_config = config_data["RestAPI"]
                self.set_field_value('restapi_host', rest_config.get('host', ''))
                self.set_field_value('restapi_port', rest_config.get('port', ''))
            
            # その他
            self.set_field_value('bench_name', config_data.get('bench', ''))
            
            # アプリケーション状態更新
            self.app_state.bench_name = config_data.get('bench', '')
            
        except Exception as e:
            print(f"Config load error: {e}")
    
    def get_current_config(self) -> Dict[str, Any]:
        """現在の設定データを取得"""
        return {
            "mqtt": {
                "host": self.get_field_value('mqtt_host'),
                "port": self.get_field_value('mqtt_port'),
                "wsPort": self.get_field_value('mqtt_wsport')
            },
            "RestAPI": {
                "host": self.get_field_value('restapi_host'),
                "port": self.get_field_value('restapi_port')
            },
            "bench": self.get_field_value('bench_name')
        }
    
    def set_field_value(self, field_name: str, value: str):
        """フィールド値設定"""
        if field_name in self.config_form_fields:
            self.config_form_fields[field_name].setText(str(value))
    
    def get_field_value(self, field_name: str) -> str:
        """フィールド値取得"""
        if field_name in self.config_form_fields:
            return self.config_form_fields[field_name].text()
        return ""