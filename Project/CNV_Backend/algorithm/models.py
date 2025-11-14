from sqlalchemy import Column, String, Date, ForeignKey, JSON
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
    url = Column(String(256), nullable=True)
    input_class = Column(String(256), nullable=True)
    output_class = Column(String(256), nullable=True)
    exe_class = Column(String(256), nullable=True)

    parameters = relationship(
        "AlgorithmParameter",
        back_populates="algorithm",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    results = relationship(
        "Result", back_populates="algorithm", cascade="all, delete-orphan"
    )


class AlgorithmParameter(Base):
    __tablename__ = "algorithm_parameters"

    id = Column(String(64), primary_key=True, index=True, nullable=False)
    algorithm_id = Column(
        String(64),
        ForeignKey(
            "algorithms.id", ondelete="CASCADE", name="fk_algorithms_parameters"
        ),
        nullable=False,
    )
    value = Column(JSON, nullable=False)

    algorithm = relationship("Algorithm", back_populates="parameters")
    results = relationship(
        "Result",
        back_populates="algorithm_parameter",
        cascade="all, delete-orphan",
    )
