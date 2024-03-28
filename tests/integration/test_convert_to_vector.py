"""Test cases for the __convert_to_vector__ feature."""

import os

import fiona
import pytest

import pandarus
from pandarus import convert_to_vector
from pandarus.utils.conversion import check_dataset_type

from .. import PATH_CFS


def test_convert_to_vector_apps_dirpath(tmpdir, monkeypatch) -> None:
    """Test the convert_to_vector function with apps_dirpath."""
    monkeypatch.setattr(pandarus.core, "get_appdirs_path", lambda name: tmpdir)
    out = convert_to_vector(PATH_CFS)
    assert check_dataset_type(out) == "vector"


def test_convert_to_vector_out_not_a_dir() -> None:
    """Test the convert_to_vector function with out_dir."""
    with pytest.raises(NotADirectoryError):
        convert_to_vector(PATH_CFS, "invalid")


def test_convert_to_vector_out_non_writable_dir(tmpdir, monkeypatch) -> None:
    """Test the convert_to_vector function with out_dir."""
    monkeypatch.setattr(os, "access", lambda *args, **kwargs: False)
    with pytest.raises(PermissionError):
        convert_to_vector(PATH_CFS, tmpdir)


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
