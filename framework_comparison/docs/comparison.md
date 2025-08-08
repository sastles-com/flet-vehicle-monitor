# フレームワーク比較：Vehicle Monitor編集機能

## 要件
1. フルサイズ画像をウィンドウに合わせて表示
2. ラバーバンドでマウス操作による図形の描画・編集
3. 画像の拡大縮小に図形が追従
4. フルサイズ画像のピクセル座標でJSON保存

## 実装比較

### 1. **PyQt/PySide6** ⭐推奨
```python
# vehicle_monitor_pyqt.py として実装済み
```

**メリット:**
- ✅ QGraphicsViewでラバーバンド機能が標準実装
- ✅ 図形の選択・移動・リサイズが高性能
- ✅ 座標変換が組み込み（mapToScene/mapFromScene）
- ✅ ズーム・パン操作が滑らか
- ✅ リアルタイムプレビューが高速

**デメリット:**
- ❌ ライセンス（商用利用時）
- ❌ 学習コスト高め

**実行方法:**
```bash
pip install PySide6
python vehicle_monitor_pyqt.py
```

### 2. **Flet** (現在の実装)

**メリット:**
- ✅ Webデプロイ可能
- ✅ モダンなUI
- ✅ 学習が簡単

**デメリット:**
- ❌ ラバーバンド機能を自作必要
- ❌ マウス操作の精度が劣る
- ❌ 座標変換を手動実装必要

**改善案（Flet継続の場合）:**
```python
import flet as ft
from PIL import Image
import json

class VehicleMonitorFlet:
    def __init__(self):
        self.shapes = []
        self.scale = 1.0
        self.dragging = False
        self.drag_start = None
        
    def on_pan_start(self, e: ft.DragStartEvent):
        """ドラッグ開始（ラバーバンド開始）"""
        self.dragging = True
        self.drag_start = (e.local_x, e.local_y)
        
    def on_pan_update(self, e: ft.DragUpdateEvent):
        """ドラッグ中（ラバーバンド描画）"""
        if self.dragging:
            # 一時的な矩形を描画
            width = e.local_x - self.drag_start[0]
            height = e.local_y - self.drag_start[1]
            # Flet Canvasで描画更新
            
    def on_pan_end(self, e: ft.DragEndEvent):
        """ドラッグ終了（図形確定）"""
        if self.dragging:
            # 図形を確定してリストに追加
            self.dragging = False
```

### 3. **Tkinter Canvas**

**メリット:**
- ✅ 標準ライブラリ
- ✅ 軽量・高速
- ✅ Canvasウィジェットで図形操作

**デメリット:**
- ❌ ラバーバンド機能が基本的
- ❌ 古いUI
- ❌ 高度な図形操作に制限

**実装例:**
```python
import tkinter as tk
from PIL import Image, ImageTk

class VehicleMonitorTk:
    def __init__(self, root):
        self.canvas = tk.Canvas(root)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # ラバーバンド用の変数
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        # イベントバインド
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        
    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, 
            self.start_x, self.start_y,
            outline='red', width=2
        )
        
    def on_move_press(self, event):
        curX = self.canvas.canvasx(event.x)
        curY = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, 
                          self.start_x, self.start_y, 
                          curX, curY)
```

### 4. **Kivy**

**メリット:**
- ✅ タッチ操作対応
- ✅ モバイル展開可能
- ✅ GPUアクセラレーション

**デメリット:**
- ❌ デスクトップUIが特殊
- ❌ 依存関係が多い
- ❌ 学習コスト高

## 性能比較表

| 機能 | PyQt | Flet | Tkinter | Kivy |
|------|------|------|---------|------|
| ラバーバンド | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ |
| 図形編集 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ |
| 座標変換 | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ |
| パフォーマンス | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 学習容易性 | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| Webデプロイ | ❌ | ⭐⭐⭐ | ❌ | ⭐ |

## 結論

**Vehicle Monitor編集機能には PyQt/PySide6 が最適**

理由：
1. QGraphicsViewがラバーバンド機能を完全サポート
2. 座標変換が組み込みで正確
3. 図形の選択・編集が高度に実装可能
4. 業界標準で資料豊富

次善策：
- Web展開必須 → **Flet** + カスタムラバーバンド実装
- 最軽量 → **Tkinter** + 基本機能のみ