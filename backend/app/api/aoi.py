from fastapi import APIRouter
from ..schemas.aoi import AOIRequest, AOIValidationResult
from ..services.aoi_service import validate_aoi

router = APIRouter(tags=["aoi"])


@router.post("/api/aoi/validate", response_model=AOIValidationResult)
def validate(aoi: AOIRequest):
    return validate_aoi(aoi)
