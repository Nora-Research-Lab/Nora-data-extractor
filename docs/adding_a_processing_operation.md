# Adding a new processing operation

Processing operations live in two places:

1. The actual operation (`app/extraction/raster.py` or `app/extraction/vector.py`)
2. The dispatch in `app/processing/pipeline.py`, which is dataset-*kind*-aware
   but never dataset-*id*-aware.

## Example: add a vector "smooth" operation

**1. Implement it** in `app/extraction/vector.py`:

```python
def smooth_vector(gdf: gpd.GeoDataFrame, iterations: int = 1) -> gpd.GeoDataFrame:
    out = gdf.copy()
    for _ in range(iterations):
        out["geometry"] = out.geometry.buffer(0.0001).buffer(-0.0001)
    return out
```

**2. Add a field** to `ProcessingOptions` in `app/schemas/extraction.py`:

```python
smooth_iterations: Optional[int] = None
```

**3. Wire it into the pipeline** in `app/processing/pipeline.py`'s
`_process_vector()`:

```python
if options.smooth_iterations:
    gdf = vector_ext.smooth_vector(gdf, options.smooth_iterations)
```

**4. Expose it in the frontend** - add a field to the "Advanced" section of
`frontend/src/export/FormatStep.tsx`.

That's the whole loop. The job system, packaging, and API layer need no
changes since they just pass `ProcessingOptions` through untouched.

## Ordering matters

Operations in `_process_vector`/`_process_raster` run in a fixed order
(clip → filter → dissolve → buffer → simplify → reproject for vectors; clip →
reproject for rasters). If your new operation is order-sensitive, insert it
at the appropriate point rather than appending it at the end.
