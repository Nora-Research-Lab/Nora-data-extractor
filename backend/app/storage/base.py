from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    """
    Abstraction over where OUTPUT/job artifacts live. Not to be confused with
    DatasetProvider (app/providers), which is about where SOURCE datasets live.
    """

    @abstractmethod
    def save_file(self, local_path: str | Path, remote_key: str) -> str:
        """Upload/copy a local file to the backend. Returns the remote key/path."""

    @abstractmethod
    def get_local_path(self, remote_key: str) -> str:
        """Return a local filesystem path usable to read the object (download if needed)."""

    @abstractmethod
    def get_download_url(self, remote_key: str, expires_seconds: int = 3600) -> str:
        """Return a URL (or API path) the client can use to download the object."""

    @abstractmethod
    def delete(self, remote_key: str) -> None:
        ...

    @abstractmethod
    def exists(self, remote_key: str) -> bool:
        ...
