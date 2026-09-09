import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from ..services.security import sanitize_filename, validate_upload_size
from ..config import get_settings
from ..conversion import raster_convert, vector_convert
from ..extraction import vector as vector_ext
from ..storage.factory import get_storage

router = APIRouter(tags=["convert"])


@router.post("/api/convert")
async def convert_file(
    file: UploadFile = File(...),
    kind: str = Form(...),  # "raster" | "vector"
    output_format: str = Form(...),
):
    if kind not in ("raster", "vector"):
        raise HTTPException(status_code=400, detail="kind must be 'raster' or 'vector'")

    settings = get_settings()
    safe_name = sanitize_filename(file.filename or "upload")
    contents = await file.read()
    validate_upload_size(len(contents), settings.MAX_UPLOAD_MB)

    tmp_dir = Path(tempfile.mkdtemp(prefix="nora_convert_"))
    in_path = tmp_dir / safe_name
    in_path.write_bytes(contents)

    try:
        if kind == "raster":
            ext = raster_convert.EXTENSIONS.get(output_format)
            if not ext:
                raise HTTPException(status_code=400, detail=f"Unsupported raster format: {output_format}")
            out_path = tmp_dir / f"converted{ext}"
            raster_convert.write_raster(str(in_path), str(out_path), output_format)
        else:
            ext = vector_convert.EXTENSIONS.get(output_format)
            if not ext:
                raise HTTPException(status_code=400, detail=f"Unsupported vector format: {output_format}")
            gdf = vector_ext.load_vector(str(in_path))
            out_path = tmp_dir / f"converted{ext}"
            vector_convert.write_vector(gdf, str(out_path), output_format)

        storage = get_storage()
        remote_key = f"conversions/{uuid.uuid4().hex}/{out_path.name}"
        storage.save_file(out_path, remote_key)
        return {"download_url": storage.get_download_url(remote_key)}
    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
