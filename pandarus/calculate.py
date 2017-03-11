# -*- coding: utf-8 -*-
from .conversion import check_type
from .filesystem import json_exporter, get_appdirs_path, sha256
from .maps import Map
from .matching import MatchMaker, areal_calculation, intersection_calculation
from .rasters import gen_zonal_stats
from fiona.crs import from_string
from shapely.geometry import mapping
import datetime
import fiona
import json
import os
import rasterio
import warnings


WGS84 = from_string("+datum=WGS84 +ellps=WGS84 +no_defs +proj=longlat")

MISMATCHED_CRS = """Possible coordinate reference systems (CRS) mismatch. The raster statistics may be incorrect, please only use this method when both vector and raster have the same CRS.
    Vector: {}
    Raster: {}"""

class Pandarus(object):
    """An object that manages most Pandarus capabilities.

    A ``Pandarus`` class instance is initiated with a vector dataset filepath, and optionally a second vector dataset filepath. For both vector datasets, additional metadata should be provided - at a minimum, you should specify the field name (called ``field``) that uniquely identifies each feature in each dataset. Other metadata, such as a layer name, can also be provided.

    After class instantiation, you can call methods that interact with one or both of the provided vector datasets.

    To instantiate a ``Pandarus`` class with a GeoJSON dataset saved at filepath ``foo.geojson``, with a field named ``bar`` that is unique for each feature, do the following:

    ..code-block:: python

        Pandarus("foo.geojson", from_metadata={"field": "bar"})

    If you wanted to also include a second file, e.g. ``iowa.geojson``, with a unique field named ``county``:

    ..code-block:: python

        Pandarus("foo.geojson", "iowa.geojson", from_metadata={"field": "bar"}, to_metadata={"field": "county"})

    """
    def __init__(self, from_filepath, to_filepath=None,
            from_metadata={}, to_metadata={}):
        self.data = None
        self.from_filepath = from_filepath
        self.from_map = Map(from_filepath, **from_metadata)
        self.metadata = {'first': {
            'sha256': self.from_map.hash,
            'filename': os.path.basename(from_filepath),
            'path': os.path.abspath(from_filepath),
        }}
        self.metadata['first'].update(from_metadata)
        if to_filepath is not None:
            self.to_map = Map(to_filepath, **to_metadata)
            self.metadata['second'] = {
                'sha256': self.to_map.hash,
                'filename': os.path.basename(to_filepath),
                'path': os.path.abspath(to_filepath)
            }
            self.metadata['second'].update(to_metadata)

    def rasterstats(self, raster, filepath=None, band=1, compressed=True, **kwargs):
        """Create statistics by matching ``raster`` against each spatial unit in ``self.from_map``.

        * ``raster``: str. Filepath of the raster used for calculations.
        * ``filepath``: str. Path of the results file to be created. Can be auto-generated.
        * ``band``: int. Raster band used for calculations. Default is 1.
        * ``compressed``: bool. Compress JSON results file.

        Any additional ``kwargs`` are passed to ``gen_zonal_stats``.

        """
        assert check_type(raster) == 'raster'

        with rasterio.open(raster) as r:
            raster_crs = r.crs.to_string()

        if self.from_map.crs != raster_crs:
            warnings.warn(MISMATCHED_CRS.format(self.from_map.crs, raster_crs))

        if not filepath:
            dirpath = get_appdirs_path("rasterstats")
            filepath = os.path.join(
                dirpath,
                "{}-{}-{}.json".format(self.from_map.hash, sha256(raster), band)
            )

        if os.path.exists(filepath):
            os.remove(filepath)

        stats_generator = gen_zonal_stats(self.from_filepath, raster, band=band, **kwargs)
        mapping_dict = self.from_map.get_fieldnames_dictionary(None)
        results = [(mapping_dict[index], row)
                   for index, row in enumerate(stats_generator)]

        metadata = {
            'vector': self.metadata['first'],
            'raster': {
                'sha256': sha256(raster),
                'filepath': raster,
                'band': band
            },
            'timestep': datetime.datetime.now().isoformat()
        }
        json_exporter(results, metadata, filepath, compressed)
        return filepath

    def intersections(self, cpus=None, to_meters=True):
        if cpus:
            self.data = MatchMaker.intersect(
                self.from_map.filepath,
                self.to_map.filepath,
                cpus=cpus,
            )
        else:
            self.data = intersection_calculation(
                self.from_map.filepath,
                None,
                self.to_map.filepath,
                1,
                to_meters=to_meters,
            )
        return self.data

    def as_features(self, dct):
        for index, key in enumerate(dct):
            row = dct[key]
            gj = {
                'geometry': mapping(row['geom']),
                'properties': {
                    'id': index,
                    'from_label': key[0],
                    'to_label': key[1],
                    'measure': row['measure']},
            }
            yield gj

    def intersect(self, dirpath=None, cpus=None, driver='GeoJSON', compress=True):
        """Calculate the intersection of two vector spatial datasets.

        The first spatial input file (``from_filepath``) **must** have only one type of geometries, excluding geometry collections. Any of the following are allowed: Point, MultiPoint, LineString, LinearRing, MultiLineString, Polygon, MultiPolygon.

        The second spatial input file (``to_filepath``) **must** have either Polygons or MultiPolygons.

        Input parameters:

            * ``dirpath``: Optional. Directory to save output files.
            * ``cpus``: Integer, optional. Number of CPU cores to use when calculating.
            * ``driver``: Fiona driver name to use when writing geospatial output file. Common values are ``GeoJSON`` (default) or ``GPKG``.
            * ``compress``: Boolean. Compress JSON output file; default is true.

        Returns filepaths for two created files.

        The first is a geospatial file that has the geometry of each possible intersection of spatial units from the two input files. The geometry of this file will depend on the geometry of the first input file, but will always be a multi geometry, i.e. one of MultiPoint, MultiLineString, MultiPolygon. This output file has the following schema:

            * ``id``: Integer. Auto-increment field starting from zero.
            * ``from_label``: String. The value for the uniquely identifying field from the first input file.
            * ``to_label``: String. The value for the uniquely identifying field from the second input file.
            * ``measure``: Float. A measure of the intersected shape. For polygons, this is the area of the feature in square meters. For lines, this is the length in meters. For points, this is the number of points.

        The second file is an extract of some of the feature fields in JSON. This is used by programs that don't want to depend on GIS data reader libraries. The JSON data format is:

        .. code-block:: python

            {
                'metadata': {
                    'first': {
                        'field': 'name of uniquely identifying field',
                        'path': 'path to first input file',
                        'filename': 'name of first input file',
                        'sha256': 'sha256 hash of input file'
                    },
                    'second': {
                        'field': 'name of uniquely identifying field',
                        'path': 'path to second input file',
                        'filename': 'name of second input file',
                        'sha256': 'sha256 hash of input file'
                    }
                },
                'data': [
                    [
                        'identifying field for first file',
                        'identifying field for second file',
                        'measure value'
                    ]
                ]
            }

        """
        if not hasattr(self, 'to_map'):
            raise ValueError("Need ``to_map`` for intersection")
        if not dirpath:
            dirpath = get_appdirs_path("intersections")

        base_filepath = os.path.join(dirpath, "{}.{}.".format(
            *sorted([self.from_map.hash, self.to_map.hash]))
        )

        fiona_fp = base_filepath + driver.lower()
        data_fp = base_filepath + "json"

        if os.path.exists(fiona_fp):
            os.remove(fiona_fp)
        if os.path.exists(data_fp):
            os.remove(data_fp)

        self.intersections(cpus)

        from_mapping = self.from_map.get_fieldnames_dictionary(None)
        to_mapping = self.to_map.get_fieldnames_dictionary(None)
        self.data = {
            (from_mapping[k[0]], to_mapping[k[1]]): v
            for k, v in self.data.items()
        }

        schema = {
            'properties': {
                'id': 'int',
                'from_label': 'str',
                'to_label': 'str',
                'measure': 'float',
            },
            'geometry': 'MultiPolygon',
        }

        with fiona.drivers():
            with fiona.open(
                    fiona_fp, 'w',
                    crs=WGS84,
                    driver=driver,
                    schema=schema,
                ) as sink:
                for f in self.as_features(self.data):
                    sink.write(f)

        json_exporter(
            [(k[0], k[1], v['measure']) for k, v in self.data.items()],
            self.metadata,
            data_fp,
            compressed=compress
        )

        return fiona_fp, data_fp

    def calculate_areas(self, cpus=None):
        if cpus:
            self.data = MatchMaker.areas(
                self.from_map.filepath,
                None,
                cpus=cpus,
            )
        else:
            self.data = areal_calculation(
                self.from_map.filepath, None, 1
            )
        return self.data

    def areas(self, dirpath=None, cpus=None, compress=True):
        if not dirpath:
            dirpath = get_appdirs_path("areas")

        filepath = os.path.join(dirpath, self.from_map.hash + ".json")

        if os.path.exists(filepath):
            os.remove(filepath)

        self.calculate_areas(cpus)

        json_exporter(
            [(k[0], k[1], v['measure']) for k, v in self.data.items()],
            self.metadata,
            data_fp,
            compressed=compress
        )

        mapping_dict = self.from_map.get_fieldnames_dictionary(fieldname)
        json_exporter(
            [(mapping_dict[k], v) for k, v in self.data.items()],
            self.metadata['first'],
            filepath,
            compressed=compress
        )
