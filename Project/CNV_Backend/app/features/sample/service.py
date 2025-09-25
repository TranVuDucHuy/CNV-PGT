import io
import uuid
from typing import Optional


from ...extensions import db
from .model import Sample
from ...utils.minio_utils import save_file, delete_file, get_file

class SampleService:

    @staticmethod
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

        print(f"File uploaded to MinIO: {object_uri}")
        sample = Sample(patient_id=patient_id, bam_url=object_uri)
        db.session.add(sample)
        db.session.commit()

        print(f"Sample created: {sample}")

        return sample

    @staticmethod
    def get_sample(sample_id: int) -> Optional[Sample]:
        return Sample.query.get(sample_id)

    @staticmethod
    def get_all_samples() -> list[Sample]:
        return Sample.query.all()


    @staticmethod
    def remove_sample(sample_id: int) -> bool:
        sample = Sample.query.get(sample_id)
        if not sample:
            return False

        # Remove file in MinIO
        delete_file(sample.bam_url)

        db.session.delete(sample)
        db.session.commit()
        return True

    @staticmethod
    def get_sample_file(sample_id: int) -> Optional[io.BytesIO]:
        sample = Sample.query.get(sample_id)
        if not sample:
            return None
        return get_file(sample.bam_url)



