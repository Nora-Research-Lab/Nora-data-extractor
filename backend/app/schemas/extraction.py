from typing import Literal, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .aoi import AOIRequest

JobStatus = Literal["queued", "processing", "completed", "failed"]
Stage = Literal["preparing", "extracting", "converting", "packaging", "complete", "failed"]


class ProcessingOptions(BaseModel):
    mode: Literal["basic", "advanced"] = "basic"
    clip: bool = True
    reproject_to: Optional[str] = None  # EPSG code string e.g. "EPSG:32631"; None = automatic/native
    resample: Optional[Literal["nearest", "bilinear", "cubic"]] = None
    target_resolution: Optional[float] = None  # in target CRS units
    simplify_tolerance: Optional[float] = None  # vector generalization, in degrees or CRS units
    dissolve: bool = False
    dissolve_by: Optional[str] = None
    buffer_meters: Optional[float] = None
    attribute_filter: Optional[str] = None  # pandas-style query string applied to vector attributes


class DatasetOutputSpec(BaseModel):
    dataset_id: str
    output_format: Optional[str] = None  # None -> use recommended default for that dataset kind


class ExtractionRequest(BaseModel):
    aoi: AOIRequest
    datasets: list[DatasetOutputSpec]
    processing: ProcessingOptions = Field(default_factory=ProcessingOptions)
    study_area_name: str = "study_area"


class ExtractionJobCreated(BaseModel):
    job_id: str
    status: JobStatus = "queued"


class ExtractionJobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    stage: Stage
    progress_pct: Optional[int] = None
    message: str = ""
    created_at: datetime
    updated_at: datetime
    result_files: list[str] = []
    download_url: Optional[str] = None
    error: Optional[str] = None
