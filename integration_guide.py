#!/usr/bin/env python3
"""
app.pyにBar形状circumference機能を統合するためのガイドとヘルパー関数

このファイルは統合の参考として使用し、実際のapp.pyの構造に合わせて調整してください。
"""

import json
import os
from typing import List, Dict, Any
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

# 新しく作成した機能をインポート
from components.shapes import IntegratedBarShape, BarShapeFactory


class VehicleMonitorIntegration:
    """app.pyにBar形状circumference機能を統合するためのヘルパークラス"""
    
    def __init__(self, graphics_scene: QGraphicsScene):
        self.scene = graphics_scene
        self.bar_shapes: List[IntegratedBarShape] = []
        self.scene_scale = 1.0
    
    def set_scene_scale(self, scale: float):
        """シーンスケールを設定"""
        self.scene_scale = scale
        # 既存のBar形状のスケールも更新
        for bar_shape in self.bar_shapes:
            if bar_shape.circumference_manager:
                bar_shape.circumference_manager.scene_scale = scale
    
    def load_vehicle_json(self, json_path: str) -> bool:
        """vehicle.jsonを読み込んでBar形状を作成"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                vehicle_data = json.load(f)
            
            return self.create_shapes_from_data(vehicle_data)
            
        except Exception as e:
            print(f"vehicle.json読み込みエラー: {e}")
            return False
    
    def create_shapes_from_data(self, vehicle_data: dict) -> bool:
        """vehicle.jsonデータからBar形状を作成"""
        try:
            # meterセクションからbar形状を探す
            for meter_data in vehicle_data.get('meter', []):
                if meter_data.get('shape') == 'bar':
                    bar_shape = BarShapeFactory.create_bar_from_vehicle_data(
                        meter_data, self.scene_scale
                    )
                    
                    # シーンに追加
                    self.scene.addItem(bar_shape)
                    self.bar_shapes.append(bar_shape)
                    
                    print(f"Bar形状を作成しました: {meter_data.get('name', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"Bar形状作成エラー: {e}")
            return False
    
    def clear_bar_shapes(self):
        """すべてのBar形状をクリア"""
        for bar_shape in self.bar_shapes:
            if bar_shape.scene():
                bar_shape.scene().removeItem(bar_shape)
        self.bar_shapes.clear()
    
    def get_selected_bar_shape(self) -> IntegratedBarShape:
        """選択されているBar形状を取得"""
        for bar_shape in self.bar_shapes:
            if bar_shape.isSelected():
                return bar_shape
        return None
    
    def update_all_bar_displays(self):
        """すべてのBar形状の表示を更新"""
        for bar_shape in self.bar_shapes:
            if bar_shape.circumference_manager:
                bar_shape.circumference_manager.update_for_bar_changes()


# app.py統合例
"""
# app.py内での使用方法：

from integration_guide import VehicleMonitorIntegration

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # Bar形状統合機能を初期化
        self.bar_integration = VehicleMonitorIntegration(self.graphics_scene)
        
    def load_config(self):
        '''設定読み込み処理'''
        # 既存の設定読み込み処理...
        
        # vehicle.jsonがあれば読み込み
        vehicle_json_path = os.path.join(self.config_dir, "vehicle.json")
        if os.path.exists(vehicle_json_path):
            success = self.bar_integration.load_vehicle_json(vehicle_json_path)
            if success:
                print("Bar形状circumference機能を読み込みました")
            else:
                print("Bar形状の読み込みに失敗しました")
    
    def on_scene_scale_changed(self, scale: float):
        '''シーンスケール変更時の処理'''
        self.bar_integration.set_scene_scale(scale)
    
    def on_selection_changed(self):
        '''選択変更時の処理'''
        selected_bar = self.bar_integration.get_selected_bar_shape()
        if selected_bar:
            print(f"Bar形状が選択されました: circumference機能が有効")
            # circumferenceポイントが自動的に表示される

# 最小統合版（既存のapp.pyに3行だけ追加）
class MinimalIntegration:
    '''既存のapp.pyに最小限の変更で統合する場合'''
    
    def __init__(self, existing_app):
        # 1. インポート追加
        from integration_guide import VehicleMonitorIntegration
        
        # 2. 統合機能を初期化
        self.bar_integration = VehicleMonitorIntegration(existing_app.graphics_scene)
        
        # 3. vehicle.json読み込み
        self.bar_integration.load_vehicle_json("data/vehicle.json")
"""


def create_test_vehicle_json():
    """テスト用のvehicle.jsonを作成"""
    test_data = {
        "name": "TEST_BAR",
        "meter": [
            {
                "name": "test_bar",
                "shape": "bar", 
                "center": {"x": 200, "y": 100},
                "radius": 100,
                "circumference": [
                    {
                        "position": {"x": 150, "y": 100},
                        "value": 0.0
                    },
                    {
                        "position": {"x": 200, "y": 100}, 
                        "value": 0.5
                    },
                    {
                        "position": {"x": 250, "y": 100},
                        "value": 1.0
                    }
                ]
            }
        ]
    }
    
    with open("test_vehicle.json", "w") as f:
        json.dump(test_data, f, indent=2)
    
    print("テスト用vehicle.jsonを作成しました: test_vehicle.json")


if __name__ == "__main__":
    create_test_vehicle_json()