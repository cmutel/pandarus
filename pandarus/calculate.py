# -*- coding: utf-8 -*-
from .conversion import check_type
from .filesystem import json_exporter, get_appdirs_path, sha256
from .maps import Map
from .matching import intersect as mp_intersect, intersection_calculation
from .geometry import get_remaining
from .projection import project
from .rasters import gen_zonal_stats
from fiona.crs import from_string
from functools import partial
from shapely.geometry import mapping, asShape
import datetime
import fiona
import multiprocessing
import json
import os
import rasterio
import warnings


WGS84 = from_string("+datum=WGS84 +ellps=WGS84 +no_defs +proj=longlat")

MISMATCHED_CRS = """Possible coordinate reference systems (CRS) mismatch. The raster statistics may be incorrect, please only use this method when both vector and raster have the same CRS.
    Vector: {}
    Raster: {}"""

CPU_COUNT = multiprocessing.cpu_count()


def get_map(fp, field, kwargs):
    obj = Map(fp, field, **kwargs)
    metadata = {
        'sha256': obj.hash,
        'filename': os.path.basename(fp),
        'field': field,
        'path': os.path.abspath(fp),
    }
    return obj, metadata


def raster_statistics(vector_fp, identifying_field, raster, output=None,
        band=1, compressed=True, fiona_kwargs={}, **kwargs):
    """Create statistics by matching ``raster`` against each spatial unit in ``self.from_map``.

    * ``raster``: str. Filepath of the raster used for calculations.
    * ``filepath``: str. Path of the results file to be created. Can be auto-generated.
    * ``band``: int. Raster band used for calculations. Default is 1.
    * ``compressed``: bool. Compress JSON results file.

    Any additional ``kwargs`` are passed to ``gen_zonal_stats``.

    """
    vector, v_metadata = get_map(vector_fp, identifying_field, fiona_kwargs)
    assert check_type(raster) == 'raster'

    with rasterio.open(raster) as r:
        raster_crs = r.crs.to_string()

    if vector.crs != raster_crs:
        warnings.warn(MISMATCHED_CRS.format(vector.crs, raster_crs))

    if not output:
        dirpath = get_appdirs_path("rasterstats")
        output = os.path.join(
            dirpath,
            "{}-{}-{}.json".format(vector.hash, sha256(raster), band)
        )

    if os.path.exists(output):
        os.remove(output)

    stats_generator = gen_zonal_stats(vector_fp, raster, band=band, **kwargs)
    mapping_dict = vector.get_fieldnames_dictionary()
    results = [(mapping_dict[index], row)
               for index, row in enumerate(stats_generator)]

    metadata = {
        'vector': v_metadata,
        'raster': {
            'sha256': sha256(raster),
            'path': raster,
            'filename': os.path.basename(raster),
            'band': band
        },
        'when': datetime.datetime.now().isoformat()
    }
    json_exporter(results, metadata, output, compressed)
    return output


def get_intersections(first, second, cpus=None):
    if cpus:
        return mp_intersect(first, second, cpus=cpus)
    else:
        return intersection_calculation(first, None, second)


def as_features(dct):
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


def intersect(first_fp, first_field, second_fp, second_field,
        first_kwargs={}, second_kwargs={}, dirpath=None, cpus=CPU_COUNT,
        driver='GeoJSON', compress=True):
    """Calculate the intersection of two vector spatial datasets.

    The first spatial input file **must** have only one type of geometry, i.e. points, lines, or polygons, and excluding geometry collections. Any of the following are allowed: Point, MultiPoint, LineString, LinearRing, MultiLineString, Polygon, MultiPolygon.

    The second spatial input file **must** have either Polygons or MultiPolygons. Although no checks are made, this and other functions make a strong assumption that the spatial units in the second spatial unit do not overlap.

    Input parameters:

        * ``first_fp``: String. File path to the first spatial dataset.
        * ``first_field``: String. Name of field that uniquely identifies features in the first spatial dataset.
        * ``second_fp``: String. File path to the second spatial dataset.
        * ``second_field``: String. Name of field that uniquely identifies features in the second spatial dataset.
        * ``first_kwargs``: Dictionary, optional. Additional arguments, such as layer name, passed to fiona when opening the first spatial dataset.
        * ``second_kwargs``: Dictionary, optional. Additional arguments, such as layer name, passed to fiona when opening the second spatial dataset.
        * ``dirpath``: String, optional. Directory to save output files.
        * ``cpus``: Integer, optional. Number of CPU cores to use when calculating. Use ``cpus=0`` to avoid starting a multiprocessing pool.
        * ``driver``: Fiona driver name to use when writing geospatial output file. Common values are ``GeoJSON`` (default) or ``GPKG``.
        * ``compress``: Boolean. Compress JSON output file; default is true.

    Returns filepaths for two created files.

    The first is a geospatial file that has the geometry of each possible intersection of spatial units from the two input files. The geometry type of this file will depend on the geometry type of the first input file, but will always be a multi geometry, i.e. one of MultiPoint, MultiLineString, MultiPolygon. This file will always have to `WGS 84 CRS <http://spatialreference.org/ref/epsg/wgs-84/>`__. The output file also has the following schema:

        * ``id``: Integer. Auto-increment field starting from zero.
        * ``from_label``: String. The value for the uniquely identifying field from the first input file.
        * ``to_label``: String. The value for the uniquely identifying field from the second input file.
        * ``measure``: Float. A measure of the intersected shape. For polygons, this is the area of the feature in square meters. For lines, this is the length in meters. For points, this is the number of points. Area and length calculations are made using the Mollweide projection.

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
    first, first_metadata = get_map(first_fp, first_field, first_kwargs)
    second, second_metadata = get_map(second_fp, second_field, second_kwargs)

    if not dirpath:
        dirpath = get_appdirs_path("intersections")

    base_filepath = os.path.join(dirpath, "{}.{}.".format(
        first.hash, second.hash
    ))

    fiona_fp = base_filepath + driver.lower()
    data_fp = base_filepath + "json"

    if os.path.exists(fiona_fp):
        os.remove(fiona_fp)
    if os.path.exists(data_fp):
        os.remove(data_fp)

    data = get_intersections(first_fp, second_fp, cpus)

    first_mapping = first.get_fieldnames_dictionary()
    second_mapping = second.get_fieldnames_dictionary()
    data = {
        (first_mapping[k[0]], second_mapping[k[1]]): v
        for k, v in data.items()
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
            for f in as_features(data):
                sink.write(f)

    data_fp = json_exporter(
        [(k[0], k[1], v['measure']) for k, v in data.items()],
        {
            'first': first_metadata,
            'second': second_metadata,
            'when': datetime.datetime.now().isoformat(),
        },
        data_fp,
        compressed=compress
    )

    return fiona_fp, data_fp


def calculate_remaining(source_fp, source_field, intersection_fp,
        source_kwargs={}, dirpath=None, compress=True):
    """Calculate the remaining area/length/number of points left out of an intersections file generated by ``intersect``."""
    source, source_metadata = get_map(source_fp, source_field, source_kwargs)
    intersections, inter_metadata = get_map(intersection_fp, 'id', {})

    assert intersections.file.schema['properties'] == {
        'id': 'int',
        'from_label': 'str',
        'to_label': 'str',
        'measure': 'float',
    }

    if not dirpath:
        dirpath = get_appdirs_path("intersections")

    output = os.path.join(dirpath, "{}.{}.json".format(source.hash, intersections.hash)
    )

    _ = partial(project, from_proj=source.crs, to_proj='')

    def get_geoms(feat):
        return [
            asShape(x['geometry'])
            for x in intersections
            if (x['properties']['from_label'] ==
                feat['properties'][source_field])
        ]

    data = [(
            feat['properties'][source_field],
            get_remaining(_(asShape(feat['geometry'])), get_geoms(feat))
        ) for feat in source
    ]

    metadata = {
        'source': source_metadata,
        'intersections': inter_metadata,
        'when': datetime.datetime.now().isoformat(),
    }

    output = json_exporter(data, metadata, output, compress)
    return output
