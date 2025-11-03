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


class ReferenceGenome(Enum):
    HG19 = "GRCh37/hg19"
    HG38 = "GRCh38/hg38"


class Chromosome(Enum):
    CHR_1 = "1"
    CHR_2 = "2"
    CHR_3 = "3"
    CHR_4 = "4"
    CHR_5 = "5"
    CHR_6 = "6"
    CHR_7 = "7"
    CHR_8 = "8"
    CHR_9 = "9"
    CHR_10 = "10"
    CHR_11 = "11"
    CHR_12 = "12"
    CHR_13 = "13"
    CHR_14 = "14"
    CHR_15 = "15"
    CHR_16 = "16"
    CHR_17 = "17"
    CHR_18 = "18"
    CHR_19 = "19"
    CHR_20 = "20"
    CHR_21 = "21"
    CHR_22 = "22"
    CHR_X = "X"
    CHR_Y = "Y"
    CHR_MITOCHONDRIAL = "MT"


class Result(Base):
    __tablename__ = "results"

    id = Column(String(64), primary_key=True, index=True)
    sample_id = Column(
        String(64),
        ForeignKey("samples.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        name="fk_samples_results",
    )
    algorithm_id = Column(
        String(64),
        ForeignKey("algorithms.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        name="fk_algorithms_results",
    )
    reference_genome = Column(
        SqlEnum(ReferenceGenome), nullable=False, default=ReferenceGenome.HG19
    )
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    sample = relationship("Sample", back_populates="results")
    algorithm = relationship("Algorithm", back_populates="results")
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
        name="fk_results_sample_segments",
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
        name="fk_results_sample_bins",
    )
    chromosome = Column(SqlEnum(Chromosome), nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    copy_number = Column(Float, nullable=False)
    read_count = Column(Integer, nullable=False)
    gc_content = Column(Float, nullable=False)

    result = relationship("Result", back_populates="bins")
