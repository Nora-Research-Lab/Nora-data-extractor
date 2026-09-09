from typing import Literal, Optional
from pydantic import BaseModel, Field

GeometryType = Literal["raster", "point", "line", "polygon", "table"]
DatasetKind = Literal["raster", "vector"]


class DatasetMetadata(BaseModel):
    id: str
    name: str
    description: str = ""
    category: str = "general"
    kind: DatasetKind
    format: str  # native storage format, e.g. "COG", "GeoTIFF", "GeoPackage"
    geometry_type: GeometryType
    crs: str = "EPSG:4326"
    coverage: str = "global"
    resolution: Optional[str] = None  # e.g. "30m" for raster
    units: Optional[str] = None
    source: str = ""
    license: str = "unknown"
    available_export_formats: list[str] = Field(default_factory=list)

    # --- how to actually locate the data ---
    provider: Literal["local", "http", "object_storage", "agdfs"] = "local"
    provider_uri: str  # local path, URL, or object-storage key/prefix depending on provider

    class Config:
        extra = "allow"


RASTER_FORMATS = ["GeoTIFF", "COG"]
VECTOR_FORMATS = ["GeoPackage", "GeoJSON", "GeoParquet", "Shapefile", "CSV", "KML"]

FORMAT_DESCRIPTIONS = {
    "GeoJSON": "Good for web maps and smaller datasets.",
    "GeoParquet": "Good for large analytical datasets.",
    "GeoPackage": "Good for GIS software such as QGIS.",
    "Shapefile": "Widely compatible legacy GIS format.",
    "CSV": "Good for tabular/point data and spreadsheets.",
    "KML": "Good for Google Earth and simple sharing.",
    "COG": "Good for large raster datasets and cloud processing.",
    "GeoTIFF": "Standard raster format, compatible with most GIS software.",
}
