from pydantic import BaseModel
from typing import Optional, List

class BasicResponse(BaseModel):
    message: str

class AlgorithmParameterDto(BaseModel):
    name: str
    type: str
    description: Optional[str] = None

class AlgorithmSummary(BaseModel):
    id: str
    name: str
    version: str
    description: Optional[str] = None
    parameters: List[AlgorithmParameterDto] = []