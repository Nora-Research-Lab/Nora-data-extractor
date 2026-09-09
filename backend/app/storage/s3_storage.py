import tempfile
from pathlib import Path
from .base import StorageBackend


class S3Storage(StorageBackend):
    """Works with AWS S3 and any S3-compatible endpoint (MinIO, Wasabi, R2, Supabase's S3 endpoint)."""

    def __init__(self, bucket: str, endpoint_url: str | None, access_key: str | None,
                 secret_key: str | None, region: str = "us-east-1"):
        import boto3  # local import: keep boto3 optional unless this backend is selected
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    def save_file(self, local_path: str | Path, remote_key: str) -> str:
        self.client.upload_file(str(local_path), self.bucket, remote_key)
        return remote_key

    def get_local_path(self, remote_key: str) -> str:
        suffix = Path(remote_key).suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.close()
        self.client.download_file(self.bucket, remote_key, tmp.name)
        return tmp.name

    def get_download_url(self, remote_key: str, expires_seconds: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": remote_key},
            ExpiresIn=expires_seconds,
        )

    def delete(self, remote_key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=remote_key)

    def exists(self, remote_key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=remote_key)
            return True
        except Exception:
            return False
