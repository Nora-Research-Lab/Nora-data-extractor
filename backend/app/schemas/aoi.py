from typing import Literal, Optional, Any
from pydantic import BaseModel, model_validator


class BBox(BaseModel):
    north: float
    south: float
    east: float
    west: float

    @model_validator(mode="after")
    def check(self):
        if not (-90 <= self.south < self.north <= 90):
            raise ValueError("Invalid latitude range: require -90 <= south < north <= 90")
        if not (-180 <= self.west <= 180 and -180 <= self.east <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        return self


class CircleAOI(BaseModel):
    center_lat: float
    center_lon: float
    radius_km: float


class AOIRequest(BaseModel):
    """
    Exactly one of the source fields should be populated. `aoi_type` tells the
    server which one to look at, so the frontend doesn't have to omit keys.
    """
    aoi_type: Literal["bbox", "polygon", "rectangle", "circle", "point_buffer", "geojson", "admin_boundary", "place"]
    bbox: Optional[BBox] = None
    circle: Optional[CircleAOI] = None
    geojson: Optional[dict[str, Any]] = None  # Feature / FeatureCollection / Geometry
    admin_boundary_id: Optional[str] = None
    place_query: Optional[str] = None


class AOIValidationResult(BaseModel):
    valid: bool
    area_km2: Optional[float] = None
    bbox: Optional[BBox] = None
    geojson: Optional[dict[str, Any]] = None
    errors: list[str] = []
    warnings: list[str] = []
