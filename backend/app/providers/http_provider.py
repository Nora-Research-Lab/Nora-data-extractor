from .base import DatasetProvider
from ..schemas.dataset import DatasetMetadata


class HTTPProvider(DatasetProvider):
    """
    For datasets served over plain HTTP(S). For raster COGs this returns a
    GDAL virtual-file-system URI so rasterio can do windowed/ranged reads
    without downloading the whole file. Vector formats are downloaded fully
    since GeoPandas generally needs the complete file.
    """

    def resolve(self, dataset: DatasetMetadata) -> str:
        url = dataset.provider_uri
        if not url.startswith(("http://", "https://")):
            raise ValueError("HTTPProvider requires provider_uri to be a full URL")

        if dataset.kind == "raster" and dataset.format.upper() == "COG":
            scheme = "vsicurl"
            return f"/{scheme}/{url}"

        # Vector / non-COG raster: download to a temp file.
        import tempfile
        import httpx

        suffix = "." + url.split(".")[-1] if "." in url.split("/")[-1] else ""
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        with httpx.stream("GET", url, timeout=120, follow_redirects=True) as r:
            r.raise_for_status()
            for chunk in r.iter_bytes(1 << 20):
                tmp.write(chunk)
        tmp.close()
        return tmp.name
