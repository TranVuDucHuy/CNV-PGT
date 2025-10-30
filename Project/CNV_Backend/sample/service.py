import io
from typing import List
import uuid

from utils.minio_util import MinioUtil
from .models import Sample, CellType
from sqlalchemy.orm import Session


class SampleService:
    @staticmethod
    def _create_sample(file_stream: io.BytesIO) -> Sample:
        id = str(uuid.uuid4())
        flowcell_id = str(uuid.uuid4()) # Replace with real flowcell ID retrieval
        cycle_id = str(uuid.uuid4()) # Replace with real cycle ID retrieval
        embryo_id = str(uuid.uuid4()) # Replace with real embryo ID retrieval
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
    def save(db: Session, file_stream: io.BytesIO):
        sample = SampleService._create_sample(file_stream)
        db.add(sample)
        db.commit()


    @staticmethod
    def save_many(db: Session, files: List[io.BytesIO]):
        samples = [
            SampleService._create_sample(file_stream) for file_stream in files
        ]
        db.add_all(samples)
        db.commit()

    @staticmethod
    def get(db: Session, sample_id: str) -> Sample:
        return db.query(Sample).filter(Sample.id == sample_id).first()
    
    @staticmethod
    def delete(db: Session, sample_id: str) -> None:
        sample = db.query(Sample).filter(Sample.id == sample_id).first()
        if sample:
            MinioUtil.delete_file(sample.bam_url)
            db.delete(sample)
            db.commit()

    @staticmethod
    def get_all(db: Session):
        return db.query(Sample).all()
    
    @staticmethod
    def get_file_by_id(db: Session, sample_id: str) -> io.BytesIO:
        sample = db.query(Sample).filter(Sample.id == sample_id).first()
        if sample:
            return MinioUtil.get_file(sample.bam_url)
        return None
