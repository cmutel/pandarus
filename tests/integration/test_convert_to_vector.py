"""Test cases for the __convert_to_vector__ feature."""
import fiona

from pandarus import convert_to_vector
from pandarus.utils.conversion import check_dataset_type

from .. import PATH_CFS


def test_convert_to_vector(tmpdir) -> None:
    """Test the convert_to_vector function."""
    out = convert_to_vector(PATH_CFS, tmpdir)
    assert check_dataset_type(out) == "vector"

    # Second time should be a no-op
    out = convert_to_vector(PATH_CFS, tmpdir)
    assert check_dataset_type(out) == "vector"

    with fiona.open(out) as src:
        meta = src.meta

        assert meta["crs"] == {"init": "epsg:4326"}
        assert meta["schema"]["properties"].keys() == {"filename", "id", "val"}
        assert meta["schema"]["geometry"] in ("Polygon", "MultiPolygon")
