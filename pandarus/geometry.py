from shapely.geometry import (
    GeometryCollection,
    LinearRing,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
    shape,
)
from shapely.ops import cascaded_union


def normalize_dictionary_values(dct, total=1):
    """In a dictionary ``dct`` with numeric values, normalize these values to sum to ``total``.

    Returns a dictionary."""
    n = total / (sum(v['measure'] for v in dct.values()) or 1)
    for v in dct.values():
        v['measure'] *= n
    return dct


def clean(geom):
    """Clean invalid geometries using buffer trick.

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
                     projection_func=None,
                     return_geoms=True):
    """Return a dictionary describing the intersection of ``obj`` with ``collection[indices]``.

    ``obj`` is a Shapely geometry.
    ``kind`` is one of ``("line", "point", "polygon")`` - the kind of object to be returned.
    ``collection`` is a Fiona datasource.
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

    if projection_func is None:
        projection_func = lambda x: x

    obj = clean(obj)

    results = {
        index: {
            'geom': recursive_geom_finder(
                clean(obj.intersection(shape(collection[index]['geometry']))),
                kind
            )
        } for index in indices
        if collection[index]
        and shape(collection[index]['geometry']).intersects(obj)
    }

    results = {k: v for k, v in results.items() if v['geom']}

    for v in results.values():
        v['measure'] = get_measure(projection_func(v['geom']), kind)

    results = normalize_dictionary_values(results)
    if not return_geoms:
        for v in results.values():
            del v['geom']

    return results


def get_measure(geom, kind):
    """Get area, length, or number of points, depending on ``geom`` type"""
    if kind == 'line':
        return geom.length
    elif kind == 'polygon':
        return geom.area
    else:
        return len(geom)


def get_remaining(original, kind, geoms, projection=None):
    """Get the remaining area/length/number from ``original`` after subtracting the union of ``geoms``.

    Returns a float."""
    if projection is None or kind == 'point':
        projection = lambda x: x
    actual = get_measure(projection(original), kind)
    union_total = get_measure(projection(cascaded_union(geoms)), kind)
    individ_total = sum(get_measure(projection(geom), kind) for geom in geoms)
    return (actual - union_total) * (individ_total / union_total)
