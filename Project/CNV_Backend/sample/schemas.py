from pydantic import BaseModel


class EditRequest(BaseModel):
    cell_type: str
    date: str


class SampleSummary(BaseModel):
    id: str
    bam_url: str
    cell_type: str
    date: str
