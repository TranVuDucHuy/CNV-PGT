from sqlalchemy import (
    Column,
    String,
    Integer,
    Enum as SqlEnum,
    Float,
    Boolean,
    ForeignKey,
    DateTime,
    JSON,
)
from sqlalchemy.orm import relationship
from database import Base
from common.models import Chromosome
from datetime import datetime
from enum import Enum


class AberrationType(Enum):
    NO_CHANGE = "No_Change"
    GAIN = "Gain"
    LOSS = "Loss"


class AssessmentType(Enum):
    UNKNOWN = "Unknown"
    BENIGN = "Benign"
    PROBABLY_BENIGN = "Probably Benign"
    PROBABLY_PATHOGENIC = "Probably Pathogenic"
    PATHOGENIC = "Pathogenic"
    ARTEFACT = "Artefact"


class Aberration(Base):
    __tablename__ = "aberrations"

    id = Column(String(64), primary_key=True, index=True)
    result_id = Column(
        String(64),
        ForeignKey(
            "results.id", ondelete="CASCADE", name="fk_aberration_result"
        ),
        index=True,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    aberration_summary = Column(JSON, nullable=True)  # e.g., ["+1", "-Xs", "+13"]

    aberration_segments = relationship(
        "AberrationSegment", back_populates="aberration", cascade="all, delete-orphan"
    )


class AberrationSegment(Base):
    __tablename__ = "aberration_segments"

    id = Column(String(64), primary_key=True, index=True)
    aberration_id = Column(
        String(64),
        ForeignKey(
            "aberrations.id", ondelete="CASCADE", name="fk_aberration_segment_aberration"
        ),
        index=True,
        nullable=False,
    )
    chromosome = Column(SqlEnum(Chromosome), nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    copy_number = Column(Float, nullable=False)
    confidence = Column(Float, nullable=True)
    size = Column(Integer, nullable=False)
    type = Column(SqlEnum(AberrationType), nullable=False)
    mosaicism = Column(Float, nullable=False)
    aberration_code = Column(String(64), nullable=False)
    assessment = Column(
        SqlEnum(AssessmentType), nullable=False, default=AssessmentType.UNKNOWN
    )
    annotation_for_segment = Column(String(2048), nullable=True)
    man_change = Column(Boolean, nullable=False, default=False)

    aberration = relationship("Aberration", back_populates="aberration_segments")


class AberrationThreshold(Base):
    __tablename__ = "aberration_thresholds"

    id = Column(String(64), primary_key=True, index=True)
    mosaicism = Column(Float, nullable=False)
    type = Column(SqlEnum(AberrationType), nullable=False)
    color = Column(String(32), nullable=False)  # e.g., "#FF0000" for red
