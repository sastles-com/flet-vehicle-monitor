"""
circumferenceマーカーの座標/value対応に関する回帰テスト

背景:
    EDIT→MONITOR遷移時に呼ばれる generate_vehicle_json_data() は、
    circle/bar 図形の円周ポイント座標を shape.circumference_items から取得する。

    circumference_items は [marker0, text0, marker1, text1, ...] の交互構成で、
    マーカーは **value昇順(sorted)** で生成される。一方 shape.circumference_points は
    JSON読み込み時の **挿入順** のまま保持される。

    以前の実装には2つの不具合があった:
      (1) enumerate(circumference_items) で全要素を走査し、テキスト要素を
          マーカーと誤認していた（テキスト座標が保存される）。
      (2) marker_index=i*2 に修正後も、position は value昇順のmarker[i*2]から、
          value は挿入順の circumference_points[i] から取得していたため、
          並び順が異なると position と value の対応がずれた。

    本テストは、各markerが保持する point_data から value を取得することで
    position/value のペアが崩れないことを検証する。
"""
import unittest
from unittest.mock import Mock
import io
import contextlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# PySide6は実物を使用（venvにインストール済み）。
# generate_vehicle_json_data() はアンバウンド呼び出しするためQApplicationは不要。
from edit_mode import VehicleMonitorEditor, ShapeType, ShapeCategory


class _Pos:
    """QPointF.pos() 相当（.x()/.y() を返す）"""
    def __init__(self, x, y):
        self._x = x
        self._y = y

    def x(self):
        return self._x

    def y(self):
        return self._y


class _Point:
    """circumference_points の1要素相当（CircumferencePoint相当）"""
    def __init__(self, value):
        self.value = value
        self.position = _Pos(0, 0)


class _Marker:
    """CircumferencePointItem相当のマーカー（自身のpoint_dataを保持する）"""
    def __init__(self, center_x, center_y, point_data):
        # 実際のマーカーは setPos 基準（中心 = pos + 16）
        self._pos = _Pos(center_x - 16, center_y - 16)
        self.point_data = point_data

    def pos(self):
        return self._pos


class _Text:
    """value表示テキスト相当（point_dataを持たない）。ダミー座標を持たせる。"""
    def __init__(self, x, y):
        self._pos = _Pos(x, y)

    def pos(self):
        return self._pos


class _CircleShape:
    """CIRCLE図形のスタブ（generate_vehicle_json_dataが参照する属性のみ実装）

    現実に合わせ:
      - circumference_points は挿入順
      - circumference_items のマーカーは value昇順で並ぶ
        （update_circumference_display と同じ挙動）
    """
    def __init__(self, points_in_insertion_order, marker_centers_by_value):
        self.name = "test_meter"
        self.shape_type = ShapeType.CIRCLE
        self.category = ShapeCategory.METER
        self.scene_scale = 1.0

        # circumference_points は挿入順のまま保持
        self.circumference_points = list(points_in_insertion_order)

        # マーカーは value昇順で生成される
        sorted_points = sorted(self.circumference_points, key=lambda p: p.value)
        self.circumference_items = []
        for i, point in enumerate(sorted_points):
            cx, cy = marker_centers_by_value[point.value]
            self.circumference_items.append(_Marker(cx, cy, point))       # marker
            self.circumference_items.append(_Text(-9000 - i, -9000 - i))  # text（ダミー）

    def get_original_coords(self, scale=None):
        return (320.0, 220.0, 160.0, 160.0)


class TestCircumferenceMarkerIndex(unittest.TestCase):
    """generate_vehicle_json_data() の円周マーカー取得検証"""

    def _make_editor(self, shape):
        editor = Mock()
        editor.vehicle_data = None  # デフォルトベースdictを使わせる
        editor.canvas = Mock()
        editor.canvas.shapes = [shape]
        editor._find_original_part_data = Mock(return_value=None)
        return editor

    def _generate(self, editor):
        # edit_mode.py内のprintに絵文字が含まれ、Windowsのcp932コンソールでは
        # 出力時にUnicodeEncodeErrorになるため、実行中のstdoutをバッファへ退避する
        with contextlib.redirect_stdout(io.StringIO()):
            return VehicleMonitorEditor.generate_vehicle_json_data(editor)

    def test_position_and_value_pairing_with_unsorted_points(self):
        """挿入順とvalue順が異なる場合でも、各circumferenceのposition/valueが対応すること"""
        # 挿入順: 0.0, 1.0, 0.5 （value昇順ではない）
        p0 = _Point(0.0)
        p1 = _Point(1.0)
        p2 = _Point(0.5)
        # value -> マーカー中心座標（value昇順で 0.0, 0.5, 1.0 の順に配置される）
        marker_centers_by_value = {
            0.0: (200, 300),
            0.5: (400, 100),
            1.0: (600, 300),
        }
        shape = _CircleShape([p0, p1, p2], marker_centers_by_value)
        result = self._generate(self._make_editor(shape))

        circ = result["meter"][0]["circumference"]
        self.assertEqual(len(circ), 3)

        # value をキーに position を引けるようにする
        pos_by_value = {c["value"]: (c["position"]["x"], c["position"]["y"]) for c in circ}

        # 各 value が正しいマーカー座標と対応していること（ズレていないこと）
        for value, center in marker_centers_by_value.items():
            self.assertIn(value, pos_by_value)
            self.assertAlmostEqual(pos_by_value[value][0], center[0])
            self.assertAlmostEqual(pos_by_value[value][1], center[1])

        print("circumference position/value ペアリングOK")

    def test_ignores_text_items_dummy_coords(self):
        """テキスト要素のダミー座標が保存に混入しないこと"""
        p0 = _Point(0.0)
        p1 = _Point(0.5)
        p2 = _Point(1.0)
        marker_centers_by_value = {
            0.0: (116, 216),
            0.5: (316, 416),
            1.0: (516, 616),
        }
        shape = _CircleShape([p0, p1, p2], marker_centers_by_value)
        result = self._generate(self._make_editor(shape))

        circ = result["meter"][0]["circumference"]
        self.assertEqual(len(circ), 3)
        for point in circ:
            # ダミーのテキスト座標(-9000付近)が混入していないこと
            self.assertGreater(point["position"]["x"], 0)
            self.assertGreater(point["position"]["y"], 0)

        print("circumference テキスト座標の非混入OK")


if __name__ == '__main__':
    print("=== circumferenceマーカー座標/value回帰テスト開始 ===")
    unittest.main(verbosity=2)
