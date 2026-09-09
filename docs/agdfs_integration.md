# Connecting to AGDFS

AGDFS (https://agdfs.onrender.com) is NORA Research Lab's existing
dataset/pipeline service. It is deliberately kept **out of the core
extraction engine** - the engine only ever talks to the generic
`DatasetProvider` interface (`app/providers/base.py`).

## How it's wired

`app/providers/agdfs_provider.py`:

```python
class AGDFSProvider(HTTPProvider):
    def resolve(self, dataset: DatasetMetadata) -> str:
        base = get_settings().AGDFS_BASE_URL.rstrip("/")
        full_url = f"{base}/{dataset.provider_uri.lstrip('/')}"
        ...  # delegates to HTTPProvider, which handles COG range-reads vs full download
```

This is the *only* file that imports or knows about AGDFS. Nothing in
`extraction/`, `processing/`, or `jobs/` references it.

## To register an AGDFS-backed dataset

```json
{
  "id": "geology_agdfs",
  "name": "Geology (AGDFS)",
  "kind": "vector",
  "format": "GeoPackage",
  "geometry_type": "polygon",
  "provider": "agdfs",
  "provider_uri": "datasets/geology/nigeria_geology.gpkg",
  ...
}
```

At extraction time, `provider_uri` is appended to `AGDFS_BASE_URL`
(configured via the `AGDFS_BASE_URL` env var, default
`https://agdfs.onrender.com`) to form the full request URL.

## If AGDFS's API shape changes

If AGDFS starts requiring auth headers, a different URL scheme, or
paginated responses, only `agdfs_provider.py` needs to change. Consider:

```python
class AGDFSProvider(DatasetProvider):
    def resolve(self, dataset):
        resp = httpx.get(f"{BASE}/api/resolve/{dataset.provider_uri}",
                          headers={"Authorization": f"Bearer {settings.AGDFS_API_KEY}"})
        return resp.json()["download_url"]  # then delegate to HTTPProvider with that URL
```

## Removing AGDFS entirely

Delete `agdfs_provider.py`, remove its entry from
`app/providers/registry.py`'s `_PROVIDERS` dict, and remove any datasets
using `"provider": "agdfs"` from the registry. Nothing else breaks.
