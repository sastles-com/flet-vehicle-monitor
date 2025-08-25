#!/usr/bin/env python3
"""
Application Mode Enumeration
アプリケーションモード定義
"""

from enum import Enum


class AppMode(Enum):
    """アプリケーションモード"""
    CONFIG = "CONFIG"
    EDIT = "EDIT" 
    MONITOR = "MONITOR"