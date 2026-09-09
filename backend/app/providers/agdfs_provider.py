from .http_provider import HTTPProvider
from ..schemas.dataset import DatasetMetadata
from ..config import get_settings


class AGDFSProvider(HTTPProvider):
    """
    Thin adapter over HTTPProvider for datasets served by NORA's AGDFS pipeline
    (https://agdfs.onrender.com). `provider_uri` on the dataset is the path/id
    relative to AGDFS_BASE_URL, e.g. "datasets/global_geology/tile_04.tif".

    This class is intentionally the ONLY place that knows about AGDFS -
    the extraction/processing engine never imports it directly, so AGDFS can
    be swapped or removed without touching core logic.
    """

    def resolve(self, dataset: DatasetMetadata) -> str:
        base = get_settings().AGDFS_BASE_URL.rstrip("/")
        path = dataset.provider_uri.lstrip("/")
        full_url = f"{base}/{path}"
        proxy = DatasetMetadata(**{**dataset.model_dump(), "provider_uri": full_url})
        return super().resolve(proxy)
