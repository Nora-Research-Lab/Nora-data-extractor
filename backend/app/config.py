"""Central configuration. All values overridable via environment variables (.env)."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "NORA Data Extractor"
    ENV: str = "development"  # development | production

    # --- Storage backend selection: "local" | "s3" | "supabase" ---
    STORAGE_BACKEND: str = "local"

    LOCAL_STORAGE_DIR: str = "./storage_data"
    LOCAL_DATASET_DIR: str = "./sample_datasets"  # where "local" provider datasets live

    # S3-compatible object storage (also used for MinIO, Wasabi, etc.)
    S3_ENDPOINT_URL: str | None = None
    S3_BUCKET: str | None = None
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    S3_REGION: str = "us-east-1"

    # Supabase Storage
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_KEY: str | None = None
    SUPABASE_BUCKET: str = "nora-datasets"

    # AGDFS provider
    AGDFS_BASE_URL: str = "https://agdfs.onrender.com"

    # Job / extraction limits
    TEMP_DIR: str = "./tmp"
    MAX_UPLOAD_MB: int = 200
    MAX_AOI_AREA_KM2: float = 5_000_000  # sanity cap to avoid runaway extractions
    JOB_RETENTION_HOURS: int = 24
    JOB_STORE_PATH: str = "./tmp/jobs.json"
    MAX_WORKERS: int = 2

    DATASET_REGISTRY_PATH: str = "./data/datasets_registry.json"

    CORS_ORIGINS: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
