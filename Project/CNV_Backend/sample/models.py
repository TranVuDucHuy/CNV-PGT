from enum import Enum
from sqlalchemy import Column, String, Enum as SqlEnum, Date
from sqlalchemy.orm import relationship
from database import Base
from datetime import date


class CellType(Enum):
    """Includes "Polar body 1", "Polar body 2", "Blastomere", "Trophectoderm", "GenomicDNA", "Other" """

    POLAR_BODY_1 = "Polar body 1"
    POLAR_BODY_2 = "Polar body 2"
    BLASTOMERE = "Blastomere"
    TROPHOECTODERM = "Trophectoderm"
    GENOMIC_DNA = "GenomicDNA"
    OTHER = "Other"


class Sample(Base):
    __tablename__ = "samples"

    id = Column(String(64), primary_key=True, index=True, nullable=False)
    name = Column(String(255), unique=True, nullable=False)
    flowcell_id = Column(String(64), index=True, nullable=False)
    cycle_id = Column(String(64), index=True, nullable=False)
    embryo_id = Column(String(64), index=True, nullable=False)
    bam_url = Column(String(256), nullable=False)
    cell_type = Column(SqlEnum(CellType), nullable=False, default=CellType.OTHER)
    date = Column(Date, nullable=False, default=date.today)

    results = relationship(
        "Result", back_populates="sample", cascade="all, delete-orphan"
    )
