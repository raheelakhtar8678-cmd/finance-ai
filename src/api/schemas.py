# src/api/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class ChartInfo(BaseModel):
    path: str
    metric: str

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    charts: List[ChartInfo]
    sources: List[str]