""" Test cases for the __intersections_from_intersection__ feature. """
import os
import shutil

import pytest

from pandarus import intersections_from_intersection
from pandarus.utils.io import import_json

from .. import PATH_INTER_RES, PATH_INTER_RES_DECOMP, PATH_INTER_RES_MD


def test_intersections_from_intersection(tmpdir) -> None:
    """Test intersections_from_intersection function."""
    fp1, fp2 = intersections_from_intersection(PATH_INTER_RES, out_dir=tmpdir)
    data = import_json(fp1)
    result = [
        # Order from geojson file
        [0, "grid cell 3", 3097248058.207057],
        [1, "grid cell 2", 3097719886.041353],
        [2, "grid cell 0", 3097719886.0413523],
        [3, "grid cell 1", 3097248058.207055],
    ]
    assert data["data"] == result
    assert data["metadata"].keys() == {"first", "second", "when"}
    assert data["metadata"]["first"].keys() == {"field", "filename", "path", "sha256"}
    assert data["metadata"]["second"].keys() == {"field", "filename", "path", "sha256"}

    data = import_json(fp2)
    result = [
        [0, "single", 3097248058.207057],
        [1, "single", 3097719886.041353],
        [2, "single", 3097719886.0413523],
        [3, "single", 3097248058.207055],
    ]
    assert data["data"] == result
    assert data["metadata"].keys() == {"first", "second", "when"}
    assert data["metadata"]["first"].keys() == {"field", "filename", "path", "sha256"}
    assert data["metadata"]["second"].keys() == {"field", "filename", "path", "sha256"}


def test_intersections_from_intersection_default_path() -> None:
    """Test intersections_from_intersection with default path."""
    f1, f2 = intersections_from_intersection(PATH_INTER_RES)
    assert "intersections" in f1
    os.remove(f1)
    os.remove(f2)


def test_intersections_from_intersection_specify_md(tmpdir) -> None:
    """Test intersections_from_intersection with specified metadata."""
    fp1, _ = intersections_from_intersection(
        PATH_INTER_RES, PATH_INTER_RES_MD, out_dir=tmpdir
    )
    data = import_json(fp1)
    result = [
        # Order from geojson file
        [0, "grid cell 3", 3097248058.207057],
        [1, "grid cell 2", 3097719886.041353],
        [2, "grid cell 0", 3097719886.0413523],
        [3, "grid cell 1", 3097248058.207055],
    ]
    assert data["data"] == result

    fp1, _ = intersections_from_intersection(
        PATH_INTER_RES, PATH_INTER_RES_DECOMP, out_dir=tmpdir
    )
    data = import_json(fp1)
    result = [
        # Order from geojson file
        [0, "grid cell 3", 3097248058.207057],
        [1, "grid cell 2", 3097719886.041353],
        [2, "grid cell 0", 3097719886.0413523],
        [3, "grid cell 1", 3097248058.207055],
    ]
    assert data["data"] == result

    shutil.copy(PATH_INTER_RES, tmpdir)
    new_fp = os.path.join(tmpdir, "intersection_result.geojson")

    fp1, _ = intersections_from_intersection(
        new_fp, PATH_INTER_RES_DECOMP, out_dir=tmpdir
    )
    data = import_json(fp1)
    result = [
        # Order from geojson file
        [0, "grid cell 3", 3097248058.207057],
        [1, "grid cell 2", 3097719886.041353],
        [2, "grid cell 0", 3097719886.0413523],
        [3, "grid cell 1", 3097248058.207055],
    ]
    assert data["data"] == result


def test_intersections_from_intersection_not_filepath(tmpdir) -> None:
    """Test intersections_from_intersection with invalid filepath."""
    with pytest.raises(FileNotFoundError):
        intersections_from_intersection("")

    shutil.copy(PATH_INTER_RES, tmpdir)
    new_fp = os.path.join(tmpdir, "intersection_result.geojson")
    with pytest.raises(ValueError):
        intersections_from_intersection(new_fp, out_dir=tmpdir)


def test_intersections_from_intersection_find_metadata(tmpdir) -> None:
    """Test intersections_from_intersection with metadata in same dir."""
    shutil.copy(PATH_INTER_RES, tmpdir)
    new_fp = os.path.join(tmpdir, "intersection_result.geojson")

    shutil.copy(PATH_INTER_RES_MD, tmpdir)

    fp1, _ = intersections_from_intersection(new_fp, out_dir=tmpdir)
    data = import_json(fp1)
    result = [
        # Order from geojson file
        [0, "grid cell 3", 3097248058.207057],
        [1, "grid cell 2", 3097719886.041353],
        [2, "grid cell 0", 3097719886.0413523],
        [3, "grid cell 1", 3097248058.207055],
    ]
    assert data["data"] == result

    shutil.copy(PATH_INTER_RES, tmpdir)
    new_fp = os.path.join(tmpdir, "intersection_result.geojson")

    shutil.copy(PATH_INTER_RES_DECOMP, os.path.join(tmpdir, "intersection_result.json"))

    fp1, _ = intersections_from_intersection(new_fp, out_dir=tmpdir)
    data = import_json(fp1)
    result = [
        # Order from geojson file
        [0, "grid cell 3", 3097248058.207057],
        [1, "grid cell 2", 3097719886.041353],
        [2, "grid cell 0", 3097719886.0413523],
        [3, "grid cell 1", 3097248058.207055],
    ]
    assert data["data"] == result
