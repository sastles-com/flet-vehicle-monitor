"""
EDITボタン押下時の超高速撮影処理

遅延原因の特定と修正案:

問題1: スレッド作成のオーバーヘッド
- threading.Thread()作成で約10-50ms遅延
- 解決策: 直接実行に変更

問題2: 複数並行処理の競合
- 撮影スレッドとMQTT送信スレッドが同時実行
- 解決策: 順次処理に変更

問題3: データ準備の遅延
- config_dataとbase_urlの取得で遅延
- 解決策: 事前準備データの活用

修正後の処理フロー:
1. ボタン押下瞬間のタイムスタンプ記録
2. 事前準備済みデータ使用（遅延なし）
3. /instant_capture を直接HTTP呼び出し（スレッド化なし）
4. 撮影成功後にMQTT送信
5. /imageエンドポイントで保存済み画像取得
6. EDITモード表示
"""

def ultra_fast_capture_and_edit_transition(self):
    """最速撮影実装（遅延原因除去版）"""
    import time
    import requests
    
    # ボタン押下瞬間のタイムスタンプ
    button_press_time = time.time()
    print(f"⚡ ボタン押下瞬間: {button_press_time}")
    
    try:
        # 事前準備済みデータ使用（最速）
        if hasattr(self, '_capture_ready_data') and hasattr(self, '_capture_ready_url'):
            config_data = self._capture_ready_data
            base_url = self._capture_ready_url
            print("✅ 事前準備済みデータ使用")
        else:
            # 緊急時フォールバック
            config_data = self.config_view.get_config_data()
            rest_api_host = config_data.get("RestAPI", {}).get("host", "")
            rest_api_port = config_data.get("RestAPI", {}).get("port", "8000")
            base_url = f"http://{rest_api_host}:{rest_api_port}"
            print("⚠️ リアルタイム取得（遅延あり）")
        
        # 即座撮影実行
        timestamp = int(button_press_time * 1000)
        image_url = f"{base_url}/instant_capture?timestamp={timestamp}"
        
        capture_start = time.time()
        print(f"📸 撮影開始: {capture_start - button_press_time:.3f}秒後")
        
        # HTTP直接実行（スレッド化なし）
        response = requests.get(
            image_url,
            headers={'Cache-Control': 'no-cache'},
            timeout=8
        )
        response.raise_for_status()
        
        capture_end = time.time()
        print(f"✅ 撮影完了: {capture_end - button_press_time:.3f}秒")
        
        # 後続処理：MQTT送信 → image取得 → 画面表示
        self.mqtt_service.send_config(config_data)
        
        image_response = requests.get(f"{base_url}/image", timeout=5)
        final_image_data = image_response.content
        
        # EDITモード表示
        self.switch_to_mode(AppMode.EDIT)
        self.canvas.load_image_from_data(final_image_data)
        
        total_time = time.time() - button_press_time
        print(f"🎯 全体完了: {total_time:.3f}秒")
        
    except Exception as e:
        print(f"❌ 高速撮影エラー: {e}")
        self.switch_to_mode(AppMode.EDIT)