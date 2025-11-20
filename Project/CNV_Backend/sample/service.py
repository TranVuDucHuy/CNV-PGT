import io
from typing import List, Optional, Tuple
import uuid
import datetime
import re

from fastapi import HTTPException, status

from utils.minio_util import MinioUtil
from .models import Sample, CellType
from sqlalchemy.orm import Session
from .schemas import EditRequest, SampleSummary
from common.models import ReferenceGenome


class SampleService:
    @staticmethod
    def parse_filename(filename: str) -> Tuple[str, str, str]:
        filename = filename.replace(".bam", "").strip()
        filename = re.sub(r"_[A-Z0-9]+$", "", filename)
        pattern = r"^([A-Z0-9]+)-(.+)-([A-Z0-9]+)$"
        match = re.match(pattern, filename)
        if match:
            return match.groups()
        
        raise ValueError(
            f"Filename '{filename}' doesn't match expected pattern. "
            "Expected: FLOWCELL-CYCLE-EMBRYO[_PLATE].bam"
        )

    @staticmethod
    def _create_sample(file_stream: bytes, file_name: str, reference_genome: str = None, cell_type: str = None, date: str = None) -> Sample:
        id = str(uuid.uuid4())
        flowcell_id, cycle_id, embryo_id = SampleService.parse_filename(file_name)
        ref_genome = ReferenceGenome(reference_genome) if reference_genome else ReferenceGenome.HG19
        cell_type = CellType(cell_type) if cell_type else CellType.OTHER
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date() if date else datetime.date.today()
        object_name = f"{id}.bam"
        content_type = "application/octet-stream"

        bam_url = MinioUtil.save_file(file_stream, object_name, content_type)

        sample = Sample(
            id=id,
            name=file_name,               
            flowcell_id=flowcell_id,
            cycle_id=cycle_id,
            embryo_id=embryo_id,
            bam_url=bam_url,
            cell_type=cell_type,
            reference_genome=ref_genome,
            date=date,
        )
        return sample

    @staticmethod
    def save(db: Session, file_stream: bytes, file_name: str, reference_genome: str = None, cell_type: str = None, date: str = None):
        existing = db.query(Sample).filter(Sample.name == file_name).first()
        if not existing:
            sample = SampleService._create_sample(file_stream, file_name, reference_genome, cell_type, date)
            db.add(sample)
            db.commit()
        return {
            "success": not existing
        }

    @staticmethod
    def save_many(db: Session, files: List[bytes], names: List[str], reference_genome: str = None, cell_type: str = None, date: str = None):
        if len(files) != len(names):
            raise ValueError("Số lượng files và names phải bằng nhau.")

        created_samples = []
        skipped_names = []

        for i, (file_stream, name) in enumerate(zip(files, names)):
            existing = db.query(Sample).filter(Sample.name == name).first()
            if existing:
                skipped_names.append(name)
                continue  # Bỏ qua file trùng name

            sample = SampleService._create_sample(file_stream, name, reference_genome, cell_type, date)
            created_samples.append(sample)

        # Nếu có sample mới, thêm vào DB
        if created_samples:
            db.add_all(created_samples)
            db.commit()
            for s in created_samples:
                db.refresh(s)

        return {
            "created": [s.name for s in created_samples],
            "skipped": skipped_names,
        }


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
                name=sample.name,
                bam_url=sample.bam_url,
                cell_type=sample.cell_type.value,
                reference_genome=sample.reference_genome.value,
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
            
            if request.reference_genome:
                from result.models import Result
                sample.reference_genome = ReferenceGenome(request.reference_genome)
                db.query(Result).filter(Result.sample_id == sample.name).update(
                    {Result.reference_genome: ReferenceGenome(request.reference_genome)}
                )
            
            db.commit()
            db.refresh(sample)
        return sample
