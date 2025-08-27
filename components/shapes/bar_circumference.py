#!/usr/bin/env python3
"""
Bar形状のCircumferenceポイント管理機能
独立したモジュールとして実装され、任意のアプリケーションから利用可能
"""

import math
from typing import List, Optional
from dataclasses import dataclass
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QPen, QColor, QFont


@dataclass
class Position:
    """座標データ"""
    x: float
    y: float


@dataclass  
class CircumferencePoint:
    """circumferenceポイントのデータクラス"""
    position: Position
    value: float


class CircumferencePointItem(QGraphicsEllipseItem):
    """circumferenceポイント用のUI制御点"""
    
    def __init__(self, x, y, width, height, bar_manager, point_data, index):
        super().__init__(x, y, width, height)
        self.bar_manager = bar_manager
        self.point_data = point_data
        self.index = index
        self.is_dragging = False
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.bar_manager.circumference_dragging = True
            event.accept()
        
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.bar_manager.handle_point_drag(self, event)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.bar_manager.circumference_dragging = False
            self.bar_manager.handle_point_release(self)
            event.accept()


class BarCircumferenceManager:
    """Bar形状のCircumferenceポイント管理クラス"""
    
    def __init__(self, bar_item, scene_scale: float = 1.0):
        """
        Args:
            bar_item: バー形状のQGraphicsItem
            scene_scale: シーンのスケール
        """
        self.bar_item = bar_item
        self.scene_scale = scene_scale
        self.circumference_points: List[CircumferencePoint] = []
        self.circumference_items: List[QGraphicsItem] = []
        self.circumference_dragging = False
        self.is_selected = False
        
        # バーの向きを判定
        rect = bar_item.boundingRect()
        aspect_ratio = rect.width() / rect.height() if rect.height() > 0 else 1.0
        self.orientation = "horizontal" if aspect_ratio > 1.0 else "vertical"
        
        # 初期座標を保存
        pos = bar_item.pos()
        self.original_center_x = pos.x() + rect.width() / 2
        self.original_center_y = pos.y() + rect.height() / 2
        self.original_radius = max(rect.width(), rect.height()) / 2
        
    def set_circumference_points(self, points: List[CircumferencePoint]):
        """circumferenceポイントを設定"""
        self.circumference_points = points
        self._initialize_relative_positions()
        
    def _initialize_relative_positions(self):
        """相対位置を初期化"""
        for point in self.circumference_points:
            if not hasattr(point, '_calculated_relative_pos'):
                if hasattr(point, 'position') and point.position:
                    # vehicle.jsonの座標から相対位置を計算
                    scaled_x = point.position.x * self.scene_scale
                    scaled_y = point.position.y * self.scene_scale
                    
                    if self.orientation == "horizontal":
                        original_width = self.original_radius * 2
                        calculated_relative = (scaled_x - (self.original_center_x - original_width/2)) / original_width
                        if 0.0 <= calculated_relative <= 1.0:
                            point._calculated_relative_pos = calculated_relative
                        else:
                            point._calculated_relative_pos = point.value
                    else:
                        original_height = self.original_radius * 2
                        calculated_relative = (scaled_y - (self.original_center_y - original_height/2)) / original_height
                        if 0.0 <= calculated_relative <= 1.0:
                            point._calculated_relative_pos = calculated_relative
                        else:
                            point._calculated_relative_pos = point.value
                else:
                    # position座標がない場合はvalueを使用
                    point._calculated_relative_pos = point.value
    
    def set_selected(self, selected: bool):
        """選択状態を設定"""
        self.is_selected = selected
        if not self.circumference_dragging:
            self.update_display()
    
    def update_display(self):
        """circumferenceポイントの表示を更新"""
        if self.circumference_dragging:
            return
            
        # 既存の表示を削除
        for item in self.circumference_items:
            if item.scene():
                item.scene().removeItem(item)
        self.circumference_items.clear()
        
        if not self.is_selected or not self.bar_item.scene():
            return
            
        # 現在のバー情報を取得
        rect = self.bar_item.boundingRect()
        pos = self.bar_item.pos()
        
        # ポイントをvalue順にソート
        sorted_points = sorted(self.circumference_points, key=lambda p: p.value)
        
        for i, point in enumerate(sorted_points):
            # 分割線上の位置を計算
            display_x, display_y = self._calculate_display_position(point, rect, pos)
            
            # 制御点を作成
            self._create_point_marker(point, i, display_x, display_y)
            
            # テキストを作成
            self._create_value_text(point, display_x, display_y)
    
    def _calculate_display_position(self, point, rect, pos):
        """分割線上の表示位置を計算"""
        current_center_x = pos.x() + rect.width() / 2
        current_center_y = pos.y() + rect.height() / 2
        
        if self.orientation == "horizontal":
            # 横長：分割線は水平
            display_x = pos.x() + point._calculated_relative_pos * rect.width()
            display_y = current_center_y
        else:
            # 縦長：分割線は垂直
            display_x = current_center_x
            display_y = pos.y() + point._calculated_relative_pos * rect.height()
            
        return display_x, display_y
    
    def _create_point_marker(self, point, index, display_x, display_y):
        """制御点マーカーを作成"""
        marker_size = 32
        point_marker = CircumferencePointItem(
            0, 0, marker_size, marker_size,
            self, point, index
        )
        point_marker.setPos(display_x - marker_size/2, display_y - marker_size/2)
        point_marker.setBrush(QBrush(QColor(255, 128, 0)))
        point_marker.setPen(QPen(QColor(0, 0, 0), 2))
        point_marker.setZValue(1500)
        point_marker.setFlag(QGraphicsItem.ItemIsMovable, True)
        point_marker.setAcceptHoverEvents(True)
        
        self.bar_item.scene().addItem(point_marker)
        self.circumference_items.append(point_marker)
        
    def _create_value_text(self, point, display_x, display_y):
        """値表示テキストを作成"""
        value_text = QGraphicsTextItem(f"{point.value:.2f}")
        value_text.setPos(display_x, display_y)
        
        font = QFont("Arial", 16, QFont.Bold)
        value_text.setFont(font)
        value_text.setDefaultTextColor(QColor(255, 128, 0))
        value_text.setZValue(1501)
        
        self.bar_item.scene().addItem(value_text)
        self.circumference_items.append(value_text)
    
    def handle_point_drag(self, point_item, event):
        """ポイントのドラッグ処理"""
        rect = self.bar_item.boundingRect()
        pos = self.bar_item.pos()
        mouse_pos = event.scenePos()
        
        # 分割線上に制約
        if self.orientation == "horizontal":
            display_y = pos.y() + rect.height() / 2
            relative_x = max(0, min(1, (mouse_pos.x() - pos.x()) / rect.width()))
            display_x = pos.x() + rect.width() * relative_x
        else:
            display_x = pos.x() + rect.width() / 2
            relative_y = max(0, min(1, (mouse_pos.y() - pos.y()) / rect.height()))
            display_y = pos.y() + rect.height() * relative_y
        
        # 順序制約を適用
        display_x, display_y = self._apply_order_constraints(
            point_item, display_x, display_y, rect, pos
        )
        
        # マーカー位置を更新
        marker_size = 32
        point_item.setPos(display_x - marker_size/2, display_y - marker_size/2)
        
        # テキスト位置も更新
        self._update_corresponding_text(point_item, display_x, display_y)
        
        # 座標データを更新
        point_item.point_data.position.x = display_x / self.scene_scale
        point_item.point_data.position.y = display_y / self.scene_scale
        
        event.accept()
        
    def _apply_order_constraints(self, point_item, display_x, display_y, rect, pos):
        """順序制約を適用"""
        sorted_points = sorted(self.circumference_points, key=lambda p: p.value)
        current_index = next((i for i, p in enumerate(sorted_points) if p == point_item.point_data), -1)
        
        if current_index >= 0:
            if self.orientation == "horizontal":
                # x座標制約
                min_x = pos.x()
                max_x = pos.x() + rect.width()
                
                if current_index > 0:
                    prev_point = sorted_points[current_index - 1]
                    if hasattr(prev_point, 'position') and prev_point.position:
                        min_x = prev_point.position.x * self.scene_scale + 5
                
                if current_index < len(sorted_points) - 1:
                    next_point = sorted_points[current_index + 1]
                    if hasattr(next_point, 'position') and next_point.position:
                        max_x = next_point.position.x * self.scene_scale - 5
                
                display_x = max(min_x, min(max_x, display_x))
            else:
                # y座標制約
                min_y = pos.y()
                max_y = pos.y() + rect.height()
                
                if current_index > 0:
                    prev_point = sorted_points[current_index - 1]
                    if hasattr(prev_point, 'position') and prev_point.position:
                        max_y = prev_point.position.y * self.scene_scale - 5
                
                if current_index < len(sorted_points) - 1:
                    next_point = sorted_points[current_index + 1]
                    if hasattr(next_point, 'position') and next_point.position:
                        min_y = next_point.position.y * self.scene_scale + 5
                
                display_y = max(min_y, min(max_y, display_y))
        
        return display_x, display_y
    
    def _update_corresponding_text(self, point_item, display_x, display_y):
        """対応するテキストの位置を更新"""
        try:
            text_index = self.circumference_items.index(point_item) + 1
            if text_index < len(self.circumference_items):
                text_item = self.circumference_items[text_index]
                text_item.setPos(display_x, display_y)
        except (ValueError, IndexError):
            pass
    
    def handle_point_release(self, point_item):
        """ポイントリリース処理"""
        # 相対位置を再計算
        rect = self.bar_item.boundingRect()
        pos = self.bar_item.pos()
        
        marker_pos = point_item.pos()
        marker_center_x = marker_pos.x() + 16  # marker_size/2
        marker_center_y = marker_pos.y() + 16
        
        if self.orientation == "horizontal":
            point_item.point_data._calculated_relative_pos = (marker_center_x - pos.x()) / rect.width()
        else:
            point_item.point_data._calculated_relative_pos = (marker_center_y - pos.y()) / rect.height()
    
    def update_for_bar_changes(self):
        """バー形状変更時の更新"""
        if not self.circumference_dragging:
            self.update_display()


# 使用例とヘルパー関数
def create_bar_circumference_from_json(bar_item, vehicle_data: dict, scene_scale: float = 1.0) -> BarCircumferenceManager:
    """vehicle.jsonからBar circumference機能を作成"""
    manager = BarCircumferenceManager(bar_item, scene_scale)
    
    # vehicle.jsonからcircumferenceデータを抽出
    circumference_data = vehicle_data.get('circumference', [])
    points = []
    
    for point_data in circumference_data:
        position = Position(
            x=point_data['position']['x'],
            y=point_data['position']['y']
        )
        point = CircumferencePoint(
            position=position,
            value=point_data['value']
        )
        points.append(point)
    
    manager.set_circumference_points(points)
    return manager