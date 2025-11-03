from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List


class SampleSegment(BaseModel):
    chromosome: str
    start: int
    end: int
    copy_number: float
    confidence: float


class SampleBin(BaseModel):
    chromosome: str
    start: int
    end: int
    copy_number: float
    read_count: int
    gc_content: float


class BaseOutput(BaseModel):
    reference_genome: str
    segments: List[SampleSegment]
    bins: List[SampleBin]


class BaseInput(BaseModel):
    bam: bytes


class AlgorithmPlugin(ABC):
    @abstractmethod
    def run(self, data: BaseInput, **kwargs) -> BaseOutput:
        pass
