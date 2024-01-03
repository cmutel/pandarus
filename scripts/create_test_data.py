"""Script for creating test data for __pandarus__."""
import itertools
import json
import os
import sys
import warnings
from typing import Any, Dict, List, Optional, Tuple

import fiona
import numpy as np
import rasterio
from affine import Affine
from fiona.crs import CRS as f_crs
from rasterio import CRS as r_crs
from rasterio.errors import NotGeoreferencedWarning


def create_raster(
    fp: str,
    array: np.ndarray[np.float32],
    nodata: int = -1,
    **kwargs,
) -> str:
    """Create a test raster file."""
    profile = {
        "count": 1,
        "nodata": nodata,
        "dtype": "float32",
        "width": array.shape[1],
        "height": array.shape[0],
        "transform": Affine(0.4, 0, 0, 0, -0.2, 2),
        "driver": "GTiff",
        "compress": "lzw",
        "crs": r_crs.from_epsg(4326),
    }
    profile.update(kwargs)

    with rasterio.Env():
        with rasterio.open(fp, "w", **profile) as dst:
            dst.write(array, 1)

    return fp


def create_schema(geometry: str = "Polygon") -> Dict[str, Any]:
    """Create a schema for a GeoJSON file."""
    return {"geometry": geometry, "properties": {"name": "str"}}


def create_record(
    name: str,
    coords: List[List[Tuple[float, float]]],
    geometry: str = "Polygon",
) -> Dict[str, Dict[str, Any]]:
    """Create a record for a GeoJSON file."""
    return {
        "geometry": {"coordinates": coords, "type": geometry},
        "properties": {"name": name},
    }


def create_test_file(
    filepath: str,
    records: List[Dict[str, Dict[str, Any]]],
    schema: Dict[str, Any] = None,
    driver: str = "GeoJSON",
    crs: Optional[Dict] = None,
) -> None:
    """Create a test file."""
    if crs is None:
        crs = f_crs.from_string("+datum=WGS84 +ellps=WGS84 +no_defs +proj=longlat")
    if os.path.exists(filepath):
        os.remove(filepath)
    if schema is None:
        schema = create_schema()
    with fiona.Env():
        with fiona.open(
            filepath, "w", driver=driver, crs=crs, schema=schema
        ) as outfile:
            for record in records:
                outfile.write(record)


def create_box(
    x: float, y: float, width: float, height: float
) -> List[List[Tuple[float, float]]]:
    """Create a box."""
    return [[(x, y), (x, y + height), (x + width, y + height), (x + width, y), (x, y)]]


def create_grid(
    start: Tuple[float, float] = (0, 0),
    cols: int = 4,
    rows: int = 4,
    width: float = 1.0,
    height: float = 1.0,
) -> List[List[List[Tuple[float, float]]]]:
    """Create a grid."""
    data = []
    for x_increment in range(cols):
        for y_increment in range(rows):
            data.append(
                create_box(
                    start[0] + x_increment * width,
                    start[1] + y_increment * height,
                    width,
                    height,
                )
            )
    return data


def create_test_datasets(dirpath: str) -> None:
    """Create test datasets.
    Valid geometry types:
        - Point
        - LineString
        - Polygon
        - MultiPoint
        - MultiLineString
        - MultiPolygon
    """
    os.makedirs(dirpath, exist_ok=True)

    # Create 4x4 grid
    x, y, cols, rows = 0, 0, 2, 2
    names = [f"grid cell {i * 2 + j}" for i in range(cols) for j in range(rows)]
    cells = create_grid((x, y), cols, rows)
    create_test_file(
        os.path.join(dirpath, "grid.geojson"),
        [create_record(name, coords) for name, coords in zip(names, cells)],
    )

    names = [f"grid cell {i * 2 + j}" for i in range(cols) for j in range(rows)]
    cells = create_grid((0, 7), cols, rows)
    create_test_file(
        os.path.join(dirpath, "big-grid.geojson"),
        [create_record(name, coords) for name, coords in zip(names, cells)],
    )

    # Duplicate names
    names = itertools.repeat("foo")
    cells = create_grid((x, y), cols, rows)
    create_test_file(
        os.path.join(dirpath, "duplicates.geojson"),
        [create_record(name, coords) for name, coords in zip(names, cells)],
    )

    # Create one square
    create_test_file(
        os.path.join(dirpath, "square.geojson"),
        [create_record("single", create_box(0.5, 0.5, 1, 1))],
    )

    create_test_file(
        os.path.join(dirpath, "outside.geojson"),
        [create_record("by-myself", create_box(0.5, 1.5, 1, 1))],
    )
    # Create multipolygon

    # Create point
    create_test_file(
        os.path.join(dirpath, "point.geojson"),
        [create_record("point", (1, 1), "Point")],  # Intersects all 4 cells in `grid`
        create_schema("Point"),
    )

    # Create points
    create_test_file(
        os.path.join(dirpath, "points.geojson"),
        [
            create_record("point 1", (0.5, 0.5), "Point"),
            create_record("point 2", (1.5, 1.5), "Point"),
        ],
        create_schema("Point"),
    )

    # Create line
    create_test_file(
        os.path.join(dirpath, "lines.geojson"),
        [
            create_record("A", [(0.5, 0.5), (0.5, 1.5), (1.5, 1.5)], "LineString"),
            create_record("B", [(1, 1), (1.5, 0.5)], "LineString"),
        ],
        create_schema("LineString"),
    )

    # Create geometry collection
    gc_data = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {
                            "type": "Polygon",
                            "coordinates": [
                                (0.5, 0.5),
                                (1.5, 0.5),
                                (1.5, 1.5),
                                (0.5, 1.5),
                                (0.5, 0.5),
                            ],
                        }
                    ],
                },
                "properties": {"name": "complicated"},
            }
        ],
    }
    with open(os.path.join(dirpath, "gc.geojson"), "w", encoding="UTF-8") as f:
        json.dump(gc_data, f)

    # Test raster for rasterstats
    array = np.arange(50).reshape((10, 5)).astype(np.float32)
    array[4, :] = -1
    array[5, :] = -1
    create_raster(os.path.join(dirpath, "range.tif"), array)


if __name__ == "__main__":
    # Ignore warnings for non-georeferenced rasters since this is test data
    warnings.simplefilter(action="ignore", category=NotGeoreferencedWarning)

    def_dir_path = os.path.join(os.path.dirname(__file__), "..", "tests", "data")
    arg_dir_path = sys.argv[1] if len(sys.argv) > 1 else def_dir_path
    create_test_datasets(dirpath=arg_dir_path)
