#!/usr/bin/env python3
"""
Application State Management
アプリケーション状態管理
"""

from dataclasses import dataclass
from typing import Optional
from .app_mode import AppMode


@dataclass
class ConnectionStatus:
    """接続状態クラス"""
    mqtt: bool = False
    restapi: bool = False
    ros2: bool = False


class AppState:
    """アプリケーション状態管理クラス"""
    
    def __init__(self):
        self.current_mode: AppMode = AppMode.CONFIG
        self.sidebar_expanded: bool = True
        self.bench_name: str = ""
        self.debug_info: str = "Ready"
        self.frame_rate: float = 0.0
        self.monitoring_active: bool = False
        self.connection_status: ConnectionStatus = ConnectionStatus()
    
    def get_header_title(self) -> str:
        """ヘッダータイトルを取得"""
        title = f"Vehicle Monitor - {self.current_mode.value} Mode"
        
        if self.bench_name:
            title += f" [{self.bench_name}]"
            
        return title