"""
Generates small synthetic datasets under backend/sample_datasets/ so the
service can be run and tested end-to-end without needing real global
datasets. Covers a bounding box around Ibadan/Oyo State, Nigeria, purely
because that's a convenient example AOI for this org - swap in real data by
registering new datasets (see docs/adding_a_dataset.md) rather than editing
this script for production use.

Run: python scripts/generate_sample_data.py
"""
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

OUT = Path(__file__).resolve().parent.parent / "backend" / "sample_datasets"
OUT.mkdir(parents=True, exist_ok=True)

# Roughly covers Oyo State, Nigeria: west, south -> east, north
WEST, SOUTH, EAST, NORTH = 2.6, 6.9, 4.6, 9.2
WIDTH, HEIGHT = 400, 460
PIXEL = (EAST - WEST) / WIDTH
TRANSFORM = from_origin(WEST, NORTH, PIXEL, (NORTH - SOUTH) / HEIGHT)


def write_raster(name: str, generator):
    data = generator(HEIGHT, WIDTH).astype("float32")
    with rasterio.open(
        OUT / name, "w", driver="GTiff", height=HEIGHT, width=WIDTH, count=1,
        dtype="float32", crs="EPSG:4326", transform=TRANSFORM, nodata=-9999.0,
    ) as dst:
        dst.write(data, 1)
    print(f"wrote {name}")


def dem(h, w):
    y, x = np.mgrid[0:h, 0:w]
    return 200 + 150 * np.sin(x / 40) * np.cos(y / 55) + np.random.default_rng(1).normal(0, 5, (h, w))


def magnetic(h, w):
    y, x = np.mgrid[0:h, 0:w]
    return 30000 + 800 * np.sin(x / 15 + y / 20) + np.random.default_rng(2).normal(0, 40, (h, w))


def gravity(h, w):
    y, x = np.mgrid[0:h, 0:w]
    return -20 + 10 * np.cos(x / 30) * np.sin(y / 25) + np.random.default_rng(3).normal(0, 1, (h, w))


def write_vector_geojson(name: str, features: list[dict]):
    fc = {"type": "FeatureCollection", "features": features}
    (OUT / name).write_text(json.dumps(fc))
    print(f"wrote {name}")


def rand_point(rng):
    return [WEST + rng.random() * (EAST - WEST), SOUTH + rng.random() * (NORTH - SOUTH)]


if __name__ == "__main__":
    write_raster("global_dem.tif", dem)
    write_raster("magnetic.tif", magnetic)
    write_raster("gravity.tif", gravity)

    rng = np.random.default_rng(42)

    # Simple geology polygons: split the bbox into a 3x3 grid of "units"
    geo_features = []
    xs = np.linspace(WEST, EAST, 4)
    ys = np.linspace(SOUTH, NORTH, 4)
    units = ["Basement Complex", "Sedimentary Cover", "Migmatite Gneiss"]
    for i in range(3):
        for j in range(3):
            ring = [[xs[i], ys[j]], [xs[i+1], ys[j]], [xs[i+1], ys[j+1]], [xs[i], ys[j+1]], [xs[i], ys[j]]]
            geo_features.append({
                "type": "Feature",
                "properties": {"unit": units[(i + j) % len(units)]},
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            })
    write_vector_geojson("geology.geojson", geo_features)

    # Rivers: a handful of meandering lines
    river_features = []
    for r in range(4):
        y0 = SOUTH + rng.random() * (NORTH - SOUTH)
        coords = []
        y = y0
        for x in np.linspace(WEST, EAST, 25):
            y += rng.normal(0, 0.03)
            coords.append([float(x), float(y)])
        river_features.append({
            "type": "Feature", "properties": {"name": f"River {r+1}"},
            "geometry": {"type": "LineString", "coordinates": coords},
        })
    write_vector_geojson("rivers.geojson", river_features)

    # Mineral occurrences: random points with a mineral label
    minerals = ["Gold", "Tantalite", "Cassiterite", "Lithium (Spodumene)", "Limestone"]
    pts = []
    for i in range(60):
        pts.append({
            "type": "Feature",
            "properties": {"mineral": minerals[i % len(minerals)], "occurrence_id": i + 1},
            "geometry": {"type": "Point", "coordinates": rand_point(rng)},
        })
    write_vector_geojson("mineral_occurrences.geojson", pts)

    print(f"\nSample data written to {OUT}")
