from pandarus import intersect
from pandarus.intersections import intersection_worker
from pandarus.conversion import round_to_x_significant_digits
from math import sqrt
import fiona
import json
import numpy as np
import os
import tempfile

dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
grid = os.path.join(dirpath, "grid.geojson")
square = os.path.join(dirpath, "square.geojson")
range_raster = os.path.join(dirpath, "range.tif")
dem = os.path.join(dirpath, "DEM.tif")
outside = os.path.join(dirpath, "outside.geojson")
remain_result = os.path.join(dirpath, "remaining.geojson")
pgrid = os.path.join(dirpath, "grid-3410.geojson")
igrid = os.path.join(dirpath, "grid-ints.geojson")
psquare = os.path.join(dirpath, "square-3857.geojson")
plines =  os.path.join(dirpath, "lines-25000.geojson")
lines =  os.path.join(dirpath, "lines.geojson")
ppoints =  os.path.join(dirpath, "points-32631.geojson")
points =  os.path.join(dirpath, "points.geojson")


def test_intersection_polygon():
    area = 1/4 * (4e7 / 360) ** 2

    with tempfile.TemporaryDirectory() as dirpath:
        vector_fp, data_fp = intersect(
            outside,
            'name',
            grid,
            'name',
            dirpath=dirpath,
            compress=False,
            log_dir=dirpath
        )
        data = json.load(open(data_fp))

        assert len(data['data']) == 2
        for x, y, z in data['data']:
            assert x == 'by-myself'
            assert y in ('grid cell 1', 'grid cell 3')
            assert np.isclose(z, area, rtol=1e-2)

        assert data['metadata'].keys() == {'first', 'second', 'when'}
        assert data['metadata']['first'].keys() == {'field', 'filename', 'path', 'sha256'}
        assert data['metadata']['second'].keys() == {'field', 'filename', 'path', 'sha256'}

        with fiona.open(vector_fp) as src:
            meta = src.meta

            assert meta['driver'] == 'GeoJSON'
            assert meta['schema'] == {
                'geometry': 'MultiPolygon',
                'properties': dict([
                    ('measure', 'float'),
                    ('from_label', 'str'),
                    ('id', 'int'),
                    ('to_label', 'str')
                ])
            }
            assert meta['crs'] == {'init': 'epsg:4326'}

            coords = [
                [[[(0.5, 1.5), (0.5, 2.0), (1.0, 2.0), (1.0, 1.5), (0.5, 1.5)]]],
                [[[(1.5, 2.0), (1.5, 1.5), (1.0, 1.5), (1.0, 2.0), (1.5, 2.0)]]]
            ]

            for feature in src:
                assert feature['geometry']['coordinates'] in coords
                assert feature['geometry']['type'] == 'MultiPolygon'
                assert feature['properties'].keys() == {'measure', 'from_label', 'to_label', 'id'}
                assert np.isclose(feature['properties']['measure'], area, rtol=1e-2)

def test_intersection_polygon_integer_indices():
    area = 1/4 * (4e7 / 360) ** 2

    with tempfile.TemporaryDirectory() as dirpath:
        vector_fp, data_fp = intersect(
            outside,
            'name',
            igrid,
            'name',
            dirpath=dirpath,
            compress=False,
            log_dir=dirpath
        )
        data = json.load(open(data_fp))

        assert len(data['data']) == 2
        for x, y, z in data['data']:
            assert x == 'by-myself'
            assert y in (1, 3)
            assert np.isclose(z, area, rtol=1e-2)

        assert data['metadata'].keys() == {'first', 'second', 'when'}
        assert data['metadata']['first'].keys() == {'field', 'filename', 'path', 'sha256'}
        assert data['metadata']['second'].keys() == {'field', 'filename', 'path', 'sha256'}

        with fiona.open(vector_fp) as src:
            meta = src.meta

            assert meta['driver'] == 'GeoJSON'
            assert meta['schema'] == {
                'geometry': 'MultiPolygon',
                'properties': dict([
                    ('measure', 'float'),
                    ('from_label', 'str'),
                    ('id', 'int'),
                    ('to_label', 'int')
                ])
            }
            assert meta['crs'] == {'init': 'epsg:4326'}

            coords = [
                [[[(0.5, 1.5), (0.5, 2.0), (1.0, 2.0), (1.0, 1.5), (0.5, 1.5)]]],
                [[[(1.5, 2.0), (1.5, 1.5), (1.0, 1.5), (1.0, 2.0), (1.5, 2.0)]]]
            ]

            for feature in src:
                assert feature['geometry']['coordinates'] in coords
                assert feature['geometry']['type'] == 'MultiPolygon'
                assert feature['properties'].keys() == {'measure', 'from_label', 'to_label', 'id'}
                assert np.isclose(feature['properties']['measure'], area, rtol=1e-2)

def test_intersection_polygon_projection():
    area = 1/4 * (4e7 / 360) ** 2

    with tempfile.TemporaryDirectory() as dirpath:
        vector_fp, data_fp = intersect(
            pgrid,
            'name',
            psquare,
            'name',
            dirpath=dirpath,
            compress=False,
            log_dir=dirpath
        )
        data = json.load(open(data_fp))

        assert len(data['data']) == 4
        for x, y, z in data['data']:
            assert x in ['grid cell {}'.format(x) for x in range(4)]
            assert y == 'single'
            assert np.isclose(z, area, rtol=1e-2)

        assert data['metadata'].keys() == {'first', 'second', 'when'}
        assert data['metadata']['first'].keys() == {'field', 'filename', 'path', 'sha256'}
        assert data['metadata']['second'].keys() == {'field', 'filename', 'path', 'sha256'}

        with fiona.open(vector_fp) as src:
            meta = src.meta

            assert meta['driver'] == 'GeoJSON'
            assert meta['schema'] == {
                'geometry': 'MultiPolygon',
                'properties': dict([
                    ('measure', 'float'),
                    ('from_label', 'str'),
                    ('id', 'int'),
                    ('to_label', 'str')
                ])
            }
            assert meta['crs'] == {'init': 'epsg:4326'}

            coords = [
                [[[(0.5, 1.0), (1.0, 1.0), (1.0, 0.5), (0.5, 0.5), (0.5, 1.0)]]],
                [[[(1.0, 1.5), (1.0, 1.0), (0.5, 1.0), (0.5, 1.5), (1.0, 1.5)]]],
                [[[(1.0, 0.5), (1.0, 1.0), (1.5, 1.0), (1.5, 0.5), (1.0, 0.5)]]],
                [[[(1.0, 1.0), (1.0, 1.5), (1.5, 1.5), (1.5, 1.0), (1.0, 1.0)]]]
            ]

            for feature in src:
                print(feature['geometry']['coordinates'])
                assert feature['geometry']['coordinates'] in coords
                assert feature['geometry']['type'] == 'MultiPolygon'
                assert feature['properties'].keys() == {'measure', 'from_label', 'to_label', 'id'}
                assert np.isclose(feature['properties']['measure'], area, rtol=1e-2)

def test_intersection_line():
    one_degree = 4e7 / 360

    with tempfile.TemporaryDirectory() as dirpath:
        vector_fp, data_fp = intersect(
            lines,
            'name',
            grid,
            'name',
            dirpath=dirpath,
            compress=False,
            log_dir=dirpath
        )
        data = json.load(open(data_fp))
        data_dct = {(x, y): z for x, y, z in data['data']}

        assert len(data['data']) == 4
        assert np.isclose(data_dct[('A', 'grid cell 0')], 62000, rtol=1e-2)
        assert np.isclose(data_dct[('A', 'grid cell 1')], one_degree, rtol=1e-2)
        assert np.isclose(data_dct[('A', 'grid cell 3')], 50000, rtol=1e-2)
        assert np.isclose(data_dct[('B', 'grid cell 2')], sqrt(2) * one_degree / 2, rtol=2e-2)

        assert data['metadata'].keys() == {'first', 'second', 'when'}
        assert data['metadata']['first'].keys() == {'field', 'filename', 'path', 'sha256'}
        assert data['metadata']['second'].keys() == {'field', 'filename', 'path', 'sha256'}

        with fiona.open(vector_fp) as src:
            meta = src.meta

            assert meta['driver'] == 'GeoJSON'
            assert meta['schema'] == {
                'geometry': 'MultiLineString',
                'properties': dict([
                    ('measure', 'float'),
                    ('from_label', 'str'),
                    ('id', 'int'),
                    ('to_label', 'str')
                ])
            }
            assert meta['crs'] == {'init': 'epsg:4326'}

            coords = [
                [[(1.0, 1.5), (1.5, 1.5)]],
                [[(0.5, 1.0), (0.5, 1.5), (1.0, 1.5)]],
                [[(0.5, 0.5), (0.5, 1.0)]],
                [[(1.0, 1.0), (1.5, 0.5)]]
            ]

            for feature in src:
                assert feature['geometry']['coordinates'] in coords
                assert feature['geometry']['type'] == 'MultiLineString'
                assert feature['properties'].keys() == {'measure', 'from_label', 'to_label', 'id'}

def test_intersection_line_projection():
    one_degree = 4e7 / 360

    with tempfile.TemporaryDirectory() as dirpath:
        vector_fp, data_fp = intersect(
            plines,
            'name',
            pgrid,
            'name',
            dirpath=dirpath,
            compress=False,
            log_dir=dirpath
        )
        data = json.load(open(data_fp))
        data_dct = {(x, y): z for x, y, z in data['data']}

        assert len(data['data']) == 5
        assert np.isclose(data_dct[('A', 'grid cell 0')], 62000, rtol=1e-2)
        assert np.isclose(data_dct[('A', 'grid cell 1')], one_degree, rtol=1e-2)
        assert np.isclose(data_dct[('A', 'grid cell 3')], 50000, rtol=1e-2)
        assert np.isclose(data_dct[('B', 'grid cell 2')], sqrt(2) * one_degree / 2, rtol=2e-2)
        assert data_dct[('B', 'grid cell 3')] < 1e-3

        assert data['metadata'].keys() == {'first', 'second', 'when'}
        assert data['metadata']['first'].keys() == {'field', 'filename', 'path', 'sha256'}
        assert data['metadata']['second'].keys() == {'field', 'filename', 'path', 'sha256'}

        with fiona.open(vector_fp) as src:
            meta = src.meta

            assert meta['driver'] == 'GeoJSON'
            assert meta['schema'] == {
                'geometry': 'MultiLineString',
                'properties': dict([
                    ('measure', 'float'),
                    ('from_label', 'str'),
                    ('id', 'int'),
                    ('to_label', 'str')
                ])
            }
            assert meta['crs'] == {'init': 'epsg:4326'}

            coords = [np.array(x) for x in [
                [[[1., 1.], [1., 1.]]],
                [[(1.0, 1.5), (1.5, 1.5)]],
                [[(0.5, 1.0), (0.5, 1.5), (1.0, 1.5)]],
                [[(0.5, 0.5), (0.5, 1.0)]],
                [[(1.0, 1.0), (1.5, 0.5)]]
            ]]

            arrays = [
                round_to_x_significant_digits(np.array(x['geometry']['coordinates']))
                for x in src
            ]

            for array in arrays:
                print(array)
                assert any(np.allclose(array, obj)
                    for obj in coords
                    if array.shape == obj.shape)

            for feature in src:
                assert feature['geometry']['type'] == 'MultiLineString'
                assert feature['properties'].keys() == {'measure', 'from_label', 'to_label', 'id'}

def test_intersection_point():
    with tempfile.TemporaryDirectory() as dirpath:
        vector_fp, data_fp = intersect(
            points,
            'name',
            grid,
            'name',
            dirpath=dirpath,
            compress=False,
            log_dir=dirpath
        )
        data = json.load(open(data_fp))
        data_dct = {(x, y): z for x, y, z in data['data']}

        assert sorted(data['data']) == sorted([['point 1', 'grid cell 0', 1.0], ['point 2', 'grid cell 3', 1.0]])

        assert data['metadata'].keys() == {'first', 'second', 'when'}
        assert data['metadata']['first'].keys() == {'field', 'filename', 'path', 'sha256'}
        assert data['metadata']['second'].keys() == {'field', 'filename', 'path', 'sha256'}

        with fiona.open(vector_fp) as src:
            meta = src.meta

            assert meta['driver'] == 'GeoJSON'
            assert meta['schema'] == {
                'geometry': 'MultiPoint',
                'properties': dict([
                    ('measure', 'float'),
                    ('from_label', 'str'),
                    ('id', 'int'),
                    ('to_label', 'str')
                ])
            }
            assert meta['crs'] == {'init': 'epsg:4326'}

            coords = [[(0.5, 0.5)], [(1.5, 1.5)]]

            for feature in src:
                assert feature['geometry']['coordinates'] in coords
                assert feature['geometry']['type'] == 'MultiPoint'
                assert feature['properties'].keys() == {'measure', 'from_label', 'to_label', 'id'}

def test_intersection_point_projection():
    with tempfile.TemporaryDirectory() as dirpath:
        vector_fp, data_fp = intersect(
            ppoints,
            'name',
            pgrid,
            'name',
            dirpath=dirpath,
            compress=False,
            log_dir=dirpath
        )
        data = json.load(open(data_fp))
        data_dct = {(x, y): z for x, y, z in data['data']}

        assert len(data['data']) == 2
        assert data_dct[('point 1', 'grid cell 0')] == 1
        assert data_dct[('point 2', 'grid cell 3')] == 1
        assert data['metadata'].keys() == {'first', 'second', 'when'}
        assert data['metadata']['first'].keys() == {'field', 'filename', 'path', 'sha256'}
        assert data['metadata']['second'].keys() == {'field', 'filename', 'path', 'sha256'}

        with fiona.open(vector_fp) as src:
            meta = src.meta

            assert meta['driver'] == 'GeoJSON'
            assert meta['schema'] == {
                'geometry': 'MultiPoint',
                'properties': dict([
                    ('measure', 'float'),
                    ('from_label', 'str'),
                    ('id', 'int'),
                    ('to_label', 'str')
                ])
            }
            assert meta['crs'] == {'init': 'epsg:4326'}

            coords = [[(0.5, 0.5)], [(1.5, 1.5)]]

            for feature in src:
                print(feature)
                assert feature['geometry']['coordinates'] in coords
                assert feature['geometry']['type'] == 'MultiPoint'
                assert feature['properties'].keys() == {'measure', 'from_label', 'to_label', 'id'}
