# -*- coding: utf-8 -*-
from .conversion import check_type, convert_to_vector
from .filesystem import sha256
from fiona import crs as fiona_crs
from shapely.geometry import shape
import fiona
import rtree
import os


class DuplicateFieldID(Exception):
    """Field ID value is duplicated and should be unique"""
    pass


class Map(object):
    """A wrapper around fiona ``open`` that provides some additional functionality.

    Requires an absolute filepath.

    Additional metadata can be provided in `kwargs`:
        * `layer` specifies the shapefile layer
        * `band` specifies the raster band

    .. warning:: The Fiona field ``id`` is not used, as there are no real constraints on these values or values types (see `Fiona manual <http://toblerity.org/fiona/manual.html#record-id>`_), and real world data is often dirty and inconsistent. Instead, we use ``enumerate`` and integer indices.

    """
    def __init__(self, filepath, identifying_field, **kwargs):
        assert os.path.exists(filepath), "No file at given path"

        self.filepath = filepath
        self.fieldname = identifying_field
        self.metadata = kwargs

        kind = check_type(filepath)
        if kind == 'raster':
            self.filepath = convert_to_vector(filepath)

        with fiona.drivers():
            self.file = fiona.open(
                self.filepath,
                **kwargs
            )

    def create_rtree_index(self):
        """Create `rtree <http://toblerity.org/rtree/>`_ index for efficient spatial querying."""
        self.rtree_index = rtree.Rtree()
        for index, record in enumerate(self):
            self.rtree_index.add(
                index,
                shape(record['geometry']).bounds
            )
        return self.rtree_index

    def get_fieldnames_dictionary(self, fieldname=None):
        fieldname = fieldname or self.fieldname
        assert fieldname, "No valid identifying field name"
        assert fieldname in next(iter(self.file))['properties'], \
            "Given fieldname not in file"
        fd = {index: obj['properties'].get(fieldname, None) \
            for index, obj in enumerate(self)}
        if len(fd.keys()) != len(set(fd.values())):
            raise DuplicateFieldID(
                "Given field name not unique for all records"
            )
        return fd

    @property
    def geometry(self):
        geom = self.file.meta['schema']['geometry']
        if geom == 'Unknown':
            geoms = {obj['geometry']['type'] for obj in self}
            if len(geoms) == 1:
                return geoms.pop()
            else:
                return 'Unknown'
        return geom

    @property
    def hash(self):
        return sha256(self.filepath)

    @property
    def crs(self):
        """Coordinate reference system, as defined by vector file."""
        return fiona_crs.to_string(self.file.crs)

    def __iter__(self):
        return iter(self.file)

    def _create_index_map(self):
        self._index_map = {index: int(feature['id']) for index, feature in enumerate(self)}

    def __getitem__(self, index):
        """Get feature from a fiona dataset.

        As Fiona is just a `simple wrapper to GDAL <https://github.com/Toblerity/Fiona/blob/0af2eac3fdee25d9660e4d90dcf97513cb4a15b4/fiona/ogrext2.pyx#L715>`__, and `GDAL has no guarantees on index starting values or continuity <https://trac.osgeo.org/gdal/ticket/356>`__, we construct a mapping dictionary from what we get when we enumerate the source file to what Python expects. This mapping dictionary is only created the first time ``__getitem__`` is called. Among commonly used formats, only Geopackage starts with 1 (geopackage[0] will just return ``None``).

        Note that our lookup dictionary breaks negative indexing."""
        if not hasattr(self, "_index_map"):
            self._create_index_map()
        return self.file[self._index_map[index]]

    def __len__(self):
        return len(self.file)
