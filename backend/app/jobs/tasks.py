import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ..config import get_settings
from ..schemas.extraction import ExtractionRequest
from ..services.aoi_service import resolve_geometry
from ..services.dataset_registry import get_registry
from ..processing.pipeline import process_dataset
from ..storage.factory import get_storage
from .manager import JobManager


def _write_manifest(work_dir: Path, request: ExtractionRequest, results: list[dict]) -> None:
    minx, miny, maxx, maxy = resolve_geometry(request.aoi).bounds
    metadata = {
        "study_area_name": request.study_area_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "aoi": {"west": minx, "south": miny, "east": maxx, "north": maxy},
        "processing_options": request.processing.model_dump(),
        "datasets": results,
        "generated_by": "NORA Data Extractor",
    }
    (work_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, default=str))

    readme_lines = [
        f"NORA Data Extractor - Study Area Package: {request.study_area_name}",
        "=" * 60,
        "",
        f"Generated: {metadata['generated_at']}",
        "",
        "Area of interest (WGS84 bounding box):",
        f"  North: {maxy}",
        f"  South: {miny}",
        f"  East:  {maxx}",
        f"  West:  {minx}",
        "",
        "Datasets included:",
    ]
    for r in results:
        readme_lines.append(f"  - {r['dataset_id']} ({r['kind']}, {r['format']}) -> {Path(r['path']).name}")
    readme_lines += [
        "",
        "Processing applied:",
        json.dumps(request.processing.model_dump(), indent=2),
        "",
        "See metadata.json for full detail on sources, CRS, and processing per dataset.",
        "Produced by the NORA Data Extractor service (NORA Research Lab).",
    ]
    (work_dir / "README.txt").write_text("\n".join(readme_lines))


def run_extraction(job_id: str, mgr: JobManager, request: ExtractionRequest) -> list[str]:
    settings = get_settings()
    registry = get_registry()
    storage = get_storage()

    mgr.report_progress(job_id, "preparing", 5, "Validating area and datasets")
    aoi_geom = resolve_geometry(request.aoi)

    work_dir = Path(tempfile.mkdtemp(prefix=f"nora_job_{job_id}_", dir=settings.TEMP_DIR))
    results: list[dict] = []

    total = max(len(request.datasets), 1)
    for i, spec in enumerate(request.datasets):
        dataset = registry.get(spec.dataset_id)
        if dataset is None:
            raise ValueError(f"Unknown dataset_id: {spec.dataset_id}")

        mgr.report_progress(
            job_id, "extracting",
            5 + int(60 * i / total),
            f"Extracting {dataset.name} ({i + 1}/{total})",
        )
        result = process_dataset(dataset, aoi_geom, request.processing, spec.output_format, str(work_dir))
        results.append(result)

    mgr.report_progress(job_id, "converting", 70, "Finalizing formats")
    # (format conversion already happened inside process_dataset; this stage exists
    #  so the UI can show a distinct "Converting" step per the spec.)

    mgr.report_progress(job_id, "packaging", 85, "Packaging study area")
    _write_manifest(work_dir, request, results)

    zip_base = work_dir.parent / f"{request.study_area_name}_{job_id[:8]}"
    zip_path = shutil.make_archive(str(zip_base), "zip", root_dir=work_dir)

    remote_key = f"jobs/{job_id}/{Path(zip_path).name}"
    storage.save_file(zip_path, remote_key)

    shutil.rmtree(work_dir, ignore_errors=True)
    Path(zip_path).unlink(missing_ok=True)

    mgr.report_progress(job_id, "complete", 100, "Done")
    return [remote_key]
