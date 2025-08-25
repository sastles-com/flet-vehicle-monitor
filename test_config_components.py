#!/usr/bin/env python3
"""
Test for CONFIG Mode Components
TDD第2段階：CONFIGモードコンポーネントのテスト
"""

import unittest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# テスト対象モジュールを追加
sys.path.insert(0, os.path.dirname(__file__))

# PyQtをモック（テスト実行時にGUIが立ち上がらないようにするため）
class TestConfigSidebar(unittest.TestCase):
    """CONFIG用サイドバーのテスト"""
    
    def setUp(self):
        """テスト前準備"""
        # PyQt6のモック
        self.mock_qtwidgets = Mock()
        self.mock_qtcore = Mock()
        self.mock_qtgui = Mock()
        
        # sys.modulesにモジュールを登録
        sys.modules['PySide6'] = Mock()
        sys.modules['PySide6.QtWidgets'] = self.mock_qtwidgets
        sys.modules['PySide6.QtCore'] = self.mock_qtcore
        sys.modules['PySide6.QtGui'] = self.mock_qtgui
        
        # 基本的なQtクラスをモック
        self.mock_qtwidgets.QWidget = Mock
        self.mock_qtwidgets.QVBoxLayout = Mock
        self.mock_qtwidgets.QLabel = Mock
        self.mock_qtwidgets.QLineEdit = Mock
        self.mock_qtwidgets.QPushButton = Mock
        self.mock_qtwidgets.QFormLayout = Mock
    
    def test_config_sidebar_creation(self):
        """ConfigSidebar クラス作成テスト"""
        from models.app_state import AppState
        from components.config.config_sidebar import ConfigSidebar
        
        app_state = AppState()
        
        # ConfigSidebarインスタンス作成
        sidebar = ConfigSidebar(app_state, width=320)
        
        # 基本プロパティの確認
        self.assertEqual(sidebar.app_state, app_state)
        self.assertEqual(sidebar.width, 320)
        self.assertIsNotNone(sidebar.config_form_fields)
    
    def test_config_form_fields(self):
        """設定フォームフィールドテスト"""
        from models.app_state import AppState
        from components.config.config_sidebar import ConfigSidebar
        
        app_state = AppState()
        sidebar = ConfigSidebar(app_state)
        
        # 必要なフィールドが存在することを確認
        expected_fields = [
            'mqtt_host', 'mqtt_port', 'mqtt_wsport',
            'restapi_host', 'restapi_port', 'bench_name'
        ]
        
        for field in expected_fields:
            self.assertIn(field, sidebar.config_form_fields)
    
    def test_config_load_from_data(self):
        """設定データ読み込みテスト"""
        from models.app_state import AppState
        from components.config.config_sidebar import ConfigSidebar
        
        app_state = AppState()
        sidebar = ConfigSidebar(app_state)
        
        # テスト用設定データ
        test_config = {
            "mqtt": {"host": "192.168.1.100", "port": "1883", "wsPort": "9001"},
            "RestAPI": {"host": "raspi.local", "port": "8000"},
            "bench": "T40CD"
        }
        
        # データ読み込み
        sidebar.load_config_data(test_config)
        
        # フィールドに正しく設定されているか確認
        self.assertEqual(sidebar.get_field_value('mqtt_host'), "192.168.1.100")
        self.assertEqual(sidebar.get_field_value('mqtt_port'), "1883")
        self.assertEqual(sidebar.get_field_value('bench_name'), "T40CD")
    
    def test_config_get_current_data(self):
        """現在の設定データ取得テスト"""
        from models.app_state import AppState
        from components.config.config_sidebar import ConfigSidebar
        
        app_state = AppState()
        sidebar = ConfigSidebar(app_state)
        
        # フィールド値設定
        sidebar.set_field_value('mqtt_host', '172.20.10.4')
        sidebar.set_field_value('mqtt_port', '1883')
        sidebar.set_field_value('bench_name', 'TEST_BENCH')
        
        # 現在の設定データ取得
        current_config = sidebar.get_current_config()
        
        # 期待される構造の確認
        self.assertIn('mqtt', current_config)
        self.assertIn('RestAPI', current_config)
        self.assertEqual(current_config['mqtt']['host'], '172.20.10.4')
        self.assertEqual(current_config['bench'], 'TEST_BENCH')


class TestConfigView(unittest.TestCase):
    """CONFIG用メインビューのテスト"""
    
    def setUp(self):
        """テスト前準備"""
        # PyQt6のモック
        sys.modules['PySide6'] = Mock()
        sys.modules['PySide6.QtWidgets'] = Mock()
        sys.modules['PySide6.QtCore'] = Mock()
        sys.modules['PySide6.QtGui'] = Mock()
    
    def test_config_view_creation(self):
        """ConfigView クラス作成テスト"""
        from models.app_state import AppState
        from components.config.config_view import ConfigView
        
        app_state = AppState()
        
        # ConfigViewインスタンス作成
        view = ConfigView(app_state)
        
        # 基本プロパティの確認
        self.assertEqual(view.app_state, app_state)
        self.assertIsNotNone(view.main_widget)
    
    def test_config_info_display(self):
        """設定情報表示テスト"""
        from models.app_state import AppState
        from components.config.config_view import ConfigView
        
        app_state = AppState()
        view = ConfigView(app_state)
        
        # テスト設定データ
        test_config = {
            "mqtt": {"host": "test.local", "port": "1883"},
            "bench": "TEST"
        }
        
        # 設定情報表示
        view.show_config_info(test_config)
        
        # 表示更新が呼ばれたことを確認
        self.assertTrue(view.config_displayed)
    
    def test_connection_status_display(self):
        """接続状態表示テスト"""
        from models.app_state import AppState, ConnectionStatus
        from components.config.config_view import ConfigView
        
        app_state = AppState()
        view = ConfigView(app_state)
        
        # 接続状態設定
        status = ConnectionStatus()
        status.mqtt = True
        status.restapi = False
        status.ros2 = True
        
        # 接続状態表示更新
        view.update_connection_status(status)
        
        # 内部状態の確認
        self.assertEqual(view.connection_status.mqtt, True)
        self.assertEqual(view.connection_status.restapi, False)
        self.assertEqual(view.connection_status.ros2, True)


class TestMainLayout(unittest.TestCase):
    """メインレイアウトのテスト"""
    
    def setUp(self):
        """テスト前準備"""
        sys.modules['PySide6'] = Mock()
        sys.modules['PySide6.QtWidgets'] = Mock()
        sys.modules['PySide6.QtCore'] = Mock()
        sys.modules['PySide6.QtGui'] = Mock()
    
    def test_main_layout_creation(self):
        """MainLayout クラス作成テスト"""
        from models.app_state import AppState
        from components.common.main_layout import MainLayout
        
        app_state = AppState()
        
        # MainLayoutインスタンス作成
        layout = MainLayout(app_state)
        
        # 基本プロパティ確認
        self.assertEqual(layout.app_state, app_state)
        self.assertIsNotNone(layout.main_widget)
    
    def test_mode_switching(self):
        """モード切替テスト"""
        from models.app_state import AppState
        from models.app_mode import AppMode
        from components.common.main_layout import MainLayout
        
        app_state = AppState()
        layout = MainLayout(app_state)
        
        # 初期状態はCONFIG
        self.assertEqual(app_state.current_mode, AppMode.CONFIG)
        
        # EDITモードに切替
        layout.switch_to_mode(AppMode.EDIT)
        self.assertEqual(app_state.current_mode, AppMode.EDIT)
        
        # MONITORモードに切替
        layout.switch_to_mode(AppMode.MONITOR)
        self.assertEqual(app_state.current_mode, AppMode.MONITOR)


if __name__ == "__main__":
    print("TDD第2段階：CONFIGモードコンポーネントテスト開始")
    unittest.main(verbosity=2)