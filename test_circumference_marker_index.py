"""
circumferenceマーカーのインデックス取得に関する回帰テスト

背景:
    EDIT→MONITOR遷移時に呼ばれる generate_vehicle_json_data() は、
    circle/bar 図形の円周ポイント座標を shape.circumference_items から取得する。
    circumference_items は [marker0, text0, marker1, text1, ...] の交互構成のため、
    マーカーは必ず偶数インデックス (i*2) から取得しなければならない。

    以前は enumerate(circumference_items) で全要素を順に走査し、
    2点目以降でテキストラベルの座標をマーカー座標と誤認して保存/MQTT送信していた。
    本テストはその回帰を防ぐ。
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


class _Item:
    """circumference_items の1要素（マーカー/テキスト）相当"""
    def __init__(self, x, y):
        self._pos = _Pos(x, y)

    def pos(self):
        return self._pos


class _Point:
    """circumference_points の1要素相当"""
    def __init__(self, value):
        self.value = value
        self.position = _Pos(0, 0)


class _CircleShape:
    """CIRCLE図形のスタブ（generate_vehicle_json_dataが参照する属性のみ実装）"""
    def __init__(self, marker_centers, values):
        self.name = "test_meter"
        self.shape_type = ShapeType.CIRCLE
        self.category = ShapeCategory.METER
        self.scene_scale = 1.0
        # 交互構成 [marker0, text0, marker1, text1, ...] を再現。
        # テキスト要素にはマーカーと全く異なる座標を入れ、
        # 誤ってテキストを読んだ場合に確実に検出できるようにする。
        self.circumference_items = []
        self.circumference_points = []
        for i, ((mx, my), value) in enumerate(zip(marker_centers, values)):
            # setPos基準の座標（中心 = pos + 16）に合わせ、posを center-16 にする
            self.circumference_items.append(_Item(mx - 16, my - 16))       # marker
            self.circumference_items.append(_Item(-9000 - i, -9000 - i))    # text（ダミー座標）
            self.circumference_points.append(_Point(value))

    def get_original_coords(self, scale=None):
        # center=(400,300), radius=80 相当の矩形
        return (320.0, 220.0, 160.0, 160.0)


class TestCircumferenceMarkerIndex(unittest.TestCase):
    """generate_vehicle_json_data() の円周マーカー取得インデックス検証"""

    def _make_editor(self, shape):
        editor = Mock()
        editor.vehicle_data = None  # デフォルトベースdictを使わせる
        editor.canvas = Mock()
        editor.canvas.shapes = [shape]
        editor._find_original_part_data = Mock(return_value=None)
        return editor

    def test_circle_reads_marker_positions_not_text(self):
        """3点の円周ポイントすべてがマーカー座標(i*2)で記録されること"""
        marker_centers = [(116, 216), (316, 416), (516, 616)]
        values = [0.0, 0.5, 1.0]
        shape = _CircleShape(marker_centers, values)
        editor = self._make_editor(shape)

        # edit_mode.py内のprintに絵文字が含まれ、Windowsのcp932コンソールでは
        # 出力時にUnicodeEncodeErrorになるため、実行中のstdoutをバッファへ退避する
        with contextlib.redirect_stdout(io.StringIO()):
            result = VehicleMonitorEditor.generate_vehicle_json_data(editor)

        self.assertEqual(len(result["meter"]), 1)
        circ = result["meter"][0]["circumference"]
        self.assertEqual(len(circ), 3)

        # 各ポイントがマーカー中心座標・正しいvalueで記録されているか
        for i, (expected_center, expected_value) in enumerate(zip(marker_centers, values)):
            self.assertAlmostEqual(circ[i]["position"]["x"], expected_center[0])
            self.assertAlmostEqual(circ[i]["position"]["y"], expected_center[1])
            self.assertEqual(circ[i]["value"], expected_value)

        # テキストのダミー座標(-9000付近)が混入していないこと
        for point in circ:
            self.assertGreater(point["position"]["x"], 0)
            self.assertGreater(point["position"]["y"], 0)

        print("circle circumference マーカーインデックス取得OK")


if __name__ == '__main__':
    print("=== circumferenceマーカーインデックス回帰テスト開始 ===")
    unittest.main(verbosity=2)
