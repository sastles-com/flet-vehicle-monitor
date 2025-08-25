#!/usr/bin/env python3
"""
CONFIG Mode Main View Component
CONFIGモード用メインビューコンポーネント
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QGroupBox, QGridLayout, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

from models.app_state import AppState, ConnectionStatus
from typing import Dict, Any, Optional


class ConfigView(QWidget):
    """CONFIG用メインビュー"""
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        
        # 内部状態
        self.config_displayed = False
        self.connection_status = ConnectionStatus()
        self.main_widget = self
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI初期化"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # タイトルセクション
        title_section = self._create_title_section()
        main_layout.addWidget(title_section)
        
        # メインコンテンツ
        content_layout = QHBoxLayout()
        
        # 左側：設定情報表示
        config_info_group = self._create_config_info_section()
        content_layout.addWidget(config_info_group)
        
        # 右側：接続状態表示
        status_group = self._create_status_section()
        content_layout.addWidget(status_group)
        
        main_layout.addLayout(content_layout)
        
        # 下部：操作ガイド
        guide_section = self._create_guide_section()
        main_layout.addWidget(guide_section)
        
        # スペーサー
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def _create_title_section(self) -> QWidget:
        """タイトルセクション作成"""
        title_widget = QWidget()
        layout = QVBoxLayout()
        
        # メインタイトル
        main_title = QLabel("Vehicle Monitor - CONFIG Mode")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        main_title.setFont(title_font)
        main_title.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        main_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(main_title)
        
        # サブタイトル
        sub_title = QLabel("システム設定と接続管理")
        sub_font = QFont()
        sub_font.setPointSize(14)
        sub_title.setFont(sub_font)
        sub_title.setStyleSheet("color: #666; margin-bottom: 20px;")
        sub_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub_title)
        
        title_widget.setLayout(layout)
        return title_widget
    
    def _create_config_info_section(self) -> QGroupBox:
        """設定情報表示セクション"""
        group = QGroupBox("現在の設定")
        layout = QVBoxLayout()
        
        # 設定情報表示エリア
        self.config_info_text = QTextEdit()
        self.config_info_text.setReadOnly(True)
        self.config_info_text.setMaximumHeight(200)
        self.config_info_text.setPlainText("設定が読み込まれていません。\n左のサイドバーから Config.json を読み込んでください。")
        
        layout.addWidget(self.config_info_text)
        
        group.setLayout(layout)
        return group
    
    def _create_status_section(self) -> QGroupBox:
        """接続状態セクション"""
        group = QGroupBox("接続状態")
        layout = QGridLayout()
        
        # 接続状態インジケータ
        self.status_labels = {}
        
        services = [
            ("MQTT", "MQTTブローカー"),
            ("REST", "RestAPIサーバー"), 
            ("ROS2", "ROS2システム")
        ]
        
        for i, (key, description) in enumerate(services):
            # サービス名
            name_label = QLabel(key)
            name_font = QFont()
            name_font.setBold(True)
            name_label.setFont(name_font)
            layout.addWidget(name_label, i, 0)
            
            # 状態インジケータ
            status_label = QLabel("●")
            status_label.setStyleSheet("color: #FF5722; font-size: 16px;")  # 初期状態は赤
            self.status_labels[key.lower()] = status_label
            layout.addWidget(status_label, i, 1)
            
            # 説明
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #666;")
            layout.addWidget(desc_label, i, 2)
        
        group.setLayout(layout)
        return group
    
    def _create_guide_section(self) -> QGroupBox:
        """操作ガイドセクション"""
        group = QGroupBox("操作ガイド")
        layout = QVBoxLayout()
        
        guide_text = """
CONFIGモードでの主な操作：

1. 設定ファイル読み込み
   • 左サイドバーの「Config.json読み込み」ボタンでファイルを選択
   • 読み込んだ設定がフォームに反映されます

2. 設定値の編集
   • サイドバーのフォームで直接編集可能
   • 変更は即座にアプリケーションに反映されます

3. 接続テスト
   • 「接続テスト実行」ボタンでMQTT/RestAPI接続を確認
   • 右側パネルで接続状態を確認できます

4. 次のステップ
   • 設定完了後、右上の「EDIT モードへ」ボタンで画像編集モードに進む
        """
        
        guide_label = QLabel(guide_text)
        guide_label.setStyleSheet("""
            QLabel {
                background-color: #E3F2FD;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #2196F3;
            }
        """)
        guide_label.setWordWrap(True)
        
        layout.addWidget(guide_label)
        
        group.setLayout(layout)
        return group
    
    def show_config_info(self, config_data: Dict[str, Any]):
        """設定情報を表示"""
        try:
            info_text = "=== 読み込まれた設定 ===\n\n"
            
            # MQTT設定
            if "mqtt" in config_data:
                mqtt = config_data["mqtt"]
                info_text += f"MQTT設定:\n"
                info_text += f"  Host: {mqtt.get('host', 'N/A')}\n"
                info_text += f"  Port: {mqtt.get('port', 'N/A')}\n"
                info_text += f"  WebSocket Port: {mqtt.get('wsPort', 'N/A')}\n\n"
            
            # RestAPI設定
            if "RestAPI" in config_data:
                rest = config_data["RestAPI"]
                info_text += f"RestAPI設定:\n"
                info_text += f"  Host: {rest.get('host', 'N/A')}\n"
                info_text += f"  Port: {rest.get('port', 'N/A')}\n\n"
            
            # ベンチ名
            if "bench" in config_data:
                info_text += f"ベンチ名: {config_data['bench']}\n\n"
            
            # カメラ設定（あれば）
            if "camera" in config_data:
                camera = config_data["camera"]
                info_text += f"カメラ設定:\n"
                info_text += f"  解像度: {camera.get('width', 'N/A')} x {camera.get('height', 'N/A')}\n"
                info_text += f"  スケール: {camera.get('scale', 'N/A')}\n\n"
            
            self.config_info_text.setPlainText(info_text)
            self.config_displayed = True
            
        except Exception as e:
            self.config_info_text.setPlainText(f"設定表示エラー: {str(e)}")
            self.config_displayed = False
    
    def update_connection_status(self, status: ConnectionStatus):
        """接続状態を更新"""
        self.connection_status = status
        
        # UIの更新
        status_map = {
            'mqtt': status.mqtt,
            'rest': status.restapi,
            'ros2': status.ros2
        }
        
        for service, is_connected in status_map.items():
            if service in self.status_labels:
                label = self.status_labels[service]
                if is_connected:
                    label.setStyleSheet("color: #4CAF50; font-size: 16px;")  # 緑
                    label.setToolTip(f"{service.upper()}: 接続済み")
                else:
                    label.setStyleSheet("color: #FF5722; font-size: 16px;")  # 赤
                    label.setToolTip(f"{service.upper()}: 未接続")