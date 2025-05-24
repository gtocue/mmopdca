# mmopdca – Command-DSL-Driven Forecasting SaaS (MVP)

[![CI](https://github.com/***/actions/workflows/ci.yml/badge.svg)](https://github.com/***/actions/workflows/ci.yml)
[![SDK Tests](https://github.com/***/actions/workflows/sdk-tests.yml/badge.svg)](https://github.com/***/actions/workflows/sdk-tests.yml)
![PyPI](https://img.shields.io/pypi/v/mmopdca)
![License](https://img.shields.io/github/license/***) <!-- 好みでバッジ追加 -->

> **TL;DR**  -  *Plan → Do → Check → Act* を **DSL + Celery** でワンストップ自動化する PoC です。
> FastAPI / Celery / sklearn / yfinance / pandas などで構成しています。

---

## ✨ Overview

* **Plan:**  YAML DSL で取得対象・モデル・評価指標を宣言
* **Do:**  Celery ワーカーで学習 → 推論 → parquet に保存
* **Check:**  テストメトリクスを算出。閾値超過時はアラートを返却
* **Act:**  (予定) 外部 Webhook や Slack 通知と連携

アーキテクチャ図 & 詳細は [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) を参照してください。

---

## 🚀 Quick Start

### 1. Poetry 派

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1   # PowerShell
# bash ->   source .venv/bin/activate
poetry install --sync --no-root     # prod+dev 依存をインストール
poetry run uvicorn api.main_api:app --reload
```

### 2. pip 派

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt    # lock ファイル由来なので再現性◎
uvicorn api.main_api:app --reload
```

> **Tip:** `poetry.lock` を VCS 管理しているため **どちらの手順でも同一バージョン** が入ります。

---

## 📝 Plan DSL Loader Example

```python
from core.dsl.loader import PlanLoader
loader = PlanLoader(validate=True)
plan = loader.load("docs/samples/plan_sample.yaml")
print(plan["models"])
```

より詳しい解説は [`docs/PLAN_LOADER_DEMO.md`](docs/PLAN_LOADER_DEMO.md) を参照。

---

## 🧪 Testing

```powershell
# venv or poetry shell に入った前提
pytest -q                  # 70+ tests should be all green
```

CI では `pytest -q` と `sdk-tests`, `stack-health` の 3 ジョブが走ります。

---

## 🗄️ Database / Cache

* **PostgreSQL**  (default `5432`) ・・・ `HOST_POSTGRES_PORT` で上書き可能
* **Redis**       (default `6379`) ・・・ `HOST_REDIS_PORT`
* **Prometheus**  (default `9090`) ・・・ `HOST_PROM_PORT`

```bash
export HOST_POSTGRES_PORT=15432
export HOST_REDIS_PORT=16379
export HOST_PROM_PORT=19090
docker compose up -d
```

---

## 💾 Migrations (Alembic)

Windows の場合は UTF-8 を強制しないと `UnicodeDecodeError(cp932)` が出るので注意。

```powershell
$Env:PYTHONUTF8 = '1'
$Env:PG_DSN = 'postgresql://mmopdca:SuperSafePgPassw0rd!@localhost:5432/mmopdca'
alembic upgrade head
```

---

## 🔒 Security / Dependabot

`poetry.lock` を追跡しているため GitHub で脆弱性が検知されます。
アラートが出たらローカルで下記を実行し、PR を作成してください。

```powershell
poetry update <package-name>
git switch -c chore/bump-<package-name>
git add poetry.lock && git commit -m "build(deps): bump <package-name>"
git push -u origin HEAD
```

---

## 📜 License

MIT © 2025 gtocue
