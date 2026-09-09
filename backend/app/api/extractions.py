from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from ..schemas.extraction import ExtractionRequest, ExtractionJobCreated, ExtractionJobStatusResponse
from ..services.aoi_service import validate_aoi
from ..services.dataset_registry import get_registry
from ..jobs.manager import get_job_manager
from ..jobs.tasks import run_extraction
from ..storage.factory import get_storage

router = APIRouter(tags=["extractions"])


@router.post("/api/extractions", response_model=ExtractionJobCreated)
def create_extraction(request: ExtractionRequest):
    validation = validate_aoi(request.aoi)
    if not validation.valid:
        raise HTTPException(status_code=400, detail={"aoi_errors": validation.errors})

    registry = get_registry()
    unknown = [d.dataset_id for d in request.datasets if registry.get(d.dataset_id) is None]
    if unknown:
        raise HTTPException(status_code=400, detail={"unknown_datasets": unknown})
    if not request.datasets:
        raise HTTPException(status_code=400, detail="At least one dataset must be selected")

    mgr = get_job_manager()
    job_id = mgr.submit(lambda jid, m: run_extraction(jid, m, request))
    return ExtractionJobCreated(job_id=job_id, status="queued")


@router.get("/api/extractions/{job_id}", response_model=ExtractionJobStatusResponse)
def get_extraction(job_id: str):
    mgr = get_job_manager()
    job = mgr.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    download_url = None
    if job["status"] == "completed" and job["result_files"]:
        storage = get_storage()
        download_url = storage.get_download_url(job["result_files"][0])

    return ExtractionJobStatusResponse(**{**job, "download_url": download_url})


@router.get("/api/extractions/{job_id}/download")
def download_extraction(job_id: str):
    mgr = get_job_manager()
    job = mgr.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed" or not job["result_files"]:
        raise HTTPException(status_code=409, detail=f"Job is not completed (status={job['status']})")

    storage = get_storage()
    url = storage.get_download_url(job["result_files"][0])
    if url.startswith("/api/files/"):
        return RedirectResponse(url)
    return RedirectResponse(url)
