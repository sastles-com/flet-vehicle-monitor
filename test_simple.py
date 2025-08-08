#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QLabel
from PySide6.QtGui import QPixmap
import os

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test - Original Size Display")
        self.setGeometry(100, 100, 800, 600)
        
        # 簡単なラベルでテスト
        self.label = QLabel("Test Application - Original Size", self)
        self.setCentralWidget(self.label)
        
        # 画像が存在するかテスト
        image_path = "./data/image.jpg"
        if os.path.exists(image_path):
            self.label.setText(f"Image found: {image_path}")
        else:
            self.label.setText(f"Image NOT found: {image_path}")

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()