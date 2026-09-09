"""Vector clip/reproject/simplify/dissolve/filter/buffer built on GeoPandas + Shapely."""
import geopandas as gpd
from shapely.geometry import base as shp_base


def load_vector(source_uri: str, bbox_4326: tuple[float, float, float, float] | None = None) -> gpd.GeoDataFrame:
    """
    Reads a vector source. When the driver/format supports it, `bbox` pre-filters
    at read time (pyogrio/fiona push this down to avoid loading unrelated features).
    """
    if bbox_4326:
        gdf = gpd.read_file(source_uri, bbox=bbox_4326)
    else:
        gdf = gpd.read_file(source_uri)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    return gdf


def clip_vector(gdf: gpd.GeoDataFrame, aoi_geom_4326) -> gpd.GeoDataFrame:
    aoi_gdf = gpd.GeoDataFrame(geometry=[aoi_geom_4326], crs="EPSG:4326")
    if gdf.crs != aoi_gdf.crs:
        aoi_gdf = aoi_gdf.to_crs(gdf.crs)
    clipped = gpd.clip(gdf, aoi_gdf)
    return clipped


def reproject_vector(gdf: gpd.GeoDataFrame, dst_crs: str) -> gpd.GeoDataFrame:
    return gdf.to_crs(dst_crs)


def simplify_vector(gdf: gpd.GeoDataFrame, tolerance: float) -> gpd.GeoDataFrame:
    out = gdf.copy()
    out["geometry"] = out.geometry.simplify(tolerance, preserve_topology=True)
    return out


def dissolve_vector(gdf: gpd.GeoDataFrame, by: str | None) -> gpd.GeoDataFrame:
    if by and by in gdf.columns:
        return gdf.dissolve(by=by).reset_index()
    return gdf.dissolve()


def buffer_vector(gdf: gpd.GeoDataFrame, meters: float) -> gpd.GeoDataFrame:
    out = gdf.copy()
    metric_crs = out.estimate_utm_crs()
    out = out.to_crs(metric_crs)
    out["geometry"] = out.geometry.buffer(meters)
    return out.to_crs(gdf.crs)


def filter_vector(gdf: gpd.GeoDataFrame, query: str) -> gpd.GeoDataFrame:
    try:
        return gdf.query(query)
    except Exception as e:
        raise ValueError(f"Invalid attribute_filter expression: {e}")
