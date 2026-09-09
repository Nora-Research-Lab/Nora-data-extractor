from abc import ABC, abstractmethod
from ..schemas.dataset import DatasetMetadata


class DatasetProvider(ABC):
    """
    Resolves a DatasetMetadata's `provider_uri` into a local file path the
    extraction engine can open with rasterio/geopandas. Implementations should
    avoid downloading more than necessary (e.g. use range requests / windowed
    reads for cloud-native formats where possible).
    """

    @abstractmethod
    def resolve(self, dataset: DatasetMetadata) -> str:
        """Return a local path or a GDAL/rasterio-readable URI (e.g. /vsicurl/...)."""
