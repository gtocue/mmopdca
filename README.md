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
## Database Migrations
To initialize the PostgreSQL schema, start the database container and run Alembic.
On Windows shells you **must** enable UTF-8, otherwise ``configparser`` fails
with ``UnicodeDecodeError: 'cp932' codec can't decode``. Set the environment
variable or run Python with ``-X utf8``:

```powershell
$Env:PYTHONUTF8 = '1'         # ensure config is read as UTF-8
$Env:PG_DSN = 'postgresql://mmopdca:SuperSafePgPassw0rd!@localhost:5432/mmopdca'
# or `$Env:DATABASE_URL` if preferred
alembic upgrade head
```

## Docker Compose
Redis exposes port `6379` on the host. If that port is already in use,
set the `HOST_REDIS_PORT` environment variable to a free port before
starting the containers:

```bash
export HOST_REDIS_PORT=16379
docker compose up -d
```

PostgreSQL exposes port `5432` on the host. To avoid conflicts, you can
set `HOST_POSTGRES_PORT` to a free port in the same way:

```bash
export HOST_POSTGRES_PORT=15432
docker compose up -d
```

Prometheus exposes port `9090` on the host. If the port is taken,
set `HOST_PROM_PORT` accordingly:

```bash
export HOST_PROM_PORT=19090
docker compose up -d
```
If you see an error like 'Bind for 0.0.0.0:9090 failed: port is already allocated' when starting Prometheus, choose an unused port for HOST_PROM_PORT and rerun the compose command.
## Viewing Logs
To inspect container output, use service names with `docker compose logs`:
```bash
docker compose -f compose_rendered.yml logs api
docker compose -f compose_rendered.yml logs db
docker compose -f compose_rendered.yml logs redis
```
Using container names like `docker-api-1` will fail because `logs` expects service names.
