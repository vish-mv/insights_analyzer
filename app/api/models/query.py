from pydantic import BaseModel
from typing import List, Dict

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    columns: List[str]
    data: List[Dict]
    row_count: int
    execution_time: float