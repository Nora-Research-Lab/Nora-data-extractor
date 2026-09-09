import json
from functools import lru_cache
from pathlib import Path
from ..config import get_settings
from ..schemas.dataset import DatasetMetadata


class DatasetRegistry:
    """
    Single source of truth for what datasets exist. The extractor never has
    dataset-specific `if dataset_id == "global_dem"` logic anywhere - every
    behavior (recommended format, provider, CRS, etc.) is driven by this
    registry so adding a dataset is a data change, not a code change.
    """

    def __init__(self, path: str):
        self._path = Path(path)
        self._datasets: dict[str, DatasetMetadata] = {}
        self.reload()

    def reload(self) -> None:
        if not self._path.exists():
            self._datasets = {}
            return
        raw = json.loads(self._path.read_text())
        self._datasets = {d["id"]: DatasetMetadata(**d) for d in raw}

    def list(self) -> list[DatasetMetadata]:
        return list(self._datasets.values())

    def get(self, dataset_id: str) -> DatasetMetadata | None:
        return self._datasets.get(dataset_id)

    def add_or_update(self, dataset: DatasetMetadata) -> None:
        """Register a new dataset at runtime and persist it to the registry file."""
        self._datasets[dataset.id] = dataset
        raw = [d.model_dump() for d in self._datasets.values()]
        self._path.write_text(json.dumps(raw, indent=2))


@lru_cache
def get_registry() -> DatasetRegistry:
    return DatasetRegistry(get_settings().DATASET_REGISTRY_PATH)
