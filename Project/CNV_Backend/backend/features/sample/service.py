import io
import uuid
from typing import Optional

from .models import Sample
from backend.utils.minio_utils import save_file, delete_file, get_file


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
        content_type = getattr(file_storage, 'content_type', None) or "application/octet-stream"
        object_uri = save_file(binary_stream, unique_name, content_type)

        print(f"File uploaded to MinIO: {object_uri}")
        sample = Sample.objects.create(
            patient_id=patient_id, 
            bam_url=object_uri
        )

        print(f"Sample created: {sample}")

        return sample

    @staticmethod
    def get_sample(sample_id: str) -> Optional[Sample]:
        try:
            return Sample.objects.get(id=sample_id)
        except Sample.DoesNotExist:
            return None

    @staticmethod
    def get_all_samples() -> list[Sample]:
        return list(Sample.objects.all())

    @staticmethod
    def remove_sample(sample_id: str) -> bool:
        try:
            sample = Sample.objects.get(id=sample_id)
            # Remove file in MinIO
            delete_file(sample.bam_url)
            sample.delete()
            return True
        except Sample.DoesNotExist:
            return False

    @staticmethod
    def get_sample_file(sample_id: str) -> Optional[io.BytesIO]:
        sample = SampleService.get_sample(sample_id)
        if not sample:
            return None
        return get_file(sample.bam_url)

