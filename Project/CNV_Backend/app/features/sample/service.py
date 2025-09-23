import io
import uuid
from typing import Optional

from flask import current_app

from ...extensions import db
from .model import Sample
from ...utils.minio_utils import save_file, delete_file


def add_sample(patient_id: int, file_storage) -> Sample:
    """Create a new Sample.

    - Upload BAM file to MinIO
    - Persist only the MinIO URI in DB
    """
    # Derive object name to avoid collisions
    ext = "bam"
    unique_name = f"samples/{patient_id}/{uuid.uuid4().hex}.{ext}"

    binary_stream = io.BytesIO(file_storage.read())
    content_type = file_storage.mimetype or "application/octet-stream"
    object_uri = save_file(binary_stream, unique_name, content_type)

    sample = Sample(patient_id=patient_id, bam_url=object_uri)
    db.session.add(sample)
    db.session.commit()
    return sample


def get_sample(sample_id: int) -> Optional[Sample]:
    return Sample.query.get(sample_id)


def remove_sample(sample_id: int) -> bool:
    sample = Sample.query.get(sample_id)
    if not sample:
        return False

    # Remove file in MinIO
    delete_file(sample.bam_url)

    db.session.delete(sample)
    db.session.commit()
    return True


