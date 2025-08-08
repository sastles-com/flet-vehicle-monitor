import sys
import json
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from io import BytesIO
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, 
                               QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
                               QGraphicsEllipseItem, QVBoxLayout, QHBoxLayout,
                               QWidget, QPushButton, QFileDialog, QToolBar,
                               QLabel, QComboBox, QSpinBox, QDockWidget,
                               QTreeWidget, QTreeWidgetItem, QCheckBox,
                               QGroupBox, QScrollArea, QGraphicsLineItem,
                               QGraphicsPathItem)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QSizeF
from PySide6.QtGui import QPixmap, QPen, QBrush, QColor, QWheelEvent, QPainter, QPainterPath


class ShapeType(Enum):
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    BOX = "box"         # vehicle.json用
    BAR = "bar"         # バーグラフ用


class ShapeCategory(Enum):
    ICON = "icon"
    METER = "meter"
    OCR = "ocr"
    CUSTOM = "custom"


@dataclass
class Position:
    """座標データ"""
    x: float
    y: float


@dataclass  
class ConfigData:
    """config.json用データクラス"""
    mqtt_host: str
    mqtt_port: str
    mqtt_ws_port: str
    rest_api_host: str
    rest_api_port: str
    camera_width: int
    camera_height: int
    camera_scale: float
    frame: int
    bench: str
    path: str


@dataclass
class IconData:
    """アイコン（矩形）データクラス"""
    name: str
    path: str
    type: str
    shape: str
    top_left: Position
    bottom_right: Position


@dataclass 
class CircumferencePoint:
    """円周上の点データクラス"""
    position: Position
    value: float


@dataclass
class MeterData:
    """メーター（円形）データクラス"""
    name: str
    path: str
    type: str
    shape: str
    center: Position
    radius: float
    ratio: float
    circumference: List[CircumferencePoint]


@dataclass
class OCRData:
    """OCR（矩形）データクラス"""
    name: str
    type: str
    shape: str
    top_left: Position
    bottom_right: Position


@dataclass
class VehicleData:
    """vehicle.json用データクラス"""
    name: str
    path: str
    threshold: float
    gray: bool
    offset: int
    icon: List[IconData]
    meter: List[MeterData]
    ocr: List[OCRData]


@dataclass
class ShapeData:
    """図形データを保持するクラス"""
    name: str
    shape_type: ShapeType
    x: float
    y: float
    width: float
    height: float
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.shape_type.value,
            "x": round(self.x),
            "y": round(self.y),
            "width": round(self.width),
            "height": round(self.height)
        }


class ResizableGraphicsItem:
    """リサイズ可能な図形の基底クラス"""
    
    def __init__(self, x: float, y: float, width: float, height: float, 
                 scene_scale: float = 1.0, category: ShapeCategory = ShapeCategory.CUSTOM):
        self.handles: List[QGraphicsRectItem] = []
        self.handle_size = 16
        self.scene_scale = scene_scale
        self.is_selected = False
        self.name = f"Shape_{id(self)}"
        self.category = category
        self.visible = True
        # フルサイズ画像座標での元の位置を保存
        self.original_x = x
        self.original_y = y
        self.original_width = width
        self.original_height = height
        
        # パーツ名表示用テキストアイテム
        self.name_text_item = None
        # 重心制御点
        self.center_control_point = None
        
    def create_handles(self):
        """リサイズハンドルを作成（選択時のみ表示）"""
        # 既存のハンドルを削除
        for handle in self.handles:
            if handle.scene():
                handle.scene().removeItem(handle)
        self.handles.clear()
        
        # 未選択時は変形ハンドルを表示しない
        if not self.is_selected:
            return
            
        # 8つのハンドル位置を計算（アイテムの位置を考慮）
        item = self.get_item()
        rect = item.boundingRect()
        pos = item.pos()
        
        positions = [
            (pos.x() + rect.left(), pos.y() + rect.top()),      # 左上
            (pos.x() + rect.center().x(), pos.y() + rect.top()),  # 上中央
            (pos.x() + rect.right(), pos.y() + rect.top()),     # 右上
            (pos.x() + rect.right(), pos.y() + rect.center().y()),  # 右中央
            (pos.x() + rect.right(), pos.y() + rect.bottom()),  # 右下
            (pos.x() + rect.center().x(), pos.y() + rect.bottom()),  # 下中央
            (pos.x() + rect.left(), pos.y() + rect.bottom()),   # 左下
            (pos.x() + rect.left(), pos.y() + rect.center().y()),  # 左中央
        ]
        
        for x, y in positions:
            handle = QGraphicsRectItem(
                x - self.handle_size/2,
                y - self.handle_size/2,
                self.handle_size,
                self.handle_size
            )
            handle.setBrush(QBrush(QColor(255, 255, 255)))
            handle.setPen(QPen(QColor(0, 0, 0), 1))
            # ハンドルを最前面に設定
            handle.setZValue(1000)
            handle.setFlag(QGraphicsItem.ItemIsMovable, True)
            
            if self.get_item().scene():
                self.get_item().scene().addItem(handle)
            self.handles.append(handle)
    
    def update_name_display(self):
        """パーツ名を表示更新"""
        if not self.get_item().scene():
            return
            
        # 既存のテキストアイテムを削除
        if self.name_text_item:
            self.get_item().scene().removeItem(self.name_text_item)
            self.name_text_item = None
        
        # パーツ名を表示（常に表示）
        item = self.get_item()
        rect = item.boundingRect()
        pos = item.pos()
        
        # パーツ名を左上に表示
        from PySide6.QtWidgets import QGraphicsTextItem
        self.name_text_item = QGraphicsTextItem(self.name)
        self.name_text_item.setPos(pos.x() + rect.left() - 5, pos.y() + rect.top() - 25)
        
        # テキストスタイル設定（大きく、読みやすく）
        from PySide6.QtGui import QFont
        font = QFont("Arial", 18, QFont.Bold)  # サイズを14から18に変更
        self.name_text_item.setFont(font)
        self.name_text_item.setDefaultTextColor(QColor(255, 0, 0))  # 赤文字
        
        # テキストを最前面に設定（背景より前に）
        self.name_text_item.setZValue(1100)
        
        # 文字の背景を白枠付きにして読みやすく
        from PySide6.QtWidgets import QGraphicsRectItem
        text_rect = self.name_text_item.boundingRect()
        # 少し余白を追加
        bg_rect = QGraphicsRectItem(text_rect.adjusted(-3, -2, 3, 2))
        bg_rect.setBrush(QBrush(QColor(255, 255, 255, 180)))  # 半透明白背景
        bg_rect.setPen(QPen(QColor(0, 0, 0), 1))  # 黒い枠線を追加
        bg_rect.setParentItem(self.name_text_item)
        bg_rect.setZValue(-1)  # テキストアイテムの子として、テキストより後ろに
        
        self.get_item().scene().addItem(self.name_text_item)
    
    def update_center_control_point(self):
        """重心位置制御点を更新"""
        if not self.get_item().scene():
            return
            
        # 既存の制御点を削除
        if self.center_control_point:
            self.get_item().scene().removeItem(self.center_control_point)
            self.center_control_point = None
        
        # 常に重心位置に制御点を表示
        item = self.get_item()
        rect = item.boundingRect()
        pos = item.pos()
        
        # 重心位置を計算
        center_x = pos.x() + rect.center().x()
        center_y = pos.y() + rect.center().y()
        
        # 制御点（選択状態に応じてサイズと色を変更）を作成
        if self.is_selected:
            # 選択時: より大きく、カテゴリ色で表示
            control_point_size = 28
            control_color = self.get_category_color()
        else:
            # 未選択時: 通常サイズ、白色で表示
            control_point_size = 24
            control_color = QColor(255, 255, 255)
            
        self.center_control_point = QGraphicsEllipseItem(
            center_x - control_point_size/2,
            center_y - control_point_size/2,
            control_point_size,
            control_point_size
        )
        
        # 制御点のスタイル設定
        self.center_control_point.setBrush(QBrush(control_color))
        self.center_control_point.setPen(QPen(QColor(0, 0, 0), 3))
        
        # ホバー時のスタイル変更用のフラグ設定
        self.center_control_point.setAcceptHoverEvents(True)
        
        # ホバーイベントハンドラを設定
        hover_handler = CenterControlPointHover(self.center_control_point, self)
        self.center_control_point.hoverEnterEvent = hover_handler.hoverEnterEvent
        self.center_control_point.hoverLeaveEvent = hover_handler.hoverLeaveEvent
        
        # 制御点を確実に最前面に設定
        self.center_control_point.setZValue(2000)
        
        # ドラッグ可能に設定（選択は無効化：Canvas側で処理）
        self.center_control_point.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.center_control_point.setFlag(QGraphicsItem.ItemIsSelectable, False)
        
        self.get_item().scene().addItem(self.center_control_point)
        
        # 制御点のドラッグイベントをカスタムクラスで置き換え（選択処理はCanvasで処理）
        control_point_handler = CenterControlPoint(self.center_control_point, self)
        # ドラッグ処理を有効化（選択は既にCanvas側で処理済み）
        self.center_control_point.mousePressEvent = control_point_handler.mousePressEvent
        self.center_control_point.mouseMoveEvent = control_point_handler.mouseMoveEvent
        self.center_control_point.mouseReleaseEvent = control_point_handler.mouseReleaseEvent
    
    def get_category_color(self) -> QColor:
        """カテゴリの色を取得"""
        colors = {
            ShapeCategory.ICON: QColor(255, 50, 50),
            ShapeCategory.METER: QColor(50, 50, 255),
            ShapeCategory.OCR: QColor(50, 200, 50),
            ShapeCategory.CUSTOM: QColor(128, 128, 128)
        }
        return colors.get(self.category, QColor(128, 128, 128))
    
    def update_color(self):
        """カテゴリに応じて色を更新（統一方針：塗りなし、太線）"""
        pen_color = self.get_category_color()
        
        # 統一方針：塗りなし、太線（線幅3px）
        self.get_item().setBrush(QBrush(Qt.NoBrush))
        self.get_item().setPen(QPen(pen_color, 3))
    
    def set_selected(self, selected: bool):
        """選択状態を設定し、表示を更新"""
        self.is_selected = selected
        
        # 選択状態に応じて表示を更新
        self.update_selection_appearance()
        
        # 選択時のみ変形ハンドルを表示
        self.create_handles()
        
        # 制御点とパーツ名を更新
        self.update_center_control_point()
        self.update_name_display()
    
    def update_selection_appearance(self):
        """選択状態に応じて外観を更新"""
        pen_color = self.get_category_color()
        
        if self.is_selected:
            # 選択時: 太線（3px）
            line_width = 3
        else:
            # 未選択時: 細線（1px）
            line_width = 1
        
        # 図形の線の太さを更新
        self.get_item().setBrush(QBrush(Qt.NoBrush))
        self.get_item().setPen(QPen(pen_color, line_width))
    
    def create_center_control_point(self):
        """重心位置に制御点を作成"""
        self.update_center_control_point()
    
    def create_name_text(self):
        """パーツ名テキストを作成"""
        self.update_name_display()
    
    def get_original_coords(self, scale: float = None) -> Tuple[float, float, float, float]:
        """元画像の座標系での位置を返す"""
        return (self.original_x, self.original_y, self.original_width, self.original_height)
    
    def update_position_for_scale(self, scale: float):
        """スケール変更時の位置更新"""
        self.scene_scale = scale
        # 表示位置を実座標からスケールされた位置に更新
        display_x = self.original_x * scale
        display_y = self.original_y * scale
        self.get_item().setPos(display_x, display_y)
        
        # パーツ名と制御点も更新
        self.update_center_control_point()
        self.update_name_display()
    
    def set_visible(self, visible: bool):
        """図形の表示/非表示を切り替え"""
        self.visible = visible
        self.get_item().setVisible(visible)
        if self.name_text_item:
            self.name_text_item.setVisible(visible)
        if self.center_control_point:
            self.center_control_point.setVisible(visible)
        for handle in self.handles:
            handle.setVisible(visible)
    
    def get_item(self) -> QGraphicsItem:
        """実際のグラフィックアイテムを返す（サブクラスで実装）"""
        raise NotImplementedError("Subclass must implement get_item method")


class CenterControlPoint:
    """重心制御点のドラッグハンドラ（文字や図形の追従処理）"""
    
    def __init__(self, control_point_item, parent_shape):
        self.control_point_item = control_point_item
        self.parent_shape = parent_shape
        self.is_dragging = False
        self.last_pos = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # ドラッグ開始（選択処理はCanvas側で処理済み）
            self.is_dragging = True
            self.last_pos = event.scenePos()
            # デフォルトの処理も実行
            QGraphicsEllipseItem.mousePressEvent(self.control_point_item, event)
    
    def mouseMoveEvent(self, event):
        if self.is_dragging and self.last_pos:
            # 移動量を計算
            current_pos = event.scenePos()
            delta_x = current_pos.x() - self.last_pos.x()
            delta_y = current_pos.y() - self.last_pos.y()
            
            # 制御点の移動
            QGraphicsEllipseItem.mouseMoveEvent(self.control_point_item, event)
            
            # 文字と図形を同期して移動
            self.move_associated_items(delta_x, delta_y)
            
            self.last_pos = current_pos
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.last_pos = None
            
            # 移動後の位置を元座標に反映
            self.update_original_coordinates()
            
            # デフォルトの処理も実行
            QGraphicsEllipseItem.mouseReleaseEvent(self.control_point_item, event)
    
    def move_associated_items(self, delta_x: float, delta_y: float):
        """関連するアイテム（文字、図形）を移動"""
        # 図形の移動
        shape_item = self.parent_shape.get_item()
        current_pos = shape_item.pos()
        shape_item.setPos(current_pos.x() + delta_x, current_pos.y() + delta_y)
        
        # パーツ名テキストの移動
        if self.parent_shape.name_text_item:
            text_pos = self.parent_shape.name_text_item.pos()
            self.parent_shape.name_text_item.setPos(text_pos.x() + delta_x, text_pos.y() + delta_y)
    
    def update_original_coordinates(self):
        """移動後の位置を元座標に反映"""
        shape_item = self.parent_shape.get_item()
        current_pos = shape_item.pos()
        
        # 現在のスケールで割って元座標を更新
        scale = self.parent_shape.scene_scale
        self.parent_shape.original_x = current_pos.x() / scale
        self.parent_shape.original_y = current_pos.y() / scale


class CenterControlPointHover:
    """重心制御点のホバー効果ハンドラ"""
    
    def __init__(self, control_point_item, parent_shape):
        self.control_point_item = control_point_item
        self.parent_shape = parent_shape
        # サイズは動的に計算（移動時に追従するため）
    
    def get_current_sizes(self):
        """現在の選択状態に応じたサイズを取得"""
        original_size = 28 if self.parent_shape.is_selected else 24
        hover_size = original_size + 6
        return original_size, hover_size
    
    def hoverEnterEvent(self, event):
        """ホバー開始時の処理（制御点を大きく、色変更）"""
        # 動的サイズ取得
        original_size, hover_size = self.get_current_sizes()
        
        # 現在の中心位置を保持してサイズのみ変更
        current_rect = self.control_point_item.rect()
        current_pos = self.control_point_item.pos()
        
        # 現在の中心位置を計算（絶対座標）
        center_x = current_pos.x() + current_rect.center().x()
        center_y = current_pos.y() + current_rect.center().y()
        
        # 新しい位置を計算（中心を保持）
        new_pos_x = center_x - hover_size / 2
        new_pos_y = center_y - hover_size / 2
        
        # 位置とサイズを更新
        self.control_point_item.setPos(new_pos_x, new_pos_y)
        self.control_point_item.setRect(0, 0, hover_size, hover_size)
        
        # 色を明るく（選択可能を示す）
        if self.parent_shape.is_selected:
            # 選択時: カテゴリ色をより明るく
            hover_color = self.parent_shape.get_category_color().lighter(150)
        else:
            # 未選択時: カテゴリ色で表示
            hover_color = self.parent_shape.get_category_color().lighter(120)
        self.control_point_item.setBrush(QBrush(hover_color))
        self.control_point_item.setPen(QPen(QColor(0, 0, 0), 3))
        
        # デフォルトのホバー処理
        QGraphicsEllipseItem.hoverEnterEvent(self.control_point_item, event)
    
    def hoverLeaveEvent(self, event):
        """ホバー終了時の処理（元のサイズ、色に戻す）"""
        # 動的サイズ取得
        original_size, hover_size = self.get_current_sizes()
        
        # 現在の中心位置を保持して元のサイズに戻す
        current_rect = self.control_point_item.rect()
        current_pos = self.control_point_item.pos()
        
        # 現在の中心位置を計算（絶対座標）
        center_x = current_pos.x() + current_rect.center().x()
        center_y = current_pos.y() + current_rect.center().y()
        
        # 元のサイズでの新しい位置を計算（中心を保持）
        new_pos_x = center_x - original_size / 2
        new_pos_y = center_y - original_size / 2
        
        # 位置とサイズを更新
        self.control_point_item.setPos(new_pos_x, new_pos_y)
        self.control_point_item.setRect(0, 0, original_size, original_size)
        
        # 色を元に戻す（選択状態に応じて）
        if self.parent_shape.is_selected:
            # 選択時: カテゴリ色
            original_color = self.parent_shape.get_category_color()
        else:
            # 未選択時: 白色
            original_color = QColor(255, 255, 255)
        self.control_point_item.setBrush(QBrush(original_color))
        self.control_point_item.setPen(QPen(QColor(0, 0, 0), 3))
        
        # デフォルトのホバー処理
        QGraphicsEllipseItem.hoverLeaveEvent(self.control_point_item, event)
    
    def update_color(self):
        """カテゴリに応じて色を更新（type別対応）"""
        pen_color = self.get_category_color()
        
        # 統一方針：塗りなし、太線（線幅3px）
        if hasattr(self, 'shape_type'):
            if self.shape_type == ShapeType.BOX:
                # BOX: 角丸矩形風の表示
                self.get_item().setBrush(QBrush(Qt.NoBrush))
                pen = QPen(pen_color, 3)
                pen.setJoinStyle(Qt.RoundJoin)
                self.get_item().setPen(pen)
            elif self.shape_type == ShapeType.BAR:
                # BAR: バーグラフ風の表示
                self.get_item().setBrush(QBrush(Qt.NoBrush))
                self.get_item().setPen(QPen(pen_color, 3))
            else:
                # デフォルト
                self.get_item().setBrush(QBrush(Qt.NoBrush))
                self.get_item().setPen(QPen(pen_color, 3))
        else:
            # 旧コード対応
            self.get_item().setBrush(QBrush(Qt.NoBrush))
            self.get_item().setPen(QPen(pen_color, 3))
    
    def set_selected(self, selected: bool):
        """選択状態を設定し、表示を更新"""
        self.is_selected = selected
        
        # 選択状態に応じて表示を更新
        self.update_selection_appearance()
        
        # 選択時のみ変形ハンドルを表示
        self.create_handles()
        
        # 制御点とパーツ名を更新
        self.update_center_control_point()
        self.update_name_display()
    
    def update_selection_appearance(self):
        """選択状態に応じて外観を更新"""
        pen_color = self.get_category_color()
        
        if self.is_selected:
            # 選択時: 太線（3px）
            line_width = 3
        else:
            # 未選択時: 細線（1px）
            line_width = 1
        
        # 図形の線の太さを更新
        self.get_item().setBrush(QBrush(Qt.NoBrush))
        self.get_item().setPen(QPen(pen_color, line_width))
        
    def get_item(self) -> QGraphicsItem:
        """実際のグラフィックアイテムを返す（サブクラスで実装）"""
        raise NotImplementedError
        
    def get_original_coords(self, scale: float = None) -> Tuple[float, float, float, float]:
        """元画像の座標系での位置を返す"""
        return (self.original_x, self.original_y, self.original_width, self.original_height)
    
    def update_position_for_scale(self, new_scale: float):
        """フルサイズ表示（スケール1.0）では位置更新は実際には不要"""
        # フルサイズ表示では座標変換が不要（実寸表示）
        display_x = self.original_x
        display_y = self.original_y
        display_width = self.original_width
        display_height = self.original_height
        
        # 図形の位置とサイズを設定（実寸）
        item = self.get_item()
        item.setPos(display_x, display_y)
        if hasattr(item, 'setRect'):
            item.setRect(0, 0, display_width, display_height)
        
        self.scene_scale = new_scale
        
        # ハンドルサイズは固定（フルサイズ表示ではスケール無関係）
        self.handle_size = 16
        
        # ハンドルを再作成
        if self.is_selected:
            self.create_handles()
    
    def set_visible(self, visible: bool):
        """表示/非表示を設定"""
        self.visible = visible
        self.get_item().setVisible(visible)
        
        # パーツ名と制御点も同期して表示/非表示
        if self.name_text_item:
            self.name_text_item.setVisible(visible)
        if self.center_control_point:
            self.center_control_point.setVisible(visible)
            
        if not visible and self.is_selected:
            self.set_selected(False)
    
    def update_color(self):
        """カテゴリに応じて色を更新（統一方針：塗りなし、太線）"""
        pen_colors = {
            ShapeCategory.ICON: QColor(255, 50, 50),    # 赤系
            ShapeCategory.METER: QColor(50, 50, 255),   # 青系
            ShapeCategory.OCR: QColor(50, 200, 50),     # 緑系
            ShapeCategory.CUSTOM: QColor(128, 128, 128) # グレー系
        }
        
        pen_color = pen_colors.get(self.category, QColor(128, 128, 128))
        
        # 統一方針：塗りなし、太線（線幅3px）
        self.get_item().setBrush(QBrush(Qt.NoBrush))  # 塗りなし
        self.get_item().setPen(QPen(pen_color, 3))     # 太線


class ResizableRectItem(ResizableGraphicsItem):
    """リサイズ可能な矩形"""
    
    def __init__(self, x: float, y: float, width: float, height: float,
                 scene_scale: float = 1.0, category: ShapeCategory = ShapeCategory.CUSTOM,
                 is_original_coords: bool = False):
        # 実寸ベース + ウィンドウフィットシステム
        if is_original_coords:
            # フルサイズ座標からウィンドウフィット表示座標へ変換
            display_x = x * scene_scale
            display_y = y * scene_scale
            display_width = width * scene_scale
            display_height = height * scene_scale
            super().__init__(x, y, width, height, scene_scale, category)
        else:
            # 表示座標から実寸座標へ変換してからスケーリング
            display_x = x
            display_y = y
            display_width = width
            display_height = height
            super().__init__(x / scene_scale, y / scene_scale, width / scene_scale, height / scene_scale, scene_scale, category)
        
        self.rect_item = QGraphicsRectItem(0, 0, display_width, display_height)
        self.rect_item.setPos(display_x, display_y)
        # 図形自体は選択・移動禁止（制御点のみ有効）
        self.rect_item.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.rect_item.setFlag(QGraphicsItem.ItemIsSelectable, False)
        # マウスイベントを受け取らない（透過）
        self.rect_item.setAcceptedMouseButtons(Qt.NoButton)
        # 図形を手前レイヤーに設定
        self.rect_item.setZValue(100)
        self.shape_type = ShapeType.RECTANGLE
        self.update_color()
        
        # 重心制御点とパーツ名を作成
        self.create_center_control_point()
        self.create_name_text()
        
    def get_item(self) -> QGraphicsRectItem:
        return self.rect_item


class ResizableEllipseItem(ResizableGraphicsItem):
    """リサイズ可能な円"""
    
    def __init__(self, x: float, y: float, width: float, height: float,
                 scene_scale: float = 1.0, category: ShapeCategory = ShapeCategory.CUSTOM,
                 is_original_coords: bool = False):
        # 実寸ベース + ウィンドウフィットシステム
        if is_original_coords:
            # フルサイズ座標からウィンドウフィット表示座標へ変換
            display_x = x * scene_scale
            display_y = y * scene_scale
            display_width = width * scene_scale
            display_height = height * scene_scale
            super().__init__(x, y, width, height, scene_scale, category)
        else:
            # 表示座標から実寸座標へ変換してからスケーリング
            display_x = x
            display_y = y
            display_width = width
            display_height = height
            super().__init__(x / scene_scale, y / scene_scale, width / scene_scale, height / scene_scale, scene_scale, category)
        
        self.ellipse_item = QGraphicsEllipseItem(0, 0, display_width, display_height)
        self.ellipse_item.setPos(display_x, display_y)
        # 図形自体は選択・移動禁止（制御点のみ有効）
        self.ellipse_item.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.ellipse_item.setFlag(QGraphicsItem.ItemIsSelectable, False)
        # 図形を手前レイヤーに設定
        self.ellipse_item.setZValue(100)
        self.shape_type = ShapeType.CIRCLE
        self.update_color()
        
        # 重心制御点とパーツ名を作成
        self.create_center_control_point()
        self.create_name_text()
        
    def get_item(self) -> QGraphicsEllipseItem:
        return self.ellipse_item


class BoxShapeItem(ResizableGraphicsItem):
    """ボックスタイプの図形（矩形ベース、特別な描画）"""
    
    def __init__(self, x: float, y: float, width: float, height: float,
                 scene_scale: float = 1.0, category: ShapeCategory = ShapeCategory.ICON,
                 is_original_coords: bool = False):
        # 実寸ベース + ウィンドウフィットシステム
        if is_original_coords:
            display_x = x * scene_scale
            display_y = y * scene_scale
            display_width = width * scene_scale
            display_height = height * scene_scale
            super().__init__(x, y, width, height, scene_scale, category)
        else:
            display_x = x
            display_y = y
            display_width = width
            display_height = height
            super().__init__(x / scene_scale, y / scene_scale, width / scene_scale, height / scene_scale, scene_scale, category)
        
        self.rect_item = QGraphicsRectItem(0, 0, display_width, display_height)
        self.rect_item.setPos(display_x, display_y)
        # 図形自体は選択・移動禁止（制御点のみ有効）
        self.rect_item.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.rect_item.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.rect_item.setZValue(100)
        self.shape_type = ShapeType.BOX
        self.update_color()
        
        # 重心制御点とパーツ名を作成
        self.create_center_control_point()
        self.create_name_text()
        
    def get_item(self) -> QGraphicsRectItem:
        return self.rect_item


class BarShapeItem(ResizableGraphicsItem):
    """バーグラフタイプの図形（水平または垂直バー）"""
    
    def __init__(self, x: float, y: float, width: float, height: float,
                 scene_scale: float = 1.0, category: ShapeCategory = ShapeCategory.METER,
                 is_original_coords: bool = False, orientation: str = "horizontal"):
        # 実寸ベース + ウィンドウフィットシステム
        if is_original_coords:
            display_x = x * scene_scale
            display_y = y * scene_scale
            display_width = width * scene_scale
            display_height = height * scene_scale
            super().__init__(x, y, width, height, scene_scale, category)
        else:
            display_x = x
            display_y = y
            display_width = width
            display_height = height
            super().__init__(x / scene_scale, y / scene_scale, width / scene_scale, height / scene_scale, scene_scale, category)
        
        self.orientation = orientation  # "horizontal" or "vertical"
        
        # パスでバーグラフを作成
        self.path_item = QGraphicsPathItem()
        self.path_item.setPos(display_x, display_y)
        # 図形自体は選択・移動禁止（制御点のみ有効）
        self.path_item.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.path_item.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.path_item.setZValue(100)
        self.shape_type = ShapeType.BAR
        
        # バーグラフのパスを作成
        self.create_bar_path(display_width, display_height)
        self.update_color()
        
        # 重心制御点とパーツ名を作成
        self.create_center_control_point()
        self.create_name_text()
        
    def create_bar_path(self, width: float, height: float):
        """バーグラフのパスを作成"""
        path = QPainterPath()
        
        if self.orientation == "horizontal":
            # 水平バー：外框 + 中央のバー
            path.addRect(0, 0, width, height)  # 外框
            bar_height = height * 0.3
            bar_y = (height - bar_height) / 2
            path.addRect(5, bar_y, width - 10, bar_height)  # 中央バー
        else:
            # 垂直バー：外框 + 中央のバー
            path.addRect(0, 0, width, height)  # 外框
            bar_width = width * 0.3
            bar_x = (width - bar_width) / 2
            path.addRect(bar_x, 5, bar_width, height - 10)  # 中央バー
        
        self.path_item.setPath(path)
        
    def get_item(self) -> QGraphicsPathItem:
        return self.path_item


class ImageCanvas(QGraphicsView):
    """画像表示とラバーバンド機能を持つキャンバス"""
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        self.image_item = None
        self.original_pixmap = None
        self.current_scale = 1.0  # フルサイズ表示では常に1.0
        self.shapes: List[ResizableGraphicsItem] = []
        self.drawing_mode = None
        self.start_pos = None
        self.temp_item = None
        self.selected_shape = None
        
        # フルサイズ画像サイズ（config.jsonから設定）
        self.full_image_width = 2304  # デフォルト値
        self.full_image_height = 1296  # デフォルト値
        
        # 原寸表示用ビュー設定
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        # スクロールバーを必要時表示（原寸表示のため）
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    
    def set_full_image_size(self, width: int, height: int):
        """フルサイズ画像サイズを設定"""
        self.full_image_width = width
        self.full_image_height = height
        
    def load_image(self, file_path: str):
        """画像を読み込んで原寸表示"""
        self.original_pixmap = QPixmap(file_path)
        if self.image_item:
            self.scene.removeItem(self.image_item)
            
        self.image_item = self.scene.addPixmap(self.original_pixmap)
        # 画像を最背景に設定
        self.image_item.setZValue(-1000)
        # 原寸表示（スケール1.0固定）
        self.display_at_original_size()
        
    def display_at_original_size(self):
        """画像を原寸（1:1）で表示"""
        if not self.original_pixmap:
            return
            
        # 原寸表示（スケール1.0固定）
        new_scale = 1.0
        
        # ビューのトランスフォームをリセットして1.0スケール適用
        self.resetTransform()
        self.scale(new_scale, new_scale)
        
        # すべての図形の位置を原寸スケールに更新
        self.update_shapes_for_scale(new_scale)
        self.current_scale = new_scale
    
    def calculate_optimal_scale(self) -> float:
        """ウィンドウサイズに合わせた最適スケールを計算"""
        view_rect = self.viewport().rect()
        # フルサイズ画像サイズを基準にスケール計算
        full_size_rect = QRectF(0, 0, self.full_image_width, self.full_image_height)
        
        # アスペクト比を保持してスケール計算
        x_ratio = view_rect.width() / full_size_rect.width()
        y_ratio = view_rect.height() / full_size_rect.height()
        return min(x_ratio, y_ratio) * 0.95
    
    def update_shapes_for_scale(self, new_scale: float):
        """スケール変更時にすべての図形の位置を更新"""
        for shape in self.shapes:
            shape.update_position_for_scale(new_scale)
        
    def resizeEvent(self, event):
        """ウィンドウリサイズ時の処理（原寸表示では何もしない）"""
        super().resizeEvent(event)
        # 原寸表示モードではリサイズ時の自動調整を行わない
        
    # マウスホイールズーム機能を削除
    # def wheelEvent(self, event: QWheelEvent):
    #     マウスホイールズームは不要のため削除
        
    def set_drawing_mode(self, mode: str):
        """描画モードを設定"""
        self.drawing_mode = mode
        if mode:
            self.setDragMode(QGraphicsView.NoDrag)
        else:
            self.setDragMode(QGraphicsView.RubberBandDrag)
            
    def mousePressEvent(self, event):
        """マウスプレスイベント"""
        if self.drawing_mode and event.button() == Qt.LeftButton:
            self.start_pos = self.mapToScene(event.pos())
            
            # 一時的な図形を作成
            if self.drawing_mode == "rectangle":
                self.temp_item = QGraphicsRectItem(self.start_pos.x(), 
                                                   self.start_pos.y(), 0, 0)
                self.temp_item.setPen(QPen(QColor(255, 0, 0), 2))
            elif self.drawing_mode == "circle":
                self.temp_item = QGraphicsEllipseItem(self.start_pos.x(),
                                                      self.start_pos.y(), 0, 0)
                self.temp_item.setPen(QPen(QColor(0, 0, 255), 2))
                
            if self.temp_item:
                self.scene.addItem(self.temp_item)
        elif event.button() == Qt.LeftButton:
            # 描画モードでない場合、最も近い制御点を探して選択
            click_pos = self.mapToScene(event.pos())
            # 制御点がクリックされなかった場合は全選択解除
            if not self.select_nearest_control_point(click_pos):
                # 全パーツの選択を解除
                for shape in self.shapes:
                    shape.set_selected(False)
                self.selected_shape = None
                    
        super().mousePressEvent(event)
    
    def select_nearest_control_point(self, click_pos):
        """クリック位置に最も近い制御点を選択"""
        import math
        
        min_distance = float('inf')
        nearest_shape = None
        
        for shape in self.shapes:
            if shape.center_control_point and shape.visible:
                # 制御点の中心位置を計算
                control_rect = shape.center_control_point.rect()
                control_pos = shape.center_control_point.pos()
                center_x = control_pos.x() + control_rect.width() / 2
                center_y = control_pos.y() + control_rect.height() / 2
                
                # クリック位置からの距離を計算
                distance = math.sqrt((click_pos.x() - center_x)**2 + (click_pos.y() - center_y)**2)
                
                # 制御点の半径内にある場合のみ対象とする（選択可能範囲）
                control_radius = max(control_rect.width(), control_rect.height()) / 2 + 10  # +10px余裕
                
                if distance <= control_radius and distance < min_distance:
                    min_distance = distance
                    nearest_shape = shape
        
        # 最も近いパーツがあれば選択
        if nearest_shape:
            # 既存の選択をクリア
            if self.selected_shape and self.selected_shape != nearest_shape:
                self.selected_shape.set_selected(False)
            
            # 他のパーツの選択を解除
            for shape in self.shapes:
                if shape != nearest_shape:
                    shape.set_selected(False)
            
            # 最も近いパーツを選択
            self.selected_shape = nearest_shape
            nearest_shape.set_selected(True)
            return True  # 選択成功
        
        return False  # 選択失敗
            
    def mouseMoveEvent(self, event):
        """マウス移動イベント（ラバーバンド）"""
        if self.drawing_mode and self.start_pos and self.temp_item:
            current_pos = self.mapToScene(event.pos())
            
            # 矩形のサイズを更新
            width = current_pos.x() - self.start_pos.x()
            height = current_pos.y() - self.start_pos.y()
            
            if width < 0:
                x = current_pos.x()
                width = abs(width)
            else:
                x = self.start_pos.x()
                
            if height < 0:
                y = current_pos.y()
                height = abs(height)
            else:
                y = self.start_pos.y()
                
            if isinstance(self.temp_item, QGraphicsRectItem):
                self.temp_item.setRect(x, y, width, height)
            elif isinstance(self.temp_item, QGraphicsEllipseItem):
                self.temp_item.setRect(x, y, width, height)
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """マウスリリースイベント"""
        if self.drawing_mode and self.temp_item:
            # 一時アイテムを実際の図形に変換
            rect = self.temp_item.boundingRect()
            
            if rect.width() > 5 and rect.height() > 5:  # 最小サイズチェック
                if self.drawing_mode == "rectangle":
                    shape = ResizableRectItem(rect.x(), rect.y(),
                                            rect.width(), rect.height(),
                                            1.0, ShapeCategory.CUSTOM, False)
                elif self.drawing_mode == "circle":
                    shape = ResizableEllipseItem(rect.x(), rect.y(),
                                                rect.width(), rect.height(),
                                                1.0, ShapeCategory.CUSTOM, False)
                else:
                    shape = None
                    
                if shape:
                    self.scene.addItem(shape.get_item())
                    self.shapes.append(shape)
                    # 原寸表示では追加の位置更新は不要
                    
            # 一時アイテムを削除
            self.scene.removeItem(self.temp_item)
            self.temp_item = None
            self.start_pos = None
            
        super().mouseReleaseEvent(event)
        
    def get_shapes_data(self) -> List[Dict]:
        """すべての図形データを取得"""
        shapes_data = []
        for shape in self.shapes:
            x, y, w, h = shape.get_original_coords()
            data = ShapeData(
                name=shape.name,
                shape_type=shape.shape_type,
                x=x, y=y, width=w, height=h
            )
            shapes_data.append(data.to_dict())
        return shapes_data
        
    def clear_shapes(self):
        """すべての図形をクリア"""
        for shape in self.shapes:
            self.scene.removeItem(shape.get_item())
            for handle in shape.handles:
                if handle.scene():
                    self.scene.removeItem(handle)
        self.shapes.clear()


class VehicleMonitorEditor(QMainWindow):
    """メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vehicle Monitor Editor - PyQt")
        # 初期サイズ設定（すぐに最大化するので仮の値）
        self.setGeometry(100, 100, 1200, 800)
        
        # 起動時にウィンドウを最大化
        self.showMaximized()
        
        # キャンバスを作成
        self.canvas = ImageCanvas()
        
        # 設定データ
        self.config_data: Optional[ConfigData] = None
        self.vehicle_data: Optional[VehicleData] = None
        
        # UIをセットアップ
        self.setup_ui()
        
        # サイドパネルをセットアップ
        self.setup_side_panel()
        
        # 起動時にデフォルトファイルを読み込み
        self.load_default_configs()
        
        # デフォルトで画像を読み込み（最大化後に実行）
        self.load_default_image()
        
    def setup_ui(self):
        """UIをセットアップ"""
        # ツールバー
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 画像読み込みボタン
        load_action = toolbar.addAction("画像を開く")
        load_action.triggered.connect(self.load_image)
        
        toolbar.addSeparator()
        
        # 描画モードボタン
        rect_action = toolbar.addAction("矩形を描画")
        rect_action.triggered.connect(lambda: self.canvas.set_drawing_mode("rectangle"))
        
        circle_action = toolbar.addAction("円を描画")
        circle_action.triggered.connect(lambda: self.canvas.set_drawing_mode("circle"))
        
        select_action = toolbar.addAction("選択モード")
        select_action.triggered.connect(lambda: self.canvas.set_drawing_mode(None))
        
        toolbar.addSeparator()
        
        # REST API画像取得ボタン
        rest_api_action = toolbar.addAction("REST API画像取得")
        rest_api_action.triggered.connect(self.fetch_rest_api_image)
        
        toolbar.addSeparator()
        
        # 設定読み込みボタン
        load_config_action = toolbar.addAction("Config読込")
        load_config_action.triggered.connect(self.load_config)
        
        load_vehicle_action = toolbar.addAction("Vehicle読込")
        load_vehicle_action.triggered.connect(self.load_vehicle)
        
        toolbar.addSeparator()
        
        # 保存・読み込みボタン
        save_json_action = toolbar.addAction("JSONを保存")
        save_json_action.triggered.connect(self.save_json)
        
        save_vehicle_action = toolbar.addAction("Vehicle保存")
        save_vehicle_action.triggered.connect(self.save_vehicle_json)
        
        load_json_action = toolbar.addAction("JSONを読込")
        load_json_action.triggered.connect(self.load_json)
        
        clear_action = toolbar.addAction("図形をクリア")
        clear_action.triggered.connect(self.canvas.clear_shapes)
        
        # ステータスバー
        self.statusBar().showMessage("画像を開いて編集を開始")
        
        # メインウィジェットとしてキャンバスを設定
        self.setCentralWidget(self.canvas)
        
    def load_image(self):
        """画像ファイルを読み込む"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "画像を開く", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            self.canvas.load_image(file_path)
            self.statusBar().showMessage(f"画像を読み込みました: {file_path}")
            
    def save_json(self):
        """図形データをJSONに保存"""
        if not self.canvas.shapes:
            self.statusBar().showMessage("保存する図形がありません")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "JSONを保存", "", "JSON Files (*.json)"
        )
        
        if file_path:
            data = {
                "image_width": self.canvas.full_image_width,
                "image_height": self.canvas.full_image_height,
                "shapes": self.canvas.get_shapes_data()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.statusBar().showMessage(f"JSONを保存しました: {file_path}")
            
    def load_json(self):
        """JSONから図形データを読み込む"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "JSONを開く", "", "JSON Files (*.json)"
        )
        
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.canvas.clear_shapes()
            
            for shape_data in data.get("shapes", []):
                x = shape_data["x"]
                y = shape_data["y"]
                w = shape_data["width"]
                h = shape_data["height"]
                
                if shape_data["type"] == "rectangle":
                    shape = ResizableRectItem(x, y, w, h, 1.0, ShapeCategory.CUSTOM, True)
                elif shape_data["type"] == "circle":
                    shape = ResizableEllipseItem(x, y, w, h, 1.0, ShapeCategory.CUSTOM, True)
                else:
                    continue
                    
                shape.name = shape_data.get("name", shape.name)
                self.canvas.scene.addItem(shape.get_item())
                self.canvas.shapes.append(shape)
                # 原寸表示では追加の位置更新は不要
                
            self.statusBar().showMessage(f"JSONを読み込みました: {file_path}")
    
    def load_default_configs(self):
        """起動時にデフォルト設定ファイルを読み込む"""
        config_path = "./data/config.json"
        vehicle_path = "./data/vehicle.json"
        
        if os.path.exists(config_path):
            self.load_config_file(config_path)
            # config.jsonからフルサイズ画像サイズを設定
            if self.config_data:
                self.canvas.set_full_image_size(
                    self.config_data.camera_width,
                    self.config_data.camera_height
                )
            
        if os.path.exists(vehicle_path):
            self.load_vehicle_file(vehicle_path)
    
    def load_default_image(self):
        """起動時にローカル画像ファイルを読み込み"""
        # 直接実行（タイマーによる遅延を削除）
        self.load_local_default_image()
    
    def load_config(self):
        """config.jsonファイルを読み込む"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Config JSONを開く", "./data/",
            "JSON Files (*.json)"
        )
        
        if file_path:
            self.load_config_file(file_path)
    
    def load_config_file(self, file_path: str):
        """config.jsonファイルを読み込む内部処理"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.config_data = ConfigData(
                mqtt_host=data["mqtt"]["host"],
                mqtt_port=data["mqtt"]["port"],
                mqtt_ws_port=data["mqtt"]["wsPort"],
                rest_api_host=data["RestAPI"]["host"],
                rest_api_port=data["RestAPI"]["port"],
                camera_width=data["camera"]["width"],
                camera_height=data["camera"]["height"],
                camera_scale=data["camera"]["scale"],
                frame=data["frame"],
                bench=data["bench"],
                path=data["path"]
            )
            
            # フルサイズ画像サイズを更新
            self.canvas.set_full_image_size(
                self.config_data.camera_width,
                self.config_data.camera_height
            )
            
            self.statusBar().showMessage(f"Config読み込み完了: {file_path}")
            
        except Exception as e:
            self.statusBar().showMessage(f"Config読み込みエラー: {str(e)}")
    
    def load_vehicle(self):
        """vehicle.jsonファイルを読み込む"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Vehicle JSONを開く", "./data/",
            "JSON Files (*.json)"
        )
        
        if file_path:
            self.load_vehicle_file(file_path)
    
    def load_vehicle_file(self, file_path: str):
        """vehicle.jsonファイルを読み込む内部処理"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # アイコンデータを変換
            icons = []
            for icon_data in data.get("icon", []):
                icon = IconData(
                    name=icon_data["name"],
                    path=icon_data["path"],
                    type=icon_data["type"],
                    shape=icon_data["shape"],
                    top_left=Position(icon_data["top_left"]["x"], icon_data["top_left"]["y"]),
                    bottom_right=Position(icon_data["bottom_right"]["x"], icon_data["bottom_right"]["y"])
                )
                icons.append(icon)
            
            # メーターデータを変換
            meters = []
            for meter_data in data.get("meter", []):
                circumference_points = []
                for point_data in meter_data.get("circumference", []):
                    point = CircumferencePoint(
                        position=Position(point_data["position"]["x"], point_data["position"]["y"]),
                        value=point_data["value"]
                    )
                    circumference_points.append(point)
                
                meter = MeterData(
                    name=meter_data["name"],
                    path=meter_data["path"],
                    type=meter_data["type"],
                    shape=meter_data["shape"],
                    center=Position(meter_data["center"]["x"], meter_data["center"]["y"]),
                    radius=meter_data["radius"],
                    ratio=meter_data.get("ratio", 1.0),
                    circumference=circumference_points
                )
                meters.append(meter)
            
            # OCRデータを変換
            ocrs = []
            for ocr_data in data.get("ocr", []):
                ocr = OCRData(
                    name=ocr_data["name"],
                    type=ocr_data["type"],
                    shape=ocr_data["shape"],
                    top_left=Position(ocr_data["top_left"]["x"], ocr_data["top_left"]["y"]),
                    bottom_right=Position(ocr_data["bottom_right"]["x"], ocr_data["bottom_right"]["y"])
                )
                ocrs.append(ocr)
            
            self.vehicle_data = VehicleData(
                name=data["name"],
                path=data["path"],
                threshold=data["threshold"],
                gray=data["gray"],
                offset=data["offset"],
                icon=icons,
                meter=meters,
                ocr=ocrs
            )
            
            # 図形を表示に反映（最大化ウィンドウサイズに合わせて）
            self.display_vehicle_shapes()
            
            self.statusBar().showMessage(f"Vehicle読み込み完了: {file_path}")
            
        except Exception as e:
            self.statusBar().showMessage(f"Vehicle読み込みエラー: {str(e)}")
    
    def display_vehicle_shapes(self):
        """vehicle.jsonの図形を画面に表示"""
        if not self.vehicle_data:
            return
            
        # 既存の図形をクリア
        self.canvas.clear_shapes()
        
        # 原寸表示（スケール1.0固定）
        current_scale = 1.0
        
        # アイコン（矩形）を追加
        for icon in self.vehicle_data.icon:
            x = icon.top_left.x
            y = icon.top_left.y
            w = icon.bottom_right.x - icon.top_left.x
            h = icon.bottom_right.y - icon.top_left.y
            
            # 計算したスケールで作成
            shape = ResizableRectItem(x, y, w, h, current_scale, ShapeCategory.ICON, True)
            shape.name = icon.name
            self.canvas.scene.addItem(shape.get_item())
            self.canvas.shapes.append(shape)
        
        # メーター（円形）を追加
        for meter in self.vehicle_data.meter:
            x = meter.center.x - meter.radius
            y = meter.center.y - meter.radius
            w = meter.radius * 2
            h = meter.radius * 2
            
            # 計算したスケールで作成
            shape = ResizableEllipseItem(x, y, w, h, current_scale, ShapeCategory.METER, True)
            shape.name = meter.name
            self.canvas.scene.addItem(shape.get_item())
            self.canvas.shapes.append(shape)
        
        # OCR（矩形）を追加
        for ocr in self.vehicle_data.ocr:
            x = ocr.top_left.x
            y = ocr.top_left.y
            w = ocr.bottom_right.x - ocr.top_left.x
            h = ocr.bottom_right.y - ocr.top_left.y
            
            # 計算したスケールで作成
            shape = ResizableRectItem(x, y, w, h, current_scale, ShapeCategory.OCR, True)
            shape.name = ocr.name
            self.canvas.scene.addItem(shape.get_item())
            self.canvas.shapes.append(shape)
        
        # 原寸表示（スケール調整なし）
        if self.canvas.original_pixmap:
            self.canvas.display_at_original_size()
        
        # パーツリストを更新
        self.update_parts_tree()
        
        # 表示を強制更新
        self.canvas.scene.update()
        QApplication.processEvents()
    
    def save_vehicle_json(self):
        """vehicle.json形式で保存"""
        if not self.canvas.shapes:
            self.statusBar().showMessage("保存する図形がありません")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Vehicle JSONを保存", "", "JSON Files (*.json)"
        )
        
        if file_path:
            # 現在の図形データをvehicle.json形式に変換
            icons = []
            meters = []
            ocrs = []
            
            for shape in self.canvas.shapes:
                x, y, w, h = shape.get_original_coords()
                
                if shape.shape_type == ShapeType.RECTANGLE:
                    # 矩形はアイコンまたはOCRとして扱う
                    icon_data = {
                        "name": shape.name,
                        "path": f"/templates/{shape.name}.png",
                        "type": "bool",
                        "shape": "box",
                        "top_left": {"x": round(x), "y": round(y)},
                        "bottom_right": {"x": round(x + w), "y": round(y + h)}
                    }
                    icons.append(icon_data)
                    
                elif shape.shape_type == ShapeType.CIRCLE:
                    # 円形はメーターとして扱う
                    center_x = x + w / 2
                    center_y = y + h / 2
                    radius = min(w, h) / 2
                    
                    meter_data = {
                        "name": shape.name,
                        "path": f"/templates/{shape.name}.png",
                        "type": "float",
                        "shape": "circle",
                        "center": {"x": round(center_x), "y": round(center_y)},
                        "radius": round(radius),
                        "ratio": 1.0,
                        "circumference": [
                            {"position": {"x": round(center_x - radius), "y": round(center_y)}, "value": 0},
                            {"position": {"x": round(center_x), "y": round(center_y + radius)}, "value": 0.5},
                            {"position": {"x": round(center_x + radius), "y": round(center_y)}, "value": 1}
                        ]
                    }
                    meters.append(meter_data)
            
            vehicle_json = {
                "name": self.vehicle_data.name if self.vehicle_data else "VEHICLE",
                "path": self.vehicle_data.path if self.vehicle_data else "/templates",
                "threshold": self.vehicle_data.threshold if self.vehicle_data else 0.8,
                "gray": self.vehicle_data.gray if self.vehicle_data else True,
                "offset": self.vehicle_data.offset if self.vehicle_data else 50,
                "icon": icons,
                "meter": meters,
                "ocr": ocrs
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(vehicle_json, f, indent=2, ensure_ascii=False)
                
            self.statusBar().showMessage(f"Vehicle JSONを保存しました: {file_path}")
    
    def setup_side_panel(self):
        """サイドパネルをセットアップ"""
        # サイドパネルウィジェット
        self.side_panel = QDockWidget("オブジェクト管理", self)
        self.side_panel.setFeatures(QDockWidget.NoDockWidgetFeatures)
        
        # メインウィジェット
        panel_widget = QWidget()
        panel_layout = QVBoxLayout(panel_widget)
        
        # カテゴリ別チェックボックス
        category_group = QGroupBox("カテゴリ表示")
        category_layout = QVBoxLayout()
        
        self.icon_checkbox = QCheckBox("Icon (矩形)")
        self.icon_checkbox.setChecked(True)
        self.icon_checkbox.stateChanged.connect(lambda: self.toggle_category_visibility(ShapeCategory.ICON))
        
        self.meter_checkbox = QCheckBox("Meter (円形)")
        self.meter_checkbox.setChecked(True)
        self.meter_checkbox.stateChanged.connect(lambda: self.toggle_category_visibility(ShapeCategory.METER))
        
        self.ocr_checkbox = QCheckBox("OCR (矩形)")
        self.ocr_checkbox.setChecked(True)
        self.ocr_checkbox.stateChanged.connect(lambda: self.toggle_category_visibility(ShapeCategory.OCR))
        
        self.custom_checkbox = QCheckBox("Custom")
        self.custom_checkbox.setChecked(True)
        self.custom_checkbox.stateChanged.connect(lambda: self.toggle_category_visibility(ShapeCategory.CUSTOM))
        
        category_layout.addWidget(self.icon_checkbox)
        category_layout.addWidget(self.meter_checkbox)
        category_layout.addWidget(self.ocr_checkbox)
        category_layout.addWidget(self.custom_checkbox)
        category_group.setLayout(category_layout)
        
        # パーツリストツリー
        self.parts_tree = QTreeWidget()
        self.parts_tree.setHeaderLabels(["名前", "カテゴリ", "タイプ"])
        self.parts_tree.itemClicked.connect(self.on_tree_item_clicked)
        
        # レイアウトに追加
        panel_layout.addWidget(category_group)
        panel_layout.addWidget(QLabel("パーツリスト:"))
        panel_layout.addWidget(self.parts_tree)
        panel_layout.addStretch()
        
        self.side_panel.setWidget(panel_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.side_panel)
        
        # 初期幅を設定
        self.side_panel.setFixedWidth(300)
    
    def toggle_category_visibility(self, category: ShapeCategory):
        """カテゴリの表示/非表示を切り替え"""
        checkbox_map = {
            ShapeCategory.ICON: self.icon_checkbox,
            ShapeCategory.METER: self.meter_checkbox,
            ShapeCategory.OCR: self.ocr_checkbox,
            ShapeCategory.CUSTOM: self.custom_checkbox
        }
        
        checkbox = checkbox_map.get(category)
        if checkbox:
            visible = checkbox.isChecked()
            for shape in self.canvas.shapes:
                if shape.category == category:
                    shape.set_visible(visible)
        
        self.update_parts_tree()
    
    def update_parts_tree(self):
        """パーツリストツリーを更新"""
        # parts_treeが存在しない場合はスキップ（初期化前）
        if not hasattr(self, 'parts_tree'):
            return
        
        self.parts_tree.clear()
        
        # カテゴリ別にグループ化
        categories = {
            ShapeCategory.ICON: QTreeWidgetItem(["Icon", "", ""]),
            ShapeCategory.METER: QTreeWidgetItem(["Meter", "", ""]),
            ShapeCategory.OCR: QTreeWidgetItem(["OCR", "", ""]),
            ShapeCategory.CUSTOM: QTreeWidgetItem(["Custom", "", ""])
        }
        
        # 各カテゴリにアイテムを追加
        for shape in self.canvas.shapes:
            parent = categories.get(shape.category)
            if parent:
                item = QTreeWidgetItem([
                    shape.name,
                    shape.category.value,
                    shape.shape_type.value
                ])
                item.setData(0, Qt.UserRole, shape)  # shapeオブジェクトを保存
                parent.addChild(item)
        
        # カテゴリをツリーに追加
        for category, parent in categories.items():
            if parent.childCount() > 0:
                self.parts_tree.addTopLevelItem(parent)
                parent.setExpanded(True)
    
    def on_tree_item_clicked(self, item, column):
        """ツリーアイテムがクリックされた時の処理"""
        shape = item.data(0, Qt.UserRole)
        if shape:
            # 既存の選択をクリア
            for s in self.canvas.shapes:
                s.set_selected(False)
            
            # クリックされた図形を選択
            shape.set_selected(True)
            
            # ビューを図形にフォーカス
            self.canvas.centerOn(shape.get_item())
    
    def fetch_rest_api_image(self):
        """REST APIからフルサイズ画像を取得"""
        try:
            # config.jsonからREST API情報を取得
            if self.config_data:
                url = f"http://{self.config_data.rest_api_host}:{self.config_data.rest_api_port}/full_image"
            else:
                # デフォルトURL
                url = "http://raspi-t40cd.local:8000/full_image"
            
            self.statusBar().showMessage(f"画像を取得中: {url}")
            
            # REST APIから画像を取得
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # JPEG画像をQPixmapに変換
            image_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            
            if pixmap.isNull():
                self.statusBar().showMessage("画像の読み込みに失敗しました")
                return
            
            # 画像を表示
            self.canvas.original_pixmap = pixmap
            if self.canvas.image_item:
                self.canvas.scene.removeItem(self.canvas.image_item)
            
            self.canvas.image_item = self.canvas.scene.addPixmap(pixmap)
            # 画像を最背景に設定
            self.canvas.image_item.setZValue(-1000)
            self.canvas.display_at_original_size()
            
            self.statusBar().showMessage(f"REST API画像を取得しました: {url}")
            
        except requests.exceptions.RequestException as e:
            self.statusBar().showMessage(f"REST API接続エラー: {str(e)}")
        except Exception as e:
            self.statusBar().showMessage(f"画像取得エラー: {str(e)}")
    
    def load_local_default_image(self):
        """ローカルのデフォルト画像ファイルを読み込み"""
        image_path = "./data/image.jpg"
        
        if not os.path.exists(image_path):
            self.statusBar().showMessage(f"デフォルト画像が見つかりません: {image_path}")
            return
        
        try:
            pixmap = QPixmap(image_path)
            
            if pixmap.isNull():
                self.statusBar().showMessage(f"画像の読み込みに失敗しました: {image_path}")
                return
            
            # 画像を表示
            self.canvas.original_pixmap = pixmap
            if self.canvas.image_item:
                self.canvas.scene.removeItem(self.canvas.image_item)
            
            self.canvas.image_item = self.canvas.scene.addPixmap(pixmap)
            # 画像を最背景に設定
            self.canvas.image_item.setZValue(-1000)
            self.canvas.display_at_original_size()
            
            self.statusBar().showMessage(f"デフォルト画像を読み込みました: {image_path}")
            
        except Exception as e:
            self.statusBar().showMessage(f"画像読み込みエラー: {str(e)}")


def main():
    app = QApplication(sys.argv)
    window = VehicleMonitorEditor()
    # ウィンドウは既に最大化されているのでshow()は不要
    # window.show()  # showMaximized()で置き換え
    sys.exit(app.exec())


if __name__ == "__main__":
    main()