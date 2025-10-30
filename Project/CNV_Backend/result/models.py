from sqlalchemy import Column, String,  Enum, Date
from database import Base

class CellType(Enum):
    """ Includes "Polar body 1", "Polar body 2", "Blastomere", "Trophectoderm", "GenomicDNA", "Other" """
    POLAR_BODY_1 = "Polar body 1"
    POLAR_BODY_2 = "Polar body 2"
    BLASTOMERE = "Blastomere"
    TROPHOECTODERM = "Trophectoderm"
    GENOMIC_DNA = "GenomicDNA"
    OTHER = "Other"

class Sample(Base):
    __tablename__ = "samples"

    id = Column(String, primary_key=True, index=True, nullable=False)
    flowcell_id = Column(String, index=True, nullable=False)
    cycle_id = Column(String, index=True, nullable=False)
    embryo_id = Column(String, index=True, nullable=False)
    bam_url = Column(String, nullable=False)
    bai_url = Column(String, nullable=False)
    cell_type = Column(Enum(CellType), nullable=False)
    date = Column(Date, nullable=False)
