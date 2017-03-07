from pandarus import Pandarus, Map
import os

dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
grid = os.path.join(dirpath, "grid.geojson")
square = os.path.join(dirpath, "square.geojson")
point = os.path.join(dirpath, "point.geojson")
points = os.path.join(dirpath, "points.geojson")
lines = os.path.join(dirpath, "lines.geojson")
countries = os.path.join(dirpath, "test_countries.gpkg")
provinces = os.path.join(dirpath, "test_provinces.gpkg")


# def test_data_available():
#     for fn in (grid, square, point, points, lines, countries, provinces):
#         assert os.path.exists(fn)

# def test_square_grid_intersection():
#     p = Pandarus(square, grid)
#     expected = {(0, 3): 0.25, (0, 2): 0.25, (0, 1): 0.25, (0, 0): 0.25}
#     assert p.intersect(pool=False, to_meters=False) == expected

# def test_square_area():
#     p = Pandarus(grid, square)
#     expected = {0: 1, 1: 1, 2: 1, 3: 1}
#     assert p.areas(pool=False, to_meters=False) == expected

# def test_square_lines():
#     p = Pandarus(square, lines)
#     assert p.areas(pool=False, to_meters=False) == {0: 1.}
