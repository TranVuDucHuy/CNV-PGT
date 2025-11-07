"""Backward compatibility module pointing to the packaged plugin symbols."""

from huycnv.plugin import AlgorithmPlugin, BaseInput, BaseOutput, SampleBin, SampleSegment

__all__ = [
    "AlgorithmPlugin",
    "BaseInput",
    "BaseOutput",
    "SampleBin",
    "SampleSegment",
]
