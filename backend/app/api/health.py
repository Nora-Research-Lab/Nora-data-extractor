from fastapi import APIRouter
from ..config import get_settings

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health():
    s = get_settings()
    return {"status": "ok", "app": s.APP_NAME, "env": s.ENV, "storage_backend": s.STORAGE_BACKEND}
