#!/usr/bin/env python3
"""
Test for Application State Management
TDD第1段階：アプリケーション状態管理のテスト
"""

import unittest
import sys
import os

# テスト対象モジュールを追加
sys.path.insert(0, os.path.dirname(__file__))

class TestApplicationState(unittest.TestCase):
    """アプリケーション状態管理のテスト"""
    
    def test_app_mode_enum_creation(self):
        """AppModeエnum定義テスト"""
        from models.app_mode import AppMode
        
        # 3つのモードが定義されていること
        self.assertTrue(hasattr(AppMode, 'CONFIG'))
        self.assertTrue(hasattr(AppMode, 'EDIT'))
        self.assertTrue(hasattr(AppMode, 'MONITOR'))
        
        # 各モードに適切な値が設定されていること
        self.assertEqual(AppMode.CONFIG.value, 'CONFIG')
        self.assertEqual(AppMode.EDIT.value, 'EDIT')
        self.assertEqual(AppMode.MONITOR.value, 'MONITOR')
    
    def test_connection_status_creation(self):
        """ConnectionStatus クラス作成テスト"""
        from models.app_state import ConnectionStatus
        
        # デフォルトでFalseのインスタンス作成
        status = ConnectionStatus()
        self.assertFalse(status.mqtt)
        self.assertFalse(status.restapi)
        self.assertFalse(status.ros2)
        
        # 個別設定可能
        status.mqtt = True
        self.assertTrue(status.mqtt)
        self.assertFalse(status.restapi)
    
    def test_app_state_creation(self):
        """AppState クラス作成テスト"""
        from models.app_state import AppState
        from models.app_mode import AppMode
        
        # デフォルト状態でのインスタンス作成
        app_state = AppState()
        
        # デフォルトモードがCONFIG
        self.assertEqual(app_state.current_mode, AppMode.CONFIG)
        
        # サイドバーがデフォルトで展開
        self.assertTrue(app_state.sidebar_expanded)
        
        # デフォルトベンチ名
        self.assertEqual(app_state.bench_name, "")
        
        # デフォルトデバッグ情報
        self.assertEqual(app_state.debug_info, "Ready")
        
        # デフォルトフレームレート
        self.assertEqual(app_state.frame_rate, 0.0)
        
        # モニタリング状態
        self.assertFalse(app_state.monitoring_active)
    
    def test_app_state_header_title(self):
        """AppState ヘッダータイトル生成テスト"""
        from models.app_state import AppState
        from models.app_mode import AppMode
        
        app_state = AppState()
        
        # CONFIGモードのタイトル
        app_state.current_mode = AppMode.CONFIG
        expected_title = "Vehicle Monitor - CONFIG Mode"
        self.assertEqual(app_state.get_header_title(), expected_title)
        
        # EDITモードのタイトル
        app_state.current_mode = AppMode.EDIT
        expected_title = "Vehicle Monitor - EDIT Mode"
        self.assertEqual(app_state.get_header_title(), expected_title)
        
        # MONITORモードのタイトル
        app_state.current_mode = AppMode.MONITOR
        expected_title = "Vehicle Monitor - MONITOR Mode"
        self.assertEqual(app_state.get_header_title(), expected_title)
        
        # ベンチ名付きタイトル
        app_state.bench_name = "T40CD"
        app_state.current_mode = AppMode.CONFIG
        expected_title = "Vehicle Monitor - CONFIG Mode [T40CD]"
        self.assertEqual(app_state.get_header_title(), expected_title)

class TestConfigManager(unittest.TestCase):
    """設定管理のテスト"""
    
    def test_config_manager_creation(self):
        """ConfigManagerクラス作成テスト"""
        from models.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        
        # デフォルト設定データがNone
        self.assertIsNone(config_manager.config_data)
    
    def test_config_data_structure(self):
        """設定データ構造テスト"""
        from models.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        
        # サンプル設定データ
        sample_config = {
            "mqtt": {
                "host": "172.20.10.4",
                "port": "1883",
                "wsPort": "9001"
            },
            "RestAPI": {
                "host": "raspi-t40cd.local",
                "port": "8000"
            },
            "camera": {
                "width": 2304,
                "height": 1296,
                "scale": 0.125
            },
            "bench": "T40CD"
        }
        
        # 設定データの読み込み
        config_manager.config_data = sample_config
        
        # データアクセス
        self.assertEqual(config_manager.config_data["mqtt"]["host"], "172.20.10.4")
        self.assertEqual(config_manager.config_data["bench"], "T40CD")
        
    def test_config_validation(self):
        """設定データバリデーションテスト"""
        from models.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        
        # 有効な設定データ
        valid_config = {
            "mqtt": {"host": "localhost", "port": "1883"},
            "RestAPI": {"host": "localhost", "port": "8000"},
            "bench": "TEST"
        }
        
        # バリデーション成功
        self.assertTrue(config_manager.validate_config(valid_config))
        
        # 無効な設定データ（必須フィールド欠損）
        invalid_config = {
            "mqtt": {"host": "localhost"}  # portが欠損
        }
        
        # バリデーション失敗
        self.assertFalse(config_manager.validate_config(invalid_config))


if __name__ == "__main__":
    print("TDD第1段階：アプリケーション状態管理テスト開始")
    unittest.main(verbosity=2)