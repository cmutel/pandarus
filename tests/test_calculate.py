from pandarus import Map, raster_statistics, intersect, calculate_remaining
from pandarus.calculate import as_features, get_intersections
import fiona
import json
import os
import pytest
import tempfile

dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
grid = os.path.join(dirpath, "grid.geojson")
square = os.path.join(dirpath, "square.geojson")
range_raster = os.path.join(dirpath, "range.tif")
dem = os.path.join(dirpath, "DEM.tif")


def fake_zonal_stats(vector, *args, **kwargs):
    for i, f in enumerate(Map(vector, 'name')):
        yield i

def fake_intersection(first, indices, second, worker=None):
    _, geom = next(Map(second).iter_latlong())
    return {(0, 0): {'measure': 42, 'geom': geom}}

def test_rasterstats_invalid():
    with pytest.raises(AssertionError):
        raster_statistics(grid, 'name', square)

def test_rasterstats_new_path(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.gen_zonal_stats',
        fake_zonal_stats
    )

    fp = raster_statistics(grid, 'name', range_raster, compressed=False)
    assert 'rasterstats' in fp
    assert '.json' in fp
    assert os.path.isfile(fp)
    os.remove(fp)

def test_rasterstats(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.gen_zonal_stats',
        fake_zonal_stats
    )

    fp = os.path.join(tempfile.mkdtemp(), "test.json")
    result = raster_statistics(grid, 'name', range_raster, output=fp, compressed=False)
    assert result == fp

    result = json.load(open(fp))
    os.remove(fp)

    expected = [
        ['grid cell 0', 0],
        ['grid cell 1', 1],
        ['grid cell 2', 2],
        ['grid cell 3', 3],
    ]

    assert result['metadata'].keys() == {'vector', 'raster', 'when'}
    assert result['metadata']['vector'].keys() == {'field', 'filename', 'path', 'sha256'}
    assert result['metadata']['raster'].keys() == {'band', 'filename', 'path', 'sha256'}
    assert result['data'] == expected

def test_rasterstats_overwrite_existing(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.gen_zonal_stats',
        fake_zonal_stats
    )

    fp = os.path.join(tempfile.mkdtemp(), "test.json")

    with open(fp, "w") as f:
        f.write("Original content")

    result = raster_statistics(grid, 'name', range_raster, output=fp, compressed=False)

    assert result == fp

    content = open(result).read()
    assert content != 'Original content'
    os.remove(fp)

def test_rasterstats_mismatched_crs(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.gen_zonal_stats',
        fake_zonal_stats
    )

    fp = os.path.join(tempfile.mkdtemp(), "test.json")
    with pytest.warns(UserWarning):
        raster_statistics(grid, 'name', dem, output=fp)

def test_as_features(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.mapping',
        lambda x: x
    )

    expected = {
        'geometry': 'Foo',
        'properties': {
            'id': 0,
            'from_label': 1,
            'to_label': 2,
            'measure': 42
        }
    }
    dct = {(1, 2): {'measure': 42, 'geom': 'Foo'}}
    assert next(as_features(dct)) == expected

def test_mp_intersections(monkeypatch):
    def fake_intersect(*arg, **kwargs):
        return "Called intersect"

    monkeypatch.setattr(
        'pandarus.calculate.mp_intersect',
        fake_intersect
    )

    assert get_intersections(grid, square, cpus=1) == 'Called intersect'

def test_intersect(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.intersection_calculation',
        fake_intersection
    )

    dirpath = tempfile.mkdtemp()
    vector_fp, data_fp = intersect(grid, 'name', square, 'name', dirpath=dirpath, compress=False)

    data = json.load(open(data_fp))
    assert data['data'] == [['grid cell 0', 'single', 42]]
    assert data['metadata'].keys() == {'first', 'second', 'when'}
    assert data['metadata']['first'].keys() == {'field', 'filename', 'path', 'sha256'}
    assert data['metadata']['second'].keys() == {'field', 'filename', 'path', 'sha256'}

    expected = {
        'id': '0',
        'type': 'Feature',
        'geometry': {
            'coordinates': [[(0.5, 0.5), (0.5, 1.5), (1.5, 1.5), (1.5, 0.5), (0.5, 0.5)]],
            'type': 'Polygon'
        },
        'properties': dict([('id', 0), ('to_label', 'single'), ('from_label', 'grid cell 0'), ('measure', 42.0)])
    }
    assert next(iter(fiona.open(vector_fp))) == expected

def test_intersect_overwrite_existing(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.intersection_calculation',
        fake_intersection
    )

    dirpath = tempfile.mkdtemp()
    vector_fp, data_fp = intersect(grid, 'name', square, 'name', dirpath=dirpath, compress=False)

    with open(vector_fp, "w") as f:
        f.write("Weeeee!")
    with open(data_fp, "w") as f:
        f.write("Wooooo!")

    vector_fp, data_fp = intersect(grid, 'name', square, 'name', dirpath=dirpath, compress=False)

    data = json.load(open(data_fp))
    assert data['data'] == [['grid cell 0', 'single', 42]]

    assert len(fiona.open(vector_fp)) == 1
