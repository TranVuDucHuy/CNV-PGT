import os

class DatabaseConfig:
    HOST = os.getenv("DB_HOST", "localhost")
    PORT = os.getenv("DB_PORT", "3306")
    USER = os.getenv("DB_USER", "root")
    PASSWORD = os.getenv("DB_PASSWORD", "root")
    DATA_SOURCE = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/cnv_pgt_db"

class MinioConfig:
    ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"
    BUCKET = os.getenv("MINIO_BUCKET", "cnv-bucket")