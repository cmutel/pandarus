from pandarus import (
    calculate_remaining,
    intersect,
    intersections_from_intersection,
    Map,
    raster_statistics,
)
from pandarus.filesystem import json_importer
from pandarus.calculate import as_features
import fiona
import json
import numpy as np
import os
import pytest
import shutil
import tempfile

dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
grid = os.path.join(dirpath, "grid.geojson")
square = os.path.join(dirpath, "square.geojson")
range_raster = os.path.join(dirpath, "range.tif")
dem = os.path.join(dirpath, "DEM.tif")
outside = os.path.join(dirpath, "outside.geojson")
remain_result = os.path.join(dirpath, "remaining.geojson")
inter_res = os.path.join(dirpath, "intersection_result.geojson")
inter_res_md = os.path.join(dirpath, "intersection_result.json.bz2")
inter_res_decompressed = os.path.join(dirpath, "i_result.json")


def fake_zonal_stats(vector, *args, **kwargs):
    for i, f in enumerate(Map(vector, 'name')):
        yield i

def fake_intersection(first, second, indices=None, cpus=None, log_dir=None):
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

    fp = raster_statistics(grid, 'name', range_raster, compress=False)
    assert 'rasterstats' in fp
    assert '.json' in fp
    assert os.path.isfile(fp)
    os.remove(fp)

def test_rasterstats(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.gen_zonal_stats',
        fake_zonal_stats
    )

    with tempfile.TemporaryDirectory() as dirpath:
        fp = os.path.join(dirpath, "test.json")
        result = raster_statistics(grid, 'name', range_raster, output=fp, compress=False)
        assert result == fp

        result = json.load(open(fp))

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

    with tempfile.TemporaryDirectory() as dirpath:
        fp = os.path.join(dirpath, "test.json")

        with open(fp, "w") as f:
            f.write("Original content")

        result = raster_statistics(grid, 'name', range_raster, output=fp, compress=False)

        assert result == fp

        content = open(result).read()
        assert content != 'Original content'

def test_rasterstats_mismatched_crs(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.gen_zonal_stats',
        fake_zonal_stats
    )

    with tempfile.TemporaryDirectory() as dirpath:
        fp = os.path.join(dirpath, "test.json")
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

def test_intersect(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.intersection_dispatcher',
        fake_intersection
    )

    with tempfile.TemporaryDirectory() as dirpath:
        vector_fp, data_fp = intersect(grid, 'name', square, 'name', dirpath=dirpath, compress=False, cpus=None)

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

def test_intersect_default_path(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.intersection_dispatcher',
        fake_intersection
    )

    vector_fp, data_fp = intersect(grid, 'name', square, 'name', cpus=None)

    print(vector_fp)
    print(data_fp)

    assert os.path.isfile(vector_fp)
    os.remove(vector_fp)
    assert os.path.isfile(data_fp)
    os.remove(data_fp)

def test_intersect_overwrite_existing(monkeypatch):
    monkeypatch.setattr(
        'pandarus.calculate.intersection_dispatcher',
        fake_intersection
    )

    with tempfile.TemporaryDirectory() as dirpath:
        vector_fp, data_fp = intersect(grid, 'name', square, 'name', dirpath=dirpath, compress=False, cpus=None)

        with open(vector_fp, "w") as f:
            f.write("Weeeee!")
        with open(data_fp, "w") as f:
            f.write("Wooooo!")

        vector_fp, data_fp = intersect(grid, 'name', square, 'name', dirpath=dirpath, compress=False, cpus=None)

        data = json.load(open(data_fp))
        assert data['data'] == [['grid cell 0', 'single', 42]]

        assert len(fiona.open(vector_fp)) == 1

def test_calculate_remaining():
    # Remaining area is 0.5°  by 1°.
    # Circumference of earth is 40.000 km
    # We are close to equator
    # So area should be 1/2 * (4e7 / 360) ** 2 m2
    area = 1/2 * (4e7 / 360) ** 2

    with tempfile.TemporaryDirectory() as dirpath:
        data_fp = calculate_remaining(outside, 'name', remain_result, dirpath=dirpath, compress=False)
        data = json.load(open(data_fp))

    assert data['data'][0][0] == 'by-myself'
    assert np.isclose(area, data['data'][0][1], rtol=1e-2)
    assert data['metadata'].keys() == {'intersections', 'source', 'when'}
    assert data['metadata']['intersections'].keys() == {'field', 'filename', 'path', 'sha256'}
    assert data['metadata']['source'].keys() == {'field', 'filename', 'path', 'sha256'}

def test_calculate_remaining_copmressed_fp():
    with tempfile.TemporaryDirectory() as dirpath:
        data_fp = calculate_remaining(outside, 'name', remain_result, dirpath=dirpath, compress=False)
        assert os.path.isfile(data_fp)

def test_calculate_remaining_default_path():
    data_fp = calculate_remaining(outside, 'name', remain_result, compress=False)
    assert 'intersections' in data_fp
    os.remove(data_fp)

def test_intersections_from_intersection():
    with tempfile.TemporaryDirectory() as dirpath:
        fp1, fp2 = intersections_from_intersection(inter_res, dirpath=dirpath)
        data = json_importer(fp1)
        result = [
            # Order from geojson file
            [0, 'grid cell 3', 3097248058.207057],
            [1, 'grid cell 2', 3097719886.041353],
            [2, 'grid cell 0', 3097719886.0413523],
            [3, 'grid cell 1', 3097248058.207055],
        ]
        assert data['data'] == result
        assert data['metadata'].keys() == {'first', 'second', 'when'}
        assert data['metadata']['first'].keys() == {'field', 'filename', 'path', 'sha256'}
        assert data['metadata']['second'].keys() == {'field', 'filename', 'path', 'sha256'}

        data = json_importer(fp2)
        result = [
            [0, 'single', 3097248058.207057],
            [1, 'single', 3097719886.041353],
            [2, 'single', 3097719886.0413523],
            [3, 'single', 3097248058.207055],
        ]
        assert data['data'] == result
        assert data['metadata'].keys() == {'first', 'second', 'when'}
        assert data['metadata']['first'].keys() == {'field', 'filename', 'path', 'sha256'}
        assert data['metadata']['second'].keys() == {'field', 'filename', 'path', 'sha256'}

def test_intersections_from_intersection_default_path():
    f1, f2 = intersections_from_intersection(inter_res)
    assert 'intersections' in f1
    os.remove(f1)
    os.remove(f2)

def test_intersections_from_intersection_specify_md():
    with tempfile.TemporaryDirectory() as dirpath:
        fp1, _ = intersections_from_intersection(inter_res, inter_res_md, dirpath=dirpath)
        data = json_importer(fp1)
        result = [
            # Order from geojson file
            [0, 'grid cell 3', 3097248058.207057],
            [1, 'grid cell 2', 3097719886.041353],
            [2, 'grid cell 0', 3097719886.0413523],
            [3, 'grid cell 1', 3097248058.207055],
        ]
        assert data['data'] == result

    with tempfile.TemporaryDirectory() as dirpath:
        fp1, _ = intersections_from_intersection(inter_res, inter_res_decompressed, dirpath=dirpath)
        data = json_importer(fp1)
        result = [
            # Order from geojson file
            [0, 'grid cell 3', 3097248058.207057],
            [1, 'grid cell 2', 3097719886.041353],
            [2, 'grid cell 0', 3097719886.0413523],
            [3, 'grid cell 1', 3097248058.207055],
        ]
        assert data['data'] == result

    with tempfile.TemporaryDirectory() as dirpath:
        shutil.copy(inter_res, dirpath)
        new_fp = os.path.join(dirpath, "intersection_result.geojson")

        fp1, _ = intersections_from_intersection(new_fp, inter_res_decompressed, dirpath=dirpath)
        data = json_importer(fp1)
        result = [
            # Order from geojson file
            [0, 'grid cell 3', 3097248058.207057],
            [1, 'grid cell 2', 3097719886.041353],
            [2, 'grid cell 0', 3097719886.0413523],
            [3, 'grid cell 1', 3097248058.207055],
        ]
        assert data['data'] == result

def test_intersections_from_intersection_not_filepath():
    with pytest.raises(AssertionError):
        intersections_from_intersection('')

    with tempfile.TemporaryDirectory() as dirpath:
        shutil.copy(inter_res, dirpath)
        new_fp = os.path.join(dirpath, "intersection_result.geojson")
        with pytest.raises(ValueError):
            intersections_from_intersection(new_fp, dirpath=dirpath)

def test_intersections_from_intersection_find_metadata():
    with tempfile.TemporaryDirectory() as dirpath:
        shutil.copy(inter_res, dirpath)
        new_fp = os.path.join(dirpath, "intersection_result.geojson")

        shutil.copy(inter_res_md, dirpath)

        fp1, _ = intersections_from_intersection(new_fp, dirpath=dirpath)
        data = json_importer(fp1)
        result = [
            # Order from geojson file
            [0, 'grid cell 3', 3097248058.207057],
            [1, 'grid cell 2', 3097719886.041353],
            [2, 'grid cell 0', 3097719886.0413523],
            [3, 'grid cell 1', 3097248058.207055],
        ]
        assert data['data'] == result

    with tempfile.TemporaryDirectory() as dirpath:
        shutil.copy(inter_res, dirpath)
        new_fp = os.path.join(dirpath, "intersection_result.geojson")

        shutil.copy(
            inter_res_decompressed,
            os.path.join(dirpath, 'intersection_result.json')
        )

        fp1, _ = intersections_from_intersection(new_fp, dirpath=dirpath)
        data = json_importer(fp1)
        result = [
            # Order from geojson file
            [0, 'grid cell 3', 3097248058.207057],
            [1, 'grid cell 2', 3097719886.041353],
            [2, 'grid cell 0', 3097719886.0413523],
            [3, 'grid cell 1', 3097248058.207055],
        ]
        assert data['data'] == result
