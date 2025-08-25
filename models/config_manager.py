#!/usr/bin/env python3
"""
Configuration Manager
設定管理クラス
"""

import json
import os
from typing import Dict, Any, Optional


class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self):
        self.config_data: Optional[Dict[str, Any]] = None
    
    def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """設定データのバリデーション"""
        try:
            # 必須フィールドの確認
            required_fields = {
                "mqtt": ["host", "port"],
                "RestAPI": ["host", "port"]
            }
            
            for section, fields in required_fields.items():
                if section not in config_data:
                    return False
                for field in fields:
                    if field not in config_data[section]:
                        return False
            
            return True
            
        except Exception:
            return False
    
    def load_config_from_file(self, file_path: str) -> Dict[str, Any]:
        """ファイルから設定を読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if self.validate_config(config_data):
                self.config_data = config_data
                return config_data
            else:
                raise ValueError("Invalid config format")
                
        except Exception as e:
            raise Exception(f"Config load error: {e}")
    
    def save_config_to_file(self, file_path: str) -> None:
        """設定をファイルに保存"""
        if self.config_data is None:
            raise ValueError("No config data to save")
        
        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise Exception(f"Config save error: {e}")