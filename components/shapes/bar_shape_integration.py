#!/usr/bin/env python3
"""
Bar形状とCircumferenceポイント機能の統合例
app.pyに組み込む際の参考実装
"""

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QPen, QColor
from .bar_circumference import BarCircumferenceManager, create_bar_circumference_from_json


class IntegratedBarShape(QGraphicsRectItem):
    """Bar形状とCircumference機能を統合したクラス"""
    
    def __init__(self, x: float, y: float, width: float, height: float, 
                 vehicle_data: dict = None, scene_scale: float = 1.0):
        super().__init__(x, y, width, height)
        
        # バー形状の基本設定
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setPen(QPen(QColor(255, 128, 0), 2))
        self.setBrush(QBrush(QColor(255, 128, 0, 50)))
        
        # Circumference機能を追加
        self.circumference_manager = None
        if vehicle_data and 'circumference' in vehicle_data:
            self.circumference_manager = create_bar_circumference_from_json(
                self, vehicle_data, scene_scale
            )
        
        self._is_selected = False
    
    def setSelected(self, selected: bool):
        """選択状態の変更"""
        super().setSelected(selected)
        self._is_selected = selected
        
        if self.circumference_manager:
            self.circumference_manager.set_selected(selected)
    
    def itemChange(self, change, value):
        """アイテム変更時の処理"""
        result = super().itemChange(change, value)
        
        # 位置やサイズが変更された場合、circumferenceポイントを更新
        if change in [QGraphicsItem.ItemPositionHasChanged, 
                     QGraphicsItem.ItemSceneHasChanged]:
            if self.circumference_manager:
                self.circumference_manager.update_for_bar_changes()
        
        return result


# app.pyでの使用例
class BarShapeFactory:
    """app.pyで使用するためのBar形状ファクトリ"""
    
    @staticmethod
    def create_bar_from_vehicle_data(vehicle_data: dict, scene_scale: float = 1.0) -> IntegratedBarShape:
        """vehicle.jsonデータからBar形状を作成"""
        
        # vehicle.jsonから位置・サイズ情報を取得
        center_x = vehicle_data.get('center', {}).get('x', 100)
        center_y = vehicle_data.get('center', {}).get('y', 100)
        radius = vehicle_data.get('radius', 50)
        
        # バーの向きを判定（仮の実装）
        width = radius * 2
        height = radius / 2  # 横長のバー
        
        x = (center_x - width / 2) * scene_scale
        y = (center_y - height / 2) * scene_scale
        scaled_width = width * scene_scale
        scaled_height = height * scene_scale
        
        # 統合されたBar形状を作成
        bar_shape = IntegratedBarShape(
            x, y, scaled_width, scaled_height, 
            vehicle_data, scene_scale
        )
        
        return bar_shape
    
    @staticmethod
    def create_simple_bar(x: float, y: float, width: float, height: float) -> IntegratedBarShape:
        """シンプルなBar形状を作成（circumference機能なし）"""
        return IntegratedBarShape(x, y, width, height)


# app.pyでの統合方法例
"""
# app.py内での使用方法：

from components.shapes.bar_shape_integration import BarShapeFactory, IntegratedBarShape

class VehicleMonitorApp:
    def __init__(self):
        # ...既存の初期化...
        self.bar_shapes = []
    
    def load_vehicle_config(self, vehicle_json_path: str):
        '''vehicle.jsonを読み込んでBar形状を作成'''
        with open(vehicle_json_path, 'r') as f:
            vehicle_data = json.load(f)
        
        # meterセクションからbar形状を探す
        for meter_data in vehicle_data.get('meter', []):
            if meter_data.get('shape') == 'bar':
                bar_shape = BarShapeFactory.create_bar_from_vehicle_data(
                    meter_data, scene_scale=0.5
                )
                
                # シーンに追加
                self.graphics_scene.addItem(bar_shape)
                self.bar_shapes.append(bar_shape)
    
    def on_shape_selected(self, shape):
        '''図形選択時の処理'''
        if isinstance(shape, IntegratedBarShape):
            # Bar形状が選択された場合、circumferenceポイントが自動表示される
            shape.setSelected(True)
"""