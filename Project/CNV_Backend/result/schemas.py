from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime, date
from algorithm.plugin import SampleSegment, SampleBin


class ResultSummary(BaseModel):
    id: str
    sample_name: str
    algorithm_name: str
    reference_genome: str
    created_at: datetime


class ResultDto(ResultSummary):
    segments: List[SampleSegment]
    bins: List[SampleBin]


class SampleInfo(BaseModel):
    flowcell_id: str
    cycle_id: str
    embryo_id: str
    cell_type: str
    reference_genome: str
    date: date


class AlgorithmParameterInfo(BaseModel):
    name: str
    type: str
    default: Any
    value: Any


class AlgorithmInfo(BaseModel):
    name: str
    version: str
    parameters: List[AlgorithmParameterInfo] = []


class AberrationSegmentInfo(BaseModel):
    chromosome: str
    start: int
    end: int
    copy_number: float
    confidence: Optional[float] = None
    size: int
    type: str
    mosaicism: float
    aberration_code: str
    assessment: str
    annotation_for_segment: Optional[str] = None


class AberrationInfo(BaseModel):
    aberration_summary: Optional[List[str]] = None
    aberration_segments: List[AberrationSegmentInfo] = []


class ResultReportResponse(BaseModel):
    result_id: str
    sample: SampleInfo
    algorithm: AlgorithmInfo
    aberration: AberrationInfo
