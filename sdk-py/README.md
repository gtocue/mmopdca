# mmopdca-sdk

> Command-DSL-driven forecasting micro-service API only
> Python client for the MMOPDCA API (v0.4.0)

**Package version:** 1.0.0
**API version:** 0.4.0

---

## 📦 インストール

### 1. PyPI 版（公開済みの場合）

```bash
pip install mmopdca_sdk
```

### 2. GitHub から直接インストール（リポジトリ公開後）

```bash
pip install git+https://github.com/<YOUR_ORG>/mmopdca-sdk.git@main
```

> **Note:** 上記 URL は実際のリポジトリに置き換えてください。

### 3. 開発中版（ローカル編集を反映したい場合）

```bash
# 仮想環境の作成
python -m venv .venv

# ── Windows PowerShell の場合
.\.venv\Scripts\Activate.ps1

# ── macOS / Linux の場合
source .venv/bin/activate

# SDK ディレクトリへ移動して editable モードでインストール
cd sdk-py
pip install -e .
```

---

## 🚀 Quickstart (3 ステップで動かす)

1. **環境変数設定**

   ```bash
   # Windows PowerShell
   $Env:MMOP_BASE_URL="http://localhost:8000"
   $Env:MMOP_API_KEY="<YOUR_API_KEY>"

   # macOS / Linux
   export MMOP_BASE_URL="http://localhost:8000"
   export MMOP_API_KEY="<YOUR_API_KEY>"
   ```

2. **サンプル実行**

   ```bash
   cd sdk-py/examples
   python quickstart.py
   ```

   成功すると：

   ```
   ✅ Run started successfully: run_id=<your_run_id>
   ```

---

## 🔧 テスト

```bash
# 依存をインストール
pip install pytest pyyaml

# テスト実行 (sdk-py)
cd sdk-py
pytest --disable-warnings -q
```

---

## 📑 CHANGELOG

`CHANGELOG.md` にリリース履歴をまとめています。

---

## 👩‍💻 開発・貢献

1. このリポジトリをフォーク
2. 新機能／修正ブランチを切り出し
3. PR を送付
4. CI が通過後にレビュー・マージ

---

## ⚖️ ライセンス

MIT License
