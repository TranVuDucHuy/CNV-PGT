# from __future__ import annotations

import io
from typing import Optional

from minio import Minio
from minio.error import S3Error
from config import MinioConfig

class MinioUtil:
    @staticmethod
    def _get_minio_client() -> Minio:

        return Minio(
            MinioConfig.ENDPOINT,
            access_key=MinioConfig.ACCESS_KEY,
            secret_key=MinioConfig.SECRET_KEY,
            secure=MinioConfig.USE_SSL,
        )

    @staticmethod
    def ensure_bucket_exists(bucket_name: str) -> None:
        client = MinioUtil._get_minio_client()
        found = client.bucket_exists(bucket_name)
        if not found:
            client.make_bucket(bucket_name)

    @staticmethod
    def save_file(file_stream: bytes, object_name: str, content_type: Optional[str] = None) -> str:
        """Save a file to MinIO and return the object URL path.

        Returns a path like "minio://bucket/object" for storing in DB.
        """
        bucket = MinioConfig.BUCKET
        client = MinioUtil._get_minio_client()

        MinioUtil.ensure_bucket_exists(bucket)

        file_stream = io.BytesIO(file_stream)
        file_stream.seek(0, io.SEEK_END)
        size = file_stream.tell()
        file_stream.seek(0)

        client.put_object(
            bucket,
            object_name,
            data=file_stream,
            length=size,
            content_type=content_type or "application/octet-stream",
        )

        # Store as a portable URI for later retrieval/deletion
        return f"minio://{bucket}/{object_name}"

    @staticmethod
    def delete_file(object_uri: str) -> None:
        """Delete a file in MinIO by its stored URI path (minio://bucket/object)."""
        if not object_uri.startswith("minio://"):
            return
        _, remainder = object_uri.split("://", 1)
        bucket, object_name = remainder.split("/", 1)

        client = MinioUtil._get_minio_client()
        try:
            client.remove_object(bucket, object_name)
        except S3Error:
            # Ignore if not found
            pass

    @staticmethod
    def get_file(object_uri: str) -> Optional[bytes]:
        """Retrieve a file from MinIO by its stored URI path (minio://bucket/object)."""
        if not object_uri.startswith("minio://"):
            return None
        _, remainder = object_uri.split("://", 1)
        bucket, object_name = remainder.split("/", 1)

        client = MinioUtil._get_minio_client()
        try:
            response = client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error:
            return None
