from pandarus import Map
from pandarus.intersections import (
    chunker,
    get_jobs,
    intersection_worker,
    intersection_dispatcher,
    logger_init,
    worker_init,
)
import os
import numpy as np
import pytest
import tempfile

dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
grid = os.path.join(dirpath, "grid.geojson")
square = os.path.join(dirpath, "square.geojson")
point = os.path.join(dirpath, "point.geojson")
gc = os.path.join(dirpath, "gc.geojson")


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

def test_intersection_worker_indices():
    area = 1/4 * (4e7 / 360) ** 2
    result = intersection_worker(grid, [0], square)
    assert result.keys() == {(0, 0)}
    key, value = list(result.keys())[0], list(result.values())[0]
    expected = 'MULTIPOLYGON (((0.5 1, 1 1, 1 0.5, 0.5 0.5, 0.5 1)))'
    assert value['geom'].wkt == expected
    assert np.isclose(value['measure'], area, rtol=1e-2)

def test_intersection_worker_no_indices():
    result = intersection_worker(grid, None, square)
    assert len(result) == 4

def test_intersection_worker_wrong_from_type():
    with pytest.raises(ValueError):
        intersection_worker(gc, None, square)

def test_intersection_worker_wrong_to_type():
    with pytest.raises(ValueError):
        intersection_worker(grid, [0], point)

def test_intersection_dispatcher_zero_cpus():
    result = intersection_dispatcher(grid, square)
    assert len(result) == 4

def test_intersection_dispatcher_indices():
    with tempfile.TemporaryDirectory() as dirpath:
        result = intersection_dispatcher(grid, square, [0, 1], 1, dirpath)
        assert len(result) == 2
