# Registering a new dataset

The extractor has **no dataset-specific code**. Every dataset is an entry in
`backend/data/datasets_registry.json`, loaded by `DatasetRegistry`
(`app/services/dataset_registry.py`). Adding a dataset is a data change.

## 1. Add an entry to the registry

```json
{
  "id": "soil_ph",
  "name": "Soil pH",
  "description": "Topsoil pH, 0-30cm depth.",
  "category": "soil",
  "kind": "raster",
  "format": "COG",
  "geometry_type": "raster",
  "crs": "EPSG:4326",
  "coverage": "regional",
  "resolution": "250m",
  "units": "pH",
  "source": "NORA Research Lab",
  "license": "CC-BY-4.0",
  "available_export_formats": ["COG", "GeoTIFF"],
  "provider": "http",
  "provider_uri": "https://example.com/data/soil_ph_cog.tif"
}
```

Required fields: `id` (unique), `name`, `kind` (`raster`/`vector`), `format`,
`geometry_type`, `provider`, `provider_uri`. Everything else has sensible
defaults but improves the UI (descriptions, licensing, units).

## 2. Choose a `provider`

| provider         | `provider_uri` meaning                                            |
|------------------|---------------------------------------------------------------------|
| `local`          | path relative to `LOCAL_DATASET_DIR`                                |
| `http`           | full URL. Raster+COG uses ranged `/vsicurl/` reads; others download |
| `object_storage` | key inside the configured storage backend (S3/Supabase)             |
| `agdfs`          | path relative to `AGDFS_BASE_URL`                                   |

You can also register at runtime via `DatasetRegistry.add_or_update()`
(persists back to the JSON file) - useful for an admin UI later.

## 3. Restart / reload

The registry loads at startup (`app/main.py`'s startup event). Call
`get_registry().reload()` (e.g. from an internal endpoint) to hot-reload
without restarting the process.

No changes are needed anywhere else - `/api/datasets`, format recommendation,
extraction, and the frontend all read from the registry.
