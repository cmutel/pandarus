# -*- coding: utf-8 -*-
from affine import Affine
from fiona import crs as fiona_crs
from rasterio.crs import CRS
import fiona
import itertools
import json
import numpy as np
import os
import rasterio


dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))

wgs84 = fiona_crs.from_string("+datum=WGS84 +ellps=WGS84 +no_defs +proj=longlat")

"""Valid geometry types:

- Point
- LineString
- Polygon
- MultiPoint
- MultiLineString
- MultiPolygon

"""

def create_raster(fp, array, nodata=-1, **kwargs):
    profile = {
        'count': 1,
        'nodata': nodata,
        'dtype': 'float32',
        'width': array.shape[1],
        'height': array.shape[0],
        'affine': Affine(0.4, 0, 0, 0, -0.2, 2),
        'driver': 'GTiff',
        'compress': 'lzw',
        'crs': CRS.from_epsg(4326)
    }
    profile.update(kwargs)

    with rasterio.Env():
        with rasterio.open(fp, 'w', **profile) as dst:
            dst.write(array, 1)

    return fp


def create_schema(geometry='Polygon'):
    return {'geometry': geometry, 'properties': {'name': 'str'}}


def create_record(name, coords, geometry='Polygon'):
    return {
        'geometry': {'coordinates': coords, 'type': geometry},
        'properties': {'name': name}
    }


def create_test_file(filepath, records, schema=None, driver='GeoJSON', crs=wgs84):
    if os.path.exists(filepath):
        os.remove(filepath)
    if schema is None:
        schema = create_schema()
    with fiona.drivers():
        with fiona.open(filepath, 'w', driver=driver, crs=crs, schema=schema) as outfile:
            for record in records:
                outfile.write(record)


def create_box(x, y, width, height):
    return [[
        (x, y),
        (x, y + height),
        (x + width, y + height),
        (x + width, y),
        (x, y)
    ]]


def create_grid(start_x=0.0, start_y=0.0, cols=4, rows=4, width=1.0,
        height=1.0):
    data = []
    for x_increment in range(cols):
        for y_increment in range(rows):
            data.append(create_box(
                start_x + x_increment * width,
                start_y + y_increment * height,
                width,
                height,
                ))
    return data


def create_test_datasets():
    # Create 4x4 grid
    x, y, cols, rows = 0, 0, 2, 2
    names = ["grid cell {}".format(i * 2 + j)
        for i in range(cols)
        for j in range(rows)
    ]
    cells = create_grid(x, y, cols, rows)
    create_test_file(
        os.path.join(dirpath, "grid.geojson"),
        [create_record(name, coords) for name, coords in zip(names, cells)]
    )

    names = ["grid cell {}".format(i * 2 + j)
        for i in range(cols)
        for j in range(rows)
    ]
    cells = create_grid(0, 7, cols, rows)
    create_test_file(
        os.path.join(dirpath, "big-grid.geojson"),
        [create_record(name, coords) for name, coords in zip(names, cells)]
    )

    # Duplicate names
    names = itertools.repeat("foo")
    cells = create_grid(x, y, cols, rows)
    create_test_file(
        os.path.join(dirpath, "duplicates.geojson"),
        [create_record(name, coords) for name, coords in zip(names, cells)]
    )

    # Create one square
    create_test_file(
        os.path.join(dirpath, "square.geojson"),
        [create_record("single", create_box(0.5, 0.5, 1, 1))]
    )

    create_test_file(
        os.path.join(dirpath, "outside.geojson"),
        [create_record("by-myself", create_box(0.5, 1.5, 1, 1))]
    )
    # Create multipolygon

    # Create point
    create_test_file(
        os.path.join(dirpath, "point.geojson"),
        [create_record("point", (1, 1), "Point")],  # Intersects all 4 cells in `grid`
        create_schema("Point")
    )

    # Create points
    create_test_file(
        os.path.join(dirpath, "points.geojson"),
        [
            create_record("point 1", (0.5, 0.5), "Point"),
            create_record("point 2", (1.5, 1.5), "Point")
        ],
        create_schema("Point")
    )

    # Create line
    create_test_file(
        os.path.join(dirpath, "lines.geojson"),
        [
            create_record("A", [(0.5, 0.5), (0.5, 1.5), (1.5, 1.5)], "LineString"),
            create_record("B", [(1, 1), (1.5, 0.5)], "LineString")
        ],
        create_schema("LineString")
    )

    # Create geometry collection
    gc_data = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": "GeometryCollection",
                "geometries": [{
                    "type": "Polygon",
                    "coordinates": [(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)]
                }]
            },
            "properties": {"name": "complicated"}
        }]
    }
    with open("data/gc.geojson", "w") as f:
        json.dump(gc_data, f)

    # Test raster for rasterstats
    array = np.arange(50).reshape((10, 5)).astype(np.float32)
    array[4, :] = -1
    array[5, :] = -1
    create_raster(os.path.join(dirpath, 'range.tif'), array)


if __name__ == '__main__':
    create_test_datasets()
