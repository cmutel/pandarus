"""Helper classes for Pandarus."""
import os
from typing import Any, Dict, Generator, List, Tuple

import rasterio
import rasterio.features
import rasterio.warp
from rasterio import CRS
from rasterio.rio.helpers import coords, write_features


class ExtractionHelper:
    """Code from rio CLI:
    https://github.com/mapbox/rasterio/blob/master/rasterio/rio/shapes.py
    All the click stuff is cut out, as well as some option which we don't need.

    Extracts shapes from one band or mask of a dataset and writes
    them out as GeoJSON. Shapes will be transformed to WGS 84 coordinates.

    The default action of this command is to extract shapes from the
    first band of the input dataset. The shapes are polygons bounding
    contiguous regions (or features) of the same raster value. This
    command performs poorly for int16 or float type datasets."""

    def __init__(self, in_fp: str, out_fp: str, band: int) -> None:
        self.dump_kwds = {"sort_keys": True}
        self.in_fp = in_fp
        self.out_fp = out_fp
        self.band = band
        self._xs: List[float] = []
        self._ys: List[float] = []

    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        """Return the bounding box of the collection."""
        return min(self._xs), min(self._ys), max(self._xs), max(self._ys)

    def __call__(self) -> Generator[Dict[str, Any], None, None]:
        with rasterio.open(self.in_fp) as src:
            if self.band > src.count:
                raise ValueError("band is out of range for raster.")

            # Adjust transforms.
            transform = src.transform

            # Most of the time, we'll use the valid data mask.
            # We skip reading it if we're extracting every possible
            # feature (even invalid data features) from a band.
            msk = src.read_masks(self.band)
            img = src.read(self.band, masked=False)

            # Transform the raster bounds.
            bounds = src.bounds
            xs = [bounds[0], bounds[2]]
            ys = [bounds[1], bounds[3]]
            xs, ys = rasterio.warp.transform(
                src.crs, CRS({"init": "epsg:4326"}), xs, ys
            )
            self._xs = xs
            self._ys = ys

            # Prepare keyword arguments for shapes().
            kwargs = {"transform": transform}
            kwargs["mask"] = msk

            src_basename = os.path.basename(src.name)

            # Yield GeoJSON features.
            for i, (g, val) in enumerate(rasterio.features.shapes(img, **kwargs)):
                g = rasterio.warp.transform_geom(
                    src.crs, "EPSG:4326", g, antimeridian_cutting=True, precision=-1
                )
                xs, ys = zip(*coords(g))
                yield {
                    "type": "Feature",
                    "id": str(i),
                    "properties": {"val": val, "filename": src_basename, "id": i},
                    "bbox": [min(xs), min(ys), max(xs), max(ys)],
                    "geometry": g,
                }

    def write_features(self) -> None:
        """Write features to file."""
        with open(self.out_fp, "w", encoding="UTF-8") as f:
            write_features(
                f,
                self,
                sequence=False,
                geojson_type="collection",
                use_rs=False,
                **self.dump_kwds,
            )
