#!/usr/bin/env python3
import unittest
import sys
from app import VehicleMonitorApplication, ConfigData, VehicleData

try:
    from PySide6.QtWidgets import QApplication, QTabWidget
    HAS_PYSIDE6 = True
except ImportError:
    HAS_PYSIDE6 = False

class TestAppImplementation(unittest.TestCase):
    
    def setUp(self):
        if HAS_PYSIDE6 and not QApplication.instance():
            self.app = QApplication([])
    
    def test_config_data_creation(self):
        """Test ConfigData creation"""
        config = ConfigData(
            mqtt_host="172.20.10.4",
            mqtt_port="1883",
            mqtt_ws_port="9001",
            rest_api_host="raspi-t40cd.local", 
            rest_api_port="8000",
            camera_width=2304,
            camera_height=1296,
            camera_scale=0.125,
            camera_focus_length="10.12768268585205",
            camera_exposure=60000,
            camera_analogue_gain=1,
            frame=0,
            bench="T40CD",
            path="./config"
        )
        self.assertEqual(config.mqtt_host, "172.20.10.4")
        self.assertEqual(config.bench, "T40CD")
    
    def test_vehicle_data_creation(self):
        """Test VehicleData creation"""
        vehicle = VehicleData(
            name="XTRAIL",
            path="/ros2_ws/src/camera_system/templates",
            threshold=0.8,
            gray=True,
            offset=50,
            icon=[],
            meter=[],
            ocr=[]
        )
        self.assertEqual(vehicle.name, "XTRAIL")
        self.assertEqual(vehicle.threshold, 0.8)
    
    @unittest.skipUnless(HAS_PYSIDE6, "PySide6 not available")
    def test_application_creation(self):
        """Test VehicleMonitorApplication creation"""
        app_instance = VehicleMonitorApplication()
        self.assertEqual(app_instance.windowTitle(), "Vehicle Monitor Application")
        
        # Check tab widget
        tab_widget = app_instance.tab_widget
        self.assertEqual(tab_widget.count(), 3)
        self.assertEqual(tab_widget.tabText(0), "CONFIG")
        self.assertEqual(tab_widget.tabText(1), "EDIT") 
        self.assertEqual(tab_widget.tabText(2), "MONITOR")
        self.assertEqual(tab_widget.currentIndex(), 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)