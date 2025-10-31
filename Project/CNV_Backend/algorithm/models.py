from sqlalchemy import Column, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from database import Base
import datetime

class Algorithm(Base):
    __tablename__ = "algorithms"

    id = Column(String(64), primary_key=True, index=True, nullable=False)
    name = Column(String(128), index=True, nullable=False)
    version = Column(String(64), nullable=False)
    description = Column(String(1024), nullable=True)
    upload_date = Column(Date, nullable=False, default=datetime.datetime.now)
    url = Column(String(256), nullable=False)
    input_class = Column(String(256), nullable=False)
    output_class = Column(String(256), nullable=False)
    exe_class = Column(String(256), nullable=False)

    parameters = relationship("AlgorithmParameter", back_populates="algorithm", cascade="all, delete-orphan", lazy="joined")

class AlgorithmParameter(Base):
    __tablename__ = "algorithm_parameters"

    id = Column(String(64), primary_key=True, index=True, nullable=False)
    algorithm_id = Column(String(64), ForeignKey("algorithms.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(128), nullable=False)
    type = Column(String(256), nullable=False)
    description = Column(String(256), nullable=True)

    algorithm = relationship("Algorithm", back_populates="parameters")
