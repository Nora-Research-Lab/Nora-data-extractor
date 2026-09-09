from app.schemas.aoi import AOIRequest, BBox
from app.services.aoi_service import validate_aoi, resolve_geometry


def test_valid_bbox():
    req = AOIRequest(aoi_type="bbox", bbox=BBox(north=8.2, south=7.7, east=4.1, west=3.6))
    result = validate_aoi(req)
    assert result.valid
    assert result.area_km2 > 0
    assert result.bbox.north == 8.2


def test_invalid_bbox_flipped():
    with __import__("pytest").raises(Exception):
        BBox(north=7.0, south=8.0, east=4.1, west=3.6)


def test_polygon_geojson():
    poly = {
        "type": "Polygon",
        "coordinates": [[[3.6, 7.7], [4.1, 7.7], [4.1, 8.2], [3.6, 8.2], [3.6, 7.7]]],
    }
    req = AOIRequest(aoi_type="geojson", geojson=poly)
    result = validate_aoi(req)
    assert result.valid


def test_area_too_large_rejected(monkeypatch):
    from app.services import aoi_service

    class TinyLimitSettings:
        MAX_AOI_AREA_KM2 = 1000.0

    monkeypatch.setattr(aoi_service, "get_settings", lambda: TinyLimitSettings())

    # ~3,048 km^2 - fine normally, but exceeds the 1,000 km^2 limit patched in above.
    req = AOIRequest(aoi_type="bbox", bbox=BBox(north=8.2, south=7.7, east=4.1, west=3.6))
    result = validate_aoi(req)
    assert not result.valid
    assert any("exceeds the maximum" in e for e in result.errors)


def test_circle_resolves_to_polygon():
    req = AOIRequest(aoi_type="circle", circle={"center_lat": 7.9, "center_lon": 3.9, "radius_km": 10})
    geom = resolve_geometry(req)
    assert geom.geom_type == "Polygon"
    assert geom.area > 0
