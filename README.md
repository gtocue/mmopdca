# mmopdca – Command-DSL-Driven Forecasting SaaS (MVP)

![CI](https://github.com/***/actions/workflows/ci.yml/badge.svg)
![PyPI](https://img.shields.io/pypi/v/mmopdca)
![License](https://img.shields.io/github/license/***)  <!-- 好みでバッジ追加 -->

## ✨ Overview
“Plan–Do–Check–Act” ループを **DSL + Celery** で自動化する PoC です。
FastAPI を入口に、バックエンドでは sklearn / yfinance / pandas 等を使用します。

## 🚀 Quick Start
```bash
git clone https://github.com/your/mmopdca && cd mmopdca
python -m venv .venv && source .venv/bin/activate  # Windows は .venv\Scripts\Activate
pip install -e ".[dev]"                      # dev 依存を含めてインストール
uvicorn api.main_api:app --reload                # または ``poetry run``
```

## 📝 Plan DSL Loader Example
To load a DSL file and merge defaults from the built-in models schema, run:
```python
from core.dsl.loader import PlanLoader
loader = PlanLoader(validate=True)
plan = loader.load("docs/samples/plan_sample.yaml")
print(plan["models"])
```
See `docs/PLAN_LOADER_DEMO.md` for a brief explanation.

## 🧪 Testing
開発環境を作成したあと、次のコマンドでテストを実行できます。
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
if [ -f requirements-ci.txt ]; then pip install -r requirements-ci.txt; fi
pytest -q
```