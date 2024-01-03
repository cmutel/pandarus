"""Test cases for the __projection__ module."""
from shapely.geometry import (
    GeometryCollection,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
)

from pandarus.utils.projection import WGS84, project_geom, wgs84


def test_projection() -> None:
    """Test projection."""
    given = GeometryCollection(
        [
            MultiPoint([(1, 2), (3, 4), (5, 6), (7, 8)]),
            MultiLineString([[(20, 30), (40, 50), (60, 70)]]),
            MultiPolygon(
                [[[(1.1, 1.2), (1.3, 1.4), (1.5, 1.6), (1.7, 1.8), (1.1, 1.2)], []]]
            ),
        ]
    )
    assert project_geom(given, WGS84, WGS84) == given


def test_wgs84_none() -> None:
    """Test no crs."""
    assert wgs84(None) == WGS84


def test_wgs84_no_defs() -> None:
    """Test crs when no defs."""
    assert wgs84("+no_defs") == WGS84


def test_wgs84_existing() -> None:
    """Test crs when existing."""
    assert wgs84(1) == 1
