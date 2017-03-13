from .projection import project
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
from shapely.ops import cascaded_union


kind_mapping = {
    'Polygon': 'polygon',
    'MultiPolygon': 'polygon',
    'LineString': 'line',
    'MultiLineString': 'line',
    'LinearRing': 'line',
    'Point': 'point',
    'MultiPoint': 'point',
}


class IncompatibleTypes(Exception):
    """Geometry comparison across geometry types is meaningless"""
    pass


def clean(geom):
    """Clean invalid geometries using ``buffer(0)`` trick.

    ``geom`` is a shapely geometry; returns a shapely geometry."""
    if not geom.is_valid:
        geom = geom.buffer(0)
    return geom if geom.is_valid else GeometryCollection([])


def recursive_geom_finder(geom, kind):
    """Return all elements of ``geom`` that are of ``kind``. For example, return all linestrings in a geometry collection.

    ``geom`` is a Shapely geometry.

    ``kind`` should be one of ``("line", "point", "polygon")``.

    Returns either a ``MultiPoint``, ``MultiLineString``, or ``MultiPolygon``. Returns ``None`` is no valid element is found."""
    assert kind in ("line", "point", "polygon"), "Invalid ``kind``"

    TYPES = {
        'line': (LineString, LinearRing, MultiLineString),
        'point': (Point, MultiPoint),
        'polygon': (Polygon, MultiPolygon),
    }
    CONTAINER = {
        'line': MultiLineString,
        'point': MultiPoint,
        'polygon': MultiPolygon,
    }

    def recurse(geom, types):
        if isinstance(geom, types):
            yield geom
        elif isinstance(geom, GeometryCollection):
            for elem in geom:
                for val in recurse(elem, types):
                    yield val
        else:
            yield None

    elements = [elem for elem in recurse(geom, TYPES[kind])
                if elem is not None]
    if not elements:
        return None
    else:
        geom = clean(cascaded_union(elements))
        if 'Multi' not in geom.type:
            geom = CONTAINER[kind]([geom])
        return geom


def get_intersection(obj, kind, collection, indices,
                     to_meters=True,
                     return_geoms=True):
    """Return a dictionary describing the intersection of ``obj`` with ``collection[indices]``.

    ``obj`` is a Shapely geometry.
    ``kind`` is one of ``("line", "point", "polygon")`` - the kind of object to be returned.
    ``collection`` is a ``Map``.
    ``indices`` is an iterator of integers; indices into ``collection``.
    ``projection_func`` is a function to project the results to a new CRS before taking area, etc. If falsey, no projection will take place.
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

    The algorithm used for line and point intersections is incorrect - it will double count lines which lay along the borders of two polygons, and point that lie on the border of two polygons. A more robust function would take substantially more development and computation time, and total error should be less than 10 percent.

    """
    assert kind in ("line", "point", "polygon"), "Invalid ``kind``"

    proj_func = project if to_meters else lambda x: x
    obj = clean(obj)

    results = {}

    for index, geom in collection.iter_latlong(indices):
        if not geom.intersects(obj):
            continue
        g = recursive_geom_finder(
            clean(obj.intersection(geom)),
            kind
        )
        if not g:
            continue
        results[index] = {'measure': get_measure(proj_func(g), kind)}
        if return_geoms:
            results[index]['geom'] = g

    return results


def get_measure(geom, kind=None):
    """Get area, length, or number of points in ``geom``.

    * ``geom``: A shapely geom.
    * ``kind``: Geometry type, optional. One of `polygon`, `line`, or `point`.

    Kind will be guessed based on type of ``geom`` if not otherwise provided.

    If ``kind`` is not one of the allowed types, raises ``ValueError``.

    Returns a float."""
    if kind is None:
        kind = kind_mapping.get(geom.geom_type)

    if kind == 'polygon':
        return geom.area
    elif kind == 'line':
        return geom.length
    elif kind == 'point':
        if geom.geom_type == 'MultiPoint':
            return float(len(geom))
        elif geom.geom_type == 'Point':
            return 1.
    raise ValueError(
        "No applicable measure for geom: {}".format(geom)
    )


def get_remaining(original, geoms, to_meters=True):
    """Get the remaining area/length/number from ``original`` after subtracting the union of ``geoms``.

    * ``original``: Shapely geom in WGS84 CRS.
    * ``geoms``: List of shapely geoms in WGS84 CRS.
    * ``to_meters``: Boolean. Return value calculated in Mollweide projection.

    ``original`` and ``geoms`` should have the same geometry type, and ``geoms`` are components of ``original``.

    Returns a float."""
    try:
        kind = kind_mapping[original.geom_type]
    except KeyError:
        raise ValueError(
            "Can't use this geometry type: {}".format(original.geom_type)
        )

    if not to_meters or kind == 'point':
        proj_func = lambda x: x
    else:
        proj_func = project

    if geoms and {kind_mapping[g.geom_type] for g in geoms} != {kind}:
        raise IncompatibleTypes

    actual = get_measure(proj_func(original))
    if geoms:
        union_total = get_measure(proj_func(cascaded_union(geoms)), kind)
        individ_total = sum(get_measure(proj_func(geom), kind) for geom in geoms)
        return (actual - union_total) * (individ_total / union_total)
    else:
        return actual
