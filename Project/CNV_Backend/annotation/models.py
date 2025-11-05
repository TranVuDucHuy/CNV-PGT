from sqlalchemy import Column, String, Enum, Date, Integer
from database import Base
from common.models import Chromosome, ReferenceGenome
from datetime import date


class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(String(64), primary_key=True, index=True)
    database_id = Column(String(64), index=True, nullable=False)
    chromosome = Column(Enum(Chromosome), nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    name_for_tooltip = Column(String(256), nullable=True)
    url = Column(String(512), nullable=True)


class AnnotationDatabase(Base):
    __tablename__ = "annotation_databases"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    reference_genome = Column(Enum(ReferenceGenome), nullable=False)
    description = Column(String(2048), nullable=True)
    annotation_url = Column(String(512), nullable=False)
