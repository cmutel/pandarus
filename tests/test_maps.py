"""Test cases for the __maps__ module."""
import os

import fiona
import pytest
from rtree import Rtree

import pandarus
from pandarus.maps import DuplicateFieldID, Map

from . import PATH_COUNTRIES, PATH_DUPLICATES, PATH_GRID, PATH_RASTER


def test_init() -> None:
    """Test initializing a map."""
    m = Map(PATH_GRID, "name")
    assert m.filepath == PATH_GRID
    assert m.file


def test_raster_error() -> None:
    """Test initializing raising an error."""
    with pytest.raises(AssertionError):
        _ = Map(PATH_RASTER, None)


def test_metadata(monkeypatch) -> None:
    """Test initializing with metadata."""
    m = Map(PATH_GRID, "name")
    assert not m.metadata

    def fake_open(_, **others):
        return others

    monkeypatch.setattr(pandarus.maps, "check_type", lambda x: "vector")
    monkeypatch.setattr(pandarus.maps.fiona, "open", fake_open)

    m = Map(PATH_GRID, "name", foo="bar")
    assert m.metadata == {"foo": "bar"}
    assert m.file == {"foo": "bar"}


def test_get_fieldnames_dictionary() -> None:
    """Test getting a dictionary of fieldnames."""
    m = Map(PATH_GRID, "name")
    expected = {
        0: "PATH_GRID cell 0",
        1: "PATH_GRID cell 1",
        2: "PATH_GRID cell 2",
        3: "PATH_GRID cell 3",
    }
    assert m.get_fieldnames_dictionary("name") == expected


def test_get_fieldnames_dictionary_errors() -> None:
    """Test getting a dictionary of fieldnames."""
    m = Map(PATH_GRID, "name")
    assert m.get_fieldnames_dictionary()
    assert m.get_fieldnames_dictionary(None)
    assert m.get_fieldnames_dictionary("")
    with pytest.raises(AssertionError):
        m.get_fieldnames_dictionary("bar")

    dupes = Map(PATH_DUPLICATES, "name")
    with pytest.raises(DuplicateFieldID):
        dupes.get_fieldnames_dictionary()


def test_properties() -> None:
    """Test getting properties."""
    m = Map(PATH_GRID, "name")
    assert m.geometry == "Polygon"
    assert m.hash
    assert m.crs == "+init=epsg:4326"


def test_magic_methods() -> None:
    """Test magic methods."""
    m = Map(PATH_GRID, "name")

    i: int
    for i, _ in enumerate(m):
        pass
    assert i == 3

    expected = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [(1.0, 0.0), (1.0, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0)]
            ],
        },
        "properties": {"name": "PATH_GRID cell 2"},
        "id": "2",
        "type": "Feature",
    }

    assert m[2].geometry == expected["geometry"]
    assert m[2].id == expected["id"]
    assert m[2].properties == expected["properties"]
    assert len(m) == 4


def test_getitem() -> None:
    """Test getting an item."""
    print("Supported Fiona drivers:")
    print(fiona.supported_drivers)

    m = Map(PATH_GRID, "name")

    expected = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [(1.0, 0.0), (1.0, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0)]
            ],
        },
        "properties": {"name": "PATH_GRID cell 2"},
        "id": "2",
        "type": "Feature",
    }
    assert m[2] == expected
    assert hasattr(m, "_index_map")


@pytest.mark.skipif("TRAVIS" in os.environ, reason="No GPKG driver in Travis")
def test_getitem_geopackage() -> None:
    """Test getting an item from a GeoPackage."""
    print("Supported Fiona drivers:")
    print(fiona.supported_drivers)

    m = Map(PATH_COUNTRIES, "name")
    assert m[0]
    assert m[0]["id"] == "1"
    assert hasattr(m, "_index_map")


def test_rtree() -> None:
    """Test creating an R-tree index."""
    m = Map(PATH_GRID, "name")
    r = m.create_rtree_index()
    assert r == m.rtree_index
    assert isinstance(r, Rtree)
