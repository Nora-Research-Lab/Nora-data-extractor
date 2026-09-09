import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

from app.extraction.raster import clip_raster


def _make_test_raster(path):
    width, height = 100, 100
    transform = from_origin(0, 10, 0.1, 0.1)  # covers lon 0-10, lat 0-10
    data = np.arange(width * height, dtype="float32").reshape(height, width)
    with rasterio.open(
        path, "w", driver="GTiff", height=height, width=width, count=1,
        dtype="float32", crs="EPSG:4326", transform=transform,
    ) as dst:
        dst.write(data, 1)


def test_clip_raster_reduces_extent(tmp_path):
    src_path = tmp_path / "src.tif"
    out_path = tmp_path / "clipped.tif"
    _make_test_raster(src_path)

    aoi = box(2, 2, 4, 4)  # a 2x2 degree window well inside the source
    info = clip_raster(str(src_path), aoi, str(out_path))

    assert out_path.exists()
    assert info["width"] < 100
    assert info["height"] < 100

    with rasterio.open(out_path) as clipped:
        minx, miny, maxx, maxy = clipped.bounds
        assert minx >= 1.9 and maxx <= 4.1
        assert miny >= 1.9 and maxy <= 4.1
