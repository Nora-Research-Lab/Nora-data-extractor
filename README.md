<p align="center">
  <img src= alt="NORA Research Lab" width="100%" />
</p>

<h1 align="center">NORA Data Extractor</h1>
<p align="center">Extract any area from large geospatial datasets — clipped, converted, and packaged — without needing GIS software.</p>

<p align="center">
  <a href="https://github.com/Nora-Research-Lab"><img src="https://img.shields.io/badge/GitHub-Nora--Research--Lab-181717?logo=github" /></a>
  <a href="https://huggingface.co/NoraResearchLab"><img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-NoraResearchLab-yellow" /></a>
  <a href="https://www.linkedin.com/company/nora-research-lab"><img src="https://img.shields.io/badge/LinkedIn-NORA%20Research%20Lab-0A66C2?logo=linkedin&logoColor=white" /></a>
  <a href="https://x.com/noraresearchlab"><img src="https://img.shields.io/badge/X-@noraresearchlab-000000?logo=x" /></a>
  <a href="http://nora-research-lab.vercel.app/"><img src="https://img.shields.io/badge/Website-nora--research--lab-0d5c4a" /></a>
</p>

---

## Quick Links

- 🌐 [Website](http://nora-research-lab.vercel.app/) · 💻 [GitHub](https://github.com/Nora-Research-Lab) · 🤗 [Hugging Face](https://huggingface.co/NoraResearchLab) · 💼 [LinkedIn](https://www.linkedin.com/company/nora-research-lab) · 🐦 [X](https://x.com/noraresearchlab)
- 📖 Full API reference: [`docs/api.md`](docs/api.md)
- ➕ [Register a new dataset](docs/adding_a_dataset.md) · [Add an output format](docs/adding_an_output_format.md) · [Add a processing operation](docs/adding_a_processing_operation.md)
- 🔗 [AGDFS integration](docs/agdfs_integration.md) · [Map Engine / iframe integration](docs/map_engine_integration.md)

## What it does

A geoscientist, student, or analyst picks an area on a map, checks off the
datasets they need (DEM, magnetics, gravity, geology, rivers, mineral
occurrences...), picks a format (or takes the recommended one), and gets back
a ZIP with each dataset clipped to their area, in the right format, plus a
`metadata.json` and `README.txt` describing exactly what's in it.

**Workflow:** Choose area → Choose datasets → Choose output → Review & extract → Download.

## Architecture at a glance

- **Dataset-driven, not hardcoded** — every dataset is a JSON entry
  (`backend/data/datasets_registry.json`); there is no `if dataset_id == ...`
  anywhere in the extraction engine.
- **Provider abstraction** for *where source data lives* (local / HTTP+COG
  range-reads / object storage / AGDFS) — decoupled from...
- **Storage abstraction** for *where output artifacts live* (local disk / any
  S3-compatible store / Supabase Storage).
- **Windowed raster reads** via rasterio — never loads a full global raster
  into memory.
- **Background job system** (in-process thread pool + persisted status) with
  staged progress: `preparing → extracting → converting → packaging → complete`.
- AGDFS is isolated to a single adapter file and is never imported by the
  core engine — see [`docs/agdfs_integration.md`](docs/agdfs_integration.md).

## Project tree

```
nora-data-extractor/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app + router wiring
│   │   ├── config.py          Settings (env-driven)
│   │   ├── api/                health, datasets, aoi, extractions, preview, convert, files
│   │   ├── schemas/            pydantic request/response models
│   │   ├── services/           dataset registry, AOI validation, format recommender, security
│   │   ├── extraction/         raster.py (rasterio), vector.py (geopandas)
│   │   ├── conversion/         format writers (COG/GeoTIFF, GPKG/GeoJSON/Parquet/SHP/CSV/KML)
│   │   ├── processing/         pipeline.py — dispatches ProcessingOptions per dataset kind
│   │   ├── providers/          local / http / object_storage / agdfs
│   │   ├── storage/             local / s3 / supabase — output artifact storage
│   │   └── jobs/                 background job manager + extraction task
│   ├── data/datasets_registry.json   the 6 example datasets from the spec
│   └── sample_datasets/              small synthetic rasters/vectors for local testing
├── frontend/                    React + Vite + MapLibre 5-step wizard
├── tests/                       pytest — AOI validation, registry, raster clipping
├── docs/                        deep-dive guides (linked above)
├── scripts/generate_sample_data.py
├── Dockerfile · render.yaml · requirements.txt · .env.example
```

## Local setup

**Backend**
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example backend/.env
python scripts/generate_sample_data.py     # writes small test rasters/vectors
cd backend && uvicorn app.main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` for interactive Swagger docs.

**Frontend**
```bash
cd frontend
npm install
npm run dev     # http://localhost:5173, proxies /api to localhost:8000
```

**Tests**
```bash
pip install pytest
pytest tests/ -v
```

## Docker

```bash
docker build -t nora-data-extractor .
docker run -p 8000:8000 --env-file .env.example nora-data-extractor
```
The image generates sample data at build time so it runs out of the box.

## Deploying to Render

1. Push this repo to GitHub.
2. In Render: **New → Blueprint**, point it at the repo — `render.yaml` is
   picked up automatically.
3. Set the secret env vars Render will prompt for (`S3_BUCKET`,
   `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_ENDPOINT_URL`, or switch
   `STORAGE_BACKEND` to `supabase` and set the Supabase vars instead).
4. Deploy. Health check is `/api/health`.

**Important:** Render's local disk is ephemeral and not shared across
instances. Use `STORAGE_BACKEND=s3` or `supabase` in production — `local` is
only for quick single-instance demos.

Deploy the frontend as a separate Render **Static Site** (`npm run build`,
publish `frontend/dist`), with `VITE_API_PROXY_TARGET` (dev) or a build-time
API base URL pointed at your backend service.

## Environment variables

See [`.env.example`](.env.example) for the full list with defaults. Key ones:

| Variable | Purpose |
|---|---|
| `STORAGE_BACKEND` | `local` \| `s3` \| `supabase` — where output ZIPs live |
| `S3_*` / `SUPABASE_*` | credentials for the chosen storage backend |
| `AGDFS_BASE_URL` | base URL for AGDFS-provided datasets |
| `MAX_AOI_AREA_KM2` | sanity cap to reject runaway-sized extraction requests |
| `MAX_WORKERS` | background job concurrency |
| `DATASET_REGISTRY_PATH` | path to the dataset registry JSON |

## Example extraction request

```bash
curl -X POST http://localhost:8000/api/extractions \
  -H "Content-Type: application/json" \
  -d '{
    "aoi": {"aoi_type":"bbox","bbox":{"north":8.2,"south":7.7,"east":4.1,"west":3.6}},
    "datasets": [
      {"dataset_id":"global_dem"},
      {"dataset_id":"geology","output_format":"Shapefile"},
      {"dataset_id":"rivers"},
      {"dataset_id":"mineral_occurrences","output_format":"CSV"}
    ],
    "processing": {"mode":"advanced","clip":true,"reproject_to":"EPSG:32631","resample":"bilinear"},
    "study_area_name": "oyo_study_area"
  }'
# => {"job_id": "...", "status": "queued"}
# Poll: GET /api/extractions/{job_id}   Download: GET /api/extractions/{job_id}/download
```

This exact request was run end-to-end during development against the sample
datasets — reprojection to EPSG:32631, mixed-format multi-dataset packaging,
and the metadata.json/README.txt generation all verified working.

## Map Engine / iframe integration (summary)

```json
{ "type": "EXTRACT_AREA", "datasets": ["dem", "magnetic", "geology"], "aoi": { "type": "Polygon", "coordinates": [[]] } }
```
The Map Engine `postMessage`s this into the embedded extractor iframe, which
validates the AOI, pre-selects the datasets, and jumps to the output step.
Full example with origin-checking: [`docs/map_engine_integration.md`](docs/map_engine_integration.md).

## Extending the service

- [Register a new dataset](docs/adding_a_dataset.md) — pure data change, no code
- [Add a new output format](docs/adding_an_output_format.md)
- [Add a new processing operation](docs/adding_a_processing_operation.md)
- [Connect to / swap out AGDFS](docs/agdfs_integration.md)

## Known limitations / next steps

- Job system is an in-process thread pool (fine for a single Render
  instance); swap for Celery+Redis or RQ to scale across instances.
- `admin_boundary` and `place` AOI types are stubbed — need a boundary
  dataset and a geocoder respectively wired in `app/services/aoi_service.py`.
- NetCDF/Zarr raster output is architected for (see
  [`docs/adding_an_output_format.md`](docs/adding_an_output_format.md)) but not implemented.
- The demo basemap uses OpenStreetMap raster tiles directly — swap for a
  production tile provider before shipping publicly.

---

## Maintainer

**NORA Research Lab** — a geoscience dataset/API project suite, built with
active geological AI specialists and supporting professors at the
University of Abuja, Nigeria. NORA's AGDFS pipeline also powers
[Mira Robotics](https://github.com/Nora-Research-Lab)'s live field traction.

<p>
  <a href="https://github.com/Nora-Research-Lab"><img src="https://img.shields.io/badge/GitHub-Nora--Research--Lab-181717?logo=github" /></a>
  <a href="https://huggingface.co/NoraResearchLab"><img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-NoraResearchLab-yellow" /></a>
  <a href="https://www.linkedin.com/company/nora-research-lab"><img src="https://img.shields.io/badge/LinkedIn-NORA%20Research%20Lab-0A66C2?logo=linkedin&logoColor=white" /></a>
  <a href="https://x.com/noraresearchlab"><img src="https://img.shields.io/badge/X-@noraresearchlab-000000?logo=x" /></a>
</p>
