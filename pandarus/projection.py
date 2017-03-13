# -*- coding: utf-8 -*-
from functools import partial
from shapely.ops import transform
import pyproj


WGS84 = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
# See also http://spatialreference.org/ref/esri/54009/
# and http://cegis.usgs.gov/projection/pdf/nmdrs.usery.prn.pdf
MOLLWEIDE = "+proj=moll +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"


def wgs84(s):
    """Fix no CRS or fiona giving abbreviated wgs84 definition.

    Returns WGS84 if ``s`` is falsey."""
    if s == "+no_defs" or not s:
        return WGS84
    else:
        return s


def project(geom, from_proj=None, to_proj=None):
    """
Project a ``shapely`` geometry, and returns a new geometry of the same type from the transformed coordinates.

Default input projection is `WGS84 <https://en.wikipedia.org/wiki/World_Geodetic_System>`_, default output projection is `Mollweide <http://spatialreference.org/ref/esri/54009/>`_.

Inputs:
    *geom*: A ``shapely`` geometry.
    *from_proj*: A ``PROJ4`` string. Optional.
    *to_proj*: A ``PROJ4`` string. Optional.

Returns:
    A ``shapely`` geometry.

    """
    from_proj = wgs84(from_proj)
    if to_proj is None:
        to_proj = MOLLWEIDE
    else:
        to_proj = wgs84(to_proj)

    to_proj, from_proj = pyproj.Proj(to_proj), pyproj.Proj(from_proj)

    if ((to_proj == from_proj) or
            (to_proj.is_latlong() and from_proj.is_latlong())):
        return geom

    projection_func = partial(pyproj.transform, from_proj, to_proj)
    return transform(projection_func, geom)
