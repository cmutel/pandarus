"""Geometry utilities for Pandarus."""
from typing import Any, Dict, Iterator, List, Optional

from shapely.geometry import (
    GeometryCollection,
    LinearRing,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from ..errors import IncompatibleTypesError
from ..model import Map
from .projection import project_geom


def clean_geom(geom: BaseGeometry) -> BaseGeometry:
    """Clean invalid geometries using ``buffer(0)`` trick.

    ``geom`` is a shapely geometry; returns a shapely geometry."""
    if not geom.is_valid:
        geom = geom.buffer(0)
    return geom if geom.is_valid else GeometryCollection([])


def recursive_geom_finder(geom: BaseGeometry, kind: str) -> Optional[BaseGeometry]:
    """Return all elements of ``geom`` that are of ``kind``. For example, return all
    linestrings in a geometry collection.

    ``geom`` is a Shapely geometry.

    ``kind`` should be one of ``("line", "point", "polygon")``.

    Returns either a ``MultiPoint``, ``MultiLineString``, or ``MultiPolygon``. Returns
    ``None`` is no valid element is found."""
    if kind not in ("line", "point", "polygon"):
        raise ValueError(f"Invalid kind: {kind}.")

    tpyes_map = {
        "line": (LineString, LinearRing, MultiLineString),
        "point": (Point, MultiPoint),
        "polygon": (Polygon, MultiPolygon),
    }
    container_map = {
        "line": MultiLineString,
        "point": MultiPoint,
        "polygon": MultiPolygon,
    }

    def recurse(geom, types) -> Iterator[BaseGeometry]:
        if isinstance(geom, types):
            yield geom
        if isinstance(geom, GeometryCollection):
            for elem in geom.geoms:
                for val in recurse(elem, types):
                    yield val
        yield None

    elements = [elem for elem in recurse(geom, tpyes_map[kind]) if elem is not None]
    if not elements:
        return None

    geom = clean_geom(unary_union(elements))
    if "Multi" not in geom.geom_type:
        geom = container_map[kind]([geom])
    return geom


def get_intersection(
    obj: BaseGeometry,
    kind: str,
    collection: Map,
    indices: Iterator[int],
    to_meters: bool = True,
    return_geoms: bool = True,
) -> Dict[int, Dict[str, Any]]:
    """Return a dictionary describing the intersection of ``obj`` with
    ``collection[indices]``.

    ``obj`` is a Shapely geometry.
    ``kind`` is one of ``("line", "point", "polygon")`` - the kind of object to be
    returned.
    ``collection`` is a ``Map``.
    ``indices`` is an iterator of integers; indices into ``collection``.
    ``to_meters`` a boolean that determines if resulting groms should be projected
    to meters.
    ``return_geoms``: Return intersected geometries in addition to area, etc.

    Assumes that the polygons in ``collection`` do not overlap.

    Returns a dictionary of form:

    .. code-block:: python

        {
            collection_index: {
                'measure': measure of are or length,
                'geom': intersected geometry # if return_geoms
            }
        }

    The algorithm used for line and point intersections is incorrect - it will double
    count lines which lay along the borders of two polygons, and point that lie on the
    border of two polygons. A more robust function would take substantially more
    development and computation time, and total error should be less than 10 percent.

    """
    if kind not in ("line", "point", "polygon"):
        raise ValueError(f"Invalid kind: {kind}.")

    proj_func = project_geom if to_meters else lambda x: x
    obj = clean_geom(obj)

    results: Dict[int, Dict[str, Any]] = {}

    for index, geom in collection.iter_latlong(indices):
        if not geom.intersects(obj):
            continue
        g = recursive_geom_finder(clean_geom(obj.intersection(geom)), kind)
        if not g:
            continue
        results[index] = {"measure": get_geom_measure(proj_func(g))}
        if return_geoms:
            results[index]["geom"] = g

    return results


def get_geom_kind(geom: BaseGeometry) -> str:
    """Get the kind of geometry (polygon, line, or point)."""
    kind_mapping = {
        "Polygon": "polygon",
        "MultiPolygon": "polygon",
        "LineString": "line",
        "MultiLineString": "line",
        "LinearRing": "line",
        "Point": "point",
        "MultiPoint": "point",
    }

    return kind_mapping[geom.geom_type]


def get_geom_measure(geom: BaseGeometry, kind: Optional[str] = None) -> float:
    """Get area, length, or number of points in ``geom``.

    * ``geom``: A shapely geom.
    * ``kind``: Geometry type, optional. One of `polygon`, `line`, or `point`.

    Kind will be guessed based on type of ``geom`` if not otherwise provided.

    If ``kind`` is not one of the allowed types, raises ``ValueError``.

    Returns a float."""

    if kind is None:
        kind = get_geom_kind(geom)

    if kind == "polygon":
        return geom.area
    if kind == "line":
        return geom.length
    if kind == "point":
        if geom.geom_type == "MultiPoint":
            return float(len(geom.geoms))
        if geom.geom_type == "Point":
            return 1.0

    raise ValueError(f"No applicable measure for geom of kind {kind}")


def get_geom_remaining_measure(
    original: BaseGeometry,
    geoms: List[BaseGeometry],
    to_meters: bool = True,
) -> float:
    """Get the remaining area/length/number from ``original`` after subtracting
    the union of ``geoms``.

    * ``original``: Shapely geom in WGS84 CRS.
    * ``geoms``: List of shapely geoms in WGS84 CRS.
    * ``to_meters``: Boolean. Return value calculated in Mollweide projection.

    ``original`` and ``geoms`` should have the same geometry type, and ``geoms`` are
    components of ``original``.

    Returns a float."""
    try:
        kind = get_geom_kind(original)
    except KeyError as exc:
        raise ValueError(f"Can't use this geometry type: {original.geom_type}") from exc

    proj_func = project_geom if to_meters and kind != "point" else lambda x: x

    if geoms and {get_geom_kind(g) for g in geoms} != {kind}:
        raise IncompatibleTypesError

    actual = get_geom_measure(proj_func(original))
    if geoms:
        union_total = get_geom_measure(proj_func(unary_union(geoms)), kind)
        individ_total = sum(get_geom_measure(proj_func(geom), kind) for geom in geoms)
        return (actual - union_total) * (individ_total / union_total)
    return actual
