"""Test cases for the __helpers__ module."""
import numpy as np
import pytest
import rasterio

from pandarus.helpers import ExtractionHelper


@pytest.mark.filterwarnings("ignore::rasterio.errors.NotGeoreferencedWarning")
def test_helper_class_invalid_band(tmpdir) -> None:
    """Test the ExtractionHelper class with an invalid band."""
    raster_file = str(tmpdir.join("test.tif"))
    output_file = str(tmpdir.join("out.tif"))
    with rasterio.open(
        raster_file,
        "w",
        driver="GTiff",
        width=10,
        height=10,
        count=1,
        dtype="uint8",
    ) as dst:
        dst.write(np.random.random(size=(10, 10)), 1)

    with pytest.raises(ValueError):
        ExtractionHelper(raster_file, output_file, 2).write_features()
