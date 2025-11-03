import io
from typing import List, Optional, Tuple
import uuid
import datetime
import re

from utils.minio_util import MinioUtil
from .models import Sample, CellType
from sqlalchemy.orm import Session
from .schemas import EditRequest, SampleSummary


class SampleService:
    @staticmethod
    def parse_filename(filename: str) -> Tuple[str, str, str]:
        """
        Parse BAM filename to extract IDs.

        Args:
            filename: BAM filename (with or without .bam extension)

        Returns:
            Tuple of (flowcell_id, cycle_id, embryo_id)
        """
        filename = filename.replace(".bam", "")
        pattern = r"^([A-Z0-9]+)-([A-Z0-9-]+)-([A-Z0-9]+)_([A-Z0-9]+)$"
        match = re.match(pattern, filename)

        if not match:
            raise ValueError(
                f"Filename '{filename}' doesn't match expected pattern: "
                "[Flowcell ID]-[Cycle ID]-[Embryo ID]_[Plate ID].bam"
            )

        flowcell_id, cycle_id, embryo_id, plate_id = match.groups()
        return flowcell_id, cycle_id, embryo_id

    @staticmethod
    def _create_sample(file_stream: bytes) -> Sample:
        id = str(uuid.uuid4())
        flowcell_id = str(uuid.uuid4())  # Replace with real flowcell ID retrieval
        cycle_id = str(uuid.uuid4())  # Replace with real cycle ID retrieval
        embryo_id = str(uuid.uuid4())  # Replace with real embryo ID retrieval
        cell_type = CellType.OTHER  # Replace with real cell type

        object_name = f"{id}.bam"
        content_type = "application/octet-stream"

        bam_url = MinioUtil.save_file(file_stream, object_name, content_type)

        sample = Sample(
            id=id,
            flowcell_id=flowcell_id,
            cycle_id=cycle_id,
            embryo_id=embryo_id,
            bam_url=bam_url,
            cell_type=cell_type,
        )

        return sample

    @staticmethod
    def save(db: Session, file_stream: bytes):
        sample = SampleService._create_sample(file_stream)
        db.add(sample)
        db.commit()

    @staticmethod
    def save_many(db: Session, files: List[bytes]):
        samples = [SampleService._create_sample(file_stream) for file_stream in files]
        db.add_all(samples)
        db.commit()

    @staticmethod
    def get(db: Session, sample_id: str) -> Optional[Sample]:
        return db.query(Sample).filter(Sample.id == sample_id).first()

    @staticmethod
    def delete(db: Session, sample_id: str) -> None:
        sample = db.query(Sample).filter(Sample.id == sample_id).first()
        if sample:
            MinioUtil.delete_file(sample.bam_url)
            db.delete(sample)
            db.commit()

    @staticmethod
    def get_all(db: Session) -> List[SampleSummary]:
        return [
            SampleSummary(
                id=sample.id,
                bam_url=sample.bam_url,
                cell_type=sample.cell_type.value,
                date=sample.date.strftime("%Y-%m-%d"),
            )
            for sample in db.query(Sample).all()
        ]

    @staticmethod
    def get_file_by_id(db: Session, sample_id: str) -> Optional[bytes]:
        sample = db.query(Sample).filter(Sample.id == sample_id).first()
        if sample:
            return MinioUtil.get_file(sample.bam_url)
        return None

    @staticmethod
    def update(db: Session, sample_id: str, request: EditRequest) -> Optional[Sample]:
        sample = db.query(Sample).filter(Sample.id == sample_id).first()
        if sample:
            sample.cell_type = CellType(request.cell_type)
            sample.date = datetime.datetime.strptime(request.date, "%Y-%m-%d").date()
            db.commit()
            db.refresh(sample)
        return sample
