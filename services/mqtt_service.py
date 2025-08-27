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
from PySide6.QtCore import QObject, Signal, Slot

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
    ros2_alive_received = Signal()  # ROS2応答受信（{"alive": true}）
    
    def __init__(self):
        super().__init__()
        self.client: Optional[mqtt.Client] = None
        self.config: Optional[Dict[str, Any]] = None
        self._is_connected = False
        
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
                self._is_connected = False
                self.connected.emit(False)
        
        # バックグラウンドで接続
        threading.Thread(target=connect_in_background, daemon=True).start()
        return True
    
    def disconnect(self):
        """MQTT接続を切断"""
        if self.client:
            self.client.disconnect()
            self.client = None
        self._is_connected = False
    
    def subscribe_image_topic(self) -> bool:
        """画像トピックを購読"""
        # imageトピックと、デバッグのためにすべてのトピックを購読
        image_result = self.subscribe("image")
        debug_result = self.subscribe("#")  # すべてのトピックを購読
        print(f"*** MQTT: Subscribed to 'image': {image_result}, all topics '#': {debug_result} ***")
        return image_result
    
    def subscribe(self, topic: str) -> bool:
        """トピックを購読"""
        if not self.client or not self._is_connected:
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
            self._is_connected = True
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
            self._is_connected = False
            self.connected.emit(False)
    
    def _on_message(self, client, userdata, msg):
        """MQTT メッセージ受信時のコールバック"""
        try:
            # image/response/data以外のトピックのメッセージのみログ表示
            if msg.topic not in ["image", "response", "data"]:
                print(f"*** MQTT message received on topic: '{msg.topic}' ***")
                print(f"*** Message payload size: {len(msg.payload)} bytes ***")
                try:
                    preview = msg.payload.decode('utf-8', errors='ignore')[:200]
                    print(f"*** Message content: {preview} ***")
                except:
                    print(f"*** Binary message, size: {len(msg.payload)} bytes ***")
            
            if msg.topic == "image":
                try:
                    # JSON解析を試行
                    message_data = json.loads(msg.payload.decode())
                    
                    # 画像データの存在確認
                    if "image" in message_data and message_data["image"]:
                        image_data = message_data["image"]
                        
                        # 画像データをスレッドセーフにシグナル送信
                        try:
                            # 直接シグナルを送信（Qt自体がスレッドセーフ）
                            self.image_received.emit(image_data)
                        except RuntimeError as e:
                            # シグナル送信先が削除されている場合のエラーを無視
                            if "Signal source has been deleted" in str(e):
                                pass  # 無視
                            else:
                                print(f"*** MQTT: Runtime error during signal scheduling: {e} ***")
                                raise e
                        except Exception as e:
                            print(f"*** MQTT: Unexpected error during signal scheduling: {e} ***")
                            raise e
                    else:
                        print(f"*** CRITICAL: Invalid image message format - missing 'image' key or empty data ***")
                        
                except json.JSONDecodeError as e:
                    print(f"*** Image topic JSON decode error: {e} ***")
                except Exception as e:
                    print(f"*** Unexpected error during image processing: {e} ***")
                    import traceback
                    traceback.print_exc()
            
            elif msg.topic == "response":
                # responseトピック受信処理（ROS2生存確認）
                try:
                    message_data = json.loads(msg.payload.decode())
                    
                    # ROS2生存確認
                    if "alive" in message_data and message_data["alive"] is True:
                        # ROS2応答シグナル送信
                        self.ros2_alive_received.emit()
                    
                except json.JSONDecodeError as e:
                    print(f"*** Response topic JSON decode error: {e} ***")
                except Exception as e:
                    print(f"*** Unexpected error during response processing: {e} ***")
                    import traceback
                    traceback.print_exc()
                    
        except Exception as e:
            print(f"*** MQTT message processing error: {e} ***")
            import traceback
            traceback.print_exc()
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT切断時のコールバック"""
        print(f"MQTT disconnected with code {rc}")
        self._is_connected = False
        self.disconnected.emit()
    
    def set_mode(self, mode: str):
        """動作モードを設定"""
        self.current_mode = mode
        print(f"MQTT service mode set to: {mode}")
    
    def is_connected(self) -> bool:
        """接続状態を確認（統一インターフェース）"""
        return self._is_connected
    
# _emit_image_signal メソッドは直接シグナル送信に変更のため削除
    
    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> bool:
        """MQTTメッセージを送信"""
        try:
            if not self.client or not self._is_connected:
                print(f"*** MQTT not connected - cannot publish to {topic} ***")
                return False
            
            print(f"*** Attempting to publish to topic '{topic}' ***")
            print(f"*** Payload preview: {payload[:200]}... ***")
            
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"*** Successfully published to '{topic}' (QoS: {qos}, Retain: {retain}): {len(payload)} chars ***")
                return True
            else:
                print(f"*** Failed to publish to '{topic}': {mqtt.error_string(result.rc)} ***")
                return False
                
        except Exception as e:
            print(f"*** Error publishing to MQTT topic '{topic}': {e} ***")
            import traceback
            traceback.print_exc()
            return False