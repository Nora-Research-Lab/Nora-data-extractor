from .base import DatasetProvider
from ..schemas.dataset import DatasetMetadata
from ..storage.factory import get_storage


class ObjectStorageProvider(DatasetProvider):
    """Source datasets that live in the same object-storage backend used for output artifacts."""

    def resolve(self, dataset: DatasetMetadata) -> str:
        storage = get_storage()
        return storage.get_local_path(dataset.provider_uri)
