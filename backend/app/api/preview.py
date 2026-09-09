from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..schemas.aoi import AOIRequest
from ..services.aoi_service import validate_aoi, resolve_geometry
from ..services.dataset_registry import get_registry
from ..providers.registry import resolve_dataset_path
from ..extraction.raster import approximate_output_size_mb

router = APIRouter(tags=["preview"])


class PreviewRequest(BaseModel):
    aoi: AOIRequest
    dataset_ids: list[str]


@router.post("/api/preview")
def preview(req: PreviewRequest):
    validation = validate_aoi(req.aoi)
    if not validation.valid:
        raise HTTPException(status_code=400, detail={"aoi_errors": validation.errors})

    aoi_geom = resolve_geometry(req.aoi)
    registry = get_registry()
    dataset_previews = []
    for dsid in req.dataset_ids:
        d = registry.get(dsid)
        if d is None:
            dataset_previews.append({"dataset_id": dsid, "error": "unknown dataset"})
            continue
        entry = {
            "dataset_id": dsid, "name": d.name, "kind": d.kind, "coverage": d.coverage,
            "approx_output_size_mb": None,
        }
        if d.kind == "raster":
            try:
                source_uri = resolve_dataset_path(d)
                entry["approx_output_size_mb"] = approximate_output_size_mb(source_uri, aoi_geom)
            except Exception as e:  # noqa: BLE001
                entry["note"] = f"Could not estimate size: {e}"
        dataset_previews.append(entry)

    return {
        "aoi": validation.model_dump(),
        "datasets": dataset_previews,
    }
