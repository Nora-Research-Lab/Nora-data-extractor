from pathlib import Path
import geopandas as gpd

_DRIVER = {
    "GeoJSON": "GeoJSON",
    "GeoPackage": "GPKG",
    "Shapefile": "ESRI Shapefile",
    "KML": "KML",
}


def write_vector(gdf: gpd.GeoDataFrame, out_path: str, fmt: str) -> str:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    if fmt == "GeoParquet":
        gdf.to_parquet(out_path)
        return out_path

    if fmt == "CSV":
        flat = gdf.copy()
        flat["geometry_wkt"] = flat.geometry.apply(lambda g: g.wkt if g is not None else None)
        flat.drop(columns="geometry").to_csv(out_path, index=False)
        return out_path

    driver = _DRIVER.get(fmt)
    if not driver:
        raise ValueError(f"Unsupported vector output format: {fmt}")

    if fmt == "KML":
        # KML requires lon/lat.
        gdf = gdf.to_crs("EPSG:4326")

    gdf.to_file(out_path, driver=driver)
    return out_path


EXTENSIONS = {
    "GeoJSON": ".geojson",
    "GeoPackage": ".gpkg",
    "GeoParquet": ".parquet",
    "Shapefile": ".shp",
    "CSV": ".csv",
    "KML": ".kml",
}
