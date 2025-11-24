from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from common.models import Chromosome


class AberrationSegment(BaseModel):
    id: str
    chromosome: Chromosome
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
    man_change: bool = False


class AberrationSummary(BaseModel):
    id: str
    result_id: str
    created_at: datetime
    aberration_summary: Optional[List[str]] = None


class AberrationDTO(AberrationSummary):
    segments: List[AberrationSegment]
