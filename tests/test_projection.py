from math import sin, cos, pi, sqrt
from pandarus.projection import MOLLWEIDE, WGS84, project, wgs84
from shapely.geometry import (
    GeometryCollection,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
)
import itertools


def mollweide(lat, lon, lon_0=0, R=6371000):
    """Convert latitude and longitude to cartesian mollweide coordinates
    arguments
    lat, lon -- Latitude and longitude with South and West as Negative
        both as decimal values
    lon_0 -- the longitude of the central meridian, default = Greenwich
    R -- radius of the globe

    Return
    x, y a tuple of coordinates in range $x\in\pm 2R\sqrt{2}$,
      $y\in\pm R\sqrt{2}$
    """
    lat = lat * pi / 180
    lon = lon * pi / 180
    lon_0 = lon_0 * pi / 180  # convert to radians
    theta = solve_theta(lat)
    return (R * 2 * sqrt(2) * (lon - lon_0) * cos(theta) / pi,
            R * sqrt(2) * sin(theta))


def test_projection():
    given = GeometryCollection([
        MultiPoint([(1, 2), (3, 4), (5, 6), (7, 8)]),
        MultiLineString([[(20, 30), (40, 50), (60, 70)]]),
        MultiPolygon([[[(1.1, 1.2), (1.3, 1.4), (1.5, 1.6), (1.7, 1.8), (1.1, 1.2)], []]]),
    ])
    result = project(given, WGS84, MOLLWEIDE).wkt
    assert 'MULTIPOINT' in result
    assert 'GEOMETRYCOLLECTION' in result

    expected = 'GEOMETRYCOLLECTION (MULTIPOINT (1 2, 3 4, 5 6, 7 8), MULTILINESTRING ((20 30, 40 50, 60 70)), MULTIPOLYGON (((1.1 1.2, 1.3 1.4, 1.5 1.6, 1.7 1.8, 1.1 1.2))))'
    assert project(given, WGS84, WGS84).wkt == expected


def test_wgs84():
    """Fix no CRS or fiona giving abbreviated wgs84 definition."""
    assert wgs84(None) == WGS84
    assert wgs84("+no_defs") == WGS84
    assert wgs84(1) == 1
