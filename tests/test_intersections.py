from pandarus import Map
from pandarus.intersections import (
    chunker,
    get_jobs,
    logger_init,
    worker_init,
)
import os
import tempfile

dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
grid = os.path.join(dirpath, "grid.geojson")
square = os.path.join(dirpath, "square.geojson")
point = os.path.join(dirpath, "point.geojson")
points = os.path.join(dirpath, "points.geojson")
lines = os.path.join(dirpath, "lines.geojson")
countries = os.path.join(dirpath, "test_countries.gpkg")
provinces = os.path.join(dirpath, "test_provinces.gpkg")


def test_chunker():
    numbers = list(range(10))
    expected = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [8, 9]
    ]
    assert list(chunker(numbers, 4)) == expected

def test_worker_init():
    with tempfile.TemporaryDirectory() as dirpath:
        ql, lq = logger_init(dirpath)
        worker_init(lq)
        assert os.listdir(dirpath)

def test_get_jobs():
    assert get_jobs(10) == (20, 1)
    assert get_jobs(100) == (20, 5)
    assert get_jobs(110) == (20, 6)
    assert get_jobs(10000) == (50, 200)

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
