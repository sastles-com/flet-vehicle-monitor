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
                               QGraphicsPathItem, QSizePolicy)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QSizeF, QTimer, QSize, Slot
from PySide6.QtGui import QPixmap, QPen, QBrush, QColor, QWheelEvent, QPainter, QPainterPath, QFont
import time
import base64
from io import BytesIO

# MQTTサービスをインポート
from services.mqtt_service import MQTTService

# デバッグフラグ
DEBUG_MODE = False


class AppMode(Enum):
    """アプリケーションモード"""
    CONFIG = "CONFIG"
    EDIT = "EDIT"
    MONITOR = "MONITOR"


class IDataLoader:
    """データ取得インターフェース（テスト/本格実装切り替え用）"""
    def load_config(self) -> dict:
        """config.json取得"""
        raise NotImplementedError
    
    def load_full_size_image(self) -> bytes:
        """フルサイズ画像取得"""
        raise NotImplementedError


class FileDataLoader(IDataLoader):
    """テスト用：ファイルからデータ読み込み"""
    
    def load_config(self) -> dict:
        """C:/Users/table0/Desktop/config/config-40.jsonから読み込み"""
        config_path = "C:/Users/table0/Desktop/config/config-40.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Config読み込みエラー: {e}")
            return {}
    
    def load_full_size_image(self) -> bytes:
        """提供された机の下画像から読み込み"""
        image_path = "./data/full_image.jpg"
        try:
            with open(image_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"フルサイズ画像読み込みエラー: {e}")
            # フォールバック: image.jpgを使用
            try:
                fallback_path = "./data/image.jpg"
                with open(fallback_path, 'rb') as f:
                    return f.read()
            except Exception as e2:
                print(f"フォールバック画像読み込みエラー: {e2}")
                return b''


class RestAPIDataLoader(IDataLoader):
    """本格実装用：RESTAPI経由でデータ取得"""
    
    def __init__(self, rest_api_host: str, rest_api_port: str):
        self.rest_api_host = rest_api_host
        self.rest_api_port = rest_api_port
    
    def load_config(self) -> dict:
        """RESTAPI経由でconfig.json取得"""
        # 将来実装
        return {}
    
    def load_full_size_image(self) -> bytes:
        """RESTAPI経由でフルサイズ画像取得"""
        # 将来実装
        return b''


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
        
        # 円形の場合は四隅のハンドルを除外
        is_circle = (self.shape_type == ShapeType.CIRCLE if hasattr(self, 'shape_type') else False)
        
        if is_circle:
            # 円形: 左右の2つのハンドルのみ（半径変更用）
            handle_types = [
                "middle_right",  # 右中央
                "middle_left",   # 左中央
            ]
            
            positions = [
                (pos.x() + rect.right(), pos.y() + rect.center().y()),  # 右中央
                (pos.x() + rect.left(), pos.y() + rect.center().y()),  # 左中央
            ]
        else:
            # 矩形: 8つのハンドル全て
            handle_types = [
                "top_left",      # 左上
                "top_center",    # 上中央
                "top_right",     # 右上
                "middle_right",  # 右中央
                "bottom_right",  # 右下
                "bottom_center", # 下中央
                "bottom_left",   # 左下
                "middle_left",   # 左中央
            ]
            
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
        
        for i, (x, y) in enumerate(positions):
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
            handle.setAcceptHoverEvents(True)
            
            # カスタムデータとしてハンドルタイプを設定
            handle.setData(0, handle_types[i])
            
            # ハンドルのドラッグイベントをカスタムハンドラで処理
            resize_handler = ResizeHandle(handle, self, handle_types[i])
            handle.mousePressEvent = resize_handler.mousePressEvent
            handle.mouseMoveEvent = resize_handler.mouseMoveEvent
            handle.mouseReleaseEvent = resize_handler.mouseReleaseEvent
            handle.hoverEnterEvent = resize_handler.hoverEnterEvent
            handle.hoverLeaveEvent = resize_handler.hoverLeaveEvent
            
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
        
        # 重心位置を計算（barのみ50ピクセル上に移動）
        center_x = pos.x() + rect.center().x()
        if hasattr(self, 'shape_type') and self.shape_type == ShapeType.BAR:
            center_y = pos.y() + rect.center().y() - 50  # barのみオフセット
        else:
            center_y = pos.y() + rect.center().y()  # 他のパーツは重心位置
        
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
            
            # ハンドルを再作成して正しい位置に配置
            self.parent_shape.create_handles()
            
            # 円形の場合はcircumferenceポイントは既に正しい位置にあるので再描画不要
            # 座標データは update_original_coordinates() で更新済み
            
            # デフォルトの処理も実行
            QGraphicsEllipseItem.mouseReleaseEvent(self.control_point_item, event)
    
    def move_associated_items(self, delta_x: float, delta_y: float):
        """関連するアイテム（文字、図形、ハンドル）を移動"""
        # 図形の移動
        shape_item = self.parent_shape.get_item()
        current_pos = shape_item.pos()
        shape_item.setPos(current_pos.x() + delta_x, current_pos.y() + delta_y)
        
        # パーツ名テキストの移動
        if self.parent_shape.name_text_item:
            text_pos = self.parent_shape.name_text_item.pos()
            self.parent_shape.name_text_item.setPos(text_pos.x() + delta_x, text_pos.y() + delta_y)
        
        # リサイズハンドルの移動
        for handle in self.parent_shape.handles:
            handle_pos = handle.pos()
            handle.setPos(handle_pos.x() + delta_x, handle_pos.y() + delta_y)
        
        # circumferenceポイントの移動（楕円の場合）
        if hasattr(self.parent_shape, 'circumference_items'):
            for item in self.parent_shape.circumference_items:
                item_pos = item.pos()
                item.setPos(item_pos.x() + delta_x, item_pos.y() + delta_y)
    
    def update_original_coordinates(self):
        """移動後の位置を元座標に反映"""
        shape_item = self.parent_shape.get_item()
        current_pos = shape_item.pos()
        
        # 現在のスケールで割って元座標を更新
        scale = self.parent_shape.scene_scale
        self.parent_shape.original_x = current_pos.x() / scale
        self.parent_shape.original_y = current_pos.y() / scale
        
        # 円形の場合は元の中心座標も更新
        if hasattr(self.parent_shape, 'original_center_x') and hasattr(self.parent_shape, 'original_center_y'):
            rect = shape_item.boundingRect()
            center_x = current_pos.x() + rect.width() / 2
            center_y = current_pos.y() + rect.height() / 2
            self.parent_shape.original_center_x = center_x
            self.parent_shape.original_center_y = center_y
        
        # circumferenceポイントの元座標も更新（楕円の場合）
        if hasattr(self.parent_shape, 'circumference_points') and hasattr(self.parent_shape, 'circumference_items'):
            for i, point_data in enumerate(self.parent_shape.circumference_points):
                # 対応するアイテムを見つける（マーカーは偶数インデックス）
                marker_index = i * 2
                if marker_index < len(self.parent_shape.circumference_items):
                    marker_item = self.parent_shape.circumference_items[marker_index]
                    marker_pos = marker_item.pos()
                    # マーカーの中心位置を計算（マーカーサイズの半分を加算）
                    marker_center_x = marker_pos.x() + 16  # marker_size/2 = 32/2 = 16
                    marker_center_y = marker_pos.y() + 16
                    # 元座標を更新
                    point_data.position.x = marker_center_x / scale
                    point_data.position.y = marker_center_y / scale


class ResizeHandle:
    """リサイズハンドルのドラッグハンドラ"""
    
    def __init__(self, handle_item, parent_shape, handle_type):
        self.handle_item = handle_item
        self.parent_shape = parent_shape
        self.handle_type = handle_type
        self.is_dragging = False
        self.start_pos = None
        self.start_rect = None
        self.start_item_pos = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.start_pos = event.scenePos()
            
            # 現在の図形の位置とサイズを記録
            item = self.parent_shape.get_item()
            self.start_rect = item.boundingRect()
            self.start_item_pos = item.pos()
            
            # デフォルトの処理を実行
            QGraphicsRectItem.mousePressEvent(self.handle_item, event)
    
    def mouseMoveEvent(self, event):
        if self.is_dragging and self.start_pos:
            current_pos = event.scenePos()
            delta_x = current_pos.x() - self.start_pos.x()
            delta_y = current_pos.y() - self.start_pos.y()
            
            # ハンドルタイプに応じてリサイズ処理
            self.resize_shape(delta_x, delta_y)
            
            # ハンドル自体も移動
            QGraphicsRectItem.mouseMoveEvent(self.handle_item, event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.start_pos = None
            
            # リサイズ後の座標を元座標に反映
            self.update_original_size()
            
            # ハンドルを再作成して正しい位置に配置
            self.parent_shape.create_handles()
            
            # パーツ名と制御点も更新
            self.parent_shape.update_name_display()
            self.parent_shape.update_center_control_point()
            
            # 円形の場合はcircumferenceポイントも更新（リサイズ時のみ実行）
            if hasattr(self.parent_shape, 'update_circumference_display'):
                # リサイズ完了後なので再描画が必要
                self.parent_shape.update_circumference_display()
            
            # バー形状の場合は形状を更新（アスペクト比変更に対応）
            if hasattr(self.parent_shape, 'update_shape_on_resize'):
                self.parent_shape.update_shape_on_resize()
            
            # デフォルトの処理を実行
            QGraphicsRectItem.mouseReleaseEvent(self.handle_item, event)
    
    def resize_shape(self, delta_x, delta_y):
        """ハンドルタイプに応じて図形をリサイズ"""
        item = self.parent_shape.get_item()
        
        # 円形かどうか判定
        is_circle = (self.parent_shape.shape_type == ShapeType.CIRCLE if hasattr(self.parent_shape, 'shape_type') else False)
        
        # 現在の矩形情報
        new_x = self.start_item_pos.x()
        new_y = self.start_item_pos.y()
        new_width = self.start_rect.width()
        new_height = self.start_rect.height()
        
        if is_circle:
            # 円形の場合: 半径の変更（縦横比維持）
            center_x = self.start_item_pos.x() + self.start_rect.width() / 2
            center_y = self.start_item_pos.y() + self.start_rect.height() / 2
            
            if "left" in self.handle_type:
                # 左側のハンドル: 半径を縮小
                new_radius = (self.start_rect.width() / 2) - delta_x
            elif "right" in self.handle_type:
                # 右側のハンドル: 半径を拡大
                new_radius = (self.start_rect.width() / 2) + delta_x
            else:
                new_radius = self.start_rect.width() / 2
            
            # 最小半径制限
            if new_radius < 10:
                new_radius = 10
            
            # 新しい直径
            new_diameter = new_radius * 2
            
            # 中心点から新しい位置を計算
            new_x = center_x - new_radius
            new_y = center_y - new_radius
            new_width = new_diameter
            new_height = new_diameter
        else:
            # 矩形の場合: 従来通りの処理
            # ハンドルタイプに応じて調整
            if "left" in self.handle_type:
                # 左側のハンドル: 左端を移動（幅を調整）
                new_x = self.start_item_pos.x() + delta_x
                new_width = self.start_rect.width() - delta_x
            elif "right" in self.handle_type:
                # 右側のハンドル: 右端を移動（幅を調整）
                new_width = self.start_rect.width() + delta_x
            
            if "top" in self.handle_type:
                # 上側のハンドル: 上端を移動（高さを調整）
                new_y = self.start_item_pos.y() + delta_y
                new_height = self.start_rect.height() - delta_y
            elif "bottom" in self.handle_type:
                # 下側のハンドル: 下端を移動（高さを調整）
                new_height = self.start_rect.height() + delta_y
            
            # 最小サイズ制限
            if new_width < 20:
                new_width = 20
                if "left" in self.handle_type:
                    new_x = self.start_item_pos.x() + self.start_rect.width() - 20
            
            if new_height < 20:
                new_height = 20
                if "top" in self.handle_type:
                    new_y = self.start_item_pos.y() + self.start_rect.height() - 20
        
        # 図形を更新
        item.setPos(new_x, new_y)
        
        # 矩形または楕円のサイズを更新
        if hasattr(item, 'setRect'):
            item.setRect(0, 0, new_width, new_height)
        
        # 他のハンドルの位置も更新（リアルタイム更新）
        self.update_other_handles()
    
    def update_other_handles(self):
        """他のハンドルの位置を更新"""
        item = self.parent_shape.get_item()
        rect = item.boundingRect()
        pos = item.pos()
        
        # 円形かどうか判定
        is_circle = (self.parent_shape.shape_type == ShapeType.CIRCLE if hasattr(self.parent_shape, 'shape_type') else False)
        
        if is_circle:
            # 円形: 左右2つのハンドル
            positions = [
                (pos.x() + rect.right(), pos.y() + rect.center().y()),  # 右中央
                (pos.x() + rect.left(), pos.y() + rect.center().y()),  # 左中央
            ]
        else:
            # 矩形: 8つのハンドル
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
        
        # 現在ドラッグ中のハンドル以外を更新
        for i, handle in enumerate(self.parent_shape.handles):
            if handle != self.handle_item:
                x, y = positions[i]
                handle.setPos(x - self.parent_shape.handle_size/2, 
                            y - self.parent_shape.handle_size/2)
    
    def update_original_size(self):
        """リサイズ後のサイズを元座標に反映"""
        item = self.parent_shape.get_item()
        rect = item.boundingRect()
        pos = item.pos()
        
        # 現在のスケールで割って元座標を更新
        scale = self.parent_shape.scene_scale
        self.parent_shape.original_x = pos.x() / scale
        self.parent_shape.original_y = pos.y() / scale
        self.parent_shape.original_width = rect.width() / scale
        self.parent_shape.original_height = rect.height() / scale
        
        # 円形の場合は元の中心座標も更新
        if hasattr(self.parent_shape, 'original_center_x') and hasattr(self.parent_shape, 'original_center_y'):
            center_x = pos.x() + rect.width() / 2
            center_y = pos.y() + rect.height() / 2
            self.parent_shape.original_center_x = center_x
            self.parent_shape.original_center_y = center_y
    
    def hoverEnterEvent(self, event):
        """ホバー時にハンドルを強調表示"""
        self.handle_item.setBrush(QBrush(QColor(100, 200, 255)))
        self.handle_item.setPen(QPen(QColor(0, 0, 0), 2))
        
        # カーソルを変更（リサイズカーソル）
        from PySide6.QtCore import Qt
        if self.handle_type in ["top_left", "bottom_right"]:
            self.handle_item.setCursor(Qt.SizeFDiagCursor)
        elif self.handle_type in ["top_right", "bottom_left"]:
            self.handle_item.setCursor(Qt.SizeBDiagCursor)
        elif self.handle_type in ["top_center", "bottom_center"]:
            self.handle_item.setCursor(Qt.SizeVerCursor)
        elif self.handle_type in ["middle_left", "middle_right"]:
            self.handle_item.setCursor(Qt.SizeHorCursor)
        
        QGraphicsRectItem.hoverEnterEvent(self.handle_item, event)
    
    def hoverLeaveEvent(self, event):
        """ホバー終了時に元の色に戻す"""
        self.handle_item.setBrush(QBrush(QColor(255, 255, 255)))
        self.handle_item.setPen(QPen(QColor(0, 0, 0), 1))
        self.handle_item.setCursor(Qt.ArrowCursor)
        
        QGraphicsRectItem.hoverLeaveEvent(self.handle_item, event)


class CircumferencePointDrag:
    """circumferenceポイントのドラッグハンドラ（円上を移動）"""
    
    def __init__(self, point_item, parent_ellipse, point_data, index):
        self.point_item = point_item
        self.parent_ellipse = parent_ellipse
        self.point_data = point_data
        self.index = index
        self.is_dragging = False
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            # 親図形にドラッグ中フラグを設定
            self.parent_ellipse.circumference_dragging = True
            # イベントを消費して、選択解除を防ぐ
            event.accept()
    
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            # 円の中心と半径を取得
            rect = self.parent_ellipse.ellipse_item.boundingRect()
            pos = self.parent_ellipse.ellipse_item.pos()
            center_x = pos.x() + rect.width() / 2
            center_y = pos.y() + rect.height() / 2
            radius = rect.width() / 2
            
            # マウス位置から角度を計算（右が0度、反時計回り）
            mouse_pos = event.scenePos()
            dx = mouse_pos.x() - center_x
            dy = mouse_pos.y() - center_y
            
            import math
            # マウス位置の角度を計算（0〜2π）
            mouse_angle = math.atan2(dy, dx)
            if mouse_angle < 0:
                mouse_angle += 2 * math.pi
            
            # 角度をvalue（0〜1）に変換
            target_value = mouse_angle / (2 * math.pi)
            
            # value順序制約を適用
            sorted_points = sorted(self.parent_ellipse.circumference_points, key=lambda p: p.value)
            current_index = next((i for i, p in enumerate(sorted_points) if p == self.point_data), -1)
            
            if current_index >= 0:
                min_value = 0.0
                max_value = 1.0
                
                # 前のポイントのvalue制約
                if current_index > 0:
                    min_value = sorted_points[current_index - 1].value + 0.01  # 1%マージン
                
                # 次のポイントのvalue制約
                if current_index < len(sorted_points) - 1:
                    max_value = sorted_points[current_index + 1].value - 0.01  # 1%マージン
                
                # target_valueを制約範囲内に収める
                target_value = max(min_value, min(max_value, target_value))
            
            # valueから角度を計算（0〜2π）
            final_angle = target_value * 2 * math.pi
            
            # 円周上の座標を計算
            new_x = center_x + radius * math.cos(final_angle)
            new_y = center_y + radius * math.sin(final_angle)
            
            # ポイントマーカーの位置を更新
            marker_size = 32
            self.point_item.setPos(new_x - marker_size/2, new_y - marker_size/2)
            
            # テキストの位置を更新
            try:
                text_index = self.parent_ellipse.circumference_items.index(self.point_item) + 1
                if text_index < len(self.parent_ellipse.circumference_items):
                    text_item = self.parent_ellipse.circumference_items[text_index]
                    text_offset = 30
                    text_x = center_x + (radius + text_offset) * math.cos(final_angle)
                    text_y = center_y + (radius + text_offset) * math.sin(final_angle)
                    text_item.setPos(text_x - 15, text_y - 15)
            except (ValueError, IndexError):
                pass
            
            # 元座標系での位置を更新
            scale = self.parent_ellipse.scene_scale
            self.point_data.position.x = new_x / scale
            self.point_data.position.y = new_y / scale
            
            event.accept()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            # 親図形のドラッグ中フラグをクリア
            self.parent_ellipse.circumference_dragging = False
            # circumferenceドラッグ終了後は再描画不要（既に正しい位置にある）
            # self.parent_ellipse.update_circumference_display()
            event.accept()


class CircumferencePointItem(QGraphicsEllipseItem):
    """circumferenceポイント用のカスタムアイテム"""
    
    def __init__(self, x, y, width, height, parent_ellipse, point_data, index):
        super().__init__(x, y, width, height)
        self.parent_ellipse = parent_ellipse
        self.point_data = point_data
        self.index = index
        self.is_dragging = False
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.parent_ellipse.circumference_dragging = True
            event.accept()
        
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            # 親の図形タイプをチェック
            if isinstance(self.parent_ellipse, BarShapeItem):
                self.handle_bar_drag(event)
            else:
                self.handle_circle_drag(event)
            
    def handle_circle_drag(self, event):
        """円形の場合のドラッグ処理"""
        # 円の中心と半径を取得
        rect = self.parent_ellipse.ellipse_item.boundingRect()
        pos = self.parent_ellipse.ellipse_item.pos()
        center_x = pos.x() + rect.width() / 2
        center_y = pos.y() + rect.height() / 2
        radius = rect.width() / 2
        
        # デバッグ出力
        if DEBUG_MODE: print(f"[DEBUG mouseMoveEvent] Circle center: ({center_x:.2f}, {center_y:.2f})")
        if DEBUG_MODE: print(f"[DEBUG mouseMoveEvent] Circle pos: ({pos.x():.2f}, {pos.y():.2f})")
        if DEBUG_MODE: print(f"[DEBUG mouseMoveEvent] Circle rect: {rect.width():.2f} x {rect.height():.2f}")
        if DEBUG_MODE: print(f"[DEBUG mouseMoveEvent] Radius: {radius:.2f}")
        
        # マウス位置から角度を計算
        mouse_pos = event.scenePos()
        dx = mouse_pos.x() - center_x
        dy = mouse_pos.y() - center_y
        
        import math
        # マウス位置の角度を計算
        mouse_angle = math.atan2(dy, dx)
        
        # 前回の角度との差を計算して連続回転を判定
        if hasattr(self.point_data, '_last_angle'):
            angle_diff = mouse_angle - self.point_data._last_angle
            
            # 角度の不連続性を検出（-π〜πの境界をまたぐ場合）
            if angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            elif angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            # 累積角度を更新（360度以上の回転を記録）
            if hasattr(self.point_data, '_accumulated_angle'):
                self.point_data._accumulated_angle += angle_diff
            else:
                self.point_data._accumulated_angle = mouse_angle
        else:
            # 初回の場合
            self.point_data._accumulated_angle = mouse_angle
        
        self.point_data._last_angle = mouse_angle
        
        # 累積角度を0〜2πの範囲に正規化（表示用）
        normalized_angle = self.point_data._accumulated_angle % (2 * math.pi)
        if normalized_angle < 0:
            normalized_angle += 2 * math.pi
        
        # 角度制約を適用（valueは変更しない、valueが小さいほど角度も小さく）
        # circumferenceポイントをvalue順にソート
        sorted_points = sorted(self.parent_ellipse.circumference_points, key=lambda p: p.value)
        current_index = next((i for i, p in enumerate(sorted_points) if p == self.point_data), -1)
        
        # 各ポイントの現在の角度を取得
        point_angles = []
        for point in sorted_points:
            if hasattr(point, '_calculated_angle'):
                angle = point._calculated_angle
                # 角度を0〜2πに正規化
                if angle < 0:
                    angle += 2 * math.pi
                elif angle >= 2 * math.pi:
                    angle = angle % (2 * math.pi)
                point_angles.append(angle)
            else:
                # 初期角度がない場合はvalueから推定
                point_angles.append(point.value * 2 * math.pi)
        
        # 角度制約を計算
        min_angle = 0.0
        max_angle = 2 * math.pi
        margin = 0.05  # 約3度のマージン
        
        if current_index >= 0:
            # 前のポイント（小さいvalue）: 小さいvalueは大きい角度なので、このポイントはそれより小さい角度でなければならない
            if current_index > 0:
                max_angle = point_angles[current_index - 1] - margin
            
            # 次のポイント（大きいvalue）: 大きいvalueは小さい角度なので、このポイントはそれより大きい角度でなければならない
            if current_index < len(sorted_points) - 1:
                min_angle = point_angles[current_index + 1] + margin
            
            # 制約を適用
            # min_angle > max_angle の場合は2πをまたいでいる
            if min_angle >= max_angle:
                # 2πをまたぐ場合は制約を緩和
                if normalized_angle >= min_angle or normalized_angle <= max_angle:
                    # 現在の角度が許可範囲内
                    pass
                else:
                    # 最も近い許可範囲の境界に移動
                    dist_to_min = abs(normalized_angle - min_angle)
                    dist_to_max = abs(normalized_angle - max_angle)
                    if dist_to_min < dist_to_max:
                        normalized_angle = min_angle
                    else:
                        normalized_angle = max_angle
            else:
                # 通常の場合
                normalized_angle = max(min_angle, min(max_angle, normalized_angle))
        
        # 制約された角度を使用
        final_angle = normalized_angle
        
        # 円周上の座標を計算（制約された角度を使用）
        new_x = center_x + radius * math.cos(final_angle)
        new_y = center_y + radius * math.sin(final_angle)
        
        # このアイテムの位置を更新
        marker_size = 32
        self.setPos(new_x - marker_size/2, new_y - marker_size/2)
        
        # 対応するテキストアイテムも更新
        try:
            text_index = self.parent_ellipse.circumference_items.index(self) + 1
            if text_index < len(self.parent_ellipse.circumference_items):
                text_item = self.parent_ellipse.circumference_items[text_index]
                text_offset = 30
                text_x = center_x + (radius + text_offset) * math.cos(final_angle)
                text_y = center_y + (radius + text_offset) * math.sin(final_angle)
                text_item.setPos(text_x - 15, text_y - 15)
        except (ValueError, IndexError):
            pass
        
        # 元座標系での位置を更新
        scale = self.parent_ellipse.scene_scale
        self.point_data.position.x = new_x / scale
        self.point_data.position.y = new_y / scale
        
        event.accept()
    
    def handle_bar_drag(self, event):
        """バー形状の場合のドラッグ処理"""
        # 矩形の情報を取得
        rect = self.parent_ellipse.rect_item.boundingRect()
        pos = self.parent_ellipse.rect_item.pos()
        
        # マウス位置を取得
        mouse_pos = event.scenePos()
        
        # バーの向きに応じて制約
        if self.parent_ellipse.orientation == "horizontal":
            # 横長：横分割線上に制約（y座標は固定、x座標のみ変更可能）
            display_y = pos.y() + rect.height() / 2  # 分割線のy座標
            # x座標をマウス位置に基づいて計算（矩形内に制約）
            relative_x = max(0, min(1, (mouse_pos.x() - pos.x()) / rect.width()))
            display_x = pos.x() + rect.width() * relative_x
        else:
            # 縦長：縦分割線上に制約（x座標は固定、y座標のみ変更可能）
            display_x = pos.x() + rect.width() / 2  # 分割線のx座標
            # y座標をマウス位置に基づいて計算（矩形内に制約）
            relative_y = max(0, min(1, (mouse_pos.y() - pos.y()) / rect.height()))
            display_y = pos.y() + rect.height() * relative_y
        
        # value順序制約を適用
        sorted_points = sorted(self.parent_ellipse.circumference_points, key=lambda p: p.value)
        current_index = next((i for i, p in enumerate(sorted_points) if p == self.point_data), -1)
        
        # 順序制約を適用（value順序に基づく位置制約）
        if current_index >= 0:
            # 前のポイント（小さいvalue）と次のポイント（大きいvalue）の位置を取得
            if self.parent_ellipse.orientation == "horizontal":
                # 横長の場合：x座標で制約
                min_x = pos.x()
                max_x = pos.x() + rect.width()
                
                if current_index > 0:
                    # 前のポイントのx座標より右でなければならない
                    prev_point = sorted_points[current_index - 1]
                    if hasattr(prev_point, 'position') and prev_point.position:
                        min_x = prev_point.position.x * self.parent_ellipse.scene_scale + 5  # 5px余裕
                
                if current_index < len(sorted_points) - 1:
                    # 次のポイントのx座標より左でなければならない
                    next_point = sorted_points[current_index + 1]
                    if hasattr(next_point, 'position') and next_point.position:
                        max_x = next_point.position.x * self.parent_ellipse.scene_scale - 5  # 5px余裕
                
                # x座標を制約
                display_x = max(min_x, min(max_x, display_x))
            else:
                # 縦長の場合：y座標で制約（value順序と逆：小さいvalueが下）
                min_y = pos.y()
                max_y = pos.y() + rect.height()
                
                if current_index > 0:
                    # 前のポイント（小さいvalue）のy座標より上でなければならない
                    prev_point = sorted_points[current_index - 1]
                    if hasattr(prev_point, 'position') and prev_point.position:
                        max_y = prev_point.position.y * self.parent_ellipse.scene_scale - 5  # 5px余裕
                
                if current_index < len(sorted_points) - 1:
                    # 次のポイント（大きいvalue）のy座標より下でなければならない
                    next_point = sorted_points[current_index + 1]
                    if hasattr(next_point, 'position') and next_point.position:
                        min_y = next_point.position.y * self.parent_ellipse.scene_scale + 5  # 5px余裕
                
                # y座標を制約
                display_y = max(min_y, min(max_y, display_y))
        
        # valueは変更しない（vehicle.jsonの固定値を維持）
        # self.point_data.value = target_value  # コメントアウト
        
        # 最終位置はドラッグ位置をそのまま使用（分割線制約は既に適用済み）
        # target_valueは使用しない
        
        # ポイントマーカーの位置を更新
        marker_size = 32
        self.setPos(display_x - marker_size/2, display_y - marker_size/2)
        
        # 対応するテキストアイテムも更新
        try:
            text_index = self.parent_ellipse.circumference_items.index(self) + 1
            if text_index < len(self.parent_ellipse.circumference_items):
                text_item = self.parent_ellipse.circumference_items[text_index]
                text_offset = 30
                if self.parent_ellipse.orientation == "horizontal":
                    text_x = display_x + (text_offset if display_x < pos.x() + rect.width()/2 else -text_offset)
                    text_y = display_y - 15
                else:
                    text_x = display_x - 15
                    text_y = display_y + (text_offset if display_y < pos.y() + rect.height()/2 else -text_offset)
                text_item.setPos(text_x, text_y)
        except (ValueError, IndexError):
            pass
        
        # 元座標系での位置を更新（マーカーの中心座標を使用）
        scale = self.parent_ellipse.scene_scale
        # setPos()で設定した座標にマーカーサイズの半分を加えて、実際の中心座標を取得
        actual_center_x = display_x
        actual_center_y = display_y
        self.point_data.position.x = actual_center_x / scale
        self.point_data.position.y = actual_center_y / scale
        
        event.accept()
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.parent_ellipse.circumference_dragging = False
            
            # 親の図形タイプを判定
            if hasattr(self.parent_ellipse, 'shape_type') and self.parent_ellipse.shape_type == ShapeType.BAR:
                # バー形状の場合：相対位置を再計算して保存
                marker_pos = self.pos()
                marker_center_x = marker_pos.x() + 16  # marker_size/2
                marker_center_y = marker_pos.y() + 16
                scale = self.parent_ellipse.scene_scale
                
                # ドラッグ後の座標を更新
                self.point_data.position.x = marker_center_x / scale
                self.point_data.position.y = marker_center_y / scale
                
                # 相対位置を再計算（次回の表示で正しく配置されるように）
                rect = self.parent_ellipse.rect_item.boundingRect()
                pos = self.parent_ellipse.rect_item.pos()
                current_center_x = pos.x() + rect.width() / 2
                current_center_y = pos.y() + rect.height() / 2
                current_radius = max(rect.width(), rect.height()) / 2
                
                rel_x = marker_center_x - current_center_x
                rel_y = marker_center_y - current_center_y
                
                if self.parent_ellipse.orientation == "horizontal":
                    self.point_data._calculated_relative_pos = (marker_center_x - pos.x()) / rect.width()
                else:
                    self.point_data._calculated_relative_pos = (marker_center_y - pos.y()) / rect.height()
            else:
                # 円形の場合：角度計算
                rect = self.parent_ellipse.ellipse_item.boundingRect()
                pos = self.parent_ellipse.ellipse_item.pos()
                center_x = pos.x() + rect.width() / 2
                center_y = pos.y() + rect.height() / 2
                
                # マーカーの中心位置を取得
                marker_pos = self.pos()
                marker_center_x = marker_pos.x() + 16  # marker_size/2
                marker_center_y = marker_pos.y() + 16
                
                # 円の中心からマーカーの中心への角度を計算
                dx = marker_center_x - center_x
                dy = marker_center_y - center_y
                
                import math
                new_angle = math.atan2(dy, dx)
                
                # 正規化された角度を保存（次回の表示更新で使用される）
                self.point_data._calculated_angle = new_angle
                
                # 累積角度もリセット（ドラッグ完了時）
                if hasattr(self.point_data, '_accumulated_angle'):
                    delattr(self.point_data, '_accumulated_angle')
                if hasattr(self.point_data, '_last_angle'):
                    delattr(self.point_data, '_last_angle')
            
            # ドラッグ完了後は再描画不要（既に正しい位置にある）
            # self.parent_ellipse.update_circumference_display()
            
            event.accept()


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
                 is_original_coords: bool = False, circumference_points: List[CircumferencePoint] = None):
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
        
        # circumferenceポイントデータを保存
        self.circumference_points = circumference_points or []
        self.circumference_items = []  # 表示用のグラフィックアイテム
        self.circumference_dragging = False  # ドラッグ中フラグ
        
        # 元の中心座標を初期化（circumferenceポイントの相対位置計算用）
        rect = self.ellipse_item.boundingRect()
        pos = self.ellipse_item.pos()
        self.original_center_x = pos.x() + rect.width() / 2
        self.original_center_y = pos.y() + rect.height() / 2
        
        # circumferenceポイントを表示
        self.update_circumference_display()
        
        # 重心制御点とパーツ名を作成
        self.create_center_control_point()
        self.create_name_text()
    
    def update_circumference_display(self):
        """circumferenceポイントの表示を更新（選択時のみ）"""
        # シンプルなドラッグ中チェック
        if hasattr(self, 'circumference_dragging') and self.circumference_dragging:
            return  # circumferenceドラッグ中は更新しない
        
        # 中心制御点がドラッグ中かチェック
        if hasattr(self, 'center_control_point_handler'):
            if hasattr(self.center_control_point_handler, 'is_dragging') and self.center_control_point_handler.is_dragging:
                return  # 中心点ドラッグ中も更新しない
        
        # 既存の表示を削除
        for item in self.circumference_items:
            if item.scene():
                item.scene().removeItem(item)
        self.circumference_items.clear()
        
        if not self.ellipse_item.scene():
            return
        
        # 選択されていない場合は表示しない
        if not self.is_selected:
            return
        
        # 円の中心と半径を計算
        rect = self.ellipse_item.boundingRect()
        pos = self.ellipse_item.pos()
        center_x = pos.x() + rect.width() / 2
        center_y = pos.y() + rect.height() / 2
        radius = rect.width() / 2  # 正円なので幅から半径を計算
        
        import math
        
        # circumferenceポイントをvalue順にソート
        sorted_points = sorted(self.circumference_points, key=lambda p: p.value)
        
        # デバッグ出力
        if DEBUG_MODE: print(f"[DEBUG update_circumference_display] Circle center: ({center_x:.2f}, {center_y:.2f})")
        if DEBUG_MODE: print(f"[DEBUG update_circumference_display] Circle pos: ({pos.x():.2f}, {pos.y():.2f})")
        if DEBUG_MODE: print(f"[DEBUG update_circumference_display] Circle rect: {rect.width():.2f} x {rect.height():.2f}")
        if DEBUG_MODE: print(f"[DEBUG update_circumference_display] Radius: {radius:.2f}")
        if DEBUG_MODE: print(f"[DEBUG update_circumference_display] Circumference points: {len(sorted_points)}")
        
        # 各circumferenceポイントを現在の円の中心・半径に基づいて配置
        for i, point in enumerate(sorted_points):
            # vehicle.jsonのposition座標がある場合、それから角度を逆算
            if hasattr(point, 'position') and point.position:
                # 初期設定時のみ：vehicle.jsonの座標から角度を計算して保存
                if not hasattr(point, '_calculated_angle'):
                    # vehicle.jsonで定義された元の円の中心を取得
                    # （これは初期化時の円の中心と仮定）
                    original_center_x = self.original_center_x if hasattr(self, 'original_center_x') else center_x
                    original_center_y = self.original_center_y if hasattr(self, 'original_center_y') else center_y
                    
                    # 元の座標から角度を計算
                    rel_x = point.position.x - original_center_x
                    rel_y = point.position.y - original_center_y
                    point._calculated_angle = math.atan2(rel_y, rel_x)
                
                # 計算された角度を使用して現在の円周上に配置
                display_x = center_x + radius * math.cos(point._calculated_angle)
                display_y = center_y + radius * math.sin(point._calculated_angle)
            else:
                # position座標がない場合：valueから角度を計算
                angle = point.value * 2 * math.pi - math.pi / 2  # -π/2で上方向を0とする
                display_x = center_x + radius * math.cos(angle)
                display_y = center_y + radius * math.sin(angle)
            
            if DEBUG_MODE: 
                angle_debug = point.value * 2 * math.pi - math.pi / 2 if not (hasattr(point, 'position') and point.position) else 0
                print(f"[DEBUG] Point {i}: value={point.value:.3f}, angle={angle_debug:.3f}, pos=({display_x:.2f}, {display_y:.2f})")
            
            # ポイントマーカー（大きな円）
            marker_size = 32  # さらに大きくして選択しやすく
            point_marker = CircumferencePointItem(
                display_x - marker_size/2,
                display_y - marker_size/2,
                marker_size,
                marker_size,
                self,
                point,
                i
            )
            point_marker.setBrush(QBrush(QColor(255, 128, 0)))  # オレンジ色
            point_marker.setPen(QPen(QColor(0, 0, 0), 2))
            point_marker.setZValue(1500)  # ハンドルより前面
            point_marker.setFlag(QGraphicsItem.ItemIsMovable, True)
            point_marker.setAcceptHoverEvents(True)
            
            # カスタムデータとして元のポイントデータを保存
            point_marker.setData(0, point)
            point_marker.setData(1, i)  # インデックスも保存
            
            # 値を表示するテキスト（大きく）
            from PySide6.QtWidgets import QGraphicsTextItem
            from PySide6.QtGui import QFont
            value_text = QGraphicsTextItem(f"{point.value:.2f}")
            
            # テキストの位置を円の外側に配置
            text_offset = 30
            # ポイントから円の中心への方向ベクトルを計算
            dx = display_x - center_x
            dy = display_y - center_y
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                # 正規化してテキスト位置を計算
                text_x = display_x + (dx / distance) * text_offset
                text_y = display_y + (dy / distance) * text_offset
            else:
                text_x = display_x + text_offset
                text_y = display_y
            value_text.setPos(text_x - 15, text_y - 15)  # 中央寄せ調整
            
            font = QFont("Arial", 16, QFont.Bold)  # フォントサイズを大きく
            value_text.setFont(font)
            value_text.setDefaultTextColor(QColor(255, 128, 0))
            value_text.setZValue(1501)
            
            # シーンに追加
            self.ellipse_item.scene().addItem(point_marker)
            self.ellipse_item.scene().addItem(value_text)
            
            self.circumference_items.append(point_marker)
            self.circumference_items.append(value_text)
    
    def update_position_for_scale(self, scale: float):
        """スケール変更時の位置更新（circumferenceポイントも更新）"""
        super().update_position_for_scale(scale)
        # circumferenceポイントの表示も更新
        self.update_circumference_display()
    
    def set_visible(self, visible: bool):
        """表示/非表示を設定（circumferenceポイントも同期）"""
        super().set_visible(visible)
        # circumferenceポイントの表示も同期
        for item in self.circumference_items:
            item.setVisible(visible)
    
    def set_selected(self, selected: bool):
        """選択状態を設定し、表示を更新（circumferenceポイントも含む）"""
        super().set_selected(selected)
        # circumferenceポイントの表示も更新（ドラッグ中でない場合のみ）
        if not (hasattr(self, 'circumference_dragging') and self.circumference_dragging):
            self.update_circumference_display()
    
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
                 is_original_coords: bool = False, circumference_points: List[CircumferencePoint] = None):
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
        
        # アスペクト比によるorientation自動判定
        aspect_ratio = display_width / display_height if display_height > 0 else 1.0
        self.orientation = "horizontal" if aspect_ratio > 1.0 else "vertical"
        
        # 矩形アイテムを作成（基本形状）
        self.rect_item = QGraphicsRectItem(0, 0, display_width, display_height)
        self.rect_item.setPos(display_x, display_y)
        self.rect_item.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.rect_item.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.rect_item.setZValue(100)
        
        # 分割線アイテムを作成
        self.divider_line = QGraphicsLineItem()
        self.divider_line.setPos(display_x, display_y)
        self.divider_line.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.divider_line.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.divider_line.setZValue(101)  # 矩形より前面
        
        self.shape_type = ShapeType.BAR
        
        # circumferenceポイントデータを保存
        self.circumference_points = circumference_points or []
        self.circumference_items = []  # 表示用のグラフィックアイテム
        self.circumference_dragging = False  # ドラッグ中フラグ
        
        # 初期の中心・サイズを保存（相対位置計算用）
        self.original_center_x = display_x + display_width / 2
        self.original_center_y = display_y + display_height / 2
        self.original_radius = max(display_width, display_height) / 2
        
        # バー形状を作成（矩形 + 分割線）
        self.create_bar_shape(display_width, display_height)
        self.update_color()
        
        # circumferenceポイントを表示
        self.update_circumference_display()
        
        # 重心制御点とパーツ名を作成
        self.create_center_control_point()
        self.create_name_text()
        
    def create_bar_shape(self, width: float, height: float):
        """バー形状を作成（矩形 + 分割線）"""
        from PySide6.QtCore import QLineF
        
        # 矩形のサイズを設定
        self.rect_item.setRect(0, 0, width, height)
        
        # アスペクト比を再判定（リサイズ時にも対応）
        aspect_ratio = width / height if height > 0 else 1.0
        self.orientation = "horizontal" if aspect_ratio > 1.0 else "vertical"
        
        # 分割線を設定
        if self.orientation == "horizontal":
            # 横長：縦に二分する線（中央を縦に通る）
            line = QLineF(width / 2, 0, width / 2, height)
        else:
            # 縦長：横に二分する線（中央を横に通る）
            line = QLineF(0, height / 2, width, height / 2)
        
        self.divider_line.setLine(line)
        
        # 分割線のペンを設定
        pen = QPen(QColor(0, 0, 0), 2)  # 黒色、2px幅
        self.divider_line.setPen(pen)
        
    def get_item(self) -> QGraphicsRectItem:
        return self.rect_item
    
    def update_color(self):
        """選択状態に応じて色を更新"""
        if self.is_selected:
            # 選択時の色（ピンク）
            brush = QBrush(QColor(255, 192, 203, 128))  # 半透明ピンク
            pen = QPen(QColor(255, 0, 255), 3)  # マゼンタの枠線
        else:
            # 非選択時の色（薄い青）
            brush = QBrush(QColor(173, 216, 230, 100))  # 半透明ライトブルー
            pen = QPen(QColor(0, 0, 255), 2)  # 青の枠線
        
        self.rect_item.setBrush(brush)
        self.rect_item.setPen(pen)
        
        # 分割線の色も更新
        divider_pen = QPen(QColor(0, 0, 0), 2)  # 常に黒色
        self.divider_line.setPen(divider_pen)
    
    def update_shape_on_resize(self):
        """リサイズ時に形状を更新"""
        rect = self.rect_item.boundingRect()
        self.create_bar_shape(rect.width(), rect.height())
    
    def update_circumference_display(self):
        """circumferenceポイントを分割線上に表示（選択時のみ）"""
        # ドラッグ中は更新しない
        if hasattr(self, 'circumference_dragging') and self.circumference_dragging:
            return
        
        # 中心制御点がドラッグ中かチェック
        if hasattr(self, 'center_control_point_handler'):
            if hasattr(self.center_control_point_handler, 'is_dragging') and self.center_control_point_handler.is_dragging:
                return
        
        # 既存の表示を削除
        for item in self.circumference_items:
            if item.scene():
                item.scene().removeItem(item)
        self.circumference_items.clear()
        
        if not self.rect_item.scene():
            return
        
        # 選択されていない場合は表示しない
        if not self.is_selected:
            return
        
        # 矩形の情報を取得
        rect = self.rect_item.boundingRect()
        pos = self.rect_item.pos()
        
        # 分割線の情報を取得
        line = self.divider_line.line()
        
        import math
        
        # circumferenceポイントをvalue順にソート
        sorted_points = sorted(self.circumference_points, key=lambda p: p.value)
        
        # 各circumferenceポイントを分割線上に配置
        for i, point in enumerate(sorted_points):
            # vehicle.jsonのposition座標がある場合、それから相対位置を計算して保存
            if hasattr(point, 'position') and point.position:
                # 初期設定時のみ：vehicle.jsonの座標から相対位置を計算して保存
                if not hasattr(point, '_calculated_relative_pos'):
                    # vehicle.jsonで定義された元のバーの中心・サイズを取得
                    original_center_x = self.original_center_x if hasattr(self, 'original_center_x') else pos.x() + rect.width() / 2
                    original_center_y = self.original_center_y if hasattr(self, 'original_center_y') else pos.y() + rect.height() / 2
                    original_radius = self.original_radius if hasattr(self, 'original_radius') else max(rect.width(), rect.height()) / 2
                    
                    # スケール調整された座標を取得
                    scaled_x = point.position.x * self.scene_scale
                    scaled_y = point.position.y * self.scene_scale
                    
                    # 元の中心からの相対位置を計算
                    rel_x = scaled_x - original_center_x
                    rel_y = scaled_y - original_center_y
                    
                    # バーの向きに応じて相対位置を正規化（0～1の範囲）
                    if self.orientation == "horizontal":
                        # 横長：x方向の相対位置を0～1で正規化
                        original_width = original_radius * 2
                        calculated_relative_0_1 = (scaled_x - (original_center_x - original_width/2)) / original_width
                        # 分割線上にない場合（バー矩形外）は、value値に基づいて初期配置
                        if calculated_relative_0_1 < 0.0 or calculated_relative_0_1 > 1.0:
                            point._calculated_relative_pos = point.value
                        else:
                            point._calculated_relative_pos = calculated_relative_0_1
                    else:
                        # 縦長：y方向の相対位置を0～1で正規化
                        original_height = original_radius * 2
                        calculated_relative_0_1 = (scaled_y - (original_center_y - original_height/2)) / original_height
                        # 分割線上にない場合（バー矩形外）は、value値に基づいて初期配置
                        if calculated_relative_0_1 < 0.0 or calculated_relative_0_1 > 1.0:
                            point._calculated_relative_pos = point.value
                        else:
                            point._calculated_relative_pos = calculated_relative_0_1
                
                # 計算された相対位置を使用して現在の分割線上に配置
                current_center_x = pos.x() + rect.width() / 2
                current_center_y = pos.y() + rect.height() / 2
                current_radius = max(rect.width(), rect.height()) / 2
                
                if self.orientation == "horizontal":
                    # 横長：分割線は水平、y座標は中央固定
                    display_x = pos.x() + point._calculated_relative_pos * rect.width()
                    display_y = current_center_y  # 分割線上（水平中央）
                else:
                    # 縦長：分割線は垂直、x座標は中央固定
                    display_x = current_center_x  # 分割線上（垂直中央）
                    display_y = pos.y() + point._calculated_relative_pos * rect.height()
            else:
                # position座標がない場合：value値に基づいて分割線上に初期配置
                current_center_x = pos.x() + rect.width() / 2
                current_center_y = pos.y() + rect.height() / 2
                
                # value値（0.0～1.0）をそのまま使用（handle_bar_dragと一致）
                if self.orientation == "horizontal":
                    display_x = pos.x() + point.value * rect.width()
                    display_y = current_center_y
                else:
                    display_x = current_center_x
                    display_y = pos.y() + point.value * rect.height()
            
            if DEBUG_MODE:
                print(f"[DEBUG] Bar Point {i}: value={point.value:.3f}, pos=({display_x:.2f}, {display_y:.2f})")
                print(f"[DEBUG] Bar rect: pos=({pos.x():.2f}, {pos.y():.2f}), size=({rect.width():.2f}, {rect.height():.2f})")
                if self.orientation == "horizontal":
                    expected_y = pos.y() + rect.height() / 2
                    print(f"[DEBUG] Expected y for horizontal bar: {expected_y:.2f}, actual display_y: {display_y:.2f}")
                else:
                    expected_x = pos.x() + rect.width() / 2  
                    print(f"[DEBUG] Expected x for vertical bar: {expected_x:.2f}, actual display_x: {display_x:.2f}")
            
            # テキストの位置を分割線上に配置
            text_x = display_x
            text_y = display_y
            
            # ポイントマーカー（大きな円）
            marker_size = 32
            # 制御点をテキストと全く同じ位置に配置
            point_marker = CircumferencePointItem(
                0,  # boundingRectのx座標（相対位置）
                0,  # boundingRectのy座標（相対位置）
                marker_size,
                marker_size,
                self,
                point,
                i
            )
            # 実際の位置をsetPosで設定
            point_marker.setPos(text_x - marker_size/2, text_y - marker_size/2)
            point_marker.setBrush(QBrush(QColor(255, 128, 0)))  # オレンジ色
            point_marker.setPen(QPen(QColor(0, 0, 0), 2))
            point_marker.setZValue(1500)  # ハンドルより前面
            point_marker.setFlag(QGraphicsItem.ItemIsMovable, True)
            point_marker.setAcceptHoverEvents(True)
            
            if DEBUG_MODE:
                marker_pos = point_marker.pos()
                marker_center_x = marker_pos.x() + marker_size/2
                marker_center_y = marker_pos.y() + marker_size/2
                print(f"[DEBUG] Marker created at: pos=({marker_pos.x():.2f}, {marker_pos.y():.2f}), center=({marker_center_x:.2f}, {marker_center_y:.2f})")
                print(f"[DEBUG] Text will be created at: ({text_x:.2f}, {text_y:.2f})")
            
            # 値を表示するテキスト（大きく）
            from PySide6.QtWidgets import QGraphicsTextItem
            from PySide6.QtGui import QFont
            value_text = QGraphicsTextItem(f"{point.value:.2f}")
            
            value_text.setPos(text_x, text_y)
            font = QFont("Arial", 16, QFont.Bold)
            value_text.setFont(font)
            value_text.setDefaultTextColor(QColor(255, 128, 0))
            value_text.setZValue(1501)
            
            # シーンに追加
            self.rect_item.scene().addItem(point_marker)
            self.rect_item.scene().addItem(value_text)
            
            self.circumference_items.append(point_marker)
            self.circumference_items.append(value_text)
    
    def set_visible(self, visible: bool):
        """表示状態を設定"""
        super().set_visible(visible)
        if hasattr(self, 'rect_item'):
            self.rect_item.setVisible(visible)
        if hasattr(self, 'divider_line'):
            self.divider_line.setVisible(visible)


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
    
    def calculate_fit_to_view_scale(self) -> float:
        """画像を表示領域に最適フィットするスケールを計算"""
        if not self.original_pixmap:
            return 1.0
            
        view_rect = self.viewport().rect()
        image_width = self.original_pixmap.width()
        image_height = self.original_pixmap.height()
        
        # 表示領域に画像をフィットさせるスケールを計算
        x_ratio = view_rect.width() / image_width
        y_ratio = view_rect.height() / image_height
        
        # 画像が表示領域を最大限活用するスケール（アスペクト比保持）
        fit_scale = min(x_ratio, y_ratio) * 0.95  # 5%マージンを確保
        
        return fit_scale
    
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
            self.start_pos = self.mapToScene(event.position().toPoint())
            
            # 一時的な図形を作成
            if self.drawing_mode == "rectangle":
                self.temp_item = QGraphicsRectItem(self.start_pos.x(), 
                                                   self.start_pos.y(), 0, 0)
                self.temp_item.setPen(QPen(QColor(255, 0, 0), 2))
            elif self.drawing_mode == "circle":
                self.temp_item = QGraphicsEllipseItem(self.start_pos.x(),
                                                      self.start_pos.y(), 0, 0)
                self.temp_item.setPen(QPen(QColor(0, 0, 255), 2))
            elif self.drawing_mode == "bar":
                self.temp_item = QGraphicsRectItem(self.start_pos.x(),
                                                   self.start_pos.y(), 0, 0)
                self.temp_item.setPen(QPen(QColor(0, 255, 0), 2))  # 緑色でbar
                
            if self.temp_item:
                self.scene.addItem(self.temp_item)
        elif event.button() == Qt.LeftButton:
            # クリック位置のアイテムを取得
            click_pos = self.mapToScene(event.position().toPoint())
            clicked_item = self.scene.itemAt(click_pos, self.transform())
            
            # クリックされたアイテムがリサイズハンドルまたはcircumferenceポイントかチェック
            is_resize_handle = False
            is_circumference_point = False
            if clicked_item:
                # 選択中の図形のハンドルかチェック
                for shape in self.shapes:
                    if shape.is_selected and clicked_item in shape.handles:
                        is_resize_handle = True
                        break
                    # circumferenceポイントかチェック（選択中の楕円のみ）
                    if (shape.is_selected and hasattr(shape, 'circumference_items') 
                        and clicked_item in shape.circumference_items):
                        is_circumference_point = True
                        break
            
            # リサイズハンドルまたはcircumferenceポイントがクリックされた場合は選択解除しない
            if not is_resize_handle and not is_circumference_point:
                # 描画モードでない場合、最も近い制御点を探して選択
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
            current_pos = self.mapToScene(event.position().toPoint())
            
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
                elif self.drawing_mode == "bar":
                    shape = BarShapeItem(rect.x(), rect.y(),
                                        rect.width(), rect.height(),
                                        1.0, ShapeCategory.METER, False)
                else:
                    shape = None
                    
                if shape:
                    if isinstance(shape, BarShapeItem):
                        # BarShapeItemの場合は両方のアイテムを追加
                        self.scene.addItem(shape.rect_item)
                        self.scene.addItem(shape.divider_line)
                    else:
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


class ConfigMainView(QWidget):
    """CONFIGモード用メインビュー（ユーザー体験フロー対応版）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.config_data = None
        
        # MQTTサービス初期化
        self.mqtt_service = MQTTService()
        self.mqtt_service.connected.connect(self.on_mqtt_connected)
        self.mqtt_service.image_received.connect(self.on_image_received)
        
        # MQTTプレビュー用
        self.image_label = None
        self.current_pixmap = None
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        
        self.setup_ui()
        
        # ユーザー体験フロー: 起動時に自動でconfig.jsonダイアログを表示
        QTimer.singleShot(500, self.auto_show_config_dialog)
    
    def setup_ui(self):
        """UI設定（サイドバー+メインプレビュー構成）"""
        # メインレイアウト（プレビューエリア全幅利用）
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # メインプレビューエリア（全幅利用）
        preview_panel = self.create_main_preview_panel()
        main_layout.addWidget(preview_panel)
        
        # サイドバー（設定パネル）を後で追加
        self.create_config_sidebar()
    
    def create_config_panel(self):
        """設定パネル作成"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # タイトル
        title = QLabel("CONFIG MODE")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2196F3;
                padding: 16px 8px 8px 8px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # ステップ表示
        step_label = QLabel("📂 Step 1: config.json読み込み")
        step_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #333;
                padding: 8px;
                background-color: #e3f2fd;
                border-radius: 6px;
                border-left: 4px solid #2196F3;
            }
        """)
        layout.addWidget(step_label)
        
        # config.json読み込みボタン
        self.load_config_btn = QPushButton("📁 config.json読み込み")
        self.load_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 8px 0;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        self.load_config_btn.clicked.connect(self.load_config_file)
        layout.addWidget(self.load_config_btn)
        
        # 設定状態表示
        self.status_label = QLabel("⏳ config.json未読み込み\n\nデスクトップ/configフォルダから\n設定ファイルを選択してください")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
                padding: 12px;
                background-color: #f5f5f5;
                border-radius: 6px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.status_label)
        
        # MQTT接続状態
        self.mqtt_status_label = QLabel("🔴 MQTT: 未接続")
        self.mqtt_status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #f44336;
                padding: 8px 12px;
                background-color: rgba(244, 67, 54, 0.1);
                border-radius: 4px;
                margin: 8px 0;
            }
        """)
        layout.addWidget(self.mqtt_status_label)
        
        # スペーサー
        layout.addStretch()
        
        return panel
    
    def create_config_sidebar(self):
        """設定用サイドバー作成（QDockWidget使用）"""
        if not self.parent_window:
            return
            
        # サイドバーをQDockWidgetとして作成
        self.config_dock = QDockWidget("CONFIG Settings", self.parent_window)
        self.config_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.config_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        
        # サイドバーコンテンツ
        sidebar_content = self.create_config_panel()
        self.config_dock.setWidget(sidebar_content)
        
        # 親ウィンドウに追加（左側）
        self.parent_window.addDockWidget(Qt.LeftDockWidgetArea, self.config_dock)
        self.config_dock.setFixedWidth(350)
        
        # 初期状態では表示
        self.config_dock.show()
    
    def create_main_preview_panel(self):
        """メインプレビューパネル作成（全幅利用）"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # プレビュータイトル
        preview_title = QLabel("📹 カメラライブプレビュー")
        preview_title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2196F3;
                padding: 20px;
                text-align: center;
            }
        """)
        preview_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(preview_title)
        
        # 状態表示
        self.connection_status = QLabel("⏳ config.jsonを読み込んでMQTTに接続してください")
        self.connection_status.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #666;
                padding: 10px 20px;
                text-align: center;
                background-color: #f5f5f5;
                border-radius: 8px;
                margin: 10px;
            }
        """)
        self.connection_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.connection_status)
        
        # 画像表示エリア（全幅利用）
        self.image_label = QLabel()
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 3px dashed #dee2e6;
                border-radius: 12px;
                min-height: 500px;
            }
        """)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("📹 MQTTに接続後、\nリアルタイムカメラ映像が表示されます\n\nカメラ位置を調整してください\n\n画角が決まったら右上のEDITボタンを押してください")
        self.image_label.setScaledContents(True)
        layout.addWidget(self.image_label, 1)  # 拡張可能
        
        # FPS・解像度表示
        info_layout = QHBoxLayout()
        
        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #495057;
                padding: 8px 16px;
                background-color: #e9ecef;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        info_layout.addWidget(self.fps_label)
        
        self.resolution_label = QLabel("解像度: --")
        self.resolution_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #495057;
                padding: 8px 16px;
                background-color: #e9ecef;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        info_layout.addWidget(self.resolution_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        return panel
    
    def create_preview_panel(self):
        """リアルタイムプレビューパネル作成"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # プレビュータイトル
        preview_title = QLabel("📹 カメラプレビュー（画角調整用）")
        preview_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                padding: 8px;
                text-align: center;
            }
        """)
        preview_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(preview_title)
        
        # 画像表示エリア
        self.image_label = QLabel()
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px dashed #ccc;
                border-radius: 8px;
                min-height: 400px;
            }
        """)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("MQTTに接続後、\nリアルタイム画像が表示されます\n\nカメラアングルを調整してください")
        self.image_label.setScaledContents(True)
        layout.addWidget(self.image_label)
        
        # FPS表示
        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
                padding: 4px 8px;
                text-align: right;
            }
        """)
        self.fps_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.fps_label)
        
        return panel
    
    def auto_show_config_dialog(self):
        """ユーザー体験フロー: 起動時に自動でconfig.jsonダイアログ表示"""
        print("CONFIG MODE: 自動でconfig.jsonファイルダイアログを表示します")
        self.load_config_file()
    
    def load_config_file(self):
        """config.jsonファイル読み込み（デフォルト：デスクトップ/config）"""
        try:
            default_folder = r"C:\Users\table0\Desktop\config"
            
            # デフォルトフォルダが存在しない場合は作成
            import os
            if not os.path.exists(default_folder):
                try:
                    os.makedirs(default_folder, exist_ok=True)
                    print(f"Created default config folder: {default_folder}")
                except Exception as e:
                    print(f"Could not create config folder: {e}")
                    default_folder = "."
            
            print(f"CONFIG: Opening file dialog with default: {default_folder}")
            
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select config.json for bench connection",
                default_folder,
                "JSON files (*.json);;All files (*.*)"
            )
            
            if file_path:
                self.load_config_data(file_path)
            else:
                print("CONFIG: No config file selected")
                
        except Exception as e:
            print(f"CONFIG: Error opening file dialog: {e}")
    
    def load_config_data(self, file_path: str):
        """config.jsonデータ読み込みと処理"""
        try:
            import json
            print(f"CONFIG: Loading config file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            
            # ステータス更新
            bench_name = self.config_data.get("bench", "Unknown")
            mqtt_host = self.config_data.get("mqtt", {}).get("host", "Unknown")
            
            self.status_label.setText(f"✅ config.json読み込み完了\n\nベンチ: {bench_name}\nMQTT: {mqtt_host}")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #4caf50;
                    padding: 12px;
                    background-color: rgba(76, 175, 80, 0.1);
                    border-radius: 6px;
                    line-height: 1.4;
                }
            """)
            
            # ユーザー体験フロー: MQTTに接続してプレビュー開始
            self.connect_mqtt()
            
            print(f"CONFIG: Loaded config for bench: {bench_name}")
            
        except Exception as e:
            print(f"CONFIG: Error loading config: {e}")
            self.status_label.setText(f"❌ config.json読み込みエラー\n\n{str(e)}")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #f44336;
                    padding: 12px;
                    background-color: rgba(244, 67, 54, 0.1);
                    border-radius: 6px;
                    line-height: 1.4;
                }
            """)
    
    def connect_mqtt(self):
        """MQTTブローカーに接続してimageトピック購読"""
        try:
            print("CONFIG: Connecting to MQTT broker...")
            
            # ステータス更新
            self.mqtt_status_label.setText("🟢 MQTT: 接続中...")
            self.mqtt_status_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #ff9800;
                    padding: 8px 12px;
                    background-color: rgba(255, 152, 0, 0.1);
                    border-radius: 4px;
                    margin: 8px 0;
                }
            """)
            
            # MQTTサービスに設定を送信
            mqtt_config = self.config_data.get("mqtt", {})
            self.mqtt_service.set_config(mqtt_config)
            
            # 非同期接続開始
            success = self.mqtt_service.connect_async()
            if not success:
                self.mqtt_connection_failed("MQTT library not available")
            
        except Exception as e:
            print(f"CONFIG: MQTT connection error: {e}")
            self.mqtt_connection_failed(str(e))
    
    def on_mqtt_connected(self, connected: bool):
        """MQTT接続状態変更時の処理"""
        if connected:
            self.mqtt_connected()
        else:
            self.mqtt_connection_failed("Connection failed")
    
    def mqtt_connection_failed(self, error_message: str):
        """MQTT接続失敗処理"""
        self.mqtt_status_label.setText(f"🔴 MQTT: 接続失敗 - {error_message}")
        self.mqtt_status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #f44336;
                padding: 8px 12px;
                background-color: rgba(244, 67, 54, 0.1);
                border-radius: 4px;
                margin: 8px 0;
            }
        """)
        print(f"CONFIG: MQTT connection failed: {error_message}")
    
    def mqtt_connected(self):
        """MQTT接続完了処理"""
        self.mqtt_status_label.setText("🟢 MQTT: 接続完了 - imageトピック購読中")
        self.mqtt_status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #4caf50;
                padding: 8px 12px;
                background-color: rgba(76, 175, 80, 0.1);
                border-radius: 4px;
                margin: 8px 0;
            }
        """)
        
        # imageトピック購読開始
        self.mqtt_service.subscribe_image_topic()
        
        # FPS計測開始
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps_display)
        self.fps_timer.start(1000)  # 1秒ごと
        
        print("CONFIG: MQTT connected - Ready for camera adjustment")
    
    @Slot(str)
    def on_image_received(self, base64_image: str):
        """MQTT画像データ受信時の処理（メインスレッドで実行）"""
        try:
            import threading
            print(f"CONFIG: Received image in thread: {threading.current_thread().name}")
            
            # base64データをデコード
            image_data = base64.b64decode(base64_image)
            
            # QPixmapに変換
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                # FPS計算
                current_time = time.time()
                if hasattr(self, 'last_frame_time'):
                    frame_interval = current_time - self.last_frame_time
                    if frame_interval > 0:
                        self.current_fps = 1.0 / frame_interval
                self.last_frame_time = current_time
                
                # 画像表示（プレビューエリアにフィット）
                self.display_preview_image(pixmap)
                
            else:
                print("CONFIG: Failed to load image from MQTT data")
                
        except Exception as e:
            print(f"CONFIG: Error processing MQTT image: {e}")
    
    def display_preview_image(self, pixmap: QPixmap):
        """プレビュー画像を表示（適切なスケーリング）"""
        try:
            if self.image_label:
                # ラベルサイズに合わせてスケーリング（アスペクト比維持）
                label_size = self.image_label.size()
                scaled_pixmap = pixmap.scaled(
                    label_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.current_pixmap = pixmap
                
                # 解像度情報更新
                if hasattr(self, 'resolution_label'):
                    self.resolution_label.setText(f"解像度: {pixmap.width()}x{pixmap.height()}")
                
                # 接続状態更新
                if hasattr(self, 'connection_status'):
                    self.connection_status.setText("✅ MQTTライブプレビュー表示中 - カメラ位置を調整してください")
                    self.connection_status.setStyleSheet("""
                        QLabel {
                            font-size: 16px;
                            color: #28a745;
                            padding: 10px 20px;
                            text-align: center;
                            background-color: rgba(40, 167, 69, 0.1);
                            border-radius: 8px;
                            margin: 10px;
                        }
                    """)
                
        except Exception as e:
            print(f"CONFIG: Error displaying image: {e}")
    
    def update_fps_display(self):
        """FPS表示更新"""
        if hasattr(self, 'current_fps') and self.current_fps > 0:
            self.fps_label.setText(f"FPS: {self.current_fps:.1f}")
        else:
            self.fps_label.setText("FPS: 0.0")
    
    def get_config_data(self):
        """設定データを取得（EDIT移行時に使用）"""
        return self.config_data


class MonitorMainView(QWidget):
    """MONITORモード用リアルタイム画像表示＋パーツ検出結果表示ビュー"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent  # VehicleMonitorEditorへの参照
        self.mqtt_service = None  # MQTTサービス（親から設定される）
        
        # 画像表示関連
        self.current_pixmap = None
        self.current_fps = 0.0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        
        # パーツ検出結果管理
        self.detection_results = {}  # パーツ名: 検出結果の辞書
        self.vehicle_data = None  # VehicleDataへの参照
        
        self.setup_ui()
    
    def setup_ui(self):
        """MONITOR用UI設定"""
        # メインレイアウト
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # ===== 左側：画像表示エリア =====
        image_area = self.create_image_display_area()
        main_layout.addWidget(image_area, 3)  # 75%の幅
        
        # ===== 右側：検出結果パネル =====
        results_panel = self.create_detection_results_panel()
        main_layout.addWidget(results_panel, 1)  # 25%の幅
    
    def create_image_display_area(self):
        """画像表示エリア作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # ヘッダー：タイトルとFPS表示
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(20)
        
        # タイトル
        title_label = QLabel("📊 MONITOR MODE - リアルタイム画像監視")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin: 0;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # FPS・解像度表示
        self.fps_label = QLabel("FPS: 0.0 | 解像度: -- x --")
        self.fps_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7f8c8d;
                margin: 0;
                padding: 5px 10px;
                background-color: rgba(52, 152, 219, 0.1);
                border-radius: 4px;
            }
        """)
        header_layout.addWidget(self.fps_label)
        
        layout.addWidget(header_widget)
        
        # 画像表示ラベル
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                min-height: 400px;
                font-size: 14px;
                color: #7f8c8d;
            }
        """)
        self.image_label.setText("📷 MQTT画像ストリーム待機中...\n\nSTARTボタンを押して監視を開始してください")
        layout.addWidget(self.image_label)
        
        # ステータス表示
        self.status_label = QLabel("⏸️ 監視停止中")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #e74c3c;
                padding: 8px 12px;
                background-color: rgba(231, 76, 60, 0.1);
                border-radius: 4px;
                margin: 5px 0;
            }
        """)
        layout.addWidget(self.status_label)
        
        return widget
    
    def create_detection_results_panel(self):
        """検出結果パネル作成"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-left: 3px solid #3498db;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # パネルタイトル
        panel_title = QLabel("🔍 パーツ検出結果")
        panel_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                margin: 0 0 10px 0;
            }
        """)
        layout.addWidget(panel_title)
        
        # スクロール可能な結果表示エリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(8)
        
        # 初期メッセージ
        initial_msg = QLabel("監視開始後に\n検出結果が表示されます")
        initial_msg.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 12px;
                text-align: center;
                margin: 20px 0;
            }
        """)
        initial_msg.setAlignment(Qt.AlignCenter)
        self.results_layout.addWidget(initial_msg)
        
        scroll_area.setWidget(self.results_container)
        layout.addWidget(scroll_area)
        
        return widget
    
    def set_mqtt_service(self, mqtt_service):
        """MQTTサービスを設定"""
        # 既存の接続があれば切断
        if self.mqtt_service and hasattr(self.mqtt_service, 'image_received'):
            try:
                self.mqtt_service.image_received.disconnect(self.on_image_received)
                print("MONITOR: Disconnected from previous MQTT service")
            except TypeError:
                # 接続がない場合のエラーを無視
                pass
        
        self.mqtt_service = mqtt_service
        if mqtt_service:
            # 画像受信シグナルに接続
            try:
                mqtt_service.image_received.connect(self.on_image_received)
                print("MONITOR: Connected to MQTT image_received signal")
            except Exception as e:
                print(f"MONITOR: Failed to connect MQTT signal: {e}")
    
    def set_vehicle_data(self, vehicle_data):
        """VehicleDataを設定"""
        self.vehicle_data = vehicle_data
        
    def start_monitoring(self):
        """監視開始"""
        print("MONITOR: Starting monitoring process...")
        
        self.status_label.setText("🟢 監視実行中 - リアルタイム画像受信中")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #27ae60;
                padding: 8px 12px;
                background-color: rgba(39, 174, 96, 0.1);
                border-radius: 4px;
                margin: 5px 0;
            }
        """)
        
        # MQTTサービスのモードを設定
        if self.mqtt_service:
            self.mqtt_service.set_mode("MONITOR")
            print(f"MONITOR: MQTT service mode set, connected: {self.mqtt_service.is_connected()}")
        
        # FPS計測の初期化
        self.fps_counter = 0
        self.last_frame_time = time.time()
        self.current_fps = 0.0
        
        # FPS計測タイマー開始
        if hasattr(self, 'fps_timer'):
            self.fps_timer.stop()
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps_display)
        self.fps_timer.start(1000)
        
        print("MONITOR: Monitoring started - waiting for MQTT images...")
    
    def stop_monitoring(self):
        """監視停止"""
        self.status_label.setText("⏸️ 監視停止中")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #e74c3c;
                padding: 8px 12px;
                background-color: rgba(231, 76, 60, 0.1);
                border-radius: 4px;
                margin: 5px 0;
            }
        """)
        
        if hasattr(self, 'fps_timer'):
            self.fps_timer.stop()
        
        print("MONITOR: Monitoring stopped")
    
    @Slot(str)
    def on_image_received(self, base64_image: str):
        """MQTT画像データ受信時の処理（CONFIGと同様だが、パーツ検出処理も追加）（メインスレッドで実行）"""
        try:
            import threading
            print(f"MONITOR: Received image in thread: {threading.current_thread().name}")
            
            # base64データをデコード
            image_data = base64.b64decode(base64_image)
            print(f"MONITOR: Decoded image data size: {len(image_data)} bytes")
            
            # QPixmapに変換
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                print(f"MONITOR: Created pixmap {pixmap.width()}x{pixmap.height()}")
                
                # FPS計算
                current_time = time.time()
                if hasattr(self, 'last_frame_time'):
                    frame_interval = current_time - self.last_frame_time
                    if frame_interval > 0:
                        self.current_fps = 1.0 / frame_interval
                self.last_frame_time = current_time
                self.fps_counter += 1
                
                # 画像にパーツ検出結果をオーバーレイ
                annotated_pixmap = self.add_detection_overlay(pixmap)
                print(f"MONITOR: Added detection overlay")
                
                # 画像を表示
                self.display_monitor_image(annotated_pixmap)
                print("MONITOR: Image displayed successfully")
                
            else:
                print("MONITOR: Failed to load pixmap from image data")
                
        except Exception as e:
            print(f"MONITOR: Error processing image: {e}")
            import traceback
            traceback.print_exc()
    
    def add_detection_overlay(self, pixmap):
        """画像にパーツ検出結果をオーバーレイ表示"""
        if not self.vehicle_data:
            return pixmap
        
        # 新しいQPixmapを作成してオーバーレイ描画
        overlay_pixmap = QPixmap(pixmap.size())
        overlay_pixmap.fill(Qt.transparent)
        
        painter = QPainter(overlay_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 元画像を描画
        painter.drawPixmap(0, 0, pixmap)
        
        # パーツごとに検出結果を描画
        scale_x = pixmap.width() / 2304  # 元画像サイズからの縮尺
        scale_y = pixmap.height() / 1296
        
        # アイコン（Icon）パーツの描画
        for icon in self.vehicle_data.icon:
            result = self.detection_results.get(icon.name, False)
            self.draw_icon_overlay(painter, icon, result, scale_x, scale_y)
        
        # メーター（Meter）パーツの描画
        for meter in self.vehicle_data.meter:
            value = self.detection_results.get(meter.name, 0.0)
            self.draw_meter_overlay(painter, meter, value, scale_x, scale_y)
        
        # OCRパーツの描画
        for ocr in self.vehicle_data.ocr:
            text = self.detection_results.get(ocr.name, "")
            self.draw_ocr_overlay(painter, ocr, text, scale_x, scale_y)
        
        painter.end()
        return overlay_pixmap
    
    def draw_icon_overlay(self, painter, icon, detected, scale_x, scale_y):
        """アイコンパーツのオーバーレイ描画"""
        # 矩形座標をスケール変換
        x1 = int(icon.top_left.x * scale_x)
        y1 = int(icon.top_left.y * scale_y)
        x2 = int(icon.bottom_right.x * scale_x)
        y2 = int(icon.bottom_right.y * scale_y)
        
        # 検出結果に応じて色を変更
        if detected:
            color = QColor(255, 0, 0, 120)  # 赤色（検出あり）
            border_color = QColor(255, 0, 0, 255)
        else:
            color = QColor(0, 255, 0, 80)  # 緑色（検出なし）
            border_color = QColor(0, 255, 0, 200)
        
        # 矩形を描画
        painter.setBrush(color)
        painter.setPen(QPen(border_color, 2))
        painter.drawRect(x1, y1, x2-x1, y2-y1)
        
        # パーツ名とステータスを描画
        painter.setPen(QPen(Qt.white, 1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        status_text = "ON" if detected else "OFF"
        painter.drawText(x1 + 5, y1 + 15, f"{icon.name}: {status_text}")
    
    def draw_meter_overlay(self, painter, meter, value, scale_x, scale_y):
        """メーターパーツのオーバーレイ描画"""
        # 円の中心と半径をスケール変換
        center_x = int(meter.center.x * scale_x)
        center_y = int(meter.center.y * scale_y)
        radius = int(meter.radius * min(scale_x, scale_y))
        
        # 円を描画
        painter.setBrush(QColor(0, 100, 255, 60))
        painter.setPen(QPen(QColor(0, 100, 255, 200), 2))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # 現在値に対応する針を描画
        import math
        angle = value * 2 * math.pi - math.pi / 2  # 0を上方向として角度計算
        needle_end_x = center_x + int((radius - 10) * math.cos(angle))
        needle_end_y = center_y + int((radius - 10) * math.sin(angle))
        
        painter.setPen(QPen(Qt.red, 3))
        painter.drawLine(center_x, center_y, needle_end_x, needle_end_y)
        
        # パーツ名と値を描画
        painter.setPen(QPen(Qt.white, 1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(center_x - 30, center_y + radius + 20, f"{meter.name}: {value:.2f}")
    
    def draw_ocr_overlay(self, painter, ocr, text, scale_x, scale_y):
        """OCRパーツのオーバーレイ描画"""
        # 矩形座標をスケール変換
        x1 = int(ocr.top_left.x * scale_x)
        y1 = int(ocr.top_left.y * scale_y)
        x2 = int(ocr.bottom_right.x * scale_x)
        y2 = int(ocr.bottom_right.y * scale_y)
        
        # 矩形を描画
        painter.setBrush(QColor(255, 255, 0, 80))
        painter.setPen(QPen(QColor(255, 255, 0, 200), 2))
        painter.drawRect(x1, y1, x2-x1, y2-y1)
        
        # パーツ名とOCR結果を描画
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        display_text = text if text else "---"
        painter.drawText(x1 + 5, y1 + 15, f"{ocr.name}: {display_text}")
    
    def display_monitor_image(self, pixmap):
        """監視画像を表示"""
        try:
            if not self.image_label:
                print("MONITOR: Error - image_label is None")
                return
            
            # ラベルのサイズを確認
            label_size = self.image_label.size()
            print(f"MONITOR: Image label size: {label_size.width()} x {label_size.height()}")
            
            # ラベルサイズが小さすぎる場合は、親ウィジェットのサイズを使用
            if label_size.width() < 100 or label_size.height() < 100:
                # 親ウィジェットのサイズを取得
                parent_size = self.size()
                # 適切なサイズに調整（75%の幅、高さから他のウィジェット分を除く）
                target_width = int(parent_size.width() * 0.75 * 0.9)  # 左側75%の90%
                target_height = int(parent_size.height() * 0.7)  # 高さの70%
                label_size = QSize(max(target_width, 400), max(target_height, 300))
                print(f"MONITOR: Using adjusted size: {label_size.width()} x {label_size.height()}")
            
            # スケーリングして表示
            scaled_pixmap = pixmap.scaled(
                label_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            print(f"MONITOR: Scaled pixmap to {scaled_pixmap.width()} x {scaled_pixmap.height()}")
            
            self.image_label.setPixmap(scaled_pixmap)
            self.current_pixmap = pixmap
            
            # 解像度情報更新
            self.update_resolution_display(pixmap)
            print("MONITOR: Image label updated successfully")
            
        except Exception as e:
            print(f"MONITOR: Error displaying image: {e}")
            import traceback
            traceback.print_exc()
    
    def update_resolution_display(self, pixmap):
        """解像度表示更新"""
        if pixmap:
            width = pixmap.width()
            height = pixmap.height()
            self.fps_label.setText(f"FPS: {self.current_fps:.1f} | 解像度: {width} x {height}")
    
    def update_fps_display(self):
        """FPS表示更新（1秒ごと）"""
        if hasattr(self, 'fps_counter'):
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            
            if self.current_pixmap:
                self.update_resolution_display(self.current_pixmap)
    
    def update_detection_results(self, results_dict):
        """パーツ検出結果を更新"""
        self.detection_results = results_dict
        self.update_results_display()
    
    def update_results_display(self):
        """検出結果表示パネルを更新"""
        # 既存のウィジェットをクリア
        for i in reversed(range(self.results_layout.count())):
            child = self.results_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not self.detection_results:
            # 結果がない場合
            no_results = QLabel("検出結果なし")
            no_results.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-size: 12px;
                    text-align: center;
                    margin: 20px 0;
                }
            """)
            no_results.setAlignment(Qt.AlignCenter)
            self.results_layout.addWidget(no_results)
            return
        
        # 検出結果を表示
        for part_name, result in self.detection_results.items():
            result_widget = self.create_result_item(part_name, result)
            self.results_layout.addWidget(result_widget)
        
        # スペーサーを追加
        self.results_layout.addStretch()
    
    def create_result_item(self, part_name, result):
        """個別の検出結果アイテムを作成"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 6px;
                margin: 2px 0;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # パーツ名
        name_label = QLabel(part_name)
        name_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 13px;
                color: #2c3e50;
            }
        """)
        layout.addWidget(name_label)
        
        # 結果値
        if isinstance(result, bool):
            # アイコン系（bool値）
            status = "🔴 ON" if result else "🟢 OFF"
            color = "#e74c3c" if result else "#27ae60"
        elif isinstance(result, (int, float)):
            # メーター系（数値）
            status = f"📊 {result:.2f}"
            color = "#3498db"
        else:
            # OCR系（文字列）
            status = f"📝 {result}" if result else "📝 ---"
            color = "#f39c12"
        
        result_label = QLabel(status)
        result_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {color};
                background-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1);
                padding: 4px 8px;
                border-radius: 4px;
            }}
        """)
        layout.addWidget(result_label)
        
        return widget


class VehicleMonitorEditor(QMainWindow):
    """3モード遷移対応メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vehicle Monitor - 3Mode System")
        self.setGeometry(100, 100, 1200, 800)
        self.showMaximized()
        
        # モード管理
        self.current_mode = AppMode.CONFIG
        self.data_loader = FileDataLoader()  # テスト用、後で切り替え可能
        
        # EDIT用コンポーネント（main.pyの機能保持）
        self.canvas = ImageCanvas()
        self.config_data: Optional[ConfigData] = None
        self.vehicle_data: Optional[VehicleData] = None
        
        # モード別ビューを作成（親ウィンドウ参照を渡す）
        self.config_view = ConfigMainView(self)
        self.monitor_view = MonitorMainView()
        
        # UIをセットアップ
        self.setup_ui()
        
        # サイドパネル初期化（EDIT用）
        self.setup_side_panel()
        
        # 初期モードをCONFIGに設定
        self.switch_to_mode(AppMode.CONFIG)
        
        # 初期ナビゲーションボタン設定
        self.update_navigation_buttons()
        
    def setup_ui(self):
        """3モード対応UIセットアップ"""
        # メインウィジェットとレイアウト
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ヘッダー作成
        self.create_header(main_layout)
        
        # メインコンテンツエリア
        self.main_content_area = QWidget()
        main_layout.addWidget(self.main_content_area)
        
        # フッター作成
        self.create_footer(main_layout)
    
    def create_header(self, main_layout):
        """ヘッダー作成（統一レイアウト：左右2セクション）"""
        header_widget = QWidget()
        header_widget.setFixedHeight(80)
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border-bottom: 3px solid #34495e;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_layout.setSpacing(30)  # セクション間の間隔
        
        # ===== 左セクション =====
        left_section = QWidget()
        left_layout = QHBoxLayout(left_section)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)
        
        # サイドバー開閉ボタン
        self.sidebar_btn = QPushButton("≡")
        self.sidebar_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                border: 2px solid #4a6741;
                padding: 10px 15px;
                border-radius: 6px;
                font-size: 20px;
                font-weight: bold;
                min-width: 50px;
                min-height: 45px;
                max-height: 45px;
            }
            QPushButton:hover {
                background-color: #4a6741;
            }
        """)
        self.sidebar_btn.clicked.connect(self.toggle_sidebar)
        left_layout.addWidget(self.sidebar_btn)
        
        # モード表示インジケータ
        self.mode_labels = {}
        mode_icons = {"CONFIG": "⚙️", "EDIT": "✏️", "MONITOR": "📊"}
        for mode in AppMode:
            icon = mode_icons.get(mode.value, "")
            mode_label = QLabel(f"{icon} {mode.value}")
            mode_label.setStyleSheet("""
                QLabel {
                    color: #bdc3c7;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 6px 12px;
                    margin: 0 3px;
                    border-radius: 4px;
                    background-color: rgba(255,255,255,0.1);
                }
            """)
            self.mode_labels[mode] = mode_label
            left_layout.addWidget(mode_label)
        
        left_layout.addStretch()
        header_layout.addWidget(left_section, 1)
        
        # ===== 右セクション =====
        right_section = QWidget()
        right_layout = QHBoxLayout(right_section)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)
        
        # 戻るボタン（インスタンス変数に変更）
        self.prev_btn = QPushButton("◀ 戻る")
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: 2px solid #2980b9;
                padding: 8px 15px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                min-width: 65px;
                max-width: 65px;
                min-height: 35px;
                max-height: 35px;
            }
            QPushButton:hover {
                background-color: #2980b9;
                border-color: #21618c;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                border-color: #95a5a6;
                color: #bdc3c7;
            }
        """)
        self.prev_btn.clicked.connect(self.previous_mode)
        right_layout.addWidget(self.prev_btn)
        
        # 中央タイトル（車種情報）
        self.title_label = QLabel("🚗 XTRAIL")
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 0 20px;
                background-color: rgba(255,255,255,0.1);
                border-radius: 8px;
                min-height: 45px;
            }
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.title_label)
        
        # 進むボタン（インスタンス変数に変更）
        self.next_btn = QPushButton("進む ▶")
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: 2px solid #c0392b;
                padding: 8px 15px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                min-width: 65px;
                max-width: 65px;
                min-height: 35px;
                max-height: 35px;
            }
            QPushButton:hover {
                background-color: #c0392b;
                border-color: #a93226;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                border-color: #95a5a6;
                color: #bdc3c7;
            }
        """)
        self.next_btn.clicked.connect(self.next_mode)
        right_layout.addWidget(self.next_btn)
        
        header_layout.addWidget(right_section, 2)
        main_layout.addWidget(header_widget)
    
    def toggle_sidebar(self):
        """サイドバーの開閉を切り替え（モード別対応）"""
        if self.current_mode == AppMode.CONFIG:
            # CONFIGモードのサイドバー制御
            if hasattr(self.config_view, 'config_dock') and self.config_view.config_dock:
                if self.config_view.config_dock.isVisible():
                    self.config_view.config_dock.hide()
                    self.sidebar_btn.setText("≡")
                else:
                    self.config_view.config_dock.show()
                    self.sidebar_btn.setText("×")
        elif self.current_mode == AppMode.EDIT:
            # EDITモードのサイドパネル制御
            if hasattr(self, 'side_panel') and self.side_panel:
                if self.side_panel.isVisible():
                    self.side_panel.hide()
                    self.sidebar_btn.setText("≡")
                else:
                    self.side_panel.show()
                    self.sidebar_btn.setText("×")
    
    def create_footer(self, main_layout):
        """フッター作成（インジケータ・デバッグ情報表示）"""
        self.status_bar = self.statusBar()
        self.status_bar.setFixedHeight(50)  # 高さを拡大
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #34495e;
                color: white;
                font-size: 12px;
                border-top: 3px solid #2c3e50;
                padding: 5px 20px;
            }
            QStatusBar QLabel {
                margin-right: 15px;
                padding: 2px 8px;
                border-radius: 3px;
            }
        """)
        
        # 接続状態インジケータを作成
        self.mqtt_indicator = QLabel("MQTT: 未接続")
        self.mqtt_indicator.setStyleSheet("background-color: #e74c3c; color: white;")
        self.status_bar.addPermanentWidget(self.mqtt_indicator)
        
        self.rest_indicator = QLabel("REST: 未接続")
        self.rest_indicator.setStyleSheet("background-color: #e74c3c; color: white;")
        self.status_bar.addPermanentWidget(self.rest_indicator)
        
        self.ros2_indicator = QLabel("ROS2: 未接続")
        self.ros2_indicator.setStyleSheet("background-color: #e74c3c; color: white;")
        self.status_bar.addPermanentWidget(self.ros2_indicator)
        
        self.update_status_bar()
    
    def update_navigation_buttons(self):
        """現在のモードに基づいてナビゲーションボタンを更新"""
        if not hasattr(self, 'prev_btn') or not hasattr(self, 'next_btn'):
            return  # ボタンが初期化されていない場合はスキップ
        
        if self.current_mode == AppMode.CONFIG:
            # CONFIGモード: 戻るボタン無効化、進むボタンは"EDIT"
            self.prev_btn.setEnabled(False)
            self.prev_btn.setText("◀ ─")  # 無効化を視覚的に表現
            
            self.next_btn.setEnabled(True)
            self.next_btn.setText("EDIT ▶")
            # 通常の赤色スタイル
            self.next_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: 2px solid #c0392b;
                    padding: 8px 15px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    min-width: 65px;
                    max-width: 65px;
                    min-height: 35px;
                    max-height: 35px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                    border-color: #a93226;
                }
                QPushButton:pressed {
                    background-color: #a93226;
                }
            """)
            
        elif self.current_mode == AppMode.EDIT:
            # EDITモード: 両ボタン有効、前後のモードを表示
            self.prev_btn.setEnabled(True)
            self.prev_btn.setText("◀ CONFIG")
            
            self.next_btn.setEnabled(True)
            self.next_btn.setText("MONITOR ▶")
            # 通常の赤色スタイル
            self.next_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: 2px solid #c0392b;
                    padding: 8px 15px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    min-width: 75px;
                    max-width: 75px;
                    min-height: 35px;
                    max-height: 35px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                    border-color: #a93226;
                }
                QPushButton:pressed {
                    background-color: #a93226;
                }
            """)
            
        elif self.current_mode == AppMode.MONITOR:
            # MONITORモード: 戻るボタンは"EDIT"、進むボタンは"START"
            self.prev_btn.setEnabled(True)
            self.prev_btn.setText("◀ EDIT")
            
            self.next_btn.setEnabled(True)
            self.next_btn.setText("START")
            # STARTボタンは緑色スタイル
            self.next_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: 2px solid #229954;
                    padding: 8px 15px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    min-width: 65px;
                    max-width: 65px;
                    min-height: 35px;
                    max-height: 35px;
                }
                QPushButton:hover {
                    background-color: #229954;
                    border-color: #1e8449;
                }
                QPushButton:pressed {
                    background-color: #1e8449;
                }
            """)
    
    def start_monitoring(self):
        """監視開始処理（STARTボタンの機能）"""
        try:
            print("MONITOR: Starting monitoring process...")
            
            # MONITORビューにMQTTサービスとvehicle.jsonデータを設定
            if hasattr(self.config_view, 'mqtt_service'):
                self.monitor_view.set_mqtt_service(self.config_view.mqtt_service)
            
            # vehicle.jsonデータを設定
            if self.vehicle_data:
                self.monitor_view.set_vehicle_data(self.vehicle_data)
            
            # 監視開始
            self.monitor_view.start_monitoring()
            
            # ダミーデータで検出結果テスト（実際のシステムではREST APIまたはMQTTから取得）
            self.simulate_detection_results()
            
            # ステータスバー更新
            self.statusBar().showMessage("🟢 監視実行中 - パーツ検出結果をリアルタイム表示中")
            
        except Exception as e:
            print(f"MONITOR: Failed to start monitoring: {e}")
            self.statusBar().showMessage(f"❌ 監視開始エラー: {e}")
    
    def simulate_detection_results(self):
        """ダミーの検出結果をシミュレート（テスト用）"""
        import threading
        import time
        import random
        
        def update_detection_loop():
            """検出結果を定期的に更新"""
            while hasattr(self, 'monitoring_active') and self.monitoring_active:
                try:
                    # ダミーデータ生成
                    results = {}
                    
                    if self.vehicle_data:
                        # アイコンパーツ（bool値）
                        for icon in self.vehicle_data.icon:
                            results[icon.name] = random.choice([True, False])
                        
                        # メーターパーツ（float値）
                        for meter in self.vehicle_data.meter:
                            results[meter.name] = random.uniform(0.0, 1.0)
                        
                        # OCRパーツ（文字列）
                        for ocr in self.vehicle_data.ocr:
                            if ocr.type == "int":
                                results[ocr.name] = str(random.randint(0, 99))
                            else:
                                results[ocr.name] = f"Value_{random.randint(1, 999)}"
                    
                    # 検出結果を更新
                    self.monitor_view.update_detection_results(results)
                    
                    time.sleep(2)  # 2秒ごとに更新
                    
                except Exception as e:
                    print(f"Detection simulation error: {e}")
                    break
        
        # 監視フラグを設定して開始
        self.monitoring_active = True
        detection_thread = threading.Thread(target=update_detection_loop, daemon=True)
        detection_thread.start()
    
    def switch_to_mode(self, mode: AppMode):
        """モード切り替え"""
        # MONITORモードから他のモードに切り替える際は監視を停止
        if self.current_mode == AppMode.MONITOR and mode != AppMode.MONITOR:
            self.stop_monitoring()
        
        self.current_mode = mode
        
        # メインコンテンツエリアをクリア
        if self.main_content_area.layout():
            for i in reversed(range(self.main_content_area.layout().count())):
                self.main_content_area.layout().itemAt(i).widget().setParent(None)
        else:
            layout = QHBoxLayout(self.main_content_area)
            layout.setContentsMargins(0, 0, 0, 0)
        
        # モード別ビューを設定
        if mode == AppMode.CONFIG:
            self.main_content_area.layout().addWidget(self.config_view)
            # CONFIGモードではサイドパネル非表示
            if hasattr(self, 'side_panel'):
                self.side_panel.hide()
        elif mode == AppMode.EDIT:
            self.setup_edit_mode()
        elif mode == AppMode.MONITOR:
            self.main_content_area.layout().addWidget(self.monitor_view)
            # MONITORモードではサイドパネル非表示
            if hasattr(self, 'side_panel'):
                self.side_panel.hide()
        
        # ヘッダーのモード表示を更新
        self.update_mode_display()
        self.update_navigation_buttons()  # ナビゲーションボタンを更新
        self.update_status_bar()
    
    def stop_monitoring(self):
        """監視停止処理"""
        try:
            print("MONITOR: Stopping monitoring process...")
            
            # 監視フラグを無効化
            if hasattr(self, 'monitoring_active'):
                self.monitoring_active = False
            
            # MONITORビューの監視停止
            self.monitor_view.stop_monitoring()
            
            # ステータスバー更新
            self.statusBar().showMessage("⏸️ 監視停止")
            
        except Exception as e:
            print(f"MONITOR: Failed to stop monitoring: {e}")
            self.statusBar().showMessage(f"❌ 監視停止エラー: {e}")
    
    def setup_edit_mode(self):
        """EDITモードのセットアップ（CONFIGモードと同じレイアウト構造）"""
        # CONFIGモードと同じ統一レイアウトを使用
        # キャンバスをメインコンテンツエリアに配置
        self.main_content_area.layout().addWidget(self.canvas)
        self.canvas.show()
        
        # サイドパネルを表示（EDITモード専用操作パネル）
        if hasattr(self, 'side_panel'):
            self.side_panel.show()
    
    
    def next_mode(self):
        """次のモードに遷移または監視開始"""
        if self.current_mode == AppMode.CONFIG:
            # CONFIG→EDIT遷移時にデータロード
            self.transition_to_edit_mode()
        elif self.current_mode == AppMode.EDIT:
            # EDIT→MONITOR遷移
            self.switch_to_mode(AppMode.MONITOR)
        elif self.current_mode == AppMode.MONITOR:
            # MONITORモードでは監視開始
            self.start_monitoring()
    
    def previous_mode(self):
        """前のモードに遷移"""
        modes = list(AppMode)
        current_index = modes.index(self.current_mode)
        prev_index = (current_index - 1) % len(modes)
        self.switch_to_mode(modes[prev_index])
    
    def transition_to_edit_mode(self):
        """CONFIG→EDIT遷移時のデータ受け渡し（ユーザー体験フロー対応）"""
        try:
            print("CONFIG→EDIT移行: ユーザー体験フローを実行中...")
            
            # CONFIGモードからconfig.jsonデータを取得
            config_data = None
            if hasattr(self.config_view, 'get_config_data'):
                config_data = self.config_view.get_config_data()
            
            if not config_data:
                print("ERROR: config.jsonデータが見つかりません")
                return
            
            # ユーザー体験フロー: Step 10 - config.jsonをMQTTに送信
            self.send_config_to_mqtt(config_data)
            
            # ユーザー体験フロー: Step 11 - RestAPIでfull_imageを取得
            image_data = self.get_full_image_from_rest_api(config_data)
            
            # config.jsonデータを設定
            self.config_data = ConfigData(
                mqtt_host=config_data.get("mqtt", {}).get("host", ""),
                mqtt_port=config_data.get("mqtt", {}).get("port", ""),
                mqtt_ws_port=config_data.get("mqtt", {}).get("wsPort", ""),
                rest_api_host=config_data.get("RestAPI", {}).get("host", ""),
                rest_api_port=config_data.get("RestAPI", {}).get("port", ""),
                camera_width=config_data.get("camera", {}).get("width", 2304),
                camera_height=config_data.get("camera", {}).get("height", 1296),
                camera_scale=config_data.get("camera", {}).get("scale", 1.0),
                frame=config_data.get("frame", 0),
                bench=config_data.get("bench", ""),
                path=config_data.get("path", "")
            )
            
            # キャンバスのフルサイズ設定
            self.canvas.set_full_image_size(
                self.config_data.camera_width,
                self.config_data.camera_height
            )
            
            # フルサイズ画像を表示
            if image_data:
                # テスト用: データから一時ファイルに保存して読み込み
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                    tmp_file.write(image_data)
                    tmp_path = tmp_file.name
                
                self.canvas.load_image(tmp_path)
                # 一時ファイルを削除
                os.unlink(tmp_path)
            
            # EDITモードに切り替え
            self.switch_to_mode(AppMode.EDIT)
            
            # EDITモードでvehicle.jsonを自動読み込み
            vehicle_json_path = "C:/Users/table0/Desktop/Vehicles/vehicle.json"
            if os.path.exists(vehicle_json_path):
                self.load_vehicle_file(vehicle_json_path)
            
        except Exception as e:
            print(f"CONFIG→EDIT遷移エラー: {e}")
            self.switch_to_mode(AppMode.EDIT)  # エラーでもEDITモードに切り替え
    
    def send_config_to_mqtt(self, config_data: dict):
        """ユーザー体験フロー Step 10: config.jsonをMQTTに送信"""
        try:
            print("Step 10: config.jsonをMQTTに送信中...")
            
            # TODO: 実際のMQTT送信実装
            # 暫定実装
            mqtt_host = config_data.get("mqtt", {}).get("host", "")
            bench_name = config_data.get("bench", "Unknown")
            
            print(f"MQTT送信先: {mqtt_host}")
            print(f"送信データ: ベンチ={bench_name}, カメラ設定={config_data.get('camera', {})}")
            
            # シミュレーション
            import time
            time.sleep(0.5)  # 送信完了待機
            
            print("✅ config.json送信完了")
            
        except Exception as e:
            print(f"MQTT送信エラー: {e}")
    
    def get_full_image_from_rest_api(self, config_data: dict) -> Optional[bytes]:
        """ユーザー体験フロー Step 11: RestAPIでfull_imageを取得"""
        try:
            print("Step 11: RestAPIでfull_imageを取得中...")
            
            rest_api_host = config_data.get("RestAPI", {}).get("host", "")
            rest_api_port = config_data.get("RestAPI", {}).get("port", "8000")
            
            if not rest_api_host:
                print("ERROR: RestAPI host情報がありません")
                return None
            
            # full_image取得URL構築
            full_image_url = f"http://{rest_api_host}:{rest_api_port}/full_image"
            print(f"RestAPI取得先: {full_image_url}")
            
            # TODO: 実際のREST API呼び出し実装
            # 暫定実装（テスト用の固定パス）
            test_image_path = r"C:\Users\table0\Desktop\Vehicles\vehicle.json"  # vehicle.jsonと同じフォルダの画像
            test_image_dir = os.path.dirname(test_image_path)
            
            # テスト用画像ファイルを探す
            for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                test_file = os.path.join(test_image_dir, f"test_image{ext}")
                if os.path.exists(test_file):
                    print(f"テスト用画像を使用: {test_file}")
                    with open(test_file, 'rb') as f:
                        return f.read()
            
            print("⚠️  テスト用画像が見つかりません（full_image取得スキップ）")
            return None
            
        except Exception as e:
            print(f"RestAPI取得エラー: {e}")
            return None
    
    def update_mode_display(self):
        """ヘッダーのモード表示を更新（改善版）"""
        mode_icons = {"CONFIG": "⚙️", "EDIT": "✏️", "MONITOR": "📊"}
        for mode, label in self.mode_labels.items():
            icon = mode_icons.get(mode.value, "")
            if mode == self.current_mode:
                label.setText(f"{icon} {mode.value}")
                label.setStyleSheet("""
                    QLabel {
                        color: white;
                        font-size: 16px;
                        font-weight: bold;
                        padding: 8px 15px;
                        margin: 0 8px;
                        background-color: #e74c3c;
                        border-radius: 6px;
                        border: 2px solid #c0392b;
                    }
                """)
            else:
                label.setText(f"{icon} {mode.value}")
                label.setStyleSheet("""
                    QLabel {
                        color: #bdc3c7;
                        font-size: 16px;
                        font-weight: bold;
                        padding: 8px 15px;
                        margin: 0 8px;
                        border-radius: 6px;
                        background-color: rgba(255,255,255,0.1);
                    }
                """)
    
    def update_status_bar(self):
        """ステータスバーを更新（デバッグ情報）"""
        # デバッグ情報とシステム情報
        mode_icons = {"CONFIG": "⚙️", "EDIT": "✏️", "MONITOR": "📊"}
        current_icon = mode_icons.get(self.current_mode.value, "")
        
        vehicle_name = self.vehicle_data.name if self.vehicle_data else "未選択"
        parts_count = len(self.canvas.shapes) if hasattr(self.canvas, 'shapes') else 0
        
        # 簡潔なデバッグ情報
        debug_info = f"{current_icon} {self.current_mode.value} | 🚗 {vehicle_name} | 🔧 {parts_count}個"
        
        # 画像情報
        if hasattr(self.canvas, 'original_pixmap') and self.canvas.original_pixmap:
            img_w = self.canvas.original_pixmap.width()
            img_h = self.canvas.original_pixmap.height()
            debug_info += f" | 🖼️ {img_w}×{img_h}"
        
        self.status_bar.showMessage(debug_info)
        
        # タイトルラベルも更新（車種情報）
        if hasattr(self, 'title_label'):
            vehicle_display = f"🚗 {vehicle_name}" if vehicle_name != "未選択" else "🚗 Vehicle Monitor"
            self.title_label.setText(vehicle_display)
        
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
            self, "Vehicle JSONを開く", "C:/Users/table0/Desktop/Vehicles/",
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
    
    def add_shape_to_canvas(self, shape):
        """図形をキャンバスに追加（BarShapeItemの場合は複数アイテムに対応）"""
        if isinstance(shape, BarShapeItem):
            # BarShapeItemの場合は両方のアイテムを追加
            self.canvas.scene.addItem(shape.rect_item)
            self.canvas.scene.addItem(shape.divider_line)
        else:
            # 通常の図形の場合
            self.canvas.scene.addItem(shape.get_item())
        
        self.canvas.shapes.append(shape)
    
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
            self.add_shape_to_canvas(shape)
        
        # メーター（円形・バー）を追加
        for meter in self.vehicle_data.meter:
            x = meter.center.x - meter.radius
            y = meter.center.y - meter.radius
            w = meter.radius * 2
            h = meter.radius * 2
            
            # shape種別に応じて作成
            if meter.shape == "bar":
                # バー形状の場合（circumferenceポイントも渡す）
                shape = BarShapeItem(x, y, w, h, current_scale, ShapeCategory.METER, True, meter.circumference)
            else:
                # 円形の場合（circumferenceポイントも渡す）
                shape = ResizableEllipseItem(x, y, w, h, current_scale, ShapeCategory.METER, True, meter.circumference)
                
            shape.name = meter.name
            self.add_shape_to_canvas(shape)
            
            # circumferenceポイントの表示を更新（円形・バー両方）
            if hasattr(shape, 'update_circumference_display'):
                shape.update_circumference_display()
        
        # OCR（矩形）を追加
        for ocr in self.vehicle_data.ocr:
            x = ocr.top_left.x
            y = ocr.top_left.y
            w = ocr.bottom_right.x - ocr.top_left.x
            h = ocr.bottom_right.y - ocr.top_left.y
            
            # 計算したスケールで作成
            shape = ResizableRectItem(x, y, w, h, current_scale, ShapeCategory.OCR, True)
            shape.name = ocr.name
            self.add_shape_to_canvas(shape)
        
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