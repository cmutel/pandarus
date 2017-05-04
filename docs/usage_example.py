from pandarus import *
import geopandas as gpd
import rasterio
import os
import json
from pprint import pprint

# Get filepaths of data used in tests
grid_fp = os.path.join('..', 'tests', 'data', 'grid.geojson')
points_fp = os.path.join('..', 'tests', 'data', 'points.geojson')
square_fp = os.path.join('..', 'tests', 'data', 'square.geojson')
lines_fp = os.path.join('..', 'tests', 'data', 'lines.geojson')
range_fp = os.path.join('..', 'tests', 'data', 'range.tif')

# Load test fixtures
grid = gpd.read_file(grid_fp)
square =  gpd.read_file(square_fp)
points = gpd.read_file(points_fp)
lines = gpd.read_file(lines_fp)


# Intersecting polygons
spatial_result, json_data = intersect(
    square_fp,
    'name',
    grid_fp,
    'name',
    compress=False
)

# Load resulting output data
print("Output from intersecting polygons")
pprint(json.load(open(json_data)))


# Intersecting lines
spatial_result, json_data = intersect(
    lines_fp,
    'name',
    grid_fp,
    'name',
    compress=False
)

# Load resulting output data
print("Output from intersecting lines")
pprint(json.load(open(json_data)))
print("Vector file with calculated intersections written to:", spatial_result)

# Intersecting points
spatial_result, json_data = intersect(
    points_fp,
    'name',
    grid_fp,
    'name',
    compress=False
)

# Load resulting output data
print("Output from intersecting points")
pprint(json.load(open(json_data)))
print("Vector file with calculated intersections written to:", spatial_result)


# Getting raster statistics for polygons
json_data = raster_statistics(
    grid_fp,
    'name',
    range_fp,
    compress=False
)

# Load resulting output data
print("Output from raster statistics for polygons")
pprint(json.load(open(json_data)))
print("Vector file with calculated intersections written to:", spatial_result)


# Getting raster statistics for lines
json_data = raster_statistics(
    lines_fp,
    'name',
    range_fp,
    compress=False
)

# Load resulting output data
print("Output from raster statistics for lines")
pprint(json.load(open(json_data)))


# Getting raster statistics for points
json_data = raster_statistics(
    points_fp,
    'name',
    range_fp,
    compress=False
)

# Load resulting output data
print("Output from raster statistics for points")
pprint(json.load(open(json_data)))
