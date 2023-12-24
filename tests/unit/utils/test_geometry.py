"""Test cases for the __geometry__ module."""
import numpy as np
import pytest
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

from pandarus import Map
from pandarus.errors import IncompatibleTypesError
from pandarus.utils.geometry import (
    clean_geom,
    get_geom_measure,
    get_geom_remaining_measure,
)
from pandarus.utils.geometry import get_intersection as _get_intersection
from pandarus.utils.geometry import recursive_geom_finder

from ... import PATH_GRID


def get_intersection(*args, **kwargs):
    """Unwrap ``get_intersection`` result dictionaries to give geometries in GeoJSON"""
    dct = _get_intersection(*args, **kwargs)
    for v in dct.values():
        if "geom" in v:
            v["geom"] = mapping(v["geom"])
    return dct


# get_intersection


def test_no_return_geoms():
    """Test the get_intersection function with return_geoms=False."""
    mp = Point((0.5, 1))
    expected = {0: {"measure": 1}, 1: {"measure": 1}}
    result = get_intersection(
        mp,
        "point",
        Map(PATH_GRID, "name"),
        (0, 1, 2, 3),
        to_meters=False,
        return_geoms=False,
    )
    print(result)
    assert result == expected


def test_recurse_geometry_collection():
    """Test the get_intersection function with a GeometryCollection."""
    mp = MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])
    gc = GeometryCollection([mp])
    assert recursive_geom_finder(gc, "point").wkt == mp.wkt

    mp = MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])
    gc = GeometryCollection([mp])
    assert recursive_geom_finder(gc, "line") is None


# Points


def test_single_point():
    """Test the intersection of a point with a grid."""
    mp = Point((0.5, 1))
    expected = {
        0: {"geom": {"type": "MultiPoint", "coordinates": ((0.5, 1.0),)}, "measure": 1},
        1: {"geom": {"type": "MultiPoint", "coordinates": ((0.5, 1.0),)}, "measure": 1},
    }
    result = get_intersection(mp, "point", Map(PATH_GRID, "name"), (0, 1, 2, 3))
    assert result == expected

    expected = {
        0: {"geom": {"type": "MultiPoint", "coordinates": ((0.5, 1.0),)}, "measure": 1}
    }
    assert get_intersection(mp, "point", Map(PATH_GRID, "name"), (0, 2)) == expected


def test_multi_point():
    """Test the intersection of a multi-point with a grid."""
    mp = MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])
    expected = {
        0: {
            "geom": {
                "coordinates": ((0.5, 0.5), (0.5, 1.0), (1.0, 1.0)),
                "type": "MultiPoint",
            },
            "measure": 3,
        },
        1: {
            "geom": {"coordinates": ((0.5, 1.0), (1.0, 1.0)), "type": "MultiPoint"},
            "measure": 2,
        },
        2: {"geom": {"coordinates": ((1.0, 1.0),), "type": "MultiPoint"}, "measure": 1},
        3: {
            "geom": {"coordinates": ((1.0, 1.0), (1.5, 1.5)), "type": "MultiPoint"},
            "measure": 2,
        },
    }
    assert (
        get_intersection(mp, "point", Map(PATH_GRID, "name"), (0, 1, 2, 3)) == expected
    )


def test_point_geometry_collection():
    """Test the intersection of a point with a grid."""
    mp = GeometryCollection([MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])])
    expected = {
        0: {
            "geom": {
                "coordinates": ((0.5, 0.5), (0.5, 1.0), (1.0, 1.0)),
                "type": "MultiPoint",
            },
            "measure": 3,
        },
        1: {
            "geom": {"coordinates": ((0.5, 1.0), (1.0, 1.0)), "type": "MultiPoint"},
            "measure": 2,
        },
        2: {"geom": {"coordinates": ((1.0, 1.0),), "type": "MultiPoint"}, "measure": 1},
        3: {
            "geom": {"coordinates": ((1.0, 1.0), (1.5, 1.5)), "type": "MultiPoint"},
            "measure": 2,
        },
    }
    assert (
        get_intersection(mp, "point", Map(PATH_GRID, "name"), (0, 1, 2, 3)) == expected
    )


def test_point_wrong_geometry():
    """Test the intersection of a wrong point with a grid."""
    ls = LineString([(0.5, 0.5), (1.5, 0.5)])
    assert not get_intersection(ls, "point", Map(PATH_GRID, "name"), (0, 1, 2, 3))


# Lines


def test_line_string():
    """Test the intersection of a line with a grid."""
    ls = LineString([(0.5, 0.5), (1.5, 0.5)])
    expected = {
        0: {
            "measure": 0.5,
            "geom": {
                "coordinates": (((0.5, 0.5), (1.0, 0.5)),),
                "type": "MultiLineString",
            },
        },
        2: {
            "measure": 0.5,
            "geom": {
                "coordinates": (((1.0, 0.5), (1.5, 0.5)),),
                "type": "MultiLineString",
            },
        },
    }
    result = get_intersection(
        ls, "line", Map(PATH_GRID, "name"), (0, 1, 2, 3), to_meters=False
    )
    assert result == expected

    expected = {
        0: {
            "geom": {
                "type": "MultiLineString",
                "coordinates": (((0.5, 0.5), (1.0, 0.5)),),
            },
            "measure": 0.5,
        }
    }
    result = get_intersection(
        ls, "line", Map(PATH_GRID, "name"), (0, 1), to_meters=False
    )
    print(result)
    assert result == expected


def test_multi_line_string():
    """Test the intersection of a multi-line with a grid."""
    ls = MultiLineString([[(0.5, 0.5), (1.5, 0.5)]])
    expected = {
        0: {
            "measure": 0.5,
            "geom": {
                "type": "MultiLineString",
                "coordinates": (((0.5, 0.5), (1.0, 0.5)),),
            },
        },
        2: {
            "measure": 0.5,
            "geom": {
                "type": "MultiLineString",
                "coordinates": (((1.0, 0.5), (1.5, 0.5)),),
            },
        },
    }
    assert (
        get_intersection(
            ls, "line", Map(PATH_GRID, "name"), (0, 1, 2, 3), to_meters=False
        )
        == expected
    )

    expected = {
        0: {
            "measure": 0.5,
            "geom": {
                "coordinates": (((0.5, 0.5), (1.0, 0.5)),),
                "type": "MultiLineString",
            },
        }
    }
    assert (
        get_intersection(ls, "line", Map(PATH_GRID, "name"), (0, 1), to_meters=False)
        == expected
    )


def test_linear_ring():
    """Test the intersection of a linear ring with a grid."""
    ls = LinearRing([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)])
    expected = {
        0: {
            "measure": 1,
            "geom": {
                "type": "MultiLineString",
                "coordinates": (((0.5, 0.5), (1.0, 0.5)), ((0.5, 1.0), (0.5, 0.5))),
            },
        },
        1: {
            "measure": 1,
            "geom": {
                "type": "MultiLineString",
                "coordinates": (((1.0, 1.5), (0.5, 1.5), (0.5, 1.0)),),
            },
        },
        2: {
            "measure": 1,
            "geom": {
                "type": "MultiLineString",
                "coordinates": (((1.0, 0.5), (1.5, 0.5), (1.5, 1.0)),),
            },
        },
        3: {
            "measure": 1,
            "geom": {
                "type": "MultiLineString",
                "coordinates": (((1.5, 1.0), (1.5, 1.5), (1.0, 1.5)),),
            },
        },
    }
    result = get_intersection(
        ls, "line", Map(PATH_GRID, "name"), (0, 1, 2, 3), to_meters=False
    )
    assert result == expected

    expected = {
        0: {
            "measure": 1,
            "geom": {
                "type": "MultiLineString",
                "coordinates": (((0.5, 0.5), (1.0, 0.5)), ((0.5, 1.0), (0.5, 0.5))),
            },
        },
        1: {
            "measure": 1,
            "geom": {
                "type": "MultiLineString",
                "coordinates": (((1.0, 1.5), (0.5, 1.5), (0.5, 1.0)),),
            },
        },
    }
    assert (
        get_intersection(ls, "line", Map(PATH_GRID, "name"), (0, 1), to_meters=False)
        == expected
    )


def test_line_geometry_collection():
    """Test the intersection of a line with a grid."""
    ls = GeometryCollection([LineString([(0.5, 0.5), (1.5, 0.5)])])
    expected = {
        0: {
            "geom": {
                "coordinates": (((0.5, 0.5), (1.0, 0.5)),),
                "type": "MultiLineString",
            },
            "measure": 0.5,
        },
        2: {
            "geom": {
                "coordinates": (((1.0, 0.5), (1.5, 0.5)),),
                "type": "MultiLineString",
            },
            "measure": 0.5,
        },
    }
    assert (
        get_intersection(
            ls, "line", Map(PATH_GRID, "name"), (0, 1, 2, 3), to_meters=False
        )
        == expected
    )

    expected = {
        0: {
            "measure": 0.5,
            "geom": {
                "type": "MultiLineString",
                "coordinates": (((0.5, 0.5), (1.0, 0.5)),),
            },
        }
    }
    assert (
        get_intersection(ls, "line", Map(PATH_GRID, "name"), (0, 1), to_meters=False)
        == expected
    )


def test_line_wrong_geometry():
    """Test the intersection of a wrong line with a grid."""
    mp = Point((0.5, 1))
    assert not get_intersection(mp, "line", Map(PATH_GRID, "name"), (0, 1, 2, 3))


# Polygons


def test_polygon(equal_intersections):
    """Test the intersection of a polygon with a grid."""
    pg = Polygon([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)])
    expected = {
        0: {
            "measure": 0.25,
            "geom": {
                "coordinates": [
                    (((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)
                ],
                "type": "MultiPolygon",
            },
        },
        1: {
            "measure": 0.25,
            "geom": {
                "coordinates": [
                    (((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)
                ],
                "type": "MultiPolygon",
            },
        },
        2: {
            "measure": 0.25,
            "geom": {
                "coordinates": [
                    (((1.5, 1.0), (1.5, 0.5), (1.0, 0.5), (1.0, 1.0), (1.5, 1.0)),)
                ],
                "type": "MultiPolygon",
            },
        },
        3: {
            "measure": 0.25,
            "geom": {
                "coordinates": [
                    (((1.0, 1.5), (1.5, 1.5), (1.5, 1.0), (1.0, 1.0), (1.0, 1.5)),)
                ],
                "type": "MultiPolygon",
            },
        },
    }
    assert equal_intersections(
        get_intersection(
            pg, "polygon", Map(PATH_GRID, "name"), (0, 1, 2, 3), to_meters=False
        ),
        expected,
    )

    expected = {
        0: {
            "measure": 0.25,
            "geom": {
                "coordinates": [
                    (((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)
                ],
                "type": "MultiPolygon",
            },
        },
        1: {
            "measure": 0.25,
            "geom": {
                "coordinates": [
                    (((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)
                ],
                "type": "MultiPolygon",
            },
        },
    }
    assert equal_intersections(
        get_intersection(
            pg, "polygon", Map(PATH_GRID, "name"), (0, 1, 2, 3), to_meters=False
        ),
        expected,
    )


def test_multi_polygon(equal_intersections):
    """Test the intersection of a multi-polygon with a grid."""
    pg = MultiPolygon(
        [[[(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)], []]]
    )
    expected = {
        0: {
            "geom": {
                "type": "MultiPolygon",
                "coordinates": [
                    (((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)
                ],
            },
            "measure": 0.25,
        },
        1: {
            "geom": {
                "type": "MultiPolygon",
                "coordinates": [
                    (((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)
                ],
            },
            "measure": 0.25,
        },
        2: {
            "geom": {
                "type": "MultiPolygon",
                "coordinates": [
                    (((1.5, 1.0), (1.5, 0.5), (1.0, 0.5), (1.0, 1.0), (1.5, 1.0)),)
                ],
            },
            "measure": 0.25,
        },
        3: {
            "geom": {
                "type": "MultiPolygon",
                "coordinates": [
                    (((1.0, 1.5), (1.5, 1.5), (1.5, 1.0), (1.0, 1.0), (1.0, 1.5)),)
                ],
            },
            "measure": 0.25,
        },
    }
    assert equal_intersections(
        get_intersection(
            pg, "polygon", Map(PATH_GRID, "name"), (0, 1, 2, 3), to_meters=False
        ),
        expected,
    )

    expected = {
        0: {
            "measure": 0.25,
            "geom": {
                "coordinates": [
                    (((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)
                ],
                "type": "MultiPolygon",
            },
        },
        1: {
            "measure": 0.25,
            "geom": {
                "coordinates": [
                    (((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)
                ],
                "type": "MultiPolygon",
            },
        },
    }
    assert equal_intersections(
        get_intersection(
            pg, "polygon", Map(PATH_GRID, "name"), (0, 1), to_meters=False
        ),
        expected,
    )


def test_polygon_geometry_collection(equal_intersections):
    """Test the intersection of a geometry collection with a grid."""
    pg = GeometryCollection(
        [Polygon([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)])]
    )
    expected = {
        0: {
            "geom": {
                "coordinates": [
                    (((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)
                ],
                "type": "MultiPolygon",
            },
            "measure": 0.25,
        },
        1: {
            "geom": {
                "coordinates": [
                    (((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)
                ],
                "type": "MultiPolygon",
            },
            "measure": 0.25,
        },
        2: {
            "geom": {
                "coordinates": [
                    (((1.5, 1.0), (1.5, 0.5), (1.0, 0.5), (1.0, 1.0), (1.5, 1.0)),)
                ],
                "type": "MultiPolygon",
            },
            "measure": 0.25,
        },
        3: {
            "geom": {
                "coordinates": [
                    (((1.0, 1.5), (1.5, 1.5), (1.5, 1.0), (1.0, 1.0), (1.0, 1.5)),)
                ],
                "type": "MultiPolygon",
            },
            "measure": 0.25,
        },
    }
    assert equal_intersections(
        get_intersection(
            pg, "polygon", Map(PATH_GRID, "name"), (0, 1, 2, 3), to_meters=False
        ),
        expected,
    )

    expected = {
        0: {
            "geom": {
                "type": "MultiPolygon",
                "coordinates": [
                    (((1.0, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5)),)
                ],
            },
            "measure": 0.25,
        },
        1: {
            "geom": {
                "type": "MultiPolygon",
                "coordinates": [
                    (((0.5, 1.0), (0.5, 1.5), (1.0, 1.5), (1.0, 1.0), (0.5, 1.0)),)
                ],
            },
            "measure": 0.25,
        },
    }
    assert equal_intersections(
        get_intersection(
            pg, "polygon", Map(PATH_GRID, "name"), (0, 1), to_meters=False
        ),
        expected,
    )


def test_polygon_wrong_geometry():
    """Test the intersection of a wrong polygon with a grid."""
    mp = Point((0.5, 1))
    assert not get_intersection(mp, "polygon", Map(PATH_GRID, "name"), (0, 1, 2, 3))


# Clean


def test_clean_geom():
    """Test the clean function."""
    p = Polygon(
        [
            (0, 0),
            (0, 3),
            (3, 3),
            (3, 0),
            (2, 0),
            (2, 2),
            (1, 2),
            (1, 1),
            (2, 1),
            (2, 0),
            (0, 0),
        ]
    )
    pp = clean_geom(p)
    assert not p.is_valid
    assert pp.is_valid


# Get measure


def test_get_geom_measure_point():
    """Test the get_geom_measure function with a point."""
    mp = MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])
    assert get_geom_measure(mp) == 4
    assert get_geom_measure(mp, "point") == 4

    mp = Point((0.5, 1))
    assert get_geom_measure(mp) == 1
    assert get_geom_measure(mp, "point") == 1


def test_get_geom_measure_point_not_point_geom():
    """Test the get_geom_measure function with a wrong point."""
    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    with pytest.raises(ValueError):
        get_geom_measure(geom, "point")


def test_get_geom_measure_line():
    """Test the get_geom_measure function with a line."""
    geom = LineString([(0, 0), (0, 1)])
    assert get_geom_measure(geom) == 1
    assert get_geom_measure(geom, "line") == 1

    geom = MultiLineString([[(0.5, 0.5), (1.5, 0.5)], [(1, 1), (1, 11)]])
    assert get_geom_measure(geom) == 11
    assert get_geom_measure(geom, "line") == 11

    geom = LinearRing([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)])
    assert get_geom_measure(geom) == 4
    assert get_geom_measure(geom, "line") == 4


def test_get_geom_measure_polygon():
    """Test the get_geom_measure function with a polygon."""
    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    assert get_geom_measure(geom) == 1
    assert get_geom_measure(geom, "polygon") == 1

    geom = MultiPolygon(
        [
            [
                [(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)],
                [[(0.5, 0.5), (0.5, 1.5), (1.5, 1.5), (1.5, 0.5), (0.5, 0.5)]],
            ],
            [[(10, 10), (10, 17), (11, 17), (11, 10), (10, 10)], []],
        ]
    )
    assert get_geom_measure(geom) == 10
    assert get_geom_measure(geom, "polygon") == 10


def test_get_geom_measure_wrong_type():
    """Test the get_geom_measure function with a wrong type."""
    mp = MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])
    gc = GeometryCollection([mp])
    with pytest.raises(KeyError):
        get_geom_measure(gc)

    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    get_geom_measure(geom)
    with pytest.raises(ValueError):
        get_geom_measure(geom, "foo")


# Remaining calculations


def test_get_geom_remaining_measure_wrong_type():
    """Test the get_geom_remaining_measure function with a wrong type."""
    mp = MultiPoint([(0.5, 0.5), (0.5, 1), (1, 1), (1.5, 1.5)])
    gc = GeometryCollection([mp])
    with pytest.raises(ValueError):
        get_geom_remaining_measure(gc, [])


def test_remaining_incompatible_types():
    """Test remaining calculation with incompatible types."""
    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    other = LineString([(0, 0.5), (0, 1)])
    with pytest.raises(IncompatibleTypesError):
        get_geom_remaining_measure(geom, [other])


# Polygons


def test_remaining_polygons():
    """Test the remaining calculation with polygons."""
    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    half = Polygon([(0, 0), (0, 0.5), (1, 0.5), (1, 0), (0, 0)])
    assert get_geom_remaining_measure(geom, [half], False) == 0.5

    second = Polygon([(0, 0.5), (0, 1), (1, 1), (1, 0.5), (0, 0.5)])
    assert get_geom_remaining_measure(geom, [half, second], False) == 0


def test_remaining_polygons_projection():
    """Test the remaining calculation with polygons projections."""
    area = 1 / 2 * (4e7 / 360) ** 2
    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    half = Polygon([(0, 0), (0, 0.5), (1, 0.5), (1, 0), (0, 0)])
    assert np.isclose(get_geom_remaining_measure(geom, [half]), area, 1e-2)


def test_remaining_polygons_no_geoms():
    """Test the remaining calculation with no geometries."""
    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    assert get_geom_remaining_measure(geom, [], False) == 1


# Lines


def test_remaining_lines():
    """Test the remaining calculation with lines."""
    geom = LineString([(0, 0), (0, 1), (1, 1)])
    half = LineString([(0, 0), (0, 1)])
    assert get_geom_remaining_measure(geom, [half], False) == 1

    second = LineString([(0, 1), (1, 1)])
    assert get_geom_remaining_measure(geom, [half, second], False) == 0


def test_remaining_lines_overlap():
    """Test remaining calculation with overlapping lines."""
    geom = LineString([(0, 0), (0, 1), (1, 1)])
    half = LineString([(0, 0), (0, 1)])
    quarter = LineString([(0, 0.5), (0, 1)])
    result = get_geom_remaining_measure(geom, [half, quarter], False)
    assert result == (2 - 1) * (1.5 / 1)


def test_remaining_lines_projection():
    """Test remaining calculation with lines projections."""
    geom = LineString([(0, 0), (0, 1), (1, 1)])
    half = LineString([(0, 0), (0, 1)])
    assert np.isclose(get_geom_remaining_measure(geom, [half]), 1e5, 1e-2)


def test_remaining_lines_no_geoms():
    """Test remaining calculation with no geometries."""
    geom = LineString([(0, 0), (0, 1), (1, 1)])
    assert get_geom_remaining_measure(geom, [], False) == 2


# Points


def test_remaining_points():
    """Test the remaining calculation with points."""
    geom = MultiPoint([(0, 0), (0, 1)])
    half = Point((0, 0))
    assert get_geom_remaining_measure(geom, [half], False) == 1


def test_remaining_points_overlap():
    """Test remaining calculation with overlapping points."""
    geom = MultiPoint([(0, 0), (0, 1)])
    first = Point((0, 0))
    second = Point((0, 0))
    result = get_geom_remaining_measure(geom, [first, second], False)
    assert result == (2 - 1) * (2 / 1)


def test_remaining_points_projection():
    """Test remaining calculation with points projections."""
    geom = MultiPoint([(0, 0), (0, 1)])
    half = Point((0, 0))
    assert get_geom_remaining_measure(geom, [half]) == 1


def test_remaining_points_no_geoms():
    """Test remaining calculation with no geometries."""
    geom = MultiPoint([(0, 0), (0, 1)])
    assert get_geom_remaining_measure(geom, [], False) == 2
