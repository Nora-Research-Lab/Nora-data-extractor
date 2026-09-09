"""
Turns any supported AOIRequest into a canonical shapely geometry (in EPSG:4326)
plus its bounding box, and validates it. This is the ONLY place AOI shapes get
interpreted - everything downstream (extraction, preview) just consumes the
resulting geometry.
"""
import math
from shapely.geometry import shape, box, mapping, Point
from shapely.ops import transform
from shapely.validation import explain_validity
import pyproj

from ..config import get_settings
from ..schemas.aoi import AOIRequest, AOIValidationResult, BBox


def _geodesic_area_km2(geom) -> float:
    geod = pyproj.Geod(ellps="WGS84")
    area_m2, _ = geod.geometry_area_perimeter(geom)
    return abs(area_m2) / 1_000_000


def _circle_to_polygon(center_lat: float, center_lon: float, radius_km: float, segments: int = 64):
    # Build the circle in an azimuthal-equidistant projection centered on the point, then reproject back.
    proj_str = f"+proj=aeqd +lat_0={center_lat} +lon_0={center_lon} +units=m +ellps=WGS84"
    aeqd = pyproj.CRS.from_proj4(proj_str)
    to_local = pyproj.Transformer.from_crs("EPSG:4326", aeqd, always_xy=True).transform
    to_wgs84 = pyproj.Transformer.from_crs(aeqd, "EPSG:4326", always_xy=True).transform
    center_local = Point(0, 0)
    circle_local = center_local.buffer(radius_km * 1000, quad_segs=segments // 4)
    return transform(to_wgs84, circle_local)


def resolve_geometry(aoi: AOIRequest):
    """Returns a shapely geometry in EPSG:4326, or raises ValueError."""
    if aoi.aoi_type in ("bbox", "rectangle"):
        if not aoi.bbox:
            raise ValueError("bbox is required for aoi_type='bbox'/'rectangle'")
        b = aoi.bbox
        return box(b.west, b.south, b.east, b.north)

    if aoi.aoi_type == "circle":
        if not aoi.circle:
            raise ValueError("circle is required for aoi_type='circle'")
        c = aoi.circle
        return _circle_to_polygon(c.center_lat, c.center_lon, c.radius_km)

    if aoi.aoi_type in ("polygon", "geojson"):
        if not aoi.geojson:
            raise ValueError("geojson is required for aoi_type='polygon'/'geojson'")
        gj = aoi.geojson
        if gj.get("type") == "FeatureCollection":
            geoms = [shape(f["geometry"]) for f in gj["features"]]
            geom = geoms[0]
            for g in geoms[1:]:
                geom = geom.union(g)
            return geom
        if gj.get("type") == "Feature":
            return shape(gj["geometry"])
        return shape(gj)

    if aoi.aoi_type == "admin_boundary":
        raise ValueError(
            "admin_boundary lookup requires an administrative-boundary dataset to be "
            "registered and configured (see docs/adding_a_dataset.md); none is configured yet."
        )

    if aoi.aoi_type == "place":
        raise ValueError(
            "place search requires a geocoding provider to be configured; none is configured yet."
        )

    raise ValueError(f"Unsupported aoi_type: {aoi.aoi_type}")


def validate_aoi(aoi: AOIRequest) -> AOIValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        geom = resolve_geometry(aoi)
    except ValueError as e:
        return AOIValidationResult(valid=False, errors=[str(e)])

    if not geom.is_valid:
        errors.append(f"Geometry is not valid: {explain_validity(geom)}")
    if geom.is_empty:
        errors.append("Geometry is empty")

    if errors:
        return AOIValidationResult(valid=False, errors=errors)

    minx, miny, maxx, maxy = geom.bounds
    if not (-180 <= minx <= 180 and -180 <= maxx <= 180 and -90 <= miny <= 90 and -90 <= maxy <= 90):
        errors.append("Geometry extends outside valid WGS84 bounds")
        return AOIValidationResult(valid=False, errors=errors)

    area_km2 = _geodesic_area_km2(geom)
    max_area = get_settings().MAX_AOI_AREA_KM2
    if area_km2 > max_area:
        errors.append(
            f"Area of interest ({area_km2:,.0f} km²) exceeds the maximum allowed ({max_area:,.0f} km²)."
        )
        return AOIValidationResult(valid=False, errors=errors)
    if area_km2 > max_area * 0.2:
        warnings.append("This is a large area - extraction may take a while.")

    return AOIValidationResult(
        valid=True,
        area_km2=round(area_km2, 3),
        bbox=BBox(north=maxy, south=miny, east=maxx, west=minx),
        geojson=mapping(geom),
        warnings=warnings,
    )
