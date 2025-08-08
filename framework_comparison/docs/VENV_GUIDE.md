# Python仮想環境ガイド

## 概要
このプロジェクトでは、異なるGUIフレームワーク（Flet、PyQt）を独立した仮想環境で管理します。

## なぜvenvを使うのか？

### メリット
- **依存関係の分離**: 各アプリの依存関係が競合しない
- **Python標準**: 追加ツール不要（pipenv、poetryなどと比較して）
- **軽量**: 必要最小限のパッケージのみインストール
- **簡単**: セットアップと使用が簡単

### 他の選択肢との比較

| ツール | メリット | デメリット | 推奨度 |
|--------|----------|------------|--------|
| **venv** | 標準、シンプル、軽量 | 基本機能のみ | ⭐⭐⭐ |
| pipenv | Pipfile管理、セキュリティ | 遅い、複雑 | ⭐⭐ |
| poetry | 依存関係解決、パッケージ管理 | 学習コスト | ⭐⭐ |
| conda | 科学計算向け、バイナリ管理 | 重い、商用制限 | ⭐ |

## セットアップ方法

### Windows
```bash
# 1. セットアップスクリプトを実行
setup_venv.bat

# 2. 各アプリを実行
run_flet.bat    # Flet版
run_pyqt.bat    # PyQt版
```

### macOS/Linux
```bash
# 1. 実行権限を付与
chmod +x setup_venv.sh run_flet.sh run_pyqt.sh

# 2. セットアップスクリプトを実行
./setup_venv.sh

# 3. 各アプリを実行
./run_flet.sh    # Flet版
./run_pyqt.sh    # PyQt版
```

## 仮想環境の構造

```
image_editor/
├── venv_flet/          # Flet用仮想環境
│   ├── Scripts/ (Win) or bin/ (Unix)
│   ├── Lib/ or lib/
│   └── ...
├── venv_pyqt/          # PyQt用仮想環境
│   ├── Scripts/ (Win) or bin/ (Unix)
│   ├── Lib/ or lib/
│   └── ...
├── requirements.txt     # Flet用依存関係
├── requirements_pyqt.txt # PyQt用依存関係
└── ...
```

## 手動での環境管理

### 仮想環境の作成
```bash
# Flet環境
python -m venv venv_flet
venv_flet\Scripts\activate  # Windows
source venv_flet/bin/activate  # Unix
pip install -r requirements.txt

# PyQt環境
python -m venv venv_pyqt
venv_pyqt\Scripts\activate  # Windows
source venv_pyqt/bin/activate  # Unix
pip install -r requirements_pyqt.txt
```

### 仮想環境の切り替え
```bash
# 現在の環境を無効化
deactivate

# 別の環境を有効化
venv_flet\Scripts\activate  # または
venv_pyqt\Scripts\activate
```

### 仮想環境の確認
```bash
# 現在の環境を確認
where python  # Windows
which python  # Unix

# インストール済みパッケージを確認
pip list
```

## トラブルシューティング

### Q: "python"コマンドが認識されない
A: Python 3.xがインストールされているか確認し、必要なら`python3`を使用

### Q: 仮想環境が有効化されない
A: PowerShellの場合、実行ポリシーを変更:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q: パッケージのインストールが失敗する
A: 仮想環境が有効化されているか確認:
```bash
# プロンプトに(venv_flet)や(venv_pyqt)が表示されているか確認
```

## 依存関係の更新

### 新しいパッケージを追加
```bash
# 1. 対象の仮想環境を有効化
venv_flet\Scripts\activate

# 2. パッケージをインストール
pip install new-package

# 3. requirements.txtを更新
pip freeze > requirements.txt
```

### パッケージのアップグレード
```bash
# すべてのパッケージをアップグレード
pip install --upgrade -r requirements.txt

# 特定のパッケージのみ
pip install --upgrade flet
```

## .gitignoreの設定

```gitignore
# 仮想環境ディレクトリを除外
venv_*/
venv/
.venv/
```

## まとめ

- **venv**は最もシンプルで確実な選択
- 各フレームワーク用に独立した環境を維持
- スクリプトで自動化して手間を削減
- 依存関係の競合を完全に回避