"""Test cases for the __conversion__ module."""
import fiona
import numpy as np
import pytest

from pandarus.errors import MalformedMetaError, UnknownDatasetTypeError
from pandarus.utils.conversion import (
    check_dataset_type,
    dict_to_features,
    round_to_x_significant_digits,
)

from ... import PATH_CFS, PATH_GRID, PATH_INVALID


def test_dict_to_features(monkeypatch) -> None:
    """Test dict_to_features function."""
    monkeypatch.setattr("pandarus.utils.conversion.mapping", lambda x: x)

    expected = {
        "geometry": "Foo",
        "properties": {"id": 0, "from_label": 1, "to_label": 2, "measure": 42},
    }
    dct = {(1, 2): {"measure": 42, "geom": "Foo"}}
    assert next(dict_to_features(dct)) == expected


def test_check_dataset_type_malformed_vector(tmpdir) -> None:
    """Test the check_dataset_type function with a malformed vector file."""
    malformed_vector_file = str(tmpdir.join("test.json"))
    schema = {
        "properties": {"id": "int", "name": "str"},
    }
    with fiona.Env():
        with fiona.open(malformed_vector_file, "w", driver="GeoJSON", schema=schema):
            pass

    with pytest.raises(MalformedMetaError):
        check_dataset_type(malformed_vector_file)


def test_check_dataset_type() -> None:
    """Test the check_dataset_type function."""
    assert check_dataset_type(PATH_GRID) == "vector"
    assert check_dataset_type(PATH_CFS) == "raster"
    with pytest.raises(UnknownDatasetTypeError):
        check_dataset_type(PATH_INVALID)


def test_round_to_x_significant_digits() -> None:
    """Test the round_to_x_significant_digits function."""
    given = np.array([3.14159358979, 2.718281828459045235360, 325796139])
    expected = (3.142, 2.718, 3.258e8)
    for x, y in zip(round_to_x_significant_digits(given, 4), expected):
        assert x == y
