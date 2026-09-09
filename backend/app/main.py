from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .api import health, datasets, aoi, extractions, preview, convert, files

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Extract areas of interest from large geospatial datasets, in the format you need.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(datasets.router)
app.include_router(aoi.router)
app.include_router(extractions.router)
app.include_router(preview.router)
app.include_router(convert.router)
app.include_router(files.router)


@app.on_event("startup")
def on_startup():
    Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.LOCAL_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    from .services.dataset_registry import get_registry
    get_registry()  # loads (and caches) the registry at boot
