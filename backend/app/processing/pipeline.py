"""
Runs one dataset through: locate -> clip -> processing ops -> convert -> write.
This is the only module that needs to change to support a brand-new PROCESSING
OPERATION (see docs/adding_a_processing_operation.md); it has no dataset-specific
branches, only kind-specific (raster vs vector) ones.
"""
import tempfile
from pathlib import Path

from ..schemas.dataset import DatasetMetadata
from ..schemas.extraction import ProcessingOptions
from ..providers.registry import resolve_dataset_path
from ..extraction import raster as raster_ext
from ..extraction import vector as vector_ext
from ..conversion import raster_convert, vector_convert
from ..services.format_recommender import recommended_format


def process_dataset(dataset: DatasetMetadata, aoi_geom_4326, options: ProcessingOptions,
                     output_format: str | None, work_dir: str) -> dict:
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    fmt = output_format or recommended_format(dataset)
    source_uri = resolve_dataset_path(dataset)

    if dataset.kind == "raster":
        return _process_raster(dataset, source_uri, aoi_geom_4326, options, fmt, work)
    return _process_vector(dataset, source_uri, aoi_geom_4326, options, fmt, work)


def _process_raster(dataset, source_uri, aoi_geom_4326, options: ProcessingOptions, fmt: str, work: Path) -> dict:
    # Intermediate files (clip, reproject) go in a scratch dir OUTSIDE `work` so
    # only final deliverables end up in the study-area package that gets zipped.
    scratch = Path(tempfile.mkdtemp(prefix=f"{dataset.id}_scratch_"))
    try:
        clipped_path = str(scratch / f"{dataset.id}_clipped.tif")
        info = raster_ext.clip_raster(source_uri, aoi_geom_4326, clipped_path)

        current = clipped_path
        if options.reproject_to:
            reprojected_path = str(scratch / f"{dataset.id}_reprojected.tif")
            info = raster_ext.reproject_raster(
                current, reprojected_path, options.reproject_to,
                resampling=options.resample or "nearest",
                target_resolution=options.target_resolution,
            )
            current = reprojected_path

        ext = raster_convert.EXTENSIONS[fmt]
        final_path = str(work / f"{dataset.id}{ext}")
        raster_convert.write_raster(current, final_path, fmt)
    finally:
        import shutil
        shutil.rmtree(scratch, ignore_errors=True)

    return {"dataset_id": dataset.id, "kind": "raster", "format": fmt, "path": final_path, **info}


def _process_vector(dataset, source_uri, aoi_geom_4326, options: ProcessingOptions, fmt: str, work: Path) -> dict:
    bbox = aoi_geom_4326.bounds
    gdf = vector_ext.load_vector(source_uri, bbox_4326=bbox)

    if options.clip:
        gdf = vector_ext.clip_vector(gdf, aoi_geom_4326)

    if options.attribute_filter:
        gdf = vector_ext.filter_vector(gdf, options.attribute_filter)

    if options.dissolve:
        gdf = vector_ext.dissolve_vector(gdf, options.dissolve_by)

    if options.buffer_meters:
        gdf = vector_ext.buffer_vector(gdf, options.buffer_meters)

    if options.simplify_tolerance:
        gdf = vector_ext.simplify_vector(gdf, options.simplify_tolerance)

    if options.reproject_to:
        gdf = vector_ext.reproject_vector(gdf, options.reproject_to)

    ext = vector_convert.EXTENSIONS[fmt]
    final_path = str(work / f"{dataset.id}{ext}")
    vector_convert.write_vector(gdf, final_path, fmt)

    return {
        "dataset_id": dataset.id, "kind": "vector", "format": fmt, "path": final_path,
        "feature_count": len(gdf), "crs": str(gdf.crs),
    }
