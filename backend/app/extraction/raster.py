"""
Raster clipping/reprojection built on rasterio/GDAL. Uses windowed reads via
`mask(..., crop=True)` against a dataset handle opened directly on the source
URI (local path, /vsicurl/ URL, etc.) - the full global raster is never loaded
into memory, only the window covering the AOI.
"""
from pathlib import Path
import rasterio
from rasterio.mask import mask as rio_mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import mapping


_RESAMPLING = {
    "nearest": Resampling.nearest,
    "bilinear": Resampling.bilinear,
    "cubic": Resampling.cubic,
}


def clip_raster(source_uri: str, aoi_geom_4326, out_path: str) -> dict:
    """Clip `source_uri` to the AOI polygon (in EPSG:4326). Writes a GeoTIFF to out_path."""
    with rasterio.open(source_uri) as src:
        aoi_in_src_crs = aoi_geom_4326
        if src.crs and str(src.crs) != "EPSG:4326":
            from pyproj import Transformer
            from shapely.ops import transform as shp_transform
            transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True).transform
            aoi_in_src_crs = shp_transform(transformer, aoi_geom_4326)

        out_image, out_transform = rio_mask(src, [mapping(aoi_in_src_crs)], crop=True, filled=True)
        out_meta = src.meta.copy()
        out_meta.update({
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
        })

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_path, "w", **out_meta) as dst:
        dst.write(out_image)

    return {"width": out_meta["width"], "height": out_meta["height"], "crs": str(out_meta.get("crs"))}


def reproject_raster(in_path: str, out_path: str, dst_crs: str,
                      resampling: str = "nearest", target_resolution: float | None = None) -> dict:
    with rasterio.open(in_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds,
            resolution=target_resolution,
        )
        kwargs = src.meta.copy()
        kwargs.update({"crs": dst_crs, "transform": transform, "width": width, "height": height})

        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(out_path, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=_RESAMPLING.get(resampling, Resampling.nearest),
                )
    return {"width": width, "height": height, "crs": dst_crs}


def approximate_output_size_mb(source_uri: str, aoi_geom_4326) -> float | None:
    """Rough estimate for the UI ('approximate output size') without doing a full extraction."""
    try:
        with rasterio.open(source_uri) as src:
            minx, miny, maxx, maxy = aoi_geom_4326.bounds
            import numpy as np
            px_w = (maxx - minx) / abs(src.transform.a)
            px_h = (maxy - miny) / abs(src.transform.e)
            dtype_bytes = np.dtype(src.dtypes[0]).itemsize
            n_bytes = px_w * px_h * src.count * dtype_bytes
            return round(n_bytes / (1024 * 1024), 2)
    except Exception:
        return None
