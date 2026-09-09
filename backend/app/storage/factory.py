from functools import lru_cache
from ..config import get_settings
from .base import StorageBackend
from .local_storage import LocalStorage


@lru_cache
def get_storage() -> StorageBackend:
    s = get_settings()
    if s.STORAGE_BACKEND == "local":
        return LocalStorage(s.LOCAL_STORAGE_DIR)
    if s.STORAGE_BACKEND == "s3":
        from .s3_storage import S3Storage
        return S3Storage(s.S3_BUCKET, s.S3_ENDPOINT_URL, s.S3_ACCESS_KEY, s.S3_SECRET_KEY, s.S3_REGION)
    if s.STORAGE_BACKEND == "supabase":
        from .supabase_storage import SupabaseStorage
        return SupabaseStorage(s.SUPABASE_URL, s.SUPABASE_SERVICE_KEY, s.SUPABASE_BUCKET)
    raise ValueError(f"Unknown STORAGE_BACKEND: {s.STORAGE_BACKEND}")
