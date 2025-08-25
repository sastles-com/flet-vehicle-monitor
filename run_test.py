#!/usr/bin/env python3
"""
Test runner for app.py implementation
"""

try:
    # Import the app module to test
    from app import VehicleMonitorApplication, ConfigData, VehicleData
    print("SUCCESS: app.py imports successful")
    
    # Test ConfigData structure
    try:
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
        print("SUCCESS: ConfigData instantiation successful")
        print(f"Config mqtt_host: {config.mqtt_host}")
    except Exception as e:
        print(f"FAIL: ConfigData instantiation failed - {e}")
    
    # Test VehicleData structure
    try:
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
        print("SUCCESS: VehicleData instantiation successful")
        print(f"Vehicle name: {vehicle.name}")
    except Exception as e:
        print(f"FAIL: VehicleData instantiation failed - {e}")
    
    # Test application class
    try:
        import sys
        from PySide6.QtWidgets import QApplication
        
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
            
        main_app = VehicleMonitorApplication()
        print("SUCCESS: VehicleMonitorApplication instantiation successful")
        print(f"Window title: {main_app.windowTitle()}")
        
        # Check if tab widget exists
        tab_widget = main_app.tab_widget
        print(f"Tab count: {tab_widget.count()}")
        
        for i in range(tab_widget.count()):
            print(f"Tab {i}: {tab_widget.tabText(i)}")
            
    except Exception as e:
        print(f"FAIL: VehicleMonitorApplication test failed - {e}")
        import traceback
        traceback.print_exc()

except ImportError as e:
    print(f"FAIL: Import failed - {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"FAIL: Unexpected error - {e}")
    import traceback
    traceback.print_exc()