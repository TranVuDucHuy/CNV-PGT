from pydantic import BaseModel
from typing import Optional


class EditRequest(BaseModel):
    cell_type: str
    date: str
    reference_genome: Optional[str] = None


class SampleSummary(BaseModel):
    id: str
    name: str
    bam_url: str
    cell_type: str
    reference_genome: str
    date: str
