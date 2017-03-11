from pandarus.rasters import *
import os

dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
grid = os.path.join(dirpath, "grid.geojson")
lines = os.path.join(dirpath, "lines.geojson")
points = os.path.join(dirpath, "points.geojson")
range_raster = os.path.join(dirpath, "range.tif")

def test_rasterstats_vector():
    result = list(gen_zonal_stats(grid, range_raster))
    assert result == [
        {'count': 10.200000762939453, 'min': 30.0, 'mean': 38.32352828979492, 'max': 47.0},
        {'count': 10.199999809265137, 'min': 0.0, 'mean': 8.323529243469238, 'max': 17.0},
        {'count': 10.0, 'min': 32.0, 'mean': 40.70000076293945, 'max': 49.0},
        {'count': 10.0, 'min': 2.0, 'mean': 10.699999809265137, 'max': 19.0},
    ]

def test_rasterstats_lines():
    result = list(gen_zonal_stats(lines, range_raster))
    assert result == [
        {'max': 36.0, 'min': 11.0, 'mean': 18.450448989868164, 'count': 0.2775000035762787},
        {'max': 38.0, 'min': 33.0, 'mean': 34.666664123535156, 'count': 0.07500000298023224}
    ]

def test_rasterstats_points():
    result = list(gen_zonal_stats(points, range_raster))
    assert result == [
        {'min': 30.0, 'max': 42.0, 'count': 9, 'mean': 36.0},
        {'min': 7.0, 'max': 19.0, 'count': 9, 'mean': 13.0}
    ]
