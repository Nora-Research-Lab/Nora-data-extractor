# Adding a new output format

Formats are handled in `app/conversion/`, one function per kind.

## Vector format (e.g. FlatGeobuf)

1. In `app/conversion/vector_convert.py`, add the extension:
   ```python
   EXTENSIONS = {..., "FlatGeobuf": ".fgb"}
   _DRIVER = {..., "FlatGeobuf": "FlatGeobuf"}  # if it's a GDAL/OGR driver
   ```
2. If it needs special handling (like GeoParquet/CSV do), add a branch in
   `write_vector()` before the generic `gdf.to_file(..., driver=...)` call.
3. Add it to the relevant datasets' `available_export_formats` in
   `datasets_registry.json` (or leave it off the registry and it'll still work
   via `/api/convert` for ad-hoc conversions).

## Raster format (e.g. NetCDF)

1. Add the extension to `app/conversion/raster_convert.py`'s `EXTENSIONS`.
2. Add a branch in `write_raster()`. For most GDAL-supported raster drivers
   this is a rasterio `profile.update(driver=...)` + copy, same pattern as
   the `GeoTIFF` branch. For NetCDF/Zarr specifically, see
   `docs/netcdf_zarr_notes.md` below.

## Update the UI copy (optional)

`FORMAT_DESCRIPTIONS` in `app/schemas/dataset.py` supplies the one-line
plain-language explanation shown in the frontend (`"Good for GIS software
such as QGIS."` etc). Add an entry there for the new format.

## NetCDF / Zarr (architecture note)

The spec asks for these to be *prepared for*, not fully implemented. The
seam is the same `write_raster()` function - a NetCDF/Zarr writer would take
the clipped GeoTIFF (or, better, operate on the xarray/rioxarray object
directly before it's ever written to GeoTIFF) and write a multi-dimensional
array store instead. Recommended path: add `rioxarray`, open the clipped
raster with `rioxarray.open_rasterio()`, and call `.to_netcdf()` /
`.to_zarr()`. Keep it behind the same `fmt` dispatch so nothing upstream
changes.
