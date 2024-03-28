"""Test cases for the __round_raster__ feature."""

import numpy as np
import rasterio

from pandarus import round_raster

from .. import PATH_CFS


def test_round_raster() -> None:
    """Test the round_raster function."""
    out = round_raster(PATH_CFS)
    with rasterio.open(out) as src:
        array = src.read(1)
        profile = src.profile

    assert profile["driver"] == "GTiff"
    assert profile["compress"] == "lzw"
    assert profile["count"] == 1
    assert profile["height"] == 16
    assert np.unique(array[:3, :3]).shape == (1,)
    assert np.isclose(array[0, 0], 1.47e-7)
