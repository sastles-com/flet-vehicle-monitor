# フレームワーク比較プロジェクト

このフォルダには、異なるGUIフレームワークで実装されたVehicle Monitor編集機能の比較用コードが含まれています。

## フォルダ構造

```
framework_comparison/
├── pyqt/               # PyQt/PySide6実装
│   ├── vehicle_monitor.py
│   ├── requirements.txt
│   ├── run_pyqt.bat
│   └── run_pyqt.sh
├── tkinter/            # Tkinter実装（今後追加予定）
├── docs/               # ドキュメント
│   ├── comparison.md   # フレームワーク比較表
│   └── VENV_GUIDE.md   # 仮想環境ガイド
└── README.md           # このファイル
```

## 各実装の特徴

### PyQt/PySide6版
- **強み**: ラバーバンド機能、高度な図形操作、座標変換
- **用途**: プロフェッショナルなデスクトップアプリ
- **パフォーマンス**: 優秀

### Tkinter版（予定）
- **強み**: 標準ライブラリ、軽量、依存関係なし
- **用途**: シンプルなツール
- **パフォーマンス**: 良好

## 実行方法（Windows）

### PyQt版
```bash
cd pyqt
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python vehicle_monitor.py
```

## 比較ポイント

1. **ラバーバンド機能**: マウスドラッグで図形を描画
2. **図形の編集**: 選択、移動、リサイズ
3. **座標変換**: 画像座標とピクセル座標の変換
4. **パフォーマンス**: 描画速度とレスポンス
5. **学習曲線**: 習得の難易度

詳細な比較は [docs/comparison.md](docs/comparison.md) を参照してください。