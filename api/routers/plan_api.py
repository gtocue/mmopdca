from fastapi import APIRouter, HTTPException, status
from core.schemas.command import PlanCommand

router = APIRouter(prefix="/plan", tags=["plan"])

_FAKE_DB: dict[str, PlanCommand] = {}   # 今はインメモリ

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_plan(cmd: PlanCommand):
    if cmd.id in _FAKE_DB:
        raise HTTPException(409, "id already exists")
    _FAKE_DB[cmd.id] = cmd
    return {"ok": True, "id": cmd.id}

@router.get("/{cmd_id}", response_model=PlanCommand)
def get_plan(cmd_id: str):
    cmd = _FAKE_DB.get(cmd_id)
    if not cmd:
        raise HTTPException(404, "not found")
    return cmd

@router.get("/", response_model=list[PlanCommand])
async def list_plans() -> list[PlanCommand]:
    """登録済み Plan をすべて返す簡易版"""
    return list(memory_store.values())
