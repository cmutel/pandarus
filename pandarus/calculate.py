# -*- coding: utf-8 -*-
from .conversion import check_type
from .filesystem import json_exporter, get_appdirs_path, sha256, json_importer
from .maps import Map
from .intersections import intersection_dispatcher
from .geometry import get_remaining
from .projection import project
from .rasters import gen_zonal_stats
from fiona.crs import from_string
from functools import partial
from shapely.geometry import mapping, shape
import datetime
import fiona
import multiprocessing
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
        band=1, compress=True, fiona_kwargs={}, **kwargs):
    """Create statistics by matching ``raster`` against each spatial unit in ``self.from_map``.

    * ``raster``: str. Filepath of the raster used for calculations.
    * ``filepath``: str. Path of the results file to be created. Can be auto-generated.
    * ``band``: int. Raster band used for calculations. Default is 1.
    * ``compress``: bool. Compress JSON results file.

    Any additional ``kwargs`` are passed to ``gen_zonal_stats``.

    """
    vector, v_metadata = get_map(vector_fp, identifying_field, fiona_kwargs)
    assert check_type(raster) == 'raster'

    with rasterio.open(raster) as r:
        raster_crs = r.crs.to_string()
        meta = r.meta

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

    pcw = meta['height'] < 5000 and meta['width'] < 10000

    stats_generator = gen_zonal_stats(vector_fp, raster, band=band, percent_cover_weighting=pcw, **kwargs)
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
    return json_exporter({'data': results, 'metadata': metadata}, output, compress)


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
        driver='GeoJSON', compress=True, log_dir=None):
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
        * ``cpus``: Integer, default is ``multiprocessing.cpu_count()``. Number of CPU cores to use when calculating. Use ``cpus=0`` to avoid starting a multiprocessing pool.
        * ``driver``: String, default is ``GeoJSON``. Fiona driver name to use when writing geospatial output file. Common values are ``GeoJSON`` or ``GPKG``.
        * ``compress``: Boolean, default is True. Compress JSON output file.
        * ``log_dir``: String, optional.

    Returns filepaths for two created files.

    The first is a geospatial file that has the geometry of each possible intersection of spatial units from the two input files. The geometry type of this file will depend on the geometry type of the first input file, but will always be a multi geometry, i.e. one of MultiPoint, MultiLineString, MultiPolygon. This file will also always have the `WGS 84 CRS <http://spatialreference.org/ref/epsg/wgs-84/>`__. The output file has the following schema:

        * ``id``: Integer. Auto-increment field starting from zero.
        * ``from_label``: String. The value for the uniquely identifying field from the first input file.
        * ``to_label``: String. The value for the uniquely identifying field from the second input file.
        * ``measure``: Float. A measure of the intersected shape. For polygons, this is the area of the feature in square meters. For lines, this is the length in meters. For points, this is the number of points. Area and length calculations are made using the `Mollweide projection <https://en.wikipedia.org/wiki/Mollweide_projection>`__.

    The second file is an extract of some of the feature fields in the JSON data format. This is used by programs that don't need to depend on GIS data libraries. The JSON format is:

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
                },
                'when': 'datetime this calculation finished, ISO format'
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

    data = intersection_dispatcher(first_fp, second_fp, cpus=cpus, log_dir=log_dir)

    first_mapping = first.get_fieldnames_dictionary()
    second_mapping = second.get_fieldnames_dictionary()
    data = {
        (first_mapping[k[0]], second_mapping[k[1]]): v
        for k, v in data.items()
    }

    schema = {
        'properties': {
            'id': 'int',
            'from_label': first.file.meta['schema']['properties'][first_field],
            'to_label': second.file.meta['schema']['properties'][second_field],
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
        {
            'data': [(k[0], k[1], v['measure']) for k, v in data.items()],
            'metadata':
                {
                    'first': first_metadata,
                    'second': second_metadata,
                    'when': datetime.datetime.now().isoformat(),
                }
        },
        data_fp,
        compress=compress
    )

    return fiona_fp, data_fp


def calculate_remaining(source_fp, source_field, intersection_fp,
        source_kwargs={}, dirpath=None, compress=True):
    """Calculate the remaining area/length/number of points left out of an intersections file generated by ``intersect``.

    Input parameters:

        * ``source_fp``: String. Filepath of the input spatial data which could have features outside of the intersection result.
        * ``source_field``: String. Name of field that uniquely identifies features in the input spatial dataset.
        * ``intersection_fp``: Filepath of the intersection spatial dataset generated by the ``intersect`` function.
        * ``source_kwargs``: Dictionary, optional. Additional arguments, such as layer name, passed to fiona when opening the input spatial dataset.
        * ``dirpath``: String, optional. Directory where the output file will be saved.
        * ``compress``: Boolean. Whether or not to compress the output file.

    .. warning:: ``source_fp`` must be the first file provided to the ``intersect`` function, **not** the second!

    Returns the filepath of the output file. The output file JSON format is:

    .. code-block:: python

        {
            'metadata': {
                'source': {
                    'field': 'name of uniquely identifying field',
                    'path': 'path to the input file',
                    'filename': 'name of the input file',
                    'sha256': 'sha256 hash of the input file'
                },
                'intersections': {
                    'field': 'name of uniquely identifying field (always `id`)',
                    'path': 'path to intersections spatial dataset',
                    'filename': 'name of intersections spatial dataset',
                    'sha256': 'sha256 hash of intersection spatial dataset'
                }
                'when': 'datetime this calculation finished, ISO format'
            },
            'data': [
                [
                    'identifying field for source file',
                    'measure value'
                ]
            ]
        }

    """
    source, source_metadata = get_map(source_fp, source_field, source_kwargs)
    intersections, inter_metadata = get_map(intersection_fp, 'id', {})

    assert intersections.file.schema['properties'].keys() == \
        {'id', 'from_label', 'to_label', 'measure'}
    assert intersections.file.schema['properties']['id'] == 'int'
    assert intersections.file.schema['properties']['measure'] == 'float'

    if not dirpath:
        dirpath = get_appdirs_path("intersections")

    output = os.path.join(dirpath, "{}.{}.json".format(source.hash, intersections.hash)
    )

    _ = partial(project, from_proj=source.crs, to_proj='')

    def get_geoms(feat):
        return [
            shape(x['geometry'])
            for x in intersections
            if (x['properties']['from_label'] ==
                feat['properties'][source_field])
        ]

    data = [(
            feat['properties'][source_field],
            get_remaining(
                _(shape(feat['geometry'])), get_geoms(feat)
            )
        ) for feat in source
    ]

    metadata = {
        'source': source_metadata,
        'intersections': inter_metadata,
        'when': datetime.datetime.now().isoformat(),
    }

    return json_exporter({'data': data, 'metadata': metadata}, output, compress)


def intersections_from_intersection(fp, metadata=None, dirpath=None):
    """Process an intersections spatial dataset to create two intersections data files.

    ``fp`` is the file path of a vector dataset created by the ``intersect`` function. The intersection of two spatial scales (A, B) is a third spatial scale (C); this function creates intersection data files for (A, C) and (B, C).

    As the intersections data file includes metadata on the input files, this function must have access to the intersections data file created at the same time as intersections spatial dataset. If the ``metadata`` filepath is not provided, the metadata file is looked for in the same directory as ``fp``.

    Returns the file paths of the two new intersections data files.
    """
    assert os.path.isfile(fp)

    if metadata:
        assert os.path.isfile(metadata)
    else:
        metadata = ".".join(fp.split(".")[:-1]) + ".json"
        if not os.path.isfile(metadata):
            metadata += ".bz2"
            if not os.path.isfile(metadata):
                raise ValueError("Can't find metadata file")

    metadata = json_importer(metadata)['metadata']

    with fiona.open(fp) as source:
        for key in ('id', 'from_label', 'to_label', 'measure'):
            assert key in source.schema['properties']
        data = [feat['properties'] for feat in source]

    this = {
        'field': 'id',
        'path': fp,
        'filename': os.path.basename(fp),
        'sha256': sha256(fp)
    }

    first_dataset = {
        'data': [(o['id'], o['from_label'], o['measure']) for o in data],
        'metadata': {
            'first': this,
            'second': metadata['first'],
            'when': datetime.datetime.now().isoformat()
        }
    }
    second_dataset = {
        'data': [(o['id'], o['to_label'], o['measure']) for o in data],
        'metadata': {
            'first': this,
            'second': metadata['second'],
            'when': datetime.datetime.now().isoformat()
        }
    }

    if not dirpath:
        dirpath = get_appdirs_path("intersections")

    first_fp = os.path.join(
        dirpath,
        "{}.{}.json".format(this['sha256'], metadata['first']['sha256'])
    )
    second_fp = os.path.join(
        dirpath,
        "{}.{}.json".format(this['sha256'], metadata['second']['sha256'])
    )

    return (
        json_exporter(first_dataset, first_fp),
        json_exporter(second_dataset, second_fp)
    )
