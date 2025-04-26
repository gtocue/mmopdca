from pydantic import BaseModel, Field
from typing import Optional, List

class IndicatorCfg(BaseModel):
    name: str = Field(..., example="SMA")
    window: int = Field(..., gt=0, example=20)

class PlanCommand(BaseModel):
    id: str                     # UUID など
    symbol: str                 # 例: “AAPL”
    start: str                  # YYYY-MM-DD
    end: str                    # YYYY-MM-DD
    indicators: List[IndicatorCfg] = Field(default_factory=list)
    note: Optional[str] = None
