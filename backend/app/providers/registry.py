from .base import DatasetProvider
from .local_provider import LocalProvider
from .http_provider import HTTPProvider
from .object_storage_provider import ObjectStorageProvider
from .agdfs_provider import AGDFSProvider
from ..schemas.dataset import DatasetMetadata

_PROVIDERS: dict[str, DatasetProvider] = {
    "local": LocalProvider(),
    "http": HTTPProvider(),
    "object_storage": ObjectStorageProvider(),
    "agdfs": AGDFSProvider(),
}


def resolve_dataset_path(dataset: DatasetMetadata) -> str:
    provider = _PROVIDERS.get(dataset.provider)
    if provider is None:
        raise ValueError(f"No provider registered for '{dataset.provider}'")
    return provider.resolve(dataset)
