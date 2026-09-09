import shutil
from pathlib import Path
from .base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, root_dir: str):
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, remote_key: str) -> Path:
        # prevent path traversal outside the storage root
        candidate = (self.root / remote_key).resolve()
        if self.root.resolve() not in candidate.parents and candidate != self.root.resolve():
            raise ValueError("Invalid storage key (path traversal attempt)")
        return candidate

    def save_file(self, local_path: str | Path, remote_key: str) -> str:
        dest = self._resolve(remote_key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if Path(local_path).resolve() != dest.resolve():
            shutil.copy2(local_path, dest)
        return remote_key

    def get_local_path(self, remote_key: str) -> str:
        return str(self._resolve(remote_key))

    def get_download_url(self, remote_key: str, expires_seconds: int = 3600) -> str:
        # Served through the API's own download endpoint rather than a static URL.
        return f"/api/files/{remote_key}"

    def delete(self, remote_key: str) -> None:
        p = self._resolve(remote_key)
        if p.exists():
            p.unlink()

    def exists(self, remote_key: str) -> bool:
        return self._resolve(remote_key).exists()
