"""Pandarus model classes."""
import os
from functools import partial

import fiona
import rtree
from fiona.crs import CRS
from shapely.geometry import shape

from .conversion import check_type
from .errors import DuplicateFieldIDError
from .filesystem import sha256
from .projection import project


class Map:
    """A wrapper around fiona ``open`` that provides some additional functionality.

    Requires an absolute filepath.

    Additional metadata can be provided in `kwargs`:
        * `layer` specifies the shapefile layer

    .. warning:: The Fiona field ``id`` is not used, as there are no real constraints on
    these values or values types (see `Fiona manual
    <http://toblerity.org/fiona/manual.html#record-id>`_), and real world data is often
    dirty and inconsistent. Instead, we use ``enumerate`` and integer indices.

    """

    def __init__(self, filepath, identifying_field=None, **kwargs):
        assert os.path.exists(filepath), "No file at given path"

        self.rtree_index = None
        self._index_map = None

        self.filepath = filepath
        self.fieldname = identifying_field
        self.metadata = kwargs

        assert check_type(filepath) == "vector", "Must give a vector dataset"

        with fiona.Env():
            self.file = fiona.open(self.filepath, **kwargs)

    def iter_latlong(self, indices=None):
        """Iterate over dataset as Shapely geometries in WGS 84 CRS."""
        _ = partial(project, from_proj=self.crs, to_proj="")
        if indices is None:
            for index, feature in enumerate(self):
                yield (index, _(shape(feature["geometry"])))
        else:
            for index in indices:
                yield (index, _(shape(self[index]["geometry"])))

    def create_rtree_index(self):
        """Create `rtree <http://toblerity.org/rtree/>`_ index for efficient spatial
        querying.

        **Note**: Bounds are given in lat/long, not in the native CRS"""
        self.rtree_index = rtree.Rtree()
        for index, geom in self.iter_latlong():
            self.rtree_index.add(index, geom.bounds)
        return self.rtree_index

    def get_fieldnames_dictionary(self, fieldname=None):
        """Get a dictionary of field values to indices."""
        fieldname = fieldname or self.fieldname
        assert fieldname, "No valid identifying field name"
        assert (
            fieldname in next(iter(self.file))["properties"]
        ), "Given fieldname not in file"
        fd = {
            index: obj["properties"].get(fieldname, None)
            for index, obj in enumerate(self)
        }
        if len(fd.keys()) != len(set(fd.values())):
            raise DuplicateFieldIDError("Given field name not unique for all records")
        return fd

    @property
    def geometry(self):
        """Geometry type, as defined by vector file."""
        geom = self.file.meta["schema"]["geometry"]
        if geom == "Unknown":
            geoms = {obj["geometry"]["type"] for obj in self}
            if len(geoms) == 1:
                return geoms.pop()
            return "Unknown"
        return geom

    @property
    def hash(self):
        """SHA256 hash of file."""
        return sha256(self.filepath)

    @property
    def crs(self):
        """Coordinate reference system, as defined by vector file."""
        return CRS.to_string(self.file.crs)

    def __iter__(self):
        return iter(self.file)

    def _create_index_map(self):
        self._index_map = {
            index: int(feature["id"]) for index, feature in enumerate(self)
        }

    def __getitem__(self, index):
        """Get feature from a fiona dataset.

        As Fiona is just a `simple wrapper to GDAL https://rb.gy/qb2ue2__,
        and `GDAL has no guarantees on index starting values or continuity
        <https://trac.osgeo.org/gdal/ticket/356>`__, we construct a mapping dictionary
        from what we get when we enumerate the source file to what Python expects.
        This mapping dictionary is only created the first time ``__getitem__`` is
        called. Among commonly used formats, only Geopackage starts with 1
        (geopackage[0] will just return ``None``).

        Note that our lookup dictionary breaks negative indexing."""
        if not hasattr(self, "_index_map") or self._index_map is None:
            self._create_index_map()
        return self.file[self._index_map[index]]

    def __len__(self):
        return len(self.file)
