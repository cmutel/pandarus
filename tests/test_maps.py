from pandarus.maps import Map, DuplicateFieldID
from rtree import Rtree
import fiona
import os
import pandarus
import pytest


dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
grid = os.path.join(dirpath, "grid.geojson")
duplicates = os.path.join(dirpath, "duplicates.geojson")
raster = os.path.join(dirpath, "test_raster_cfs.tif")
countries = os.path.join(dirpath, "test_countries.gpkg")


def test_init():
    m = Map(grid, 'name')
    assert m.filepath == grid
    assert m.file


def test_raster_error(monkeypatch):
    with pytest.raises(AssertionError):
        m = Map(raster, None)

def test_metadata(monkeypatch):
    m = Map(grid, 'name')
    assert m.metadata == {}

    def fake_open(filepath, **others):
        return others

    monkeypatch.setattr(
        pandarus.maps,
        'check_type',
        lambda x: 'vector'
    )
    monkeypatch.setattr(
        pandarus.maps.fiona,
        'open',
        fake_open
    )

    m = Map(grid, 'name', foo='bar')
    assert m.metadata == {'foo': 'bar'}
    assert m.file == {'foo': 'bar'}


def test_get_fieldnames_dictionary():
    m = Map(grid, 'name')
    expected = {0: 'grid cell 0', 1: 'grid cell 1',
                2: 'grid cell 2', 3: 'grid cell 3'}
    assert m.get_fieldnames_dictionary("name") == expected


def test_get_fieldnames_dictionary_errors():
    m = Map(grid, 'name')
    assert m.get_fieldnames_dictionary()
    assert m.get_fieldnames_dictionary(None)
    assert m.get_fieldnames_dictionary("")
    with pytest.raises(AssertionError):
        m.get_fieldnames_dictionary("bar")

    dupes = Map(duplicates, 'name')
    with pytest.raises(DuplicateFieldID):
        dupes.get_fieldnames_dictionary()


def test_properties():
    m = Map(grid, 'name')
    assert m.geometry == 'Polygon'
    assert m.hash
    assert m.crs == '+init=epsg:4326'


def test_magic_methods():
    m = Map(grid, 'name')

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

def test_getitem():
    print("Supported Fiona drivers:")
    print(fiona.supported_drivers)

    m = Map(grid, 'name')

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
    assert hasattr(m, "_index_map")

@pytest.mark.skipif('TRAVIS' in os.environ,
                    reason="No GPKG driver in Travis")
def test_getitem_geopackage():
    print("Supported Fiona drivers:")
    print(fiona.supported_drivers)

    m = Map(countries, 'name')
    assert m[0]
    assert m[0]['id'] == '1'
    assert hasattr(m, "_index_map")

def test_rtree():
    m = Map(grid, 'name')
    r = m.create_rtree_index()
    assert r == m.rtree_index
    assert isinstance(r, Rtree)
