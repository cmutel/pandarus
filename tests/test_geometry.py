from pandarus import Map
from pandarus.projection import project, WGS84, MOLLWEIDE
from pandarus.geometry import (
    clean,
    get_intersection as _get_intersection,
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
import os

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
        0: {'measure': 0.5},
        1: {'measure': 0.5}
    }
    assert get_intersection(mp, 'point', Map(grid, 'name'), (0, 1, 2, 3), return_geoms=False) == expected

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
    expected = {0: {'geom': {'type': 'MultiPoint', 'coordinates': ((0.5, 1.0),)}, 'measure': 0.5}, 1: {'geom': {'type': 'MultiPoint', 'coordinates': ((0.5, 1.0),)}, 'measure': 0.5}}
    assert get_intersection(mp, 'point', Map(grid, 'name'), (0, 1, 2, 3)) == expected

    expected = {0: {'geom': {'type': 'MultiPoint', 'coordinates': ((0.5, 1.0),)}, 'measure': 1}}
    assert get_intersection(mp, 'point', Map(grid, 'name'), (0, 2)) == expected

def test_multi_point():
    mp = MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])
    expected = {
        0: {
            'geom': {'coordinates': ((0.5, 0.5), (0.5, 1.0), (1.0, 1.0)), 'type': 'MultiPoint'},
            'measure': 3/8},
        1: {
            'geom': {'coordinates': ((0.5, 1.0), (1.0, 1.0)), 'type': 'MultiPoint'},
            'measure': 2/8},
        2: {
            'geom': {'coordinates': ((1.0, 1.0),), 'type': 'MultiPoint'},
            'measure': 1/8},
        3: {
            'geom': {'coordinates': ((1.0, 1.0), (1.5, 1.5)), 'type': 'MultiPoint'},
            'measure': 2/8}
    }
    assert get_intersection(mp, 'point', Map(grid, 'name'), (0, 1, 2, 3)) == expected

def test_point_geometry_collection():
    mp = GeometryCollection([MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])])
    expected = {
        0: {
            'geom': {'coordinates': ((0.5, 0.5), (0.5, 1.0), (1.0, 1.0)), 'type': 'MultiPoint'},
            'measure': 3/8},
        1: {
            'geom': {'coordinates': ((0.5, 1.0), (1.0, 1.0)), 'type': 'MultiPoint'},
            'measure': 2/8},
        2: {
            'geom': {'coordinates': ((1.0, 1.0),), 'type': 'MultiPoint'},
            'measure': 1/8},
        3: {
            'geom': {'coordinates': ((1.0, 1.0), (1.5, 1.5)), 'type': 'MultiPoint'},
            'measure': 2/8}
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
    assert get_intersection(ls, 'line', Map(grid, 'name'), (0, 1, 2, 3)) == expected

    expected = {0: {
        'geom': {'type': 'MultiLineString', 'coordinates': (((0.5, 0.5), (1.0, 0.5)),)},
        'measure': 1.0
    }}
    assert get_intersection(ls, 'line', Map(grid, 'name'), (0, 1)) == expected

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
    assert get_intersection(ls, 'line', Map(grid, 'name'), (0, 1, 2, 3)) == expected

    expected = {0: {
        'measure': 1.0,
        'geom': {'coordinates': (((0.5, 0.5), (1.0, 0.5)),), 'type': 'MultiLineString'}
    }}
    assert get_intersection(ls, 'line', Map(grid, 'name'), (0, 1)) == expected

def test_linear_ring():
    ls = LinearRing([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)])
    expected = {
        0: {
            'measure': 0.25,
            'geom': {'type': 'MultiLineString', 'coordinates': (((0.5, 0.5), (1.0, 0.5)), ((0.5, 1.0), (0.5, 0.5)))}},
        1: {
            'measure': 0.25,
            'geom': {'type': 'MultiLineString', 'coordinates': (((1.0, 1.5), (0.5, 1.5), (0.5, 1.0)),)}},
        2: {
            'measure': 0.25,
            'geom': {'type': 'MultiLineString', 'coordinates': (((1.0, 0.5), (1.5, 0.5), (1.5, 1.0)),)}},
        3: {
            'measure': 0.25,
            'geom': {'type': 'MultiLineString', 'coordinates': (((1.5, 1.0), (1.5, 1.5), (1.0, 1.5)),)}}
    }
    assert get_intersection(ls, 'line', Map(grid, 'name'), (0, 1, 2, 3)) == expected

    expected = {
        0: {
            'measure': 0.5,
            'geom': {'type': 'MultiLineString', 'coordinates': (((0.5, 0.5), (1.0, 0.5)), ((0.5, 1.0), (0.5, 0.5)))}},
        1: {
            'measure': 0.5,
            'geom': {'type': 'MultiLineString', 'coordinates': (((1.0, 1.5), (0.5, 1.5), (0.5, 1.0)),)}}
    }
    assert get_intersection(ls, 'line', Map(grid, 'name'), (0, 1)) == expected

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
    assert get_intersection(ls, 'line', Map(grid, 'name'), (0, 1, 2, 3)) == expected

    expected = {
        0: {
            'measure': 1.0,
            'geom': {'type': 'MultiLineString', 'coordinates': (((0.5, 0.5), (1.0, 0.5)),)}}
    }
    assert get_intersection(ls, 'line', Map(grid, 'name'), (0, 1)) == expected

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
    assert get_intersection(pg, 'polygon', Map(grid, 'name'), (0, 1, 2, 3)) == expected

    expected = {
        0: {
            'measure': 0.5,
            'geom': {'coordinates': [(((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)], 'type': 'MultiPolygon'}},
        1: {
            'measure': 0.5,
            'geom': {'coordinates': [(((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)], 'type': 'MultiPolygon'}}
    }
    assert get_intersection(pg, 'polygon', Map(grid, 'name'), (0, 1)) == expected

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
    assert get_intersection(pg, 'polygon', Map(grid, 'name'), (0, 1, 2, 3)) == expected

    expected = {
        0: {
            'measure': 0.5,
            'geom': {'coordinates': [(((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)], 'type': 'MultiPolygon'}},
        1: {
            'measure': 0.5,
            'geom': {'coordinates': [(((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)], 'type': 'MultiPolygon'}}
    }
    assert get_intersection(pg, 'polygon', Map(grid, 'name'), (0, 1)) == expected

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
    assert get_intersection(pg, 'polygon', Map(grid, 'name'), (0, 1, 2, 3)) == expected

    expected = {
        0: {
            'geom': {'type': 'MultiPolygon', 'coordinates': [(((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)]},
            'measure': 0.5},
        1: {'geom': {'type': 'MultiPolygon', 'coordinates': [(((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)]},
            'measure': 0.5}
    }
    assert get_intersection(pg, 'polygon', Map(grid, 'name'), (0, 1)) == expected

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

# Measuring

# def test_measure_area():
#     pg = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
#     assert measure_area(pg) == 1
#     assert measure_area(pg, to_mollweide) > 1e6

# def test_measure_line():
#     ls = LineString([(0, 0), (0, 1)])
#     assert measure_line(ls) == 1
#     assert measure_line(ls, to_mollweide) > 1e4
