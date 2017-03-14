from pandarus import intersect
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


def test_intersection_polygon():
    area = 1/4 * (4e7 / 360) ** 2

    with tempfile.TemporaryDirectory() as dirpath:
        vector_fp, data_fp = intersect(
            outside,
            'name',
            grid,
            'name',
            dirpath=dirpath,
            compress=False
        )
        data = json.load(open(data_fp))

        assert len(data['data']) == 2
        print(data)
        print(area)
        for x, y, z in data['data']:
            assert x == 'by-myself'
            assert y in ('grid cell 1', 'grid cell 3')
            assert np.allclose(z, area, rtol=1e-2)

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
                assert np.allclose(feature['properties']['measure'], area, rtol=1e-2)

def test_intersection_polygon_projection():
    pass

def test_intersection_line():
    pass

def test_intersection_line_projection():
    pass

def test_intersection_point():
    pass

def test_intersection_point_projection():
    pass
