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
poetry install --with dev
poetry run uvicorn api.main:app --reload
