"""Test cases for the __calculate_remaining__ feature."""
import json
import os

import numpy as np

from pandarus import calculate_remaining

from .. import PATH_OUTSIDE, PATH_REMAIN_RESULT


def test_calculate_remaining(tmpdir) -> None:
    """Test calculate_remaining function."""
    # Remaining area is 0.5°  by 1°.
    # Circumference of earth is 40.000 km
    # We are close to equator
    # So area should be 1/2 * (4e7 / 360) ** 2 m2
    area = 1 / 2 * (4e7 / 360) ** 2

    data_fp = calculate_remaining(
        PATH_OUTSIDE, "name", PATH_REMAIN_RESULT, out_dir=tmpdir, compress=False
    )

    with open(data_fp, encoding="UTF-8") as f:
        data = json.load(f)

        assert data["data"][0][0] == "by-myself"
        assert np.isclose(area, data["data"][0][1], rtol=1e-2)
        assert data["metadata"].keys() == {"intersections", "source", "when"}
        assert data["metadata"]["intersections"].keys() == {
            "field",
            "filename",
            "path",
            "sha256",
        }
        assert data["metadata"]["source"].keys() == {
            "field",
            "filename",
            "path",
            "sha256",
        }


def test_calculate_remaining_copmressed_fp(tmpdir) -> None:
    """Test calculate_remaining with compressed fp."""
    data_fp = calculate_remaining(
        PATH_OUTSIDE, "name", PATH_REMAIN_RESULT, out_dir=tmpdir, compress=False
    )
    assert os.path.isfile(data_fp)


def test_calculate_remaining_default_path() -> None:
    """Test calculate_remaining with default path."""
    data_fp = calculate_remaining(
        PATH_OUTSIDE, "name", PATH_REMAIN_RESULT, compress=False
    )
    assert "intersections" in data_fp
    os.remove(data_fp)
