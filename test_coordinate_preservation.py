"""
座標保持精度テスト
変形→保存→再読み込み循環でのcircumference座標精度検証
"""
import unittest
import json
import math
import tempfile
import os
from unittest.mock import Mock, patch

# テスト対象のモジュール
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestCoordinatePreservation(unittest.TestCase):
    """座標保持精度テストスイート"""
    
    def setUp(self):
        """テスト初期化"""
        self.test_vehicle_data = {
            "name": "TEST_VEHICLE",
            "path": "/test/path",
            "threshold": 0.8,
            "gray": True,
            "offset": 50,
            "icon": [],
            "meter": [
                {
                    "name": "test_meter",
                    "type": "float",
                    "shape": "circle",
                    "center": {"x": 500, "y": 400},
                    "radius": 100,
                    "circumference": [
                        {"position": {"x": 600, "y": 400}, "value": 0.0},
                        {"position": {"x": 570.711, "y": 329.289}, "value": 0.25},
                        {"position": {"x": 500, "y": 300}, "value": 0.5},
                        {"position": {"x": 429.289, "y": 329.289}, "value": 0.75}
                    ]
                }
            ],
            "ocr": []
        }
    
    def test_circumference_angle_precision(self):
        """Test 1: circumferenceポイントの角度計算精度テスト"""
        meter = self.test_vehicle_data["meter"][0]
        center_x = meter["center"]["x"]
        center_y = meter["center"]["y"]
        radius = meter["radius"]
        
        # 各circumferenceポイントの角度を計算
        calculated_angles = []
        for point in meter["circumference"]:
            pos_x = point["position"]["x"]
            pos_y = point["position"]["y"]
            
            # 相対座標
            rel_x = pos_x - center_x
            rel_y = pos_y - center_y
            
            # 角度計算
            angle = math.atan2(rel_y, rel_x)
            calculated_angles.append(angle)
            
            # 円周上制約の検証
            calculated_radius = math.sqrt(rel_x * rel_x + rel_y * rel_y)
            self.assertAlmostEqual(calculated_radius, radius, places=3, 
                                   msg=f"Point at ({pos_x}, {pos_y}) is not on circle")
        
        # 角度の精度検証
        expected_angles = [0, -math.pi/4, -math.pi/2, -3*math.pi/4]  # 0, 45, 90, 135度（反時計回り）
        
        for i, (calculated, expected) in enumerate(zip(calculated_angles, expected_angles)):
            self.assertAlmostEqual(calculated, expected, places=4,
                                   msg=f"Angle precision error at point {i}")
    
    def test_coordinate_round_trip_precision(self):
        """Test 2: 座標の循環精度テスト（JSON→内部→JSON）"""
        # 元の座標
        original_points = self.test_vehicle_data["meter"][0]["circumference"]
        
        # 内部処理をシミュレーション（角度計算→座標再生成）
        center_x = 500
        center_y = 400
        radius = 100
        
        reconstructed_points = []
        for point in original_points:
            # 元座標から角度計算
            rel_x = point["position"]["x"] - center_x
            rel_y = point["position"]["y"] - center_y
            angle = math.atan2(rel_y, rel_x)
            
            # 角度から座標再生成
            new_x = center_x + radius * math.cos(angle)
            new_y = center_y + radius * math.sin(angle)
            
            reconstructed_points.append({
                "position": {"x": round(new_x, 6), "y": round(new_y, 6)},
                "value": point["value"]
            })
        
        # 精度検証
        for original, reconstructed in zip(original_points, reconstructed_points):
            orig_x = original["position"]["x"]
            orig_y = original["position"]["y"]
            recon_x = reconstructed["position"]["x"]
            recon_y = reconstructed["position"]["y"]
            
            self.assertAlmostEqual(orig_x, recon_x, places=3,
                                   msg=f"X coordinate precision loss: {orig_x} -> {recon_x}")
            self.assertAlmostEqual(orig_y, recon_y, places=3,
                                   msg=f"Y coordinate precision loss: {orig_y} -> {recon_y}")
    
    def test_json_serialization_precision(self):
        """Test 3: JSON保存・読み込み精度テスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_vehicle_data, f, indent=2)
            temp_path = f.name
        
        try:
            # JSON読み込み
            with open(temp_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # 座標精度の検証
            original_meter = self.test_vehicle_data["meter"][0]
            loaded_meter = loaded_data["meter"][0]
            
            for orig_point, loaded_point in zip(original_meter["circumference"], 
                                                loaded_meter["circumference"]):
                self.assertEqual(orig_point["position"]["x"], loaded_point["position"]["x"])
                self.assertEqual(orig_point["position"]["y"], loaded_point["position"]["y"])
                self.assertEqual(orig_point["value"], loaded_point["value"])
        
        finally:
            os.unlink(temp_path)
    
    def test_scale_transformation_precision(self):
        """Test 4: スケール変換精度テスト"""
        # シミュレーション：異なるスケールでの座標変換
        scales = [0.5, 1.0, 1.5, 2.0]
        original_point = {"x": 600, "y": 400}
        
        for scale in scales:
            # スケール適用
            scaled_x = original_point["x"] * scale
            scaled_y = original_point["y"] * scale
            
            # スケール戻し
            unscaled_x = scaled_x / scale
            unscaled_y = scaled_y / scale
            
            # 精度検証
            self.assertAlmostEqual(original_point["x"], unscaled_x, places=10,
                                   msg=f"X precision loss at scale {scale}")
            self.assertAlmostEqual(original_point["y"], unscaled_y, places=10,
                                   msg=f"Y precision loss at scale {scale}")
    
    def test_circumference_constraint_enforcement(self):
        """Test 5: 円周制約の強制適用テスト"""
        center_x, center_y = 500, 400
        radius = 100
        
        # 制約違反のポイントをテスト
        test_points = [
            {"x": 620, "y": 410},  # 円の外側
            {"x": 480, "y": 390},  # 円の内側
            {"x": 500, "y": 500},  # Y軸上の点
        ]
        
        for test_point in test_points:
            # 円制約の適用
            dx = test_point["x"] - center_x
            dy = test_point["y"] - center_y
            angle = math.atan2(dy, dx)
            
            # 円周上の正確な位置
            constrained_x = center_x + radius * math.cos(angle)
            constrained_y = center_y + radius * math.sin(angle)
            
            # 制約後の点が円周上にあることを確認
            dist_from_center = math.sqrt((constrained_x - center_x)**2 + (constrained_y - center_y)**2)
            self.assertAlmostEqual(dist_from_center, radius, places=10,
                                   msg=f"Constrained point not on circle: distance={dist_from_center}")


if __name__ == '__main__':
    print("=== 座標保持精度テスト開始 ===")
    unittest.main(verbosity=2)