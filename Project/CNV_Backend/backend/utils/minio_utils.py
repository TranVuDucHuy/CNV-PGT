"""MinIO utilities for file storage."""
import io
from typing import Optional
from django.conf import settings
from minio import Minio
from minio.error import S3Error


def _get_minio_client() -> Minio:
    """Get MinIO client instance."""
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )


def ensure_bucket_exists(bucket_name: str) -> None:
    """Ensure the MinIO bucket exists."""
    client = _get_minio_client()
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)


def save_file(file_stream: io.BytesIO, object_name: str, content_type: Optional[str] = None) -> str:
    """Save a file to MinIO and return the object URL path.

    Returns a path like "minio://bucket/object" for storing in DB.
    """
    bucket = settings.MINIO_BUCKET
    client = _get_minio_client()

    ensure_bucket_exists(bucket)

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


def delete_file(object_uri: str) -> None:
    """Delete a file in MinIO by its stored URI path (minio://bucket/object)."""
    if not object_uri.startswith("minio://"):
        return
    _, remainder = object_uri.split("://", 1)
    bucket, object_name = remainder.split("/", 1)

    client = _get_minio_client()
    try:
        client.remove_object(bucket, object_name)
    except S3Error:
        # Ignore if not found
        pass


def get_file(object_uri: str) -> Optional[io.BytesIO]:
    """Retrieve a file from MinIO by its stored URI path (minio://bucket/object)."""
    if not object_uri.startswith("minio://"):
        return None
    _, remainder = object_uri.split("://", 1)
    bucket, object_name = remainder.split("/", 1)

    client = _get_minio_client()
    try:
        response = client.get_object(bucket, object_name)
        data = response.read()
        response.close()
        response.release_conn()
        return io.BytesIO(data)
    except S3Error:
        return None

