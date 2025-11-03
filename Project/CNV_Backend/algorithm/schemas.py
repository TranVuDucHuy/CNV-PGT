from pydantic import BaseModel
from typing import Optional, List


class BasicResponse(BaseModel):
    message: str


class AlgorithmParameterDto(BaseModel):
    id: str
    value: dict


class AlgorithmSummary(BaseModel):
    id: str
    name: str
    version: str
    description: Optional[str] = None
    parameters: List[AlgorithmParameterDto] = None


# class AlgorithmRunRequest(BaseModel):
#     # Need bam or sample_id to run the algorithm
#     bam: Optional[bytes] = None
#     sample_id: Optional[str] = None

#     # Need params to run the algorithm
#     params: Optional[dict] = None
#     params_id: Optional[str] = None
