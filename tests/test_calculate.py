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

def test_rasterstats_overwrite_existing(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.gen_zonal_stats',
        fake_zonal_stats
    )

    fp = os.path.join(tempfile.mkdtemp(), "test.json")

    with open(fp, "w") as f:
        f.write("Original content")

    result = Pandarus(grid, from_metadata={'field': 'name'}).rasterstats(
        range_raster, fp, compressed=False)

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
    p = Pandarus(grid, from_metadata={'field': 'name'})

    with pytest.warns(UserWarning):
        result = p.rasterstats(dem, fp)

def test_as_features(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.mapping',
        lambda x: x
    )

    expected = {
        'geometry': 'Foo',
        'properties': {
            'id': 0,
            'from_label': 'grid cell 0',
            'to_label': 'single',
            'measure': 42
        }
    }
    dct = {(0, 0): {'measure': 42, 'geom': 'Foo'}}
    p = Pandarus(grid, square, {'field': 'name'}, {'field': 'name'})
    assert next(p.as_features(dct)) == expected

def test_fieldnames_errors():
    p = Pandarus(grid, square, {'field': 'name'}, {'field': 'name'})
    with pytest.raises(ValueError):
        p.add_from_map_fieldname()
    with pytest.raises(ValueError):
        p.add_to_map_fieldname()
    with pytest.raises(ValueError):
        p.add_areas_map_fieldname()

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
    with pytest.raises(ValueError):
        p.export('')

    p.data = {}
    e = p.export("foo")
    assert e.args[0] == []
    assert 'first' in e.args[1]
    assert e.args[2] == 'foo.json'

def test_unpacking():
    p = Pandarus(grid, from_metadata={'field': 'name'})
    p.data = {(1, 2): 3}
    p.unpack_tuples()
    assert p.data == [(1, 2, 3)]
    p.data = {1: 2, 3: 4}
    p.unpack_dictionary()
    assert p.data == [(1, 2), (3, 4)]

def test_calculate_mp(monkeypatch):
    class Fake:
        @staticmethod
        def intersect(*arg, **kwargs):
            return "Called intersect"

        @staticmethod
        def areas(*arg, **kwargs):
            return "Called areas"

    monkeypatch.setattr(
        'pandarus.calculate.MatchMaker',
        Fake
    )

    p = Pandarus(grid, square, {'field': 'name'}, {'field': 'name'})
    assert p.intersections(cpus=1) == 'Called intersect'
    assert p.calculate_areas(cpus=1) == 'Called areas'
