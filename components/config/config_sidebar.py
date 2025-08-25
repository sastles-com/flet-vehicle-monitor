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
        main_layout = QVBoxLayout()
        
        # MQTT設定セクション
        mqtt_label = QLabel("MQTT設定")
        mqtt_label.setStyleSheet("font-weight: bold; color: white; font-size: 14px; margin-bottom: 5px;")
        main_layout.addWidget(mqtt_label)
        
        # テキストボックスのサイズを半分に設定
        self.config_form_fields['mqtt_host'] = QLineEdit()
        self.config_form_fields['mqtt_host'].setMaximumWidth(150)
        self.config_form_fields['mqtt_port'] = QLineEdit()
        self.config_form_fields['mqtt_port'].setMaximumWidth(150)
        self.config_form_fields['mqtt_wsport'] = QLineEdit()
        self.config_form_fields['mqtt_wsport'].setMaximumWidth(150)
        
        # QFormLayoutではなく、手動でラベルとテキストボックスを配置
        mqtt_host_layout = QHBoxLayout()
        mqtt_host_label = QLabel("MQTT Host:")
        mqtt_host_label.setStyleSheet("color: white; min-width: 120px;")
        mqtt_host_layout.addWidget(mqtt_host_label)
        mqtt_host_layout.addWidget(self.config_form_fields['mqtt_host'])
        mqtt_host_layout.addStretch()
        main_layout.addLayout(mqtt_host_layout)
        
        mqtt_port_layout = QHBoxLayout()
        mqtt_port_label = QLabel("MQTT Port:")
        mqtt_port_label.setStyleSheet("color: white; min-width: 120px;")
        mqtt_port_layout.addWidget(mqtt_port_label)
        mqtt_port_layout.addWidget(self.config_form_fields['mqtt_port'])
        mqtt_port_layout.addStretch()
        main_layout.addLayout(mqtt_port_layout)
        
        ws_port_layout = QHBoxLayout()
        ws_port_label = QLabel("WebSocket Port:")
        ws_port_label.setStyleSheet("color: white; min-width: 120px;")
        ws_port_layout.addWidget(ws_port_label)
        ws_port_layout.addWidget(self.config_form_fields['mqtt_wsport'])
        ws_port_layout.addStretch()
        main_layout.addLayout(ws_port_layout)
        
        # 区切り線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #666;")
        main_layout.addWidget(line)
        
        # RestAPI設定セクション
        rest_label = QLabel("RestAPI設定")
        rest_label.setStyleSheet("font-weight: bold; color: white; font-size: 14px; margin-bottom: 5px; margin-top: 10px;")
        main_layout.addWidget(rest_label)
        
        self.config_form_fields['restapi_host'] = QLineEdit()
        self.config_form_fields['restapi_host'].setMaximumWidth(150)
        self.config_form_fields['restapi_port'] = QLineEdit()
        self.config_form_fields['restapi_port'].setMaximumWidth(150)
        
        rest_host_layout = QHBoxLayout()
        rest_host_label = QLabel("REST Host:")
        rest_host_label.setStyleSheet("color: white; min-width: 120px;")
        rest_host_layout.addWidget(rest_host_label)
        rest_host_layout.addWidget(self.config_form_fields['restapi_host'])
        rest_host_layout.addStretch()
        main_layout.addLayout(rest_host_layout)
        
        rest_port_layout = QHBoxLayout()
        rest_port_label = QLabel("REST Port:")
        rest_port_label.setStyleSheet("color: white; min-width: 120px;")
        rest_port_layout.addWidget(rest_port_label)
        rest_port_layout.addWidget(self.config_form_fields['restapi_port'])
        rest_port_layout.addStretch()
        main_layout.addLayout(rest_port_layout)
        
        # 区切り線
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        line2.setStyleSheet("color: #666;")
        main_layout.addWidget(line2)
        
        # その他設定セクション
        other_label = QLabel("その他")
        other_label.setStyleSheet("font-weight: bold; color: white; font-size: 14px; margin-bottom: 5px; margin-top: 10px;")
        main_layout.addWidget(other_label)
        
        self.config_form_fields['bench_name'] = QLineEdit()
        self.config_form_fields['bench_name'].setMaximumWidth(150)
        
        bench_layout = QHBoxLayout()
        bench_label = QLabel("ベンチ名:")
        bench_label.setStyleSheet("color: white; min-width: 120px;")
        bench_layout.addWidget(bench_label)
        bench_layout.addWidget(self.config_form_fields['bench_name'])
        bench_layout.addStretch()
        main_layout.addLayout(bench_layout)
        
        group.setLayout(main_layout)
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
    
    def clear_all_fields(self):
        """全フィールドをクリア"""
        try:
            for field_name in self.config_form_fields:
                self.config_form_fields[field_name].setText("")
            print("全設定フィールドをクリアしました")
        except Exception as e:
            print(f"フィールドクリアエラー: {e}")