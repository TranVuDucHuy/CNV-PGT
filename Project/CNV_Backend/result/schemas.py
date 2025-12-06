from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime, date


class SampleSegment(BaseModel):
    chromosome: str
    start: int
    end: int
    copy_number: float
    confidence: Optional[float] = None
    man_change: bool = False


class SampleBin(BaseModel):
    chromosome: str
    start: int
    end: int
    copy_number: float
    read_count: int
    gc_content: float


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
    annotation_for_segment: Optional[List[str]] = None
    man_change: Optional[bool] = None


class AberrationInfo(BaseModel):
    aberration_summary: Optional[List[str]] = None
    aberration_segments: List[AberrationSegmentInfo] = []


class ResultReportResponse(BaseModel):
    result_id: str
    sample: SampleInfo
    algorithm: AlgorithmInfo
    aberration: AberrationInfo


class CycleReportRequest(BaseModel):
    report_ids: List[str]


class AberrationSummary(BaseModel):
    code: str
    mosaic: float
    size: Optional[float] = None  # in Mbp
    diseases: Optional[List[str]] = None
    assessment: Optional[str] = None


class EmbryoInfo(BaseModel):
    embryo_id: str
    cell_type: str
    call: str
    abberations: List[AberrationSummary]


class CycleReportResponse(BaseModel):
    cycle_id: str
    flowcell_id: str
    embryos: List[EmbryoInfo]
