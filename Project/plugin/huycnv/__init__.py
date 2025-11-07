"""Top-level package for the huycnv plugin interface."""

from .plugin import AlgorithmPlugin, BaseInput, BaseOutput, SampleBin, SampleSegment

__all__ = [
    "AlgorithmPlugin",
    "BaseInput",
    "BaseOutput",
    "SampleBin",
    "SampleSegment",
]

