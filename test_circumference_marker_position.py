"""
circumferenceマーカーの実座標(pos())に関する回帰テスト

背景（実機Qt環境でのみ再現するバグだったため、実際のQtオブジェクトを使う）:

    ResizableEllipseItem.update_circumference_display() は、円周マーカー
    (CircumferencePointItem)を
        CircumferencePointItem(display_x - 16, display_y - 16, 32, 32, ...)
    のように、絶対座標をコンストラクタの矩形(rect)自体に焼き込んで生成し、
    setPos() を一度も呼んでいなかった。

    Qtでは QGraphicsItem のシーン上の実位置は「rect(ローカル座標)」と
    「pos()(シーン変換)」の合成で決まる。rectに絶対座標を入れて pos() を
    未設定(デフォルト(0,0))のままにすると、見た目の描画位置自体は
    rect起点で正しく出るが、.pos() を読むコード(generate_vehicle_json_data()
    やCenterControlPoint.update_original_coordinates())は「マーカーが一度も
    setPos()されていない=(0,0)」を返され、誤った座標を保存してしまう。

    さらに、ユーザーが直接マーカーをドラッグした場合はsetPos()が呼ばれる
    ため、rectのオフセットの上にさらにpos()のオフセットが乗り、描画位置が
    ズレる(二重オフセット)問題もあった。

    Bar形状(BarShapeItem)のマーカーは元々 rect=(0,0,32,32) + setPos() の
    正しい規約だったため影響がなかった。ResizableEllipseItem側をBar同様の
    規約に統一して修正した。

    合わせて、update_circumference_display() 内の "_user_moved" ガードにより
    「マーカーを直接ドラッグした後に円をリサイズ/移動すると、表示上のマーカー
    は追従するのに point.position (保存用データモデル) が古い値のまま固まる」
    バグも修正した（ガードを撤去し、常に同期するようにした）。

    本テストは実際のQGraphicsScene/QGraphicsEllipseItemを用いてこれらを検証する。
"""
import unittest
import io
import contextlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QGraphicsScene

_app = QApplication.instance() or QApplication([])

from edit_mode import (
    ResizableEllipseItem, ShapeCategory, CircumferencePoint, Position,
    VehicleMonitorEditor
)


def _make_meter(scene, center, radius, values_positions):
    points = [CircumferencePoint(position=Position(x, y), value=v) for (x, y, v) in values_positions]
    cx, cy = center
    x, y, w, h = cx - radius, cy - radius, radius * 2, radius * 2
    shape = ResizableEllipseItem(
        x, y, w, h, scene_scale=1.0,
        category=ShapeCategory.METER, is_original_coords=True,
        circumference_points=points
    )
    scene.addItem(shape.ellipse_item)
    shape.name = "test_meter"
    return shape


def _generate(shape):
    editor = type("E", (), {})()
    editor.vehicle_data = None
    canvas = type("C", (), {})()
    canvas.shapes = [shape]
    editor.canvas = canvas
    editor._find_original_part_data = lambda *a, **kw: None
    # edit_mode.py内のprintの絵文字がWindowsのcp932コンソールで出力できないため退避
    with contextlib.redirect_stdout(io.StringIO()):
        return VehicleMonitorEditor.generate_vehicle_json_data(editor)


class TestCircumferenceMarkerPosition(unittest.TestCase):
    """円周マーカーの.pos()と保存データの整合性テスト"""

    def test_marker_pos_is_not_origin_when_freshly_created(self):
        """新規生成されたマーカー(未ドラッグ)の.pos()が(0,0)のままにならないこと"""
        scene = QGraphicsScene()
        shape = _make_meter(scene, center=(400, 300), radius=80, values_positions=[
            (480, 300, 0.0), (400, 220, 0.5), (320, 300, 1.0)
        ])
        shape.set_selected(True)  # マーカーを新規生成させる

        for i in range(0, len(shape.circumference_items), 2):
            marker = shape.circumference_items[i]
            self.assertNotEqual((marker.pos().x(), marker.pos().y()), (0.0, 0.0),
                                 "マーカーが一度もドラッグされていないのに.pos()が(0,0)のまま")

    def test_save_while_selected_matches_point_position(self):
        """選択中(circumference_items非空)に保存しても、point.positionと一致すること"""
        scene = QGraphicsScene()
        shape = _make_meter(scene, center=(400, 300), radius=80, values_positions=[
            (480, 300, 0.0), (400, 220, 0.5), (320, 300, 1.0)
        ])
        shape.set_selected(True)
        self.assertGreater(len(shape.circumference_items), 0)

        result = _generate(shape)
        circ = {c["value"]: (c["position"]["x"], c["position"]["y"]) for c in result["meter"][0]["circumference"]}

        for point in shape.circumference_points:
            saved = circ[point.value]
            self.assertAlmostEqual(saved[0], point.position.x, places=3)
            self.assertAlmostEqual(saved[1], point.position.y, places=3)

    def test_dragged_point_stays_synced_after_resize(self):
        """マーカーを直接ドラッグ(_user_moved)した後に円をリサイズしても、
        point.positionが新しい半径に追従すること（古い値に固まらない）"""
        scene = QGraphicsScene()
        shape = _make_meter(scene, center=(400, 300), radius=80, values_positions=[
            (480, 300, 0.0), (400, 220, 0.5), (320, 300, 1.0)
        ])
        shape.set_selected(True)

        # value=0.5のマーカーを直接ドラッグしたことをシミュレート
        sorted_points = sorted(shape.circumference_points, key=lambda p: p.value)
        target_point = next(p for p in sorted_points if p.value == 0.5)
        marker_idx = sorted_points.index(target_point) * 2
        marker_item = shape.circumference_items[marker_idx]

        rect = shape.ellipse_item.boundingRect()
        pos = shape.ellipse_item.pos()
        center_x = pos.x() + rect.width() / 2
        center_y = pos.y() + rect.height() / 2
        radius_now = rect.width() / 2

        drag_angle = -math.pi / 3
        new_x = center_x + radius_now * math.cos(drag_angle)
        new_y = center_y + radius_now * math.sin(drag_angle)
        marker_size = 32
        marker_item.setPos(new_x - marker_size / 2, new_y - marker_size / 2)

        # mouseMoveEvent/mouseReleaseEvent相当の状態確定
        target_point.position.x = new_x
        target_point.position.y = new_y
        target_point._user_moved = True
        target_point._calculated_angle = math.atan2(new_y - center_y, new_x - center_x)

        # 円をリサイズ（半径80→130）してResizeHandle.mouseReleaseEvent相当を呼ぶ
        new_radius = 130
        shape.ellipse_item.setRect(0, 0, new_radius * 2, new_radius * 2)
        shape.ellipse_item.setPos(center_x - new_radius, center_y - new_radius)
        shape.update_circumference_display()

        model_dist = math.hypot(target_point.position.x - center_x, target_point.position.y - center_y)
        self.assertAlmostEqual(model_dist, new_radius, delta=1.0,
                                msg="ドラッグ後にリサイズしても point.position が新しい半径に追従していない")


if __name__ == '__main__':
    print("=== circumferenceマーカー座標(.pos())回帰テスト開始 ===")
    unittest.main(verbosity=2)
