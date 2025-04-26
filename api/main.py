from fastapi import FastAPI

from api.routers.plan_api import router as plan_router
from api.routers.do_api   import router as do_router
from api.routers.check_api import router as check_router
from api.routers.act_api   import router as act_router

app = FastAPI(title="mmopdca MVP")

app.include_router(plan_router)
app.include_router(do_router)
app.include_router(check_router)
app.include_router(act_router)
