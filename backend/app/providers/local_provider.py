from pathlib import Path
from .base import DatasetProvider
from ..schemas.dataset import DatasetMetadata
from ..config import get_settings


class LocalProvider(DatasetProvider):
    """Reads datasets from a local directory (dev/test, or datasets baked into the deployment image)."""

    def resolve(self, dataset: DatasetMetadata) -> str:
        base = Path(get_settings().LOCAL_DATASET_DIR)
        path = (base / dataset.provider_uri).resolve()
        if base.resolve() not in path.parents and path != base.resolve():
            raise ValueError("Invalid dataset path (outside local dataset directory)")
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {dataset.provider_uri}")
        return str(path)
