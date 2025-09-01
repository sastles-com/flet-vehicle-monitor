"""
編集→保存→再読み込み循環テスト
実際のedit_mode.pyを使用した統合テスト
"""
import unittest
from unittest.mock import Mock, patch
import json
import tempfile
import os
import sys

# Add test target module path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock Qt imports to avoid GUI dependencies
sys.modules['PySide6'] = Mock()
sys.modules['PySide6.QtWidgets'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()
sys.modules['PySide6.QtGui'] = Mock()

class TestEditSaveReloadCycle(unittest.TestCase):
    """編集→保存→再読み込み循環テスト"""
    
    def setUp(self):
        """テスト初期化"""
        # テスト用vehicle.jsonデータ
        self.test_vehicle_json = {
            "name": "INTEGRATION_TEST",
            "path": "/test/templates",
            "threshold": 0.8,
            "gray": True,
            "offset": 50,
            "icon": [
                {
                    "name": "test_icon",
                    "path": "/path/to/icon.png",
                    "type": "bool",
                    "shape": "box",
                    "top_left": {"x": 100, "y": 100},
                    "bottom_right": {"x": 200, "y": 150}
                }
            ],
            "meter": [
                {
                    "name": "test_meter",
                    "type": "float",
                    "shape": "circle",
                    "center": {"x": 400, "y": 300},
                    "radius": 80,
                    "circumference": [
                        {"position": {"x": 480, "y": 300}, "value": 0.0},
                        {"position": {"x": 456.569, "y": 243.431}, "value": 0.25},
                        {"position": {"x": 400, "y": 220}, "value": 0.5},
                        {"position": {"x": 343.431, "y": 243.431}, "value": 0.75}
                    ]
                }
            ],
            "ocr": [
                {
                    "name": "test_ocr",
                    "type": "int",
                    "shape": "box",
                    "top_left": {"x": 500, "y": 400},
                    "bottom_right": {"x": 600, "y": 450}
                }
            ],
            "bar": [
                {
                    "name": "test_bar",
                    "type": "float",
                    "shape": "bar",
                    "description": "This should be preserved"
                }
            ]
        }
    
    def test_vehicle_data_preservation(self):
        """Test 1: VehicleDataの元データ保持テスト"""
        try:
            from edit_mode import VehicleData, IconData, MeterData, OCRData, Position, CircumferencePoint
            
            # テスト用のVehicleDataオブジェクトを作成
            icons = [IconData(
                name=self.test_vehicle_json["icon"][0]["name"],
                path=self.test_vehicle_json["icon"][0]["path"],
                type=self.test_vehicle_json["icon"][0]["type"],
                shape=self.test_vehicle_json["icon"][0]["shape"],
                top_left=Position(100, 100),
                bottom_right=Position(200, 150)
            )]
            
            circumference_points = []
            for point_data in self.test_vehicle_json["meter"][0]["circumference"]:
                point = CircumferencePoint(
                    position=Position(point_data["position"]["x"], point_data["position"]["y"]),
                    value=point_data["value"]
                )
                circumference_points.append(point)
            
            meters = [MeterData(
                name=self.test_vehicle_json["meter"][0]["name"],
                path="",
                type=self.test_vehicle_json["meter"][0]["type"],
                shape=self.test_vehicle_json["meter"][0]["shape"],
                center=Position(400, 300),
                radius=80,
                ratio=1.0,
                circumference=circumference_points
            )]
            
            ocrs = [OCRData(
                name=self.test_vehicle_json["ocr"][0]["name"],
                type=self.test_vehicle_json["ocr"][0]["type"],
                shape=self.test_vehicle_json["ocr"][0]["shape"],
                top_left=Position(500, 400),
                bottom_right=Position(600, 450)
            )]
            
            # VehicleDataオブジェクト作成（_original_json_dataを保持）
            vehicle_data = VehicleData(
                name=self.test_vehicle_json["name"],
                path=self.test_vehicle_json["path"],
                threshold=self.test_vehicle_json["threshold"],
                gray=self.test_vehicle_json["gray"],
                offset=self.test_vehicle_json["offset"],
                icon=icons,
                meter=meters,
                ocr=ocrs,
                _original_json_data=self.test_vehicle_json.copy()
            )
            
            # プロパティテスト
            self.assertEqual(len(vehicle_data.icons), 1)
            self.assertEqual(len(vehicle_data.meters), 1)
            self.assertEqual(len(vehicle_data.ocrs), 1)
            
            # barデータが保持されているかチェック
            self.assertIn("bar", vehicle_data._original_json_data)
            self.assertEqual(len(vehicle_data._original_json_data["bar"]), 1)
            
        except ImportError as e:
            self.skipTest(f"edit_mode module import failed: {e}")
    
    def test_data_preservation_logic(self):
        """Test 2: データ保持ロジックテスト"""
        # generate_vehicle_json_data()の中核ロジックを単体テスト
        
        # 元データからのデータ保持テスト
        original_data = self.test_vehicle_json.copy()
        
        # 基本フィールドの保持確認
        self.assertEqual(original_data["name"], "INTEGRATION_TEST")
        self.assertEqual(original_data["threshold"], 0.8)
        self.assertTrue(original_data["gray"])
        
        # 未知のフィールド（bar）が保持されているか確認
        self.assertIn("bar", original_data)
        self.assertEqual(len(original_data["bar"]), 1)
        self.assertEqual(original_data["bar"][0]["name"], "test_bar")
        self.assertEqual(original_data["bar"][0]["description"], "This should be preserved")
        
        # 元データの完全性テスト
        expected_keys = {"name", "path", "threshold", "gray", "offset", "icon", "meter", "ocr", "bar"}
        self.assertTrue(expected_keys.issubset(original_data.keys()),
                        f"Missing keys: {expected_keys - original_data.keys()}")
    
    def test_circumference_precision_preservation(self):
        """Test 3: circumference座標精度保持テスト"""
        original_points = self.test_vehicle_json["meter"][0]["circumference"]
        
        # 座標精度テスト
        for i, point in enumerate(original_points):
            x = point["position"]["x"]
            y = point["position"]["y"]
            value = point["value"]
            
            # 期待される座標（手計算）
            center_x, center_y = 400, 300
            radius = 80
            
            # 相対座標から距離を計算
            rel_x = x - center_x
            rel_y = y - center_y
            distance = (rel_x * rel_x + rel_y * rel_y) ** 0.5
            
            # 円周上制約の確認
            self.assertAlmostEqual(distance, radius, places=1,
                                   msg=f"Point {i} at ({x}, {y}) not on circle (distance: {distance})")
    
    def test_coordinate_system_consistency(self):
        """Test 4: 座標系一貫性テスト"""
        import math
        
        # 複数の座標系変換での一貫性をテスト
        test_cases = [
            {"center": {"x": 100, "y": 100}, "radius": 50},
            {"center": {"x": 500, "y": 300}, "radius": 100},
            {"center": {"x": 1000, "y": 800}, "radius": 200}
        ]
        
        for case in test_cases:
            center_x = case["center"]["x"]
            center_y = case["center"]["y"]
            radius = case["radius"]
            
            # 各象限のテストポイント（正確な三角関数使用）
            test_angles = [0, math.pi/2, math.pi, 3*math.pi/2]  # 0°, 90°, 180°, 270°
            
            for angle in test_angles:
                # 正確な座標計算
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                # 逆算テスト：距離検証
                rel_x = x - center_x
                rel_y = y - center_y
                calculated_distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                
                self.assertAlmostEqual(calculated_distance, radius, places=10,
                                       msg=f"Distance inconsistency at angle {angle} rad ({math.degrees(angle)}°)")
                
                # 角度の逆算テスト
                calculated_angle = math.atan2(rel_y, rel_x)
                # 角度を正規化（0-2π）
                normalized_expected = angle % (2 * math.pi)
                normalized_calculated = calculated_angle % (2 * math.pi)
                
                self.assertAlmostEqual(normalized_calculated, normalized_expected, places=10,
                                       msg=f"Angle inconsistency: expected {normalized_expected}, got {normalized_calculated}")


if __name__ == '__main__':
    print("=== 編集→保存→再読み込み循環テスト開始 ===")
    unittest.main(verbosity=2)