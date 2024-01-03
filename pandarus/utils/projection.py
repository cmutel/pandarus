"""Project utilities for Pandarus."""
from pyproj import Proj, Transformer
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

WGS84 = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
# See also http://spatialreference.org/ref/esri/54009/
# and http://cegis.usgs.gov/projection/pdf/nmdrs.usery.prn.pdf
MOLLWEIDE = (
    "+proj=moll +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
)


def wgs84(crs: str):
    """Fix no CRS or fiona giving abbreviated wgs84 definition.
    Returns WGS84 if ``s`` is falsey."""

    if not crs or crs == "+no_defs":
        return WGS84
    return crs


def project_geom(geom: BaseGeometry, from_proj: str = None, to_proj: str = None):
    """
    Project a ``shapely`` geometry, and returns a new geometry of the same type from the
    transformed coordinates.

    Default input projection is `WGS84
    <https://en.wikipedia.org/wiki/World_Geodetic_System>`_, default output projection
    is `Mollweide <http://spatialreference.org/ref/esri/54009/>`_.

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

    to_pyproj, from_pyproj = Proj(to_proj), Proj(from_proj)

    if (to_pyproj == from_pyproj) or (
        to_pyproj.crs.is_geographic and from_pyproj.crs.is_geographic
    ):
        return geom

    transformer = Transformer.from_proj(from_pyproj, to_pyproj)
    return transform(transformer.transform, geom)
