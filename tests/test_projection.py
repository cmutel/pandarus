from pandarus.projection import MOLLWEIDE, WGS84, project, wgs84
from shapely.geometry import (
    GeometryCollection,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
)


def test_projection():
    given = GeometryCollection([
        MultiPoint([(1, 2), (3, 4), (5, 6), (7, 8)]),
        MultiLineString([[(20, 30), (40, 50), (60, 70)]]),
        MultiPolygon([[[(1.1, 1.2), (1.3, 1.4), (1.5, 1.6), (1.7, 1.8), (1.1, 1.2)], []]]),
    ])
    result = project(given, WGS84, MOLLWEIDE).wkt
    assert 'MULTIPOINT' in result
    assert 'GEOMETRYCOLLECTION' in result

    result = project(given).wkt
    assert 'MULTIPOINT' in result
    assert 'GEOMETRYCOLLECTION' in result


    expected = 'GEOMETRYCOLLECTION (MULTIPOINT (1 2, 3 4, 5 6, 7 8), MULTILINESTRING ((20 30, 40 50, 60 70)), MULTIPOLYGON (((1.1 1.2, 1.3 1.4, 1.5 1.6, 1.7 1.8, 1.1 1.2))))'
    assert project(given, WGS84, WGS84).wkt == expected


def test_wgs84():
    """Fix no CRS or fiona giving abbreviated wgs84 definition."""
    assert wgs84(None) == WGS84
    assert wgs84("+no_defs") == WGS84
    assert wgs84(1) == 1
