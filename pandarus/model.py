"""Pandarus model classes."""
import os
from functools import partial
from typing import Any, Dict, Generator, Iterable, Optional, Tuple

import fiona
import rtree
from fiona.crs import CRS
from shapely.geometry import shape

from .errors import DuplicateFieldIDError
from .utils.conversion import check_dataset_type
from .utils.io import sha256_file
from .utils.projection import project_geom


class Map:
    """A wrapper around fiona ``open`` that provides some additional functionality.

    Requires an absolute file_path.

    Additional metadata can be provided in `kwargs`:
        * `layer` specifies the shapefile layer

    .. warning:: The Fiona field ``id`` is not used, as there are no real constraints on
    these values or values types (see `Fiona manual
    <http://toblerity.org/fiona/manual.html#record-id>`_), and real world data is often
    dirty and inconsistent. Instead, we use ``enumerate`` and integer indices.

    """

    def __init__(
        self,
        file_path: str,
        identifying_field: Optional[str] = None,
        **kwargs: Dict[str, Any],
    ) -> None:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} does not exist")

        self.rtree_index = None
        self._index_map = None

        self.file_path = file_path
        self.field_name = identifying_field
        self.metadata = kwargs

        if check_dataset_type(file_path) != "vector":
            raise ValueError("File is not a vector dataset")

        with fiona.Env():
            self.file = fiona.open(self.file_path, **kwargs)

    def __len__(self) -> int:
        return len(self.file)

    def __iter__(self) -> fiona.Collection:
        return iter(self.file)

    def __getitem__(self, index: int) -> fiona.Collection:
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
            self._index_map = {
                index: int(feature["id"]) for index, feature in enumerate(self)
            }
        return self.file[self._index_map[index]]

    @property
    def geom_type(self) -> str:
        """Geometry type, as defined by vector file."""
        geom = self.file.meta["schema"]["geometry"]
        if geom == "Unknown":
            geoms = {obj["geometry"]["type"] for obj in self}
            if len(geoms) == 1:
                return geoms.pop()
            return "Unknown"
        return geom

    @property
    def hash(self) -> str:
        """SHA256 hash of file."""
        return sha256_file(self.file_path)

    @property
    def crs(self) -> str:
        """Coordinate reference system, as defined by vector file."""
        return CRS.to_string(self.file.crs)

    @staticmethod
    def get_map_with_metadata(
        file_path: str, identifying_field: str, **kwargs: Dict[str, Any]
    ) -> Tuple["Map", Dict[str, Any]]:
        """Create a ``Map`` object and return it with metadata."""
        obj = Map(file_path, identifying_field, **kwargs)
        metadata = {
            "sha256": obj.hash,
            "filename": os.path.basename(file_path),
            "field": identifying_field,
            "path": os.path.abspath(file_path),
        }
        return obj, metadata

    def get_label(self, field_name: str) -> str:
        """Get the label for a given field name."""
        return self.file.meta["schema"]["properties"][field_name]

    def get_fieldnames_dictionary(
        self, field_name: Optional[str] = None
    ) -> Dict[int, str]:
        """Get a dictionary of field values to indices."""
        field_name = field_name or self.field_name
        if field_name is None:
            raise ValueError("No valid identifying field name.")

        if field_name not in next(iter(self.file))["properties"]:
            raise ValueError(f"Given field_name: {field_name} is not in file.")

        fd = {
            index: obj["properties"].get(field_name, None)
            for index, obj in enumerate(self)
        }
        if len(fd.keys()) != len(set(fd.values())):
            raise DuplicateFieldIDError("Given field name not unique for all records")
        return fd

    def iter_latlong(
        self, indices: Optional[Iterable[int]] = None
    ) -> Generator[Tuple[int, Any], None, None]:
        """Iterate over dataset as Shapely geometries in WGS 84 CRS."""
        proj_geom = partial(project_geom, from_proj=self.crs, to_proj="")
        if indices is None:
            for index, feature in enumerate(self):
                yield (index, proj_geom(shape(feature["geometry"])))
        else:
            for index in indices:
                yield (index, proj_geom(shape(self[index]["geometry"])))

    def create_rtree_index(self) -> rtree.index.Index:
        """Create `rtree <http://toblerity.org/rtree/>`_ index for efficient spatial
        querying.

        **Note**: Bounds are given in lat/long, not in the native CRS"""
        self.rtree_index = rtree.Rtree()
        for index, geom in self.iter_latlong():
            self.rtree_index.add(index, geom.bounds)
        return self.rtree_index
