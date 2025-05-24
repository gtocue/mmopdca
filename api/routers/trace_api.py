from fastapi import APIRouter, HTTPException
from core.repository.factory import get_repo

router = APIRouter(prefix="/trace", tags=["trace"])

@router.get("/{run_id}")
def get_trace(run_id: str):
    repo = get_repo("trace")
    rec = repo.get(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="run not found")
    return rec
