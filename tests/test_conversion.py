"""Test cases for the __conversion__ module."""
import os

import fiona
import numpy as np
import pytest
import rasterio
from affine import Affine
from rasterio import CRS

from pandarus.conversion import (
    check_type,
    clean_raster,
    convert_to_vector,
    round_raster,
    round_to_x_significant_digits,
)

from . import PATH_CFS, PATH_DEM, PATH_GRID, PATH_INVALID, PATH_SIXTY_FOUR


def create_raster(name, array, dirpath, nodata=-1, **kwargs):
    """Create a raster file with the given array."""
    profile = {
        "count": 1,
        "nodata": nodata,
        "dtype": "float32",
        "width": array.shape[1],
        "height": array.shape[0],
        "affine": Affine(0.1, 0, 10, 0, -0.1, 10),
        "driver": "GTiff",
        "compress": "lzw",
        "crs": CRS.from_epsg(4326),
    }
    profile.update(kwargs)
    fp = os.path.join(dirpath, name)

    with rasterio.Env():
        with rasterio.open(fp, "w", **profile) as dst:
            dst.write(array, 1)

    return fp


def test_create_raster(tmpdir):
    """Test the create_raster function."""
    fp = create_raster(
        "foo.tif", np.random.random(size=(10, 10)).astype(np.float32), tmpdir
    )
    assert os.path.isfile(fp)
    assert check_type(fp) == "raster"
    with rasterio.open(fp) as f:
        assert f.read(1).shape == (10, 10)
        assert f.read(1).dtype == np.float32


def test_check_type():
    """Test the check_type function."""
    assert check_type(PATH_GRID) == "vector"
    assert check_type(PATH_CFS) == "raster"
    with pytest.raises(ValueError):
        check_type(PATH_INVALID)


def test_convert_to_vector(tmpdir):
    """Test the convert_to_vector function."""
    with pytest.raises(AssertionError):
        convert_to_vector(PATH_CFS, band="1")

    out = convert_to_vector(PATH_CFS, tmpdir)
    assert check_type(out) == "vector"

    # Second time should be a no-op
    out = convert_to_vector(PATH_CFS, tmpdir)
    assert check_type(out) == "vector"

    with fiona.open(out) as src:
        meta = src.meta

        assert meta["crs"] == {"init": "epsg:4326"}
        assert meta["schema"]["properties"].keys() == {"filename", "id", "val"}
        assert meta["schema"]["geometry"] in ("Polygon", "MultiPolygon")

    out = convert_to_vector(PATH_CFS)
    assert check_type(out) == "vector"
    os.remove(out)


def test_rounding():
    """Test the round_to_x_significant_digits function."""
    given = np.array([3.14159358979, 2.718281828459045235360, 325796139])
    expected = (3.142, 2.718, 3.258e8)
    for x, y in zip(round_to_x_significant_digits(given, 4), expected):
        assert x == y


def test_round_raster(tmpdir):
    """Test the round_raster function."""
    out = os.path.join(tmpdir, "test.tif")

    assert round_raster(PATH_CFS, out) == out

    with rasterio.open(out) as src:
        array = src.read(1)
        profile = src.profile

    assert profile["driver"] == "GTiff"
    assert profile["compress"] == "lzw"
    assert profile["count"] == 1
    assert profile["height"] == 16
    assert np.unique(array[:3, :3]).shape == (1,)
    assert np.isclose(array[0, 0], 1.47e-7)


def test_clean_raster():
    """Test the clean_raster function."""
    out = clean_raster(PATH_SIXTY_FOUR)

    with rasterio.open(out) as src:
        array = src.read(1)
        profile = src.profile

    assert array.dtype == np.float32
    assert profile["driver"] == "GTiff"
    assert profile["compress"] == "lzw"
    assert profile["count"] == 1
    assert profile["nodata"] == -1
    assert not profile["tiled"]
    os.remove(out)


def test_clean_raster_null_nodata(tmpdir):
    """Test the clean_raster function with a null nodata value."""
    out = os.path.join(tmpdir, "test.tif")
    _ = clean_raster(PATH_DEM, out)

    with rasterio.open(out) as src:
        profile = src.profile

    assert profile["nodata"] is None


def test_clean_raster_filepath(tmpdir):
    """Test the clean_raster function with a filepath."""
    out = os.path.join(tmpdir, "test.tif")
    result = clean_raster(PATH_SIXTY_FOUR, out)
    assert result == out


def test_clean_raster_64bit(tmpdir):
    """Test the clean_raster function with a 64bit raster."""
    array = np.array([[0, -1, 1e100]])

    fp = create_raster("foo.tif", array, tmpdir, dtype="float64", nodata=42)

    with rasterio.open(fp) as f:
        assert f.profile["nodata"] == 42
        assert f.read(1).dtype == np.float64

    out_fp = os.path.join(tmpdir, "clean.tif")
    _ = clean_raster(fp, out_fp)

    with rasterio.open(fp) as f:
        assert f.read(1).dtype == np.float64


def test_clean_raster_out_of_bounds(tmpdir):
    """Test the clean_raster function with out of bounds values."""
    array = np.array([[0, 1.5, 42, -1e50]])
    fp = create_raster("foo.tif", array, tmpdir, dtype="float64", nodata=None)
    with pytest.raises(ValueError):
        _ = clean_raster(fp)


def test_clean_raster_dont_change(tmpdir):
    """Test the clean_raster function with a given nodata value that doesn't change."""
    array = np.array([[0, 1.5, 42, -1e7]])
    fp = create_raster("foo.tif", array, tmpdir, dtype="float64", nodata=-1e7)
    out = clean_raster(fp)
    with rasterio.open(out) as f:
        assert f.profile["nodata"] == -1e7
    os.remove(out)


def test_clean_raster_nodata(tmpdir):
    """Test the clean_raster function with a given nodata value that changes."""
    array = np.array([[0, 1.5, 42, -1e50]])
    fp = create_raster("foo.tif", array, tmpdir, dtype="float64", nodata=-1e50)
    out = clean_raster(fp)
    with rasterio.open(out) as f:
        assert f.profile["nodata"] == -1
    os.remove(out)

    array = np.array([[0, -1.0, -99.0, 6 / 7]])
    fp = create_raster("foo.tif", array, tmpdir, dtype="float64", nodata=-1e50)
    out = clean_raster(fp)
    with rasterio.open(out) as f:
        assert f.profile["nodata"] == -999
    os.remove(out)

    array = np.array([[0, -1.0, -99.0, -999.0, -9999.0]])
    fp = create_raster("foo.tif", array, tmpdir, dtype="float64", nodata=-1e50)
    with pytest.raises(ValueError):
        _ = clean_raster(fp)


def test_clean_raster_try_given_nodata(tmpdir):
    """Test the clean_raster function with a given nodata value to try."""
    array = np.array([[0, -1.0, -99.0, -999.0, -9999]])
    fp = create_raster("foo.tif", array, tmpdir, dtype="float64", nodata=-1e50)
    out = clean_raster(fp, nodata=42)
    with rasterio.open(out) as f:
        assert f.profile["nodata"] == 42
    os.remove(out)
