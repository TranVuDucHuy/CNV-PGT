from pydantic import BaseModel
from typing import Optional, List, Any
from common.schemas import BasicResponse


class RegisterAlgorithmResponse(BasicResponse):
    algorithm_id: str
    algorithm_parameter_id: str


class AlgorithmParameterDto(BaseModel):
    id: str
    value: dict


class AlgorithmSummary(BaseModel):
    id: str
    name: str
    version: str
    description: Optional[str] = None
    references_required: int = 0
    parameters: List[AlgorithmParameterDto] = None
    last_parameter_id: Optional[str] = None


class AlgorithmDto(AlgorithmSummary):
    upload_date: str
    url: str


class AlgorithmParameterCreateRequest(BaseModel):
    name: str
    type: str
    default: Any
    value: Any


class AlgorithmMetadata(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    references_required: int = 0
    parameters: List[AlgorithmParameterCreateRequest] = None


class UpdateParameterRequest(BaseModel):
    parameters: dict  # Format: {param_name: {type, default, value}}


class UpdateParameterResponse(BasicResponse):
    algorithm_parameter_id: str


# class AlgorithmRunRequest(BaseModel):
#     # Need bam or sample_id to run the algorithm
#     bam: Optional[bytes] = None
#     sample_id: Optional[str] = None

#     # Need params to run the algorithm
#     params: Optional[dict] = None
#     params_id: Optional[str] = None
