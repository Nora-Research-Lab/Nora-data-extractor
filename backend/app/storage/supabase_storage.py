import tempfile
from pathlib import Path
import httpx
from .base import StorageBackend


class SupabaseStorage(StorageBackend):
    """Uses Supabase Storage's REST API directly (no supabase-py dependency needed)."""

    def __init__(self, project_url: str, service_key: str, bucket: str):
        self.base = project_url.rstrip("/")
        self.bucket = bucket
        self.headers = {
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
        }

    def _obj_url(self, remote_key: str) -> str:
        return f"{self.base}/storage/v1/object/{self.bucket}/{remote_key}"

    def save_file(self, local_path: str | Path, remote_key: str) -> str:
        with open(local_path, "rb") as f:
            r = httpx.put(
                self._obj_url(remote_key),
                headers={**self.headers, "x-upsert": "true"},
                content=f.read(),
                timeout=120,
            )
            r.raise_for_status()
        return remote_key

    def get_local_path(self, remote_key: str) -> str:
        r = httpx.get(self._obj_url(remote_key), headers=self.headers, timeout=120)
        r.raise_for_status()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(remote_key).suffix)
        tmp.write(r.content)
        tmp.close()
        return tmp.name

    def get_download_url(self, remote_key: str, expires_seconds: int = 3600) -> str:
        r = httpx.post(
            f"{self.base}/storage/v1/object/sign/{self.bucket}/{remote_key}",
            headers=self.headers,
            json={"expiresIn": expires_seconds},
            timeout=30,
        )
        r.raise_for_status()
        signed_path = r.json()["signedURL"]
        return f"{self.base}/storage/v1{signed_path}"

    def delete(self, remote_key: str) -> None:
        httpx.delete(
            f"{self.base}/storage/v1/object/{self.bucket}",
            headers=self.headers,
            json={"prefixes": [remote_key]},
            timeout=30,
        )

    def exists(self, remote_key: str) -> bool:
        r = httpx.head(self._obj_url(remote_key), headers=self.headers, timeout=30)
        return r.status_code == 200
