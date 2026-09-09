import re
import uuid
from pathlib import Path

_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str) -> str:
    """Strips path components and unsafe characters. Never trust a client-supplied filename directly."""
    name = Path(name).name  # drop any directory components
    name = _SAFE_CHARS.sub("_", name)
    return name or f"file_{uuid.uuid4().hex[:8]}"


def new_job_id() -> str:
    return uuid.uuid4().hex


def assert_within(base_dir: Path, target: Path) -> Path:
    """Raises ValueError if `target` would resolve outside `base_dir` (path-traversal guard)."""
    base_resolved = base_dir.resolve()
    target_resolved = target.resolve()
    if base_resolved != target_resolved and base_resolved not in target_resolved.parents:
        raise ValueError("Path traversal detected")
    return target_resolved


def validate_upload_size(size_bytes: int, max_mb: int) -> None:
    if size_bytes > max_mb * 1024 * 1024:
        raise ValueError(f"Uploaded file exceeds the {max_mb}MB limit")


ALLOWED_UPLOAD_EXTENSIONS = {".geojson", ".json", ".zip", ".shp", ".gpkg", ".kml"}


def validate_upload_extension(filename: str) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_UPLOAD_EXTENSIONS)}")
