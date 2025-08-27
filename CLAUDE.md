# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Conversation Guidelines

- 常に日本語で会話する

## Development Commands (Windows Only)

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Run the main application (loads ./data/config.json if exists)
python main.py

# Run with debug mode
python main.py --debug

# Run with specific config
python main.py --config ./data/config.json

# Skip initial file dialog
python main.py --no-dialog
```

## User Experience Flow

### CONFIG → EDIT → MONITOR モードの体験フロー
以下のフローに基づいてユーザー体験を設計・実装する：

**CONFIGモード（ベンチ接続・カメラ調整）:**
```
１．アプリを全画面で起動
２．WiFiを所望のベンチのものに接続
３．間違えて読み込まないようにconfig.jsonの内容を空に初期化
４．config.jsonを読み込むために自動でconfig.jsonファイルダイアログが表示
５．接続したベンチに合わせたconfig.jsonファイルを指定して読み込み
６．config.jsonをパースして、MQTTブローカーに接続
７．imageトピックを購読して、プレビュー画面を読み込み、メイン画面に拡大表示
８．カメラを搭載したraspiの位置を調整して、カメラのアングルを決定
９．EDITモードで使いたい画角タイミングで、ヘッダのEDITボタンを押してeditモードへ移行
```

**EDIT移行時の自動処理:**
```
１０．モード移行時にconfig.jsonをMQTTに送信
１１．そのあと、RestAPIでfull_imageを取得して編集開始
```

### 重要な設計ポイント
- **デフォルトフォルダ**: C:\Users\table0\Desktop\config
- **自動ファイルダイアログ**: 起動時に即座に表示
- **リアルタイムプレビュー**: MQTTからのimageトピック購読
- **カメラ調整**: ユーザーが画角を決定する時間を確保
- **ベンチ切り替え**: 複数ベンチ間での効率的な作業フロー対応


## Development Philosophy

### Test-Driven Development (TDD)
- 原則としてテスト駆動開発（TDD）で進める
- 期待される入出力に基づき、まずテストを作成する
- 実装コードは書かず、テストのみを用意する
- テストを実行し、失敗を確認する
- テストが正しいことを確認できた段階でコミットする
- その後、テストをパスさせる実装を進める
- 実装中はテストを変更せず、コードを修正し続ける
- すべてのテストが通過するまで繰り返す

### Implementation Policy
- **実装許可制**: 実装に入る際は必ずユーザーに許可を受けること
- **クラス単位テスト**: ユニットテストは基本的にクラスを単位として設計・実装する
- **t_wadaのTDD開発ポリシー**: 厳格なTDDサイクルに従う

### Code Style Guidelines
- Use type hints for all function parameters and return values
- Follow PEP 8 style guide (enforced by flake8)
- Keep functions small and focused (single responsibility)
- Use dataclasses for data structures
- Prefer composition over inheritance

## Data Structures

### config.json
```json
{
  "mqtt": {
    "host": "192.168.1.134",
    "port": "1883",
    "wsPort": "9001"
  },
  "RestAPI": {
    "host": "raspi-t40cd.local",
    "port": "8000"
  },
  "camera": {
    "width": 2304,
    "height": 1296,
    "scale": 0.125,
    "focus_length": "10.12768268585205",
    "exposure": 60000,
    "AnalogueGain": 1
  },
  "frame": 0,
  "bench": "T40CD",
  "path": "./config"
}
```

### vehicle.json
```json
{
  "name": "XTRAIL",
  "path": "/ros2_ws/src/camera_system/templates",
  "threshold": 0.8,
  "gray": true,
  "offset": 50,
  "icon": [
    {
      "name": "check_engine",
      "path": "/path/to/template.png",
      "type": "bool",
      "shape": "box",
      "top_left": {"x": 502, "y": 418},
      "bottom_right": {"x": 594, "y": 486}
    }
  ],
  "meter": [
    {
      "name": "temp",
      "type": "float",
      "shape": "circle",
      "center": {"x": 453, "y": 809},
      "radius": 200,
      "circumference": [
        {"position": {"x": 355, "y": 873}, "value": 0},
        {"position": {"x": 463, "y": 903}, "value": 0.5},
        {"position": {"x": 553, "y": 875}, "value": 1}
      ]
    }
  ],
  "ocr": [
    {
      "name": "time",
      "type": "int",
      "shape": "box",
      "top_left": {"x": 1294, "y": 136},
      "bottom_right": {"x": 1365, "y": 199}
    }
  ]
}
```



# SOD: edit_web_app.py
## Software Design Document / System Overview Document

### ドキュメント情報
- **プロジェクト名**: Vehicle Monitor Edit Web Application
- **バージョン**: 1.0
- **作成日**: 2025-07-16
- **対象システム**: edit_web_app.py

## 1. システム概要

### 1.1 目的
既存のFletベースVehicle Monitor EDITモードをデスクトップアプリ車両画像上での矩形・円形パーツの編集機能をWeb環境で提供する。

### 1.2 スコープ
- 車両画像の表示・ズーム・パン操作
- Vehicle JSONデータの読み込み・保存
- 図形パーツ（Icon/Meter/OCR）の描画
- 図形パーツ（Icon/Meter/OCR）の編集
- 座標変換システム
- 拡大・縮小機能
- リアルタイムプレビュー機能


