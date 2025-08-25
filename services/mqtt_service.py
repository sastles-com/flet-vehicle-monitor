#!/usr/bin/env python3
"""
MQTT Service for Vehicle Monitor
車両監視システム用MQTTサービス
"""

import json
import threading
import time
import base64
from typing import Optional, Dict, Any, Callable
from PySide6.QtCore import QObject, Signal

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Warning: paho-mqtt not installed. MQTT functionality will be disabled.")
    mqtt = None


class MQTTService(QObject):
    """MQTT接続とメッセージ送受信を管理するクラス"""
    
    # シグナル定義
    connected = Signal(bool)  # 接続状態変更
    disconnected = Signal()   # 切断
    image_received = Signal(str)  # 画像データ受信（base64文字列）
    
    def __init__(self):
        super().__init__()
        self.client: Optional[mqtt.Client] = None
        self.config: Optional[Dict[str, Any]] = None
        self.is_connected = False
        
        # サブスクリプション管理
        self.subscribed_topics = set()
        self.current_mode = "CONFIG"
        
    def set_config(self, mqtt_config: Dict[str, Any]):
        """MQTT設定を更新"""
        self.config = mqtt_config
        print(f"MQTT config updated: {mqtt_config}")
        
    def connect_async(self) -> bool:
        """MQTT接続を開始（非同期）"""
        if not mqtt:
            print("MQTT library not available")
            self.connected.emit(False)
            return False
            
        if not self.config:
            print("MQTT config not set")
            self.connected.emit(False)
            return False
            
        def connect_in_background():
            try:
                # 既存の接続があれば切断
                if self.client:
                    self.client.disconnect()
                
                # MQTTクライアントを作成
                self.client = mqtt.Client(protocol=mqtt.MQTTv311)
                self.client.on_connect = self._on_connect
                self.client.on_message = self._on_message
                self.client.on_disconnect = self._on_disconnect
                
                # 接続実行
                host = self.config.get("host", "localhost")
                port = int(self.config.get("port", 1883))
                
                print(f"Connecting to MQTT broker: {host}:{port}")
                self.client.connect(host, port, 60)
                
                # メッセージループを開始
                self.client.loop_start()
                
            except Exception as e:
                print(f"MQTT connection error: {e}")
                self.is_connected = False
                self.connected.emit(False)
        
        # バックグラウンドで接続
        threading.Thread(target=connect_in_background, daemon=True).start()
        return True
    
    def disconnect(self):
        """MQTT接続を切断"""
        if self.client:
            self.client.disconnect()
            self.client = None
        self.is_connected = False
    
    def subscribe_image_topic(self) -> bool:
        """画像トピックを購読"""
        return self.subscribe("image")
    
    def subscribe(self, topic: str) -> bool:
        """トピックを購読"""
        if not self.client or not self.is_connected:
            print(f"MQTT not connected - cannot subscribe to '{topic}'")
            return False
            
        try:
            result = self.client.subscribe(topic)
            self.subscribed_topics.add(topic)
            print(f"Subscribed to '{topic}' topic")
            return True
        except Exception as e:
            print(f"Subscribe error for topic '{topic}': {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT接続成功時のコールバック"""
        if rc == 0:
            print("MQTT connected successfully")
            self.is_connected = True
            self.connected.emit(True)
            
            # 画像トピックを自動購読
            if self.current_mode in ["CONFIG", "MONITOR"]:
                print("Auto-subscribing to 'image' topic")
                self.subscribe("image")
                
                # デバッグ用: すべてのトピックも購読してみる
                print("DEBUG: Also subscribing to wildcard topics")
                self.subscribe("#")  # すべてのトピック
        else:
            print(f"MQTT connection failed with code {rc}")
            self.is_connected = False
            self.connected.emit(False)
    
    def _on_message(self, client, userdata, msg):
        """MQTT メッセージ受信時のコールバック"""
        try:
            print(f"*** MQTT message received on topic: '{msg.topic}' ***")
            print(f"*** Message payload size: {len(msg.payload)} bytes ***")
            
            if msg.topic == "image":
                print("*** Processing 'image' topic message... ***")
                
                try:
                    # デバッグ: 生のペイロードの最初の部分を表示
                    raw_payload = msg.payload.decode('utf-8', errors='ignore')
                    print(f"*** Raw payload preview (first 200 chars): {raw_payload[:200]} ***")
                    
                    # Raspberry Piから送信されるJSON形式のメッセージを処理
                    message_data = json.loads(msg.payload.decode())
                    print(f"*** JSON parsed successfully ***")
                    print(f"*** JSON keys: {list(message_data.keys())} ***")
                    
                    if "image" in message_data and message_data["image"]:
                        image_data = message_data["image"]
                        print(f"*** Image data length: {len(image_data)} characters ***")
                        print(f"*** Image data starts with: {image_data[:50]}... ***")
                        
                        # 画像データをシグナルで送信
                        self.image_received.emit(image_data)
                        print("*** Image data emitted via signal ***")
                    else:
                        print("*** CRITICAL: Invalid image message format - no 'image' key found or empty data ***")
                        print(f"*** Message content: {message_data} ***")
                        
                except json.JSONDecodeError as e:
                    print(f"*** JSON decode error: {e} ***")
                    print(f"*** Raw payload: {msg.payload[:500]} ***")
                    
            else:
                print(f"*** Non-image topic message: {msg.topic} ***")
                # 他のトピックの場合も内容を少し表示
                try:
                    preview = msg.payload.decode('utf-8', errors='ignore')[:100]
                    print(f"*** Message preview: {preview} ***")
                except:
                    print(f"*** Binary message, size: {len(msg.payload)} bytes ***")
                    
        except Exception as e:
            print(f"*** MQTT message processing error: {e} ***")
            import traceback
            traceback.print_exc()
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT切断時のコールバック"""
        print(f"MQTT disconnected with code {rc}")
        self.is_connected = False
        self.disconnected.emit()
    
    def get_connection_status(self) -> bool:
        """接続状態を確認"""
        return self.is_connected
    
    def set_mode(self, mode: str):
        """動作モードを設定"""
        self.current_mode = mode
        print(f"MQTT service mode set to: {mode}")