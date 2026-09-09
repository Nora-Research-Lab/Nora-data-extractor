from ..schemas.dataset import DatasetMetadata, RASTER_FORMATS, VECTOR_FORMATS, FORMAT_DESCRIPTIONS


def recommended_format(dataset: DatasetMetadata) -> str:
    return "COG" if dataset.kind == "raster" else "GeoPackage"


def available_formats(dataset: DatasetMetadata) -> list[dict]:
    if dataset.available_export_formats:
        names = dataset.available_export_formats
    else:
        names = RASTER_FORMATS if dataset.kind == "raster" else VECTOR_FORMATS
    rec = recommended_format(dataset)
    return [
        {
            "format": name,
            "description": FORMAT_DESCRIPTIONS.get(name, ""),
            "recommended": name == rec,
        }
        for name in names
    ]
