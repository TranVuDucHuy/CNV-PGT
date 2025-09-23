from __future__ import annotations

import io
from typing import Optional

from flask import current_app
from minio import Minio
from minio.error import S3Error


def _get_minio_client() -> Minio:
    cfg = current_app.config
    return Minio(
        cfg["MINIO_ENDPOINT"],
        access_key=cfg["MINIO_ACCESS_KEY"],
        secret_key=cfg["MINIO_SECRET_KEY"],
        secure=cfg["MINIO_USE_SSL"],
    )


def ensure_bucket_exists(bucket_name: str) -> None:
    client = _get_minio_client()
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)


def save_file(file_stream: io.BytesIO, object_name: str, content_type: Optional[str] = None) -> str:
    """Save a file to MinIO and return the object URL path.

    Returns a path like "minio://bucket/object" for storing in DB.
    """
    cfg = current_app.config
    bucket = cfg["MINIO_BUCKET"]
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


