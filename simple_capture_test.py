"""
最もシンプルなボタン押下→画像保存テスト

ボタン押下時にRestAPIで現在のカメラ画像をimage.jpgに保存するだけ
"""

def simple_button_capture_test(self):
    """最小限：ボタン押下→image.jpg保存のみ"""
    import time
    import requests
    
    # ボタン押下瞬間
    button_time = time.time()
    print(f"⚡ ボタン押下: {button_time}")
    
    try:
        # RestAPI URL（固定値テスト用）
        base_url = "http://raspi-t40cd.local:8000"  # または実際のIP
        capture_url = f"{base_url}/instant_capture"
        
        # HTTP GET実行（最小限）
        capture_start = time.time()
        response = requests.get(capture_url, timeout=5)
        capture_end = time.time()
        
        # 結果出力
        total_time = capture_end - button_time
        api_time = capture_end - capture_start
        
        if response.status_code == 200:
            print(f"✅ 撮影成功: {total_time:.3f}秒 (API: {api_time:.3f}秒)")
        else:
            print(f"❌ 撮影失敗: {response.status_code}")
            
    except Exception as e:
        error_time = time.time() - button_time
        print(f"❌ エラー ({error_time:.3f}秒): {e}")

# 期待結果: 50-200ms程度で完了するはず