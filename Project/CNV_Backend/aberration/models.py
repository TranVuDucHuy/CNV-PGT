from sqlalchemy import (
    Column,
    String,
    Integer,
    Enum as SqlEnum,
    Float,
    Boolean,
    ForeignKey,
)
from database import Base
from common.models import Chromosome
from enum import Enum


class AberrationType(Enum):
    """Includes "No_Change", "Gain", "Loss" """

    NO_CHANGE = "No_Change"
    GAIN = "Gain"
    LOSS = "Loss"


class AssessmentType(Enum):
    """Includes "Unknown", "Benign", "Probably Benign", "Probably Pathogenic", "Pathogenic", "Artefact" """

    UNKNOWN = "Unknown"
    BENIGN = "Benign"
    PROBABLY_BENIGN = "Probably Benign"
    PROBABLY_PATHOGENIC = "Probably Pathogenic"
    PATHOGENIC = "Pathogenic"
    ARTEFACT = "Artefact"


class AberrationSegment(Base):
    __tablename__ = "aberration_segments"

    id = Column(String(64), primary_key=True, index=True)
    result_id = Column(
        String(64),
        ForeignKey(
            "results.id", ondelete="CASCADE", name="fk_aberration_segment_result"
        ),
        index=True,
        nullable=False,
    )
    annotation_id = Column(
        String(64),
        ForeignKey(
            "annotations.id",
            ondelete="CASCADE",
            name="fk_aberration_segment_annotation",
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
    mosaicism = Column(Float, nullable=True)
    assessment = Column(
        SqlEnum(AssessmentType), nullable=False, default=AssessmentType.UNKNOWN
    )
    annotation_for_segment = Column(String(2048), nullable=True)
    man_change = Column(Boolean, nullable=False, default=False)


class AberrationThreshold(Base):
    __tablename__ = "aberration_thresholds"

    id = Column(String(64), primary_key=True, index=True)
    mosaicism = Column(Float, nullable=False)
    type = Column(SqlEnum(AberrationType), nullable=False)
    color = Column(String(32), nullable=False)  # e.g., "#FF0000" for red
