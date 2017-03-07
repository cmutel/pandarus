from pandarus.maps import Map, DuplicateFieldID
from rtree import Rtree
import os
import pandarus
import pytest


dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
grid = os.path.join(dirpath, "grid.geojson")
duplicates = os.path.join(dirpath, "duplicates.geojson")
raster = os.path.join(dirpath, "test_raster_cfs.tif")


def test_init():
    m = Map(grid)
    assert m.filepath == grid
    assert m.file


def test_raster_conversion(monkeypatch):
    monkeypatch.setattr(
        pandarus.maps,
        'convert_to_vector',
        lambda x: grid
    )
    m = Map(raster)
    assert m.filepath == grid


def test_metadata():
    m = Map(grid)
    assert m.metadata == {}

    m = Map(grid, foo='bar')
    assert m.metadata == {'foo': 'bar'}


def test_get_fieldnames_dictionary():
    m = Map(grid)
    expected = {0: 'grid cell 0', 1: 'grid cell 1',
                2: 'grid cell 2', 3: 'grid cell 3'}
    assert m.get_fieldnames_dictionary("name") == expected


def test_get_fieldnames_dictionary_errors():
    m = Map(grid)
    with pytest.raises(AssertionError):
        m.get_fieldnames_dictionary(None)
    with pytest.raises(AssertionError):
        m.get_fieldnames_dictionary("")
    with pytest.raises(AssertionError):
        m.get_fieldnames_dictionary("bar")

    dupes = Map(duplicates)
    with pytest.raises(DuplicateFieldID):
        dupes.get_fieldnames_dictionary("name")


def test_properties():
    m = Map(grid)
    assert m.geometry == 'Polygon'
    assert m.hash
    assert m.crs == '+init=epsg:4326'


def test_magic_methods():
    m = Map(grid)
    for i, x in enumerate(m):
        pass

    assert i == 3

    expected = {
        'geometry': {
            'type': 'Polygon',
            'coordinates': [[(1.0, 0.0), (1.0, 1.0), (2.0, 1.0), (2.0, 0.0), (1.0, 0.0)]]
            },
        'properties': {'name': 'grid cell 2'},
        'id': '2',
        'type': 'Feature'
    }
    assert m[2] == expected

    assert len(m) == 4

def test_rtree():
    m = Map(grid)
    r = m.create_rtree_index()
    assert r == m.rtree_index
    assert isinstance(r, Rtree)
