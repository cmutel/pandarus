from math import sin, cos, pi, sqrt
from pandarus.projection import MOLLWEIDE, WGS84, project, wgs84
from shapely.geometry import (
    GeometryCollection,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
)
import itertools

# From https://gist.github.com/zeimusu/9fcf649171c72c6a5ac5

def solve_theta(lat, epsilon=1e-7):
    """Solve the equation $2\theta\sin(2\theta)=\pi\sin(\mathrm{lat})$
    using Newtons method"""
    if abs(lat) == pi / 2:
        return lat  # avoid division by zero
    theta, nexttheta = lat, 0
    while abs(theta - nexttheta) >= epsilon:
        nexttheta = theta - (
            (2 * theta + sin(2 * theta) - pi * sin(lat)) /
            (2 + 2 * cos(2 * theta))
        )
        theta = nexttheta
    return theta


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
    # coords_list = [(1, 2), (3, 4), (5, 6), (7, 8), (20, 30), (40, 50),
    #                (60, 70), (1.1, 1.2), (1.3, 1.4), (1.5, 1.6), (1.7, 1.8),
    #                (1.1, 1.2)]
    # coords_proj = itertools.chain(*[mollweide(*x) for x in coords_list])
    # expected = 'GEOMETRYCOLLECTION (POINT ({} {}), POINT ({} {}), POINT ({}, {}), POINT ({}, {}), LINESTRING ({} {}, {} {}, {} {}), POLYGON (({} {}, {} {}, {} {}, {} {}, {} {})))'.format(*coords_proj)
    # print(project(given, WGS84, MOLLWEIDE).wkt)
    # print(expected)
    expected = "GEOMETRYCOLLECTION (MULTIPOINT (100185.0882708003 247270.4910231342, 300216.2305808517 494425.512873709, 499418.3780084897 741349.5145514553, 697338.6736791801 987926.7803716012), MULTILINESTRING ((1833617.410786622 3643853.564079695, 3042532.744842044 5873471.95621065, 3049144.542873885 7774469.607891488)), MULTIPOLYGON (((110230.1139862887 148369.6836902506, 130265.5874379087 173096.2132796641, 150297.9722489233 197821.9346805766, 170326.8163664525 222546.7324211789, 110230.1139862887 148369.6836902506))))"
    assert project(given, WGS84, MOLLWEIDE).wkt == expected
    assert project(given).wkt == expected

    expected = 'GEOMETRYCOLLECTION (MULTIPOINT (1 2, 3 4, 5 6, 7 8), MULTILINESTRING ((20 30, 40 50, 60 70)), MULTIPOLYGON (((1.1 1.2, 1.3 1.4, 1.5 1.6, 1.7 1.8, 1.1 1.2))))'
    assert project(given, WGS84, WGS84).wkt == expected


def test_wgs84():
    """Fix no CRS or fiona giving abbreviated wgs84 definition."""
    assert wgs84(None) == WGS84
    assert wgs84("+no_defs") == WGS84
    assert wgs84(1) == 1
