# -*- coding: utf-8 -*-
from functools import partial
from shapely.ops import transform
import pyproj


WGS84 = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
# See also http://spatialreference.org/ref/esri/54009/
# and http://cegis.usgs.gov/projection/pdf/nmdrs.usery.prn.pdf
MOLLWEIDE = "+proj=moll +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"


def wgs84(s):
    """Fix no CRS or fiona giving abbreviated wgs84 definition."""
    if not s:
        return WGS84
    elif s == "+no_defs":
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

    if to_proj == from_proj:
        return geom

    projection_func = partial(
        pyproj.transform,
        pyproj.Proj(from_proj),
        pyproj.Proj(to_proj)
    )
    return transform(projection_func, geom)
