"""Core functions for Pandarus."""
import datetime
import multiprocessing
import os
import tempfile
import warnings
from functools import partial
from typing import Dict, List, Optional, Tuple

import fiona
import numpy as np
import rasterio
from fiona.crs import CRS
from rasterstats.io import read_features
from shapely.geometry import shape

from .helpers import ExtractionHelper
from .model import Map
from .utils.conversion import (
    check_dataset_type,
    dict_to_features,
    round_to_x_significant_digits,
)
from .utils.geometry import get_geom_remaining_measure
from .utils.io import export_json, get_appdirs_path, import_json, sha256_file
from .utils.multiprocess import intersection_dispatcher
from .utils.projection import WGS84, project_geom


def intersect(
    first_file_path: str,
    first_field: str,
    second_file_path: str,
    second_field: str,
    first_kwargs: Optional[Dict] = None,
    second_kwargs: Optional[Dict] = None,
    out_dir: str = get_appdirs_path("intersections"),
    cpus: int = multiprocessing.cpu_count(),
    driver: str = "GeoJSON",
    compress: bool = True,
    log_dir: Optional[str] = None,
):
    """Calculate the intersection of two vector spatial datasets.

    The first spatial input file **must** have only one type of geometry, i.e. points,
    lines, or polygons, and excluding geometry collections. Any of the following are
    allowed: Point, MultiPoint, LineString, LinearRing, MultiLineString, Polygon,
    MultiPolygon.

    The second spatial input file **must** have either Polygons or MultiPolygons.
    Although no checks are made, this and other functions make a strong assumption
    that the spatial units in the second spatial unit do not overlap.

    Input parameters:

        * ``first_file_path``: String. File path to the first spatial dataset.
        * ``first_field``: String. Name of field that uniquely identifies features
        in the first spatial dataset.
        * ``second_file_path``: String. File path to the second spatial dataset.
        * ``second_field``: String. Name of field that uniquely identifies features in
        the second spatial dataset.
        * ``first_kwargs``: Dictionary, optional. Additional arguments, such as layer
        name, passed to fiona when opening the first spatial dataset.
        * ``second_kwargs``: Dictionary, optional. Additional arguments, such as layer
        name, passed to fiona when opening the second spatial dataset.
        * ``out_dir``: String, optional. Directory to save output files.
        * ``cpus``: Integer, default is ``multiprocessing.cpu_count()``. Number of CPU
        cores to use when calculating. Use ``cpus=0`` to avoid starting a
        multiprocessing pool.
        * ``driver``: String, default is ``GeoJSON``. Fiona driver name to use when
        writing geospatial output file. Common values are ``GeoJSON`` or ``GPKG``.
        * ``compress``: Boolean, default is True. Compress JSON output file.
        * ``log_dir``: String, optional.

    Returns filepaths for two created files.

    The first is a geospatial file that has the geometry of each possible intersection
    of spatial units from the two input files. The geometry type of this file will
    depend on the geometry type of the first input file, but will always be a multi
    geometry, i.e. one of MultiPoint, MultiLineString, MultiPolygon. This file will also
    always have the `WGS 84 CRS <http://spatialreference.org/ref/epsg/wgs-84/>`__.
    The output file has the following schema:

        * ``id``: Integer. Auto-increment field starting from zero.
        * ``from_label``: String. The value for the uniquely identifying field from the
        first input file.
        * ``to_label``: String. The value for the uniquely identifying field from the
        second input file.
        * ``measure``: Float. A measure of the intersected shape. For polygons, this is
        the area of the feature in square meters. For lines, this is the length in
        meters. For points, this is the number of points. Area and length calculations
        are made using the `Mollweide projection
        <https://en.wikipedia.org/wiki/Mollweide_projection>`__.

    The second file is an extract of some of the feature fields in the JSON data format.
    This is used by programs that don't need to depend on GIS data libraries. The JSON
    format is:

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
    if first_kwargs is None:
        first_kwargs = {}
    if second_kwargs is None:
        second_kwargs = {}

    first_map, first_metadata = Map.get_map_with_metadata(
        first_file_path, first_field, **first_kwargs
    )
    second_map, second_metadata = Map.get_map_with_metadata(
        second_file_path, second_field, **second_kwargs
    )

    base_filepath = os.path.join(out_dir, f"{first_map.hash}.{second_map.hash}")
    fiona_fp = f"{base_filepath}.{driver.lower()}"

    data = {
        (
            first_map.get_fieldnames_dictionary()[k[0]],
            second_map.get_fieldnames_dictionary()[k[1]],
        ): v
        for k, v in intersection_dispatcher(
            first_file_path, second_file_path, cpus=cpus, log_dir=log_dir
        ).items()
    }

    schema = {
        "properties": {
            "id": "int",
            "from_label": first_map.get_label(first_field),
            "to_label": second_map.get_label(second_field),
            "measure": "float",
        },
        "geometry": next(iter(data.values()))["geom"].geom_type,
    }

    with fiona.Env():
        with fiona.open(
            fiona_fp,
            "w",
            crs=CRS.from_string(WGS84),
            driver=driver,
            schema=schema,
        ) as sink:
            for f in dict_to_features(data):
                sink.write(f)

    json_fp = export_json(
        {
            "data": [(k[0], k[1], v["measure"]) for k, v in data.items()],
            "metadata": {
                "first": first_metadata,
                "second": second_metadata,
                "when": datetime.datetime.now().isoformat(),
            },
        },
        base_filepath + ".json",
        compress=compress,
    )

    return fiona_fp, json_fp


def intersections_from_intersection(
    vector_file_path: str,
    metadata_file_path: Optional[str] = None,
    out_dir: Optional[str] = None,
) -> Tuple[str, str]:
    """Process an intersections spatial dataset to create two intersections data files.

    ``vector_file_path`` is the file path of a vector dataset created by the
    ``intersect`` function. The intersection of two spatial scales (A, B) is a third
    spatial scale (C); this function creates intersection data files for (A, C) and
    (B, C).

    As the intersections data file includes metadata on the input files, this function
    must have access to the intersections data file created at the same time as
    intersections spatial dataset. If the ``metadata_file_path`` is not provided, the
    metadata file is looked for in the same directory as ``vector_file_path``.

    Returns the file paths of the two new intersections data files.
    """
    if not os.path.isfile(vector_file_path):
        raise FileNotFoundError(f"Can't find vector file: {vector_file_path}.")

    if metadata_file_path:
        if not os.path.isfile(metadata_file_path):
            raise FileNotFoundError(f"Can't find metadata file: {metadata_file_path}.")
    else:
        metadata_file_path = ".".join(vector_file_path.split(".")[:-1]) + ".json"
        if not os.path.isfile(metadata_file_path):
            metadata_file_path += ".bz2"
            if not os.path.isfile(metadata_file_path):
                raise ValueError("Can't find metadata file")

    metadata = import_json(metadata_file_path)["metadata"]

    with fiona.open(vector_file_path) as source:
        for key in ("id", "from_label", "to_label", "measure"):
            if key not in source.schema["properties"]:
                raise ValueError(
                    f"Input file {vector_file_path} does not have required field: {key}"
                )
        data = [feat["properties"] for feat in source]

    this = {
        "field": "id",
        "path": vector_file_path,
        "filename": os.path.basename(vector_file_path),
        "sha256": sha256_file(vector_file_path),
    }

    first_dataset = {
        "data": [(o["id"], o["from_label"], o["measure"]) for o in data],
        "metadata": {
            "first": this,
            "second": metadata["first"],
            "when": datetime.datetime.now().isoformat(),
        },
    }
    second_dataset = {
        "data": [(o["id"], o["to_label"], o["measure"]) for o in data],
        "metadata": {
            "first": this,
            "second": metadata["second"],
            "when": datetime.datetime.now().isoformat(),
        },
    }

    if not out_dir:
        out_dir = get_appdirs_path("intersections")

    first_fp = os.path.join(
        out_dir, f"{this['sha256']}.{metadata['first']['sha256']}.json"
    )
    second_fp = os.path.join(
        out_dir, f"{this['sha256']}.{metadata['second']['sha256']}.json"
    )

    return (
        export_json(first_dataset, first_fp),
        export_json(second_dataset, second_fp),
    )


def calculate_remaining(
    source_file_path: str,
    source_field: str,
    intersection_file_path: str,
    source_kwargs: Optional[Dict] = None,
    out_dir: Optional[Dict] = None,
    compress: bool = True,
) -> str:
    """Calculate the remaining area/length/number of points left out of an intersections
    file generated by ``intersect``.

    Input parameters:

        * ``source_file_path``: String. Filepath of the input spatial data which could
        have features outside of the intersection result.
        * ``source_field``: String. Name of field that uniquely identifies features in
        the input spatial dataset.
        * ``intersection_file_path``: Filepath of the intersection spatial dataset
        generated by the ``intersect`` function.
        * ``source_kwargs``: Dictionary, optional. Additional arguments, such as layer
        name, passed to fiona when opening the input spatial dataset.
        * ``out_dir``: String, optional. Directory where the output file will be saved.
        * ``compress``: Boolean. Whether or not to compress the output file.

    .. warning:: ``source_file_path`` must be the first file provided to the
    ``intersect`` function, **not** the second!

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
    if source_kwargs is None:
        source_kwargs = {}

    source, source_metadata = Map.get_map_with_metadata(
        source_file_path, source_field, **source_kwargs
    )
    intersections, inter_metadata = Map.get_map_with_metadata(
        intersection_file_path, "id"
    )

    if intersections.file.schema["properties"].keys() != {
        "id",
        "from_label",
        "to_label",
        "measure",
    }:
        raise ValueError(
            """Input file does not have required fields:
            id, from_label, to_label, measure"""
        )

    if intersections.file.schema["properties"]["id"] != "int":
        raise ValueError("Expected value for field id is int but found something else.")

    if intersections.file.schema["properties"]["measure"] != "float":
        raise ValueError(
            "Expected value for field measure is float but found something else."
        )

    if not out_dir:
        out_dir = get_appdirs_path("intersections")

    output = os.path.join(out_dir, f"{source.hash}.{intersections.hash}.json")

    proj_geom = partial(project_geom, from_proj=source.crs, to_proj="")

    def get_geoms(feat) -> List:
        return [
            shape(x["geometry"])
            for x in intersections
            if (x["properties"]["from_label"] == feat["properties"][source_field])
        ]

    data = [
        (
            feat["properties"][source_field],
            get_geom_remaining_measure(
                proj_geom(shape(feat["geometry"])), get_geoms(feat)
            ),
        )
        for feat in source
    ]

    metadata = {
        "source": source_metadata,
        "intersections": inter_metadata,
        "when": datetime.datetime.now().isoformat(),
    }

    return export_json({"data": data, "metadata": metadata}, output, compress)


def raster_statistics(
    vector_file_path: str,
    identifying_field: str,
    raster_file_path: str,
    output_file_path: str = None,
    band: int = 1,
    compress: bool = True,
    fiona_kwargs: Optional[Dict] = None,
) -> str:
    # pylint: disable=import-outside-toplevel
    """Create statistics by matching ``raster_file_path`` against each spatial unit in
    ``self.from_map``.

    For each spatial unit in ``self.from_map``, calculates the following statistics
    for values from ``raster_file_path``: min, mean, max, and count. Count is the number
    of raster cells intersecting the vector spatial unit. No data values in the raster
    are not included in the generated statistics.

    If ``exactextract`` is installed, uses that library to calculate statistics. If not,
    uses the ``gen_zonal_stats`` function from ``rasterstats``.

    Input parameters:

        * ``vector_file_path``: str. Filepath of the vector dataset.
        * ``identifying_field``: str. Name of the field in ``vector_file_path`` that
        uniquely identifies each feature.
        * ``raster_file_path``: str. Filepath of the raster dataset.
        * ``output_file_path``: str, optional. Filepath of the output file. Will be
        deleted if it exists already.
        * ``band``: int, optional. Raster band used for calculations. Default is ``1``.
        * ``compress``: bool, optional. Compress JSON results file. Default is ``True``.
        * ``fiona_kwargs``: dict, optional. Additional arguments to pass to fiona when
        opening ``vector_file_path``.

    Output format:

    Output is a (maybe compressed) JSON file with the following schema:

     .. code-block:: python

        {
            'metadata': {
                'vector': {
                    'field': 'name of uniquely identifying field',
                    'path': 'path to vector input file',
                    'sha256': 'sha256 hash of input file'
                },
                'raster': {
                    'band': 'band used to calculate raster stats',
                    'path': 'path to raster input file',
                    'filename': 'name of raster file',
                    'sha256': 'sha256 hash of input file'
                },
                'when': 'datetime this calculation finished, ISO format'
            },
            'data': [
                [
                    'vector `identifying_field` value',
                    {
                        'count': 'number of raster cells included. float because
                                  consider fractional intersections',
                        'min': 'minimum raster value in this vector feature',
                        'mean': 'average raster value in this vector feature',
                        'max': 'maximum raster value in this vector feature',
                    }
                ]
            ]
        }

    """
    if fiona_kwargs is None:
        fiona_kwargs = {}

    vector, v_metadata = Map.get_map_with_metadata(
        vector_file_path, identifying_field, **fiona_kwargs
    )
    if check_dataset_type(raster_file_path) != "raster":
        raise ValueError("raster must be a raster dataset.")

    if not output_file_path:
        dirpath = get_appdirs_path("rasterstats")
        output_file_path = os.path.join(
            dirpath, f"{vector.hash}-{sha256_file(raster_file_path)}-{band}.json"
        )

    if os.path.exists(output_file_path):
        os.remove(output_file_path)

    with rasterio.open(raster_file_path) as r:
        if vector.crs != r.crs.to_string():
            warnings.warn(
                f"""
                Possible coordinate reference systems (CRS) mismatch.
                The raster statistics may be incorrect, please only use this method
                when both vector and raster have the same CRS.
                Vector: {vector.crs}
                Raster: {r.crs.to_string()}
                """
            )

        try:
            from exactextract import exact_extract
        except ImportError:
            warnings.warn(
                """exactextract module not found.
                Using gen_zonal_stats from rasterstats instead.
                Please install exactextract if you need it."""
            )
            from rasterstats import gen_zonal_stats

            stats_generator = gen_zonal_stats(
                vector_file_path,
                raster_file_path,
                band=band,
                stats=("min", "max", "mean", "count"),
                # **fiona_kwargs,
            )
        else:
            stats_generator = [
                exact_extract(
                    rast=r,
                    vec=v,
                    ops=("min", "max", "mean", "count"),
                )
                for v in read_features(vector_file_path, **fiona_kwargs)
            ]

    mapping_dict = vector.get_fieldnames_dictionary()
    results = [(mapping_dict[index], row) for index, row in enumerate(stats_generator)]

    metadata = {
        "vector": v_metadata,
        "raster": {
            "sha256": sha256_file(raster_file_path),
            "path": raster_file_path,
            "filename": os.path.basename(raster_file_path),
            "band": band,
        },
        "when": datetime.datetime.now().isoformat(),
    }
    return export_json(
        {"data": results, "metadata": metadata}, output_file_path, compress
    )


def convert_to_vector(
    vector_file_path: str,
    out_dir: Optional[str] = None,
    band: int = 1,
) -> str:
    """Convert raster file at ``vector_file_path`` to a vector file. Returns file
    path of created vector file.

    ``out_dir`` should be a writable directory. If ``out_dir`` is no specified, uses the
    `appdirs library <https://pypi.python.org/pypi/appdirs>`__ to find an appropriate
    directory.

    ``band`` should be the integer index of the band; default is 1. Note that band
    indices start from 1, not 0.

    The generated vector file will be in GeoJSON, and have the WGS84 CRS.

    Because we are using `GDAL polygonize
    <http://www.gdal.org/gdal__alg_8h.html#a7a789015334d677afcbef67e5a6b4a7c>`__, we
    can't use 64 bit floats. This function will automatically convert rasters from 64
    to 32 bit floats if necessary."""

    if out_dir is None:
        out_dir = get_appdirs_path("raster-conversion")
    else:
        if not os.path.isdir(out_dir) or not os.access(out_dir, os.W_OK):
            raise ValueError(f"Can't write to directory: {out_dir}")

    out_fp = os.path.join(out_dir, f"{sha256_file(vector_file_path)}.{band}.geojson")
    if os.path.exists(out_fp):
        return out_fp

    ExtractionHelper(vector_file_path, out_fp, band).write_features()
    return out_fp


def clean_raster(
    raster_file_path: str,
    clean_raster_file_path: Optional[str] = None,
    band: int = 1,
    nodata: Optional[float] = None,
) -> str:
    """Clean raster data and metadata:
        * Delete invalid block sizes, and remove tiling
        * Set nodata to a reasonable value, if possible
        * Convert to 32 bit floats, if currently 64 bit floats and such conversion is
        possible

    ``raster_file_path``: String. Filepath of the input raster file.

    ``clean_raster_file_path``: String, optional. Filepath of the raster to create. If
    not provided, the new raster will have the same name as the existing file, but will
    e created in a temporary directory.

    ``band``: Integer, default is ``1``. Raster band to clean and create in new file.
    Each band of a multiband raster would have to be cleaned separately.

    ``nodata``: Float, optional. Additional value to try when changing ``nodata`` value;
    must not be present in existing raster data.

    Returns the filepath of the new file as a compressed GeoTIFF. Can also return
    ``None`` if no new raster was written due to failing preconditions."""
    with rasterio.Env():
        with rasterio.open(raster_file_path) as src:
            profile = src.profile
            array = src.read(band)
            dtypes = src.dtypes

    profile.update(driver="GTiff", count=1, compress="lzw")

    # Set nodata to a reasonable value if possible
    if profile.get("nodata") is None and (array < -1e30).sum():
        raise ValueError(
            "No `nodata` value set, but large negative numbers present. "
            "Please set a valid `nodata` value in raster file."
        )
    if profile.get("nodata") and profile["nodata"] < -1e30:
        nodatas = [-1, -99, -999, -9999]
        if nodata is not None:
            nodatas = [nodata] + nodatas
        found = False
        for value in nodatas:
            if not (array == value).sum():
                nodata, found = value, True
                break

        if found:
            array[np.isclose(array, profile["nodata"])] = nodata
            array[np.isnan(array)] = nodata
            profile["nodata"] = nodata
        else:
            raise ValueError(
                f"`nodata` value is large and negative ({profile['nodata']}), but"
                "no suitable replacement value found. Please specify a `nodata` value."
            )

    if dtypes[band - 1] == rasterio.float64:
        if not (
            (array < np.finfo("float32").min).sum()
            or (array > np.finfo("float32").max).sum()
        ):
            array = array.astype(np.float32)
            profile["dtype"] = np.float32
        else:
            print("Not converting to 32 bit float; out of range values present.")

    profile["tiled"] = False
    profile.pop("blockysize", None)
    profile.pop("blockxsize", None)

    if clean_raster_file_path is None:
        clean_raster_file_path = os.path.join(
            tempfile.mkdtemp(), os.path.basename(raster_file_path)
        )

    with rasterio.Env():
        with rasterio.open(clean_raster_file_path, "w", **profile) as dst:
            dst.write(array, 1)

    return clean_raster_file_path


def round_raster(
    raster_file_path: str,
    round_raster_file_path: Optional[str] = None,
    band: int = 1,
    sig_digits: int = 3,
) -> str:
    """Round raster cell values to a certain number of significant digits in new raster
    file. For example, π rounded to 4 significant digits is 3.142.

        * ``in_fp``: String. Filepath of raster input file.
        * ``out_fp``: String, optional. Filepath of new raster to be created. Should not
        currently exist. If not provided, the new raster will have the same name as the
        existing file, but will be created in a temporary directory.
        * ``band``: Int, default is 1. Band to round. Band indices start at 1.
        * ``sig_digits``: Int, default is 3. Number of significant digits to round to.

    The created raster file will have the same ``dtype``, shape, and CRS as the input
    file. It will be a compressed GeoTIFF.

    Returns ``out_fp``, the filepath of the created file.

    """
    if round_raster_file_path is None:
        round_raster_file_path = os.path.join(
            tempfile.mkdtemp(), os.path.basename(raster_file_path)
        )

    with rasterio.Env():
        with rasterio.open(raster_file_path) as src:
            array = src.read(band)
            profile = src.profile

        profile.update(driver="GTiff", count=1, compress="lzw")

        with rasterio.open(round_raster_file_path, "w", **profile) as dst:
            dst.write(round_to_x_significant_digits(array, sig_digits), 1)

    return round_raster_file_path
