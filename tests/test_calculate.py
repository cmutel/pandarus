from pandarus import Pandarus, Map
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
    for i, f in enumerate(Map(vector)):
        yield i

def test_rasterstats_invalid():
    with pytest.raises(AssertionError):
        result = Pandarus(grid).rasterstats(square)

def test_rasterstats_new_path(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.gen_zonal_stats',
        fake_zonal_stats
    )

    fp = Pandarus(grid, from_metadata={'field': 'name'}).rasterstats(
        range_raster, compressed=False)
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
    result = Pandarus(grid, from_metadata={'field': 'name'}).rasterstats(
        range_raster, fp, compressed=False)
    assert result == fp

    result = json.load(open(fp))
    os.remove(fp)

    expected = [
        ['grid cell 0', 0],
        ['grid cell 1', 1],
        ['grid cell 2', 2],
        ['grid cell 3', 3],
    ]

    assert 'metadata' in result
    assert result['metadata']['vector']['field']
    assert result['metadata']['vector']['sha256']
    assert result['data'] == expected

def test_rasterstats_mismatched_crs(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.gen_zonal_stats',
        fake_zonal_stats
    )

    fp = os.path.join(tempfile.mkdtemp(), "test.json")
    p = Pandarus(grid, from_metadata={'field': 'name'})

    with pytest.warns(UserWarning):
        result = p.rasterstats(dem, fp)

def test_export(monkeypatch):
    class Exporter:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    monkeypatch.setattr(
        'pandarus.calculate.json_exporter',
        Exporter
    )

    p = Pandarus(grid, from_metadata={'field': 'name'})
    with pytest.raises(AttributeError):
        p.export('')

    p.data = {}
    e = p.export("foo")
    assert e.args[0] == []
    assert 'first' in e.args[1]
    assert e.args[2] == 'foo.json'
