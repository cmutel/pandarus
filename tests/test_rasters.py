from pandarus.rasters import *
import os

dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
grid = os.path.join(dirpath, "grid.geojson")
range_raster = os.path.join(dirpath, "range.tif")

def test_rasterstats_vector():
    result = list(gen_zonal_stats(grid, range_raster))
    assert result == [
        {'count': 10.200000762939453, 'min': 30.0, 'mean': 38.32352828979492, 'max': 47.0},
        {'count': 10.199999809265137, 'min': 0.0, 'mean': 8.323529243469238, 'max': 17.0},
        {'count': 10.0, 'min': 32.0, 'mean': 40.70000076293945, 'max': 49.0},
        {'count': 10.0, 'min': 2.0, 'mean': 10.699999809265137, 'max': 19.0},
    ]
