from pandarus import Map
from pandarus.projection import project, WGS84, MOLLWEIDE
from pandarus.geometry import (
    clean,
    get_intersection as _get_intersection,
    get_measure,
    get_remaining,
    IncompatibleTypes,
    recursive_geom_finder,
)
from shapely.geometry import (
    GeometryCollection,
    LinearRing,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
    mapping,
)
import numpy as np
import os
import pytest

dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
grid = os.path.join(dirpath, "grid.geojson")

to_mollweide = lambda x: project(x, WGS84, MOLLWEIDE)


def get_intersection(*args, **kwargs):
    """Unwrap ``get_intersection`` result dictionaries to give geometries in GeoJSON"""
    dct = _get_intersection(*args, **kwargs)
    for v in dct.values():
        if 'geom' in v:
            v['geom'] = mapping(v['geom'])
    return dct


# get_intersection

def test_no_return_geoms():
    mp = Point((0.5, 1))
    expected = {
        0: {'measure': 1},
        1: {'measure': 1}
    }
    result = get_intersection(mp, 'point', Map(grid, 'name'), (0, 1, 2, 3), to_meters=False, return_geoms=False)
    print(result)
    assert result == expected

def test_recurse_geometry_collection():
    mp = MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])
    gc = GeometryCollection([mp])
    assert recursive_geom_finder(gc, 'point').wkt == mp.wkt

    mp = MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])
    gc = GeometryCollection([mp])
    assert recursive_geom_finder(gc, 'line') is None


# Points

def test_single_point():
    mp = Point((0.5, 1))
    expected = {
        0: {
            'geom': {'type': 'MultiPoint', 'coordinates': ((0.5, 1.0),)},
            'measure': 1},
        1: {
            'geom': {'type': 'MultiPoint', 'coordinates': ((0.5, 1.0),)},
            'measure': 1}
        }
    result = get_intersection(mp, 'point', Map(grid, 'name'), (0, 1, 2, 3))
    assert result == expected

    expected = {0: {'geom': {'type': 'MultiPoint', 'coordinates': ((0.5, 1.0),)}, 'measure': 1}}
    assert get_intersection(mp, 'point', Map(grid, 'name'), (0, 2)) == expected

def test_multi_point():
    mp = MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])
    expected = {
        0: {
            'geom': {'coordinates': ((0.5, 0.5), (0.5, 1.0), (1.0, 1.0)), 'type': 'MultiPoint'},
            'measure': 3},
        1: {
            'geom': {'coordinates': ((0.5, 1.0), (1.0, 1.0)), 'type': 'MultiPoint'},
            'measure': 2},
        2: {
            'geom': {'coordinates': ((1.0, 1.0),), 'type': 'MultiPoint'},
            'measure': 1},
        3: {
            'geom': {'coordinates': ((1.0, 1.0), (1.5, 1.5)), 'type': 'MultiPoint'},
            'measure': 2}
    }
    assert get_intersection(mp, 'point', Map(grid, 'name'), (0, 1, 2, 3)) == expected

def test_point_geometry_collection():
    mp = GeometryCollection([MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])])
    expected = {
        0: {
            'geom': {'coordinates': ((0.5, 0.5), (0.5, 1.0), (1.0, 1.0)), 'type': 'MultiPoint'},
            'measure': 3},
        1: {
            'geom': {'coordinates': ((0.5, 1.0), (1.0, 1.0)), 'type': 'MultiPoint'},
            'measure': 2},
        2: {
            'geom': {'coordinates': ((1.0, 1.0),), 'type': 'MultiPoint'},
            'measure': 1},
        3: {
            'geom': {'coordinates': ((1.0, 1.0), (1.5, 1.5)), 'type': 'MultiPoint'},
            'measure': 2}
    }
    assert get_intersection(mp, 'point', Map(grid, 'name'), (0, 1, 2, 3)) == expected

def test_point_wrong_geometry():
    ls = LineString([(0.5, 0.5), (1.5, 0.5)])
    assert get_intersection(ls, 'point', Map(grid, 'name'), (0, 1, 2, 3)) == {}

# Lines

def test_line_string():
    ls = LineString([(0.5, 0.5), (1.5, 0.5)])
    expected = {
        0: {
            'measure': 0.5,
            'geom': {'coordinates': (((0.5, 0.5), (1.0, 0.5)),), 'type': 'MultiLineString'}},
        2: {
            'measure': 0.5,
            'geom': {'coordinates': (((1.0, 0.5), (1.5, 0.5)),), 'type': 'MultiLineString'}}
    }
    result = get_intersection(ls, 'line', Map(grid, 'name'), (0, 1, 2, 3), to_meters=False)
    assert result == expected

    expected = {0: {
        'geom': {'type': 'MultiLineString', 'coordinates': (((0.5, 0.5), (1.0, 0.5)),)},
        'measure': 0.5
    }}
    result = get_intersection(ls, 'line', Map(grid, 'name'), (0, 1), to_meters=False)
    print(result)
    assert result == expected

def test_multi_line_string():
    ls = MultiLineString([[(0.5, 0.5), (1.5, 0.5)]])
    expected = {
        0: {
            'measure': 0.5,
            'geom': {'type': 'MultiLineString', 'coordinates': (((0.5, 0.5), (1.0, 0.5)),)}},
        2: {
            'measure': 0.5,
            'geom': {'type': 'MultiLineString', 'coordinates': (((1.0, 0.5), (1.5, 0.5)),)}}
    }
    assert get_intersection(ls, 'line', Map(grid, 'name'), (0, 1, 2, 3), to_meters=False) == expected

    expected = {0: {
        'measure': 0.5,
        'geom': {'coordinates': (((0.5, 0.5), (1.0, 0.5)),), 'type': 'MultiLineString'}
    }}
    assert get_intersection(ls, 'line', Map(grid, 'name'), (0, 1), to_meters=False) == expected

def test_linear_ring():
    ls = LinearRing([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)])
    expected = {
        0: {
            'measure': 1,
            'geom': {'type': 'MultiLineString', 'coordinates': (((0.5, 0.5), (1.0, 0.5)), ((0.5, 1.0), (0.5, 0.5)))}},
        1: {
            'measure': 1,
            'geom': {'type': 'MultiLineString', 'coordinates': (((1.0, 1.5), (0.5, 1.5), (0.5, 1.0)),)}},
        2: {
            'measure': 1,
            'geom': {'type': 'MultiLineString', 'coordinates': (((1.0, 0.5), (1.5, 0.5), (1.5, 1.0)),)}},
        3: {
            'measure': 1,
            'geom': {'type': 'MultiLineString', 'coordinates': (((1.5, 1.0), (1.5, 1.5), (1.0, 1.5)),)}}
    }
    result = get_intersection(ls, 'line', Map(grid, 'name'), (0, 1, 2, 3), to_meters=False)
    assert result == expected

    expected = {
        0: {
            'measure': 1,
            'geom': {'type': 'MultiLineString', 'coordinates': (((0.5, 0.5), (1.0, 0.5)), ((0.5, 1.0), (0.5, 0.5)))}},
        1: {
            'measure': 1,
            'geom': {'type': 'MultiLineString', 'coordinates': (((1.0, 1.5), (0.5, 1.5), (0.5, 1.0)),)}}
    }
    assert get_intersection(ls, 'line', Map(grid, 'name'), (0, 1), to_meters=False) == expected

def test_line_geometry_collection():
    ls = GeometryCollection([LineString([(0.5, 0.5), (1.5, 0.5)])])
    expected = {
        0: {
            'geom': {'coordinates': (((0.5, 0.5), (1.0, 0.5)),), 'type': 'MultiLineString'},
            'measure': 0.5},
        2: {
            'geom': {'coordinates': (((1.0, 0.5), (1.5, 0.5)),), 'type': 'MultiLineString'},
            'measure': 0.5}
    }
    assert get_intersection(ls, 'line', Map(grid, 'name'), (0, 1, 2, 3), to_meters=False) == expected

    expected = {
        0: {
            'measure': 0.5,
            'geom': {'type': 'MultiLineString', 'coordinates': (((0.5, 0.5), (1.0, 0.5)),)}}
    }
    assert get_intersection(ls, 'line', Map(grid, 'name'), (0, 1), to_meters=False) == expected

def test_line_wrong_geometry():
    mp = Point((0.5, 1))
    assert get_intersection(mp, 'line', Map(grid, 'name'), (0, 1, 2, 3)) == {}

# Polygons

def test_polygon():
    pg = Polygon([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)])
    expected = {
        0: {
            'measure': 0.25,
            'geom': {'coordinates': [(((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)], 'type': 'MultiPolygon'}},
        1: {
            'measure': 0.25,
            'geom': {'coordinates': [(((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)], 'type': 'MultiPolygon'}},
        2: {
            'measure': 0.25,
            'geom': {'coordinates': [(((1.5, 1.0), (1.5, 0.5), (1.0, 0.5), (1.0, 1.0), (1.5, 1.0)),)], 'type': 'MultiPolygon'}},
        3: {
            'measure': 0.25,
            'geom': {'coordinates': [(((1.0, 1.5), (1.5, 1.5), (1.5, 1.0), (1.0, 1.0), (1.0, 1.5)),)], 'type': 'MultiPolygon'}}
    }
    assert get_intersection(pg, 'polygon', Map(grid, 'name'), (0, 1, 2, 3), to_meters=False) == expected

    expected = {
        0: {
            'measure': 0.25,
            'geom': {'coordinates': [(((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)], 'type': 'MultiPolygon'}},
        1: {
            'measure': 0.25,
            'geom': {'coordinates': [(((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)], 'type': 'MultiPolygon'}}
    }
    assert get_intersection(pg, 'polygon', Map(grid, 'name'), (0, 1), to_meters=False) == expected

def test_multi_polygon():
    pg = MultiPolygon([[
        [(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)], []
    ]])
    expected = {
        0: {
            'geom': {'type': 'MultiPolygon', 'coordinates': [(((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)]},
            'measure': 0.25},
        1: {
            'geom': {'type': 'MultiPolygon', 'coordinates': [(((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)]},
            'measure': 0.25},
        2: {'geom': {'type': 'MultiPolygon', 'coordinates': [(((1.5, 1.0), (1.5, 0.5), (1.0, 0.5), (1.0, 1.0), (1.5, 1.0)),)]},
            'measure': 0.25},
        3: {
            'geom': {'type': 'MultiPolygon', 'coordinates': [(((1.0, 1.5), (1.5, 1.5), (1.5, 1.0), (1.0, 1.0), (1.0, 1.5)),)]},
            'measure': 0.25}
    }
    assert get_intersection(pg, 'polygon', Map(grid, 'name'), (0, 1, 2, 3), to_meters=False) == expected

    expected = {
        0: {
            'measure': 0.25,
            'geom': {'coordinates': [(((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)], 'type': 'MultiPolygon'}},
        1: {
            'measure': 0.25,
            'geom': {'coordinates': [(((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)], 'type': 'MultiPolygon'}}
    }
    assert get_intersection(pg, 'polygon', Map(grid, 'name'), (0, 1), to_meters=False) == expected

def test_polygon_geometry_collection():
    pg = GeometryCollection([Polygon([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)])])
    expected = {
        0: {
            'geom': {'coordinates': [(((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)], 'type': 'MultiPolygon'},
            'measure': 0.25},
        1: {
            'geom': {'coordinates': [(((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)], 'type': 'MultiPolygon'},
            'measure': 0.25},
        2: {
            'geom': {'coordinates': [(((1.5, 1.0), (1.5, 0.5), (1.0, 0.5), (1.0, 1.0), (1.5, 1.0)),)], 'type': 'MultiPolygon'},
            'measure': 0.25},
        3: {
            'geom': {'coordinates': [(((1.0, 1.5), (1.5, 1.5), (1.5, 1.0), (1.0, 1.0), (1.0, 1.5)),)], 'type': 'MultiPolygon'},
            'measure': 0.25}
    }
    assert get_intersection(pg, 'polygon', Map(grid, 'name'), (0, 1, 2, 3), to_meters=False) == expected

    expected = {
        0: {
            'geom': {'type': 'MultiPolygon', 'coordinates': [(((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)]},
            'measure': 0.25},
        1: {'geom': {'type': 'MultiPolygon', 'coordinates': [(((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)]},
            'measure': 0.25}
    }
    assert get_intersection(pg, 'polygon', Map(grid, 'name'), (0, 1), to_meters=False) == expected

def test_polygon_wrong_geometry():
    mp = Point((0.5, 1))
    assert get_intersection(mp, 'polygon', Map(grid, 'name'), (0, 1, 2, 3)) == {}

# Clean

def test_clean():
    p = Polygon([(0,0), (0,3), (3,3), (3,0), (2,0),
                 (2,2), (1,2), (1,1), (2,1), (2,0), (0,0)])
    pp = clean(p)
    assert not p.is_valid
    assert pp.is_valid

# Get measure

def test_get_measure_point():
    mp = MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])
    assert get_measure(mp) == 4
    assert get_measure(mp, 'point') == 4

    mp = Point((0.5, 1))
    assert get_measure(mp) == 1
    assert get_measure(mp, 'point') == 1

def test_get_measure_point_not_point_geom():
    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    with pytest.raises(ValueError):
        get_measure(geom, 'point')

def test_get_measure_line():
    geom = LineString([(0, 0), (0, 1)])
    assert get_measure(geom) == 1
    assert get_measure(geom, 'line') == 1

    geom = MultiLineString([
        [(0.5, 0.5), (1.5, 0.5)],
        [(1, 1), (1, 11)]
    ])
    assert get_measure(geom) == 11
    assert get_measure(geom, 'line') == 11

    geom = LinearRing([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)])
    assert get_measure(geom) == 4
    assert get_measure(geom, 'line') == 4

def test_get_measure_polygon():
    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    assert get_measure(geom) == 1
    assert get_measure(geom, 'polygon') == 1

    geom = MultiPolygon([[
        [(0, 0), (0, 2), (2, 2), (2, 0), (0 ,0)],
        [
            [(0.5, 0.5), (0.5, 1.5), (1.5, 1.5), (1.5, 0.5), (0.5, 0.5)]
        ]
    ], [
        [(10, 10), (10, 17), (11, 17), (11, 10), (10, 10)],
        []
    ]])
    assert get_measure(geom) == 10
    assert get_measure(geom, 'polygon') == 10

def test_get_measure_wrong_type():
    mp = MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])
    gc = GeometryCollection([mp])
    with pytest.raises(ValueError):
        get_measure(gc)

    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    get_measure(geom)
    with pytest.raises(ValueError):
        get_measure(geom, 'foo')

# Remaining calculations

def test_get_remaining_wrong_type():
    mp = MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])
    gc = GeometryCollection([mp])
    with pytest.raises(ValueError):
        get_remaining(gc, [])

def test_remaining_incompatible_types():
    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    other = LineString([(0, .5), (0, 1)])
    with pytest.raises(IncompatibleTypes):
        get_remaining(geom, [other])

# Polygons

def test_remaining_polygons():
    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    half = Polygon([(0, 0), (0, .5), (1, .5), (1, 0), (0, 0)])
    assert get_remaining(geom, [half], False) == 0.5

    second = Polygon([(0, .5), (0, 1), (1, 1), (1, .5), (0, .5)])
    assert get_remaining(geom, [half, second], False) == 0

def test_remaining_polygons_projection():
    area = 1/2 * (4e7 / 360) ** 2
    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    half = Polygon([(0, 0), (0, .5), (1, .5), (1, 0), (0, 0)])
    assert np.isclose(get_remaining(geom, [half]), area, 1e-2)

def test_remaining_polygons_no_geoms():
    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    assert get_remaining(geom, [], False) == 1

# Lines

def test_remaining_lines():
    geom = LineString([(0, 0), (0, 1), (1, 1)])
    half = LineString([(0, 0), (0, 1)])
    assert get_remaining(geom, [half], False) == 1

    second = LineString([(0, 1), (1, 1)])
    assert get_remaining(geom, [half, second], False) == 0

def test_remaining_lines_overlap():
    geom = LineString([(0, 0), (0, 1), (1, 1)])
    half = LineString([(0, 0), (0, 1)])
    quarter = LineString([(0, 0.5), (0, 1)])
    result = get_remaining(geom, [half, quarter], False)
    assert result == (2 - 1) * (1.5/1)

def test_remaining_lines_projection():
    length = 4e7 / 360
    geom = LineString([(0, 0), (0, 1), (1, 1)])
    half = LineString([(0, 0), (0, 1)])
    assert np.isclose(get_remaining(geom, [half]), 1e5, 1e-2)

def test_remaining_lines_no_geoms():
    geom = LineString([(0, 0), (0, 1), (1, 1)])
    assert get_remaining(geom, [], False) == 2

# Points

def test_remaining_points():
    geom = MultiPoint([(0, 0), (0, 1)])
    half = Point((0, 0))
    assert get_remaining(geom, [half], False) == 1

def test_remaining_points_overlap():
    geom = MultiPoint([(0, 0), (0, 1)])
    first = Point((0, 0))
    second = Point((0, 0))
    result = get_remaining(geom, [first, second], False)
    assert result == (2 - 1) * (2 / 1)

def test_remaining_points_projection():
    geom = MultiPoint([(0, 0), (0, 1)])
    half = Point((0, 0))
    assert get_remaining(geom, [half]) == 1

def test_remaining_points_no_geoms():
    geom = MultiPoint([(0, 0), (0, 1)])
    assert get_remaining(geom, [], False) == 2
