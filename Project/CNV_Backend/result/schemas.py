from pydantic import BaseModel
from typing import List
from datetime import datetime
from algorithm.plugin import SampleSegment, SampleBin


class ResultSummary(BaseModel):
    id: str
    sample_id: str
    algorithm_name: str
    reference_genome: str
    created_at: datetime


class ResultDto(ResultSummary):
    segments: List[SampleSegment]
    bins: List[SampleBin]
