import os
import dotenv

dotenv.load_dotenv()


class DatabaseConfig:
    HOST = os.getenv("DB_HOST", "localhost")
    PORT = os.getenv("DB_PORT", "3306")
    USER = os.getenv("DB_USER", "root")
    PASSWORD = os.getenv("DB_PASSWORD", "root")
    DATABASE = os.getenv("DB_NAME", "cnv_pgt_db")
    DATA_SOURCE = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"


class MinioConfig:
    ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "root")
    SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "miniorootpw")
    USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"
    BUCKET = os.getenv("MINIO_BUCKET", "cnv-bucket")


class SandboxConfig:
    SANDBOX_INSTALLER_URL = os.getenv(
        "SANDBOX_INSTALLER_URL", "http://localhost:8001/api/v1/installer"
    )
    SANDBOX_RUNNER_URL = os.getenv(
        "SANDBOX_RUNNER_URL", "http://localhost:8016/api/v1/runner"
    )
