"""Test cases for the __intersections_ module."""
import os

import numpy as np
import pytest
from shapely.geometry import Polygon

from pandarus.intersections import (
    chunker,
    get_jobs,
    intersection_dispatcher,
    intersection_worker,
    logger_init,
    worker_init,
)

from . import PATH_GC, PATH_GRID, PATH_POINT, PATH_SQUARE


def test_chunker():
    """Test the chunker function."""
    numbers = list(range(10))
    expected = [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]
    assert list(chunker(numbers, 4)) == expected


def test_worker_init(tmpdir):
    """Test the worker init function."""
    ql, lq = logger_init(tmpdir)
    worker_init(lq)
    assert os.listdir(tmpdir)
    ql.stop()


def test_get_jobs():
    """Test the get jobs function."""
    assert get_jobs(10) == (20, 1)
    assert get_jobs(100) == (20, 5)
    assert get_jobs(110) == (20, 6)
    assert get_jobs(10000) == (50, 200)


def test_intersection_worker_indices():
    """Test the intersection worker function with indices."""
    area = 1 / 4 * (4e7 / 360) ** 2
    result = intersection_worker(PATH_GRID, [0], PATH_SQUARE)
    assert result.keys() == {(0, 0)}
    _, value = list(result.keys())[0], list(result.values())[0]
    expected = Polygon([(0.5, 1), (1, 1), (1, 0.5), (0.5, 0.5), (0.5, 1)])
    assert value["geom"].equals(expected)
    assert np.isclose(value["measure"], area, rtol=1e-2)


def test_intersection_worker_no_indices():
    """Test the intersection worker function without indices."""
    result = intersection_worker(PATH_GRID, None, PATH_SQUARE)
    assert len(result) == 4


def test_intersection_worker_wrong_from_type():
    """Test the intersection worker function with wrong from type."""
    with pytest.raises(ValueError):
        intersection_worker(PATH_GC, None, PATH_SQUARE)


def test_intersection_worker_wrong_to_type():
    """Test the intersection worker function with wrong to type."""
    with pytest.raises(ValueError):
        intersection_worker(PATH_GRID, [0], PATH_POINT)


def test_intersection_dispatcher_zero_cpus():
    """Test the intersection dispatcher with zero cpus."""
    result = intersection_dispatcher(PATH_GRID, PATH_SQUARE)
    assert len(result) == 4


def test_intersection_dispatcher_indices(tmpdir):
    """Test the intersection dispatcher with indices."""
    result = intersection_dispatcher(PATH_GRID, PATH_SQUARE, [0, 1], 1, tmpdir)
    assert len(result) == 2
