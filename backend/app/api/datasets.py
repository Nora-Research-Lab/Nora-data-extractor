from fastapi import APIRouter, HTTPException
from ..services.dataset_registry import get_registry
from ..services.format_recommender import available_formats

router = APIRouter(tags=["datasets"])


@router.get("/api/datasets")
def list_datasets():
    registry = get_registry()
    out = []
    for d in registry.list():
        out.append({**d.model_dump(), "format_options": available_formats(d)})
    return out


@router.get("/api/datasets/{dataset_id}")
def get_dataset(dataset_id: str):
    registry = get_registry()
    d = registry.get(dataset_id)
    if d is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
    return {**d.model_dump(), "format_options": available_formats(d)}
