import shutil
from pathlib import Path
import rasterio

EXTENSIONS = {"GeoTIFF": ".tif", "COG": ".tif"}


def write_raster(in_path: str, out_path: str, fmt: str) -> str:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    if fmt == "GeoTIFF":
        if str(in_path) != str(out_path):
            shutil.copy2(in_path, out_path)
        return out_path

    if fmt == "COG":
        try:
            from rio_cogeo.cogeo import cog_translate
            from rio_cogeo.profiles import cog_profiles
            cog_translate(
                in_path, out_path, cog_profiles.get("deflate"),
                in_memory=False, quiet=True,
            )
        except ImportError:
            # Fallback: tiled + compressed GeoTIFF (COG-friendly, if not a strict COG)
            with rasterio.open(in_path) as src:
                profile = src.profile.copy()
                profile.update(driver="GTiff", tiled=True, blockxsize=512, blockysize=512, compress="DEFLATE")
                with rasterio.open(out_path, "w", **profile) as dst:
                    dst.write(src.read())
        return out_path

    raise ValueError(f"Unsupported raster output format: {fmt}")
