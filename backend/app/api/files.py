from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from ..storage.factory import get_storage

router = APIRouter(tags=["files"])


@router.get("/api/files/{remote_key:path}")
def download_file(remote_key: str):
    storage = get_storage()
    if not storage.exists(remote_key):
        raise HTTPException(status_code=404, detail="File not found")
    local_path = storage.get_local_path(remote_key)
    return FileResponse(local_path, filename=remote_key.split("/")[-1])
