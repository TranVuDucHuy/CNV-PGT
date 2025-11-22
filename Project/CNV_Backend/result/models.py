from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    Enum as SqlEnum,
    DateTime,
    Integer,
    Float,
    Boolean,
)
from database import Base
from enum import Enum
from datetime import datetime
from sqlalchemy.orm import relationship
from common.models import Chromosome, ReferenceGenome


class Result(Base):
    __tablename__ = "results"

    id = Column(String(64), primary_key=True, index=True)
    sample_id = Column(
        String(64),
        ForeignKey("samples.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    algorithm_id = Column(
        String(64),
        ForeignKey("algorithms.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    algorithm_parameter_id = Column(
        String(64),
        ForeignKey("algorithm_parameters.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )

    reference_genome = Column(
        SqlEnum(ReferenceGenome), nullable=False, default=ReferenceGenome.HG19
    )
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    sample = relationship("Sample", back_populates="results")
    algorithm = relationship("Algorithm", back_populates="results")
    algorithm_parameter = relationship("AlgorithmParameter", back_populates="results")
    segments = relationship(
        "SampleSegment", back_populates="result", cascade="all, delete-orphan"
    )
    bins = relationship(
        "SampleBin", back_populates="result", cascade="all, delete-orphan"
    )


class SampleSegment(Base):
    __tablename__ = "sample_segments"

    id = Column(String(64), primary_key=True, index=True)
    result_id = Column(
        String(64),
        ForeignKey("results.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    chromosome = Column(SqlEnum(Chromosome), nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    copy_number = Column(Float, nullable=False)
    confidence = Column(Float, nullable=True)
    man_change = Column(Boolean, nullable=False, default=False)

    result = relationship("Result", back_populates="segments")


class SampleBin(Base):
    __tablename__ = "sample_bins"

    id = Column(String(64), primary_key=True, index=True)
    result_id = Column(
        String(64),
        ForeignKey("results.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    chromosome = Column(SqlEnum(Chromosome), nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    copy_number = Column(Float, nullable=False)
    read_count = Column(Integer, nullable=False)
    gc_content = Column(Float, nullable=False)

    result = relationship("Result", back_populates="bins")
