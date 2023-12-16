"""Test cases for the __rasters__ module."""
from pandarus.rasters import gen_zonal_stats

from . import PATH_GRID, PATH_LINES, PATH_POINTS, PATH_RANGE_RASTER


def test_rasterstats_vector():
    """Test the rasterstats function with a vector input."""
    result = list(gen_zonal_stats(PATH_GRID, PATH_RANGE_RASTER))
    assert result == [
        {
            "count": 10.0,
            "min": 30.0,
            "mean": 38.29999923706055,
            "max": 47.0,
        },
        {
            "count": 10.0,
            "min": 0.0,
            "mean": 8.300000190734863,
            "max": 17.0,
        },
        {"count": 10.0, "min": 32.0, "mean": 40.70000076293945, "max": 49.0},
        {"count": 10.0, "min": 2.0, "mean": 10.699999809265137, "max": 19.0},
    ]


def test_rasterstats_lines():
    """Test the rasterstats function with a line input."""
    result = list(gen_zonal_stats(PATH_LINES, PATH_RANGE_RASTER))
    assert result == [
        {
            "max": 36.0,
            "min": 11.0,
            "mean": 18.450448989868164,
            "count": 0.2775000035762787,
        },
        {
            "max": 38.0,
            "min": 33.0,
            "mean": 34.666664123535156,
            "count": 0.07500000298023224,
        },
    ]


def test_rasterstats_points():
    """Test the rasterstats function with a point input."""
    result = list(gen_zonal_stats(PATH_POINTS, PATH_RANGE_RASTER))
    assert result == [
        {"min": 30.0, "max": 42.0, "count": 9, "mean": 36.0},
        {"min": 7.0, "max": 19.0, "count": 9, "mean": 13.0},
    ]
