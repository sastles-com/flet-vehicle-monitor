import sys
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, 
                               QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
                               QGraphicsEllipseItem, QVBoxLayout, QHBoxLayout,
                               QWidget, QPushButton, QFileDialog, QToolBar,
                               QLabel, QComboBox, QSpinBox)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QSizeF
from PySide6.QtGui import QPixmap, QPen, QBrush, QColor, QWheelEvent, QPainter


class ShapeType(Enum):
    RECTANGLE = "rectangle"
    CIRCLE = "circle"


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
                 scene_scale: float = 1.0):
        self.handles: List[QGraphicsRectItem] = []
        self.handle_size = 8
        self.scene_scale = scene_scale
        self.is_selected = False
        self.name = f"Shape_{id(self)}"
        
    def create_handles(self):
        """リサイズハンドルを作成"""
        for handle in self.handles:
            if handle.scene():
                handle.scene().removeItem(handle)
        self.handles.clear()
        
        if not self.is_selected:
            return
            
        # 8つのハンドル位置を計算
        rect = self.get_item().boundingRect()
        positions = [
            (rect.left(), rect.top()),      # 左上
            (rect.center().x(), rect.top()),  # 上中央
            (rect.right(), rect.top()),     # 右上
            (rect.right(), rect.center().y()),  # 右中央
            (rect.right(), rect.bottom()),  # 右下
            (rect.center().x(), rect.bottom()),  # 下中央
            (rect.left(), rect.bottom()),   # 左下
            (rect.left(), rect.center().y()),  # 左中央
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
            handle.setZValue(1000)
            handle.setFlag(QGraphicsItem.ItemIsMovable, True)
            
            if self.get_item().scene():
                self.get_item().scene().addItem(handle)
            self.handles.append(handle)
    
    def set_selected(self, selected: bool):
        """選択状態を設定"""
        self.is_selected = selected
        self.create_handles()
        
    def get_item(self) -> QGraphicsItem:
        """実際のグラフィックアイテムを返す（サブクラスで実装）"""
        raise NotImplementedError
        
    def get_original_coords(self, scale: float) -> Tuple[float, float, float, float]:
        """元画像の座標系での位置を返す"""
        rect = self.get_item().boundingRect()
        pos = self.get_item().pos()
        return (
            (pos.x() + rect.x()) / scale,
            (pos.y() + rect.y()) / scale,
            rect.width() / scale,
            rect.height() / scale
        )


class ResizableRectItem(ResizableGraphicsItem):
    """リサイズ可能な矩形"""
    
    def __init__(self, x: float, y: float, width: float, height: float,
                 scene_scale: float = 1.0):
        super().__init__(x, y, width, height, scene_scale)
        self.rect_item = QGraphicsRectItem(0, 0, width, height)
        self.rect_item.setPos(x, y)
        self.rect_item.setPen(QPen(QColor(255, 0, 0), 2))
        self.rect_item.setBrush(QBrush(QColor(255, 0, 0, 50)))
        self.rect_item.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.rect_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.shape_type = ShapeType.RECTANGLE
        
    def get_item(self) -> QGraphicsRectItem:
        return self.rect_item


class ResizableEllipseItem(ResizableGraphicsItem):
    """リサイズ可能な円"""
    
    def __init__(self, x: float, y: float, width: float, height: float,
                 scene_scale: float = 1.0):
        super().__init__(x, y, width, height, scene_scale)
        self.ellipse_item = QGraphicsEllipseItem(0, 0, width, height)
        self.ellipse_item.setPos(x, y)
        self.ellipse_item.setPen(QPen(QColor(0, 0, 255), 2))
        self.ellipse_item.setBrush(QBrush(QColor(0, 0, 255, 50)))
        self.ellipse_item.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.ellipse_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.shape_type = ShapeType.CIRCLE
        
    def get_item(self) -> QGraphicsEllipseItem:
        return self.ellipse_item


class ImageCanvas(QGraphicsView):
    """画像表示とラバーバンド機能を持つキャンバス"""
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        self.image_item = None
        self.original_pixmap = None
        self.current_scale = 1.0
        self.shapes: List[ResizableGraphicsItem] = []
        self.drawing_mode = None
        self.start_pos = None
        self.temp_item = None
        self.selected_shape = None
        
        # ビューの設定
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        
    def load_image(self, file_path: str):
        """画像を読み込んでウィンドウサイズに合わせる"""
        self.original_pixmap = QPixmap(file_path)
        if self.image_item:
            self.scene.removeItem(self.image_item)
            
        self.image_item = self.scene.addPixmap(self.original_pixmap)
        self.fit_image_to_view()
        
    def fit_image_to_view(self):
        """画像をビューにフィット"""
        if not self.original_pixmap:
            return
            
        view_rect = self.viewport().rect()
        scene_rect = QRectF(self.original_pixmap.rect())
        
        # アスペクト比を保持してスケール計算
        x_ratio = view_rect.width() / scene_rect.width()
        y_ratio = view_rect.height() / scene_rect.height()
        self.current_scale = min(x_ratio, y_ratio) * 0.95
        
        self.resetTransform()
        self.scale(self.current_scale, self.current_scale)
        self.centerOn(self.image_item)
        
    def resizeEvent(self, event):
        """ウィンドウリサイズ時に画像を再フィット"""
        super().resizeEvent(event)
        self.fit_image_to_view()
        
    def wheelEvent(self, event: QWheelEvent):
        """マウスホイールでズーム"""
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        
        # 現在のスケールを保存
        old_pos = self.mapToScene(event.position().toPoint())
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            
        self.scale(zoom_factor, zoom_factor)
        self.current_scale *= zoom_factor
        
        # マウス位置を中心にズーム
        new_pos = self.mapToScene(event.position().toPoint())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
        
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
        else:
            # 図形の選択処理
            scene_pos = self.mapToScene(event.pos())
            item = self.scene.itemAt(scene_pos, self.transform())
            
            # 既存の選択をクリア
            if self.selected_shape:
                self.selected_shape.set_selected(False)
                self.selected_shape = None
                
            # 新しい図形を選択
            for shape in self.shapes:
                if shape.get_item() == item:
                    self.selected_shape = shape
                    shape.set_selected(True)
                    break
                    
            super().mousePressEvent(event)
            
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
                                            self.current_scale)
                elif self.drawing_mode == "circle":
                    shape = ResizableEllipseItem(rect.x(), rect.y(),
                                                rect.width(), rect.height(),
                                                self.current_scale)
                else:
                    shape = None
                    
                if shape:
                    self.scene.addItem(shape.get_item())
                    self.shapes.append(shape)
                    
            # 一時アイテムを削除
            self.scene.removeItem(self.temp_item)
            self.temp_item = None
            self.start_pos = None
            
        super().mouseReleaseEvent(event)
        
    def get_shapes_data(self) -> List[Dict]:
        """すべての図形データを取得"""
        shapes_data = []
        for shape in self.shapes:
            x, y, w, h = shape.get_original_coords(self.current_scale)
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
        self.setGeometry(100, 100, 1200, 800)
        
        # キャンバスを作成
        self.canvas = ImageCanvas()
        
        # UIをセットアップ
        self.setup_ui()
        
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
        
        # 保存・読み込みボタン
        save_json_action = toolbar.addAction("JSONを保存")
        save_json_action.triggered.connect(self.save_json)
        
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
                "image_width": self.canvas.original_pixmap.width() if self.canvas.original_pixmap else 0,
                "image_height": self.canvas.original_pixmap.height() if self.canvas.original_pixmap else 0,
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
                x = shape_data["x"] * self.canvas.current_scale
                y = shape_data["y"] * self.canvas.current_scale
                w = shape_data["width"] * self.canvas.current_scale
                h = shape_data["height"] * self.canvas.current_scale
                
                if shape_data["type"] == "rectangle":
                    shape = ResizableRectItem(x, y, w, h, self.canvas.current_scale)
                elif shape_data["type"] == "circle":
                    shape = ResizableEllipseItem(x, y, w, h, self.canvas.current_scale)
                else:
                    continue
                    
                shape.name = shape_data.get("name", shape.name)
                self.canvas.scene.addItem(shape.get_item())
                self.canvas.shapes.append(shape)
                
            self.statusBar().showMessage(f"JSONを読み込みました: {file_path}")


def main():
    app = QApplication(sys.argv)
    window = VehicleMonitorEditor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()