#!/usr/bin/env python3
"""
Test for MQTT Service
MQTTサービスのユニットテスト - TDD設計
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
# QSignalSpyの代替実装（PySide6.QtTestが使えない環境対応）
class QSignalSpy:
    def __init__(self, signal):
        self.signal = signal
        self.calls = []
        self.signal.connect(self._on_signal)
    
    def _on_signal(self, *args):
        self.calls.append(args)
    
    def __len__(self):
        return len(self.calls)
    
    def __getitem__(self, index):
        return self.calls[index]
    
    def count(self):
        return len(self.calls)

# テスト対象をインポート
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.mqtt_service import MQTTService


class TestMQTTService(unittest.TestCase):
    """MQTTServiceクラスのテスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラス全体の初期化"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """各テストの初期化"""
        self.mqtt_service = MQTTService()
    
    def tearDown(self):
        """各テストの後処理"""
        if hasattr(self.mqtt_service, 'client') and self.mqtt_service.client:
            self.mqtt_service.disconnect()
    
    def test_mqtt_service_initialization(self):
        """MQTTサービスの初期化テスト"""
        # 初期状態の確認
        self.assertIsNotNone(self.mqtt_service)
        self.assertFalse(self.mqtt_service.get_connection_status())
        self.assertEqual(self.mqtt_service.current_mode, "CONFIG")
        self.assertIsNone(self.mqtt_service.config)
        self.assertEqual(len(self.mqtt_service.subscribed_topics), 0)
    
    def test_config_setting(self):
        """設定情報の設定テスト"""
        config = {
            "host": "192.168.1.100",
            "port": "1883",
            "wsPort": "9001"
        }
        
        self.mqtt_service.set_config(config)
        self.assertEqual(self.mqtt_service.config, config)
    
    def test_mode_setting(self):
        """動作モードの設定テスト"""
        modes = ["CONFIG", "EDIT", "MONITOR"]
        
        for mode in modes:
            self.mqtt_service.set_mode(mode)
            self.assertEqual(self.mqtt_service.current_mode, mode)
    
    @patch('services.mqtt_service.mqtt')
    def test_connection_success(self, mock_mqtt_module):
        """MQTT接続成功テスト"""
        # モックの設定
        mock_client = Mock()
        mock_mqtt_module.Client.return_value = mock_client
        mock_mqtt_module.MQTTv311 = 4
        
        # 設定を登録
        config = {"host": "test_host", "port": "1883"}
        self.mqtt_service.set_config(config)
        
        # シグナルスパイの設定
        connection_spy = QSignalSpy(self.mqtt_service.connected)
        
        # 接続実行
        result = self.mqtt_service.connect_async()
        
        # 結果確認
        self.assertTrue(result)
        mock_mqtt_module.Client.assert_called_once()
        mock_client.connect.assert_called_once_with("test_host", 1883, 60)
        mock_client.loop_start.assert_called_once()
    
    @patch('services.mqtt_service.mqtt', None)
    def test_connection_without_mqtt_library(self):
        """MQTTライブラリが無い場合の接続テスト"""
        config = {"host": "test_host", "port": "1883"}
        self.mqtt_service.set_config(config)
        
        # シグナルスパイの設定
        connection_spy = QSignalSpy(self.mqtt_service.connected)
        
        # 接続実行
        result = self.mqtt_service.connect_async()
        
        # 結果確認
        self.assertFalse(result)
        # シグナルがFalseで発信されることを期待
        self.assertEqual(len(connection_spy), 1)
        self.assertFalse(connection_spy[0][0])  # connected(False)が発信される
    
    def test_connection_without_config(self):
        """設定なしでの接続テスト"""
        # シグナルスパイの設定
        connection_spy = QSignalSpy(self.mqtt_service.connected)
        
        # 接続実行（設定なし）
        result = self.mqtt_service.connect_async()
        
        # 結果確認
        self.assertFalse(result)
        self.assertEqual(len(connection_spy), 1)
        self.assertFalse(connection_spy[0][0])  # connected(False)が発信される
    
    def test_subscription_without_connection(self):
        """接続なしでの購読テスト"""
        result = self.mqtt_service.subscribe("test_topic")
        self.assertFalse(result)
        
        result = self.mqtt_service.subscribe_image_topic()
        self.assertFalse(result)
    
    @patch('services.mqtt_service.mqtt')
    def test_image_topic_subscription(self, mock_mqtt_module):
        """画像トピック購読テスト"""
        # モックの設定
        mock_client = Mock()
        mock_mqtt_module.Client.return_value = mock_client
        mock_mqtt_module.MQTTv311 = 4
        
        # 接続済み状態をシミュレート
        self.mqtt_service.client = mock_client
        self.mqtt_service.is_connected = True
        
        # 購読実行
        result = self.mqtt_service.subscribe_image_topic()
        
        # 結果確認
        self.assertTrue(result)
        mock_client.subscribe.assert_called_once_with("image")
        self.assertIn("image", self.mqtt_service.subscribed_topics)
    
    def test_message_processing_signal_emission(self):
        """メッセージ処理とシグナル発信テスト"""
        import json
        
        # シグナルスパイの設定
        image_spy = QSignalSpy(self.mqtt_service.image_received)
        
        # モックメッセージの作成
        mock_msg = Mock()
        mock_msg.topic = "image"
        test_image_data = "base64_encoded_image_data_here"
        mock_msg.payload.decode.return_value = json.dumps({"image": test_image_data})
        
        # メッセージ処理実行
        self.mqtt_service._on_message(None, None, mock_msg)
        
        # シグナル発信確認
        self.assertEqual(len(image_spy), 1)
        self.assertEqual(image_spy[0][0], test_image_data)
    
    def test_message_processing_invalid_json(self):
        """無効なJSONメッセージの処理テスト"""
        # シグナルスパイの設定
        image_spy = QSignalSpy(self.mqtt_service.image_received)
        
        # 無効なJSONメッセージ
        mock_msg = Mock()
        mock_msg.topic = "image"
        mock_msg.payload.decode.return_value = "invalid json data"
        
        # メッセージ処理実行（例外が発生しないことを確認）
        try:
            self.mqtt_service._on_message(None, None, mock_msg)
        except Exception as e:
            self.fail(f"Message processing should handle invalid JSON gracefully: {e}")
        
        # シグナルが発信されないことを確認
        self.assertEqual(len(image_spy), 0)
    
    def test_disconnect(self):
        """切断テスト"""
        # モッククライアントの設定
        mock_client = Mock()
        self.mqtt_service.client = mock_client
        self.mqtt_service.is_connected = True
        
        # 切断実行
        self.mqtt_service.disconnect()
        
        # 結果確認
        mock_client.disconnect.assert_called_once()
        self.assertIsNone(self.mqtt_service.client)
        self.assertFalse(self.mqtt_service.is_connected)
    
    def test_connection_callback_success(self):
        """接続成功コールバックテスト"""
        # シグナルスパイの設定
        connection_spy = QSignalSpy(self.mqtt_service.connected)
        
        # 接続成功をシミュレート
        self.mqtt_service._on_connect(None, None, None, 0)  # rc=0は成功
        
        # 結果確認
        self.assertTrue(self.mqtt_service.is_connected)
        self.assertEqual(len(connection_spy), 1)
        self.assertTrue(connection_spy[0][0])  # connected(True)が発信される
    
    def test_connection_callback_failure(self):
        """接続失敗コールバックテスト"""
        # シグナルスパイの設定
        connection_spy = QSignalSpy(self.mqtt_service.connected)
        
        # 接続失敗をシミュレート
        self.mqtt_service._on_connect(None, None, None, 1)  # rc=1は失敗
        
        # 結果確認
        self.assertFalse(self.mqtt_service.is_connected)
        self.assertEqual(len(connection_spy), 1)
        self.assertFalse(connection_spy[0][0])  # connected(False)が発信される
    
    def test_disconnect_callback(self):
        """切断コールバックテスト"""
        # シグナルスパイの設定
        disconnect_spy = QSignalSpy(self.mqtt_service.disconnected)
        
        # 切断をシミュレート
        self.mqtt_service._on_disconnect(None, None, 0)
        
        # 結果確認
        self.assertFalse(self.mqtt_service.is_connected)
        self.assertEqual(len(disconnect_spy), 1)


if __name__ == '__main__':
    # テスト実行
    unittest.main(verbosity=2)