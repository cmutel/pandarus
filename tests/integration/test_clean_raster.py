"""Test cases for the __clean_raster__ feature."""
import os
from typing import Dict

import numpy as np
import pytest
import rasterio
from rasterio import CRS, Affine

from pandarus import clean_raster

from .. import PATH_DEM, PATH_RASTER


def create_raster(
    name: str,
    array: np.ndarray,
    dirpath: str,
    nodata: int = -1,
    **kwargs: Dict,
) -> str:
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


@pytest.mark.filterwarnings("ignore::rasterio.errors.NotGeoreferencedWarning")
def test_clean_raster() -> None:
    """Test the clean_raster function."""
    out = clean_raster(PATH_RASTER)

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


@pytest.mark.filterwarnings("ignore::rasterio.errors.NotGeoreferencedWarning")
def test_clean_raster_null_nodata(tmpdir) -> None:
    """Test the clean_raster function with a null nodata value."""
    out = os.path.join(tmpdir, "test.tif")
    _ = clean_raster(PATH_DEM, out)

    with rasterio.open(out) as src:
        profile = src.profile

    assert profile["nodata"] is None


@pytest.mark.filterwarnings("ignore::rasterio.errors.NotGeoreferencedWarning")
def test_clean_raster_filepath(tmpdir) -> None:
    """Test the clean_raster function with a filepath."""
    out = os.path.join(tmpdir, "test.tif")
    result = clean_raster(PATH_RASTER, out)
    assert result == out


@pytest.mark.filterwarnings("ignore::rasterio.errors.NotGeoreferencedWarning")
def test_clean_raster_64bit(tmpdir) -> None:
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


@pytest.mark.filterwarnings("ignore::rasterio.errors.NotGeoreferencedWarning")
def test_clean_raster_out_of_bounds(tmpdir) -> None:
    """Test the clean_raster function with out of bounds values."""
    array = np.array([[0, 1.5, 42, -1e50]])
    fp = create_raster("foo.tif", array, tmpdir, dtype="float64", nodata=None)
    with pytest.raises(ValueError):
        _ = clean_raster(fp)


@pytest.mark.filterwarnings("ignore::rasterio.errors.NotGeoreferencedWarning")
def test_clean_raster_dont_change(tmpdir) -> None:
    """Test the clean_raster function with a given nodata value that doesn't change."""
    array = np.array([[0, 1.5, 42, -1e7]])
    fp = create_raster("foo.tif", array, tmpdir, dtype="float64", nodata=-1e7)
    out = clean_raster(fp)
    with rasterio.open(out) as f:
        assert f.profile["nodata"] == -1e7
    os.remove(out)


@pytest.mark.filterwarnings("ignore::rasterio.errors.NotGeoreferencedWarning")
def test_clean_raster_nodata(tmpdir) -> None:
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


@pytest.mark.filterwarnings("ignore::rasterio.errors.NotGeoreferencedWarning")
def test_clean_raster_try_given_nodata(tmpdir) -> None:
    """Test the clean_raster function with a given nodata value to try."""
    array = np.array([[0, -1.0, -99.0, -999.0, -9999]])
    fp = create_raster("foo.tif", array, tmpdir, dtype="float64", nodata=-1e50)
    out = clean_raster(fp, nodata=42)
    with rasterio.open(out) as f:
        assert f.profile["nodata"] == 42
    os.remove(out)
