from .filesystem import sha256, get_appdirs_path
import fiona
import os
import rasterio
import tempfile
import warnings

from rasterio.rio.helpers import coords, write_features
from rasterio.crs import CRS

import numpy as np
import rasterio.features
import rasterio.warp


def check_type(filepath):
    """Determine if a GIS dataset is raster or vector.

    ``filepath`` is a filepath of a GIS dataset file.

    Returns ``'vector'`` or ``'raster'``. Raises a ``ValueError`` if the file can't be opened with fiona or rasterio."""
    try:
        with fiona.open(filepath) as ds:
            assert ds.meta['schema']['geometry'] != 'None'
        return 'vector'
    except:
        try:
            with rasterio.open(filepath) as ds:
                assert ds.meta
            return 'raster'
        except:
            raise ValueError("Unknown data type")


def convert_to_vector(filepath, dirpath=None, band=1):
    """Convert raster file at ``filepath`` to a vector file. Returns filepath of created vector file.

    ``dirpath`` should be a writable directory. If ``dirpath`` is no specified, uses the `appdirs library <https://pypi.python.org/pypi/appdirs>`__ to find an appropriate directory.

    ``band`` should be the integer index of the band; default is 1. Note that band indices start from 1, not 0.

    The generated vector file will be in GeoJSON, and have the WGS84 CRS.

    Because we are using `GDAL polygonize <http://www.gdal.org/gdal__alg_8h.html#a7a789015334d677afcbef67e5a6b4a7c>`__, we can't use 64 bit floats. This function will automatically convert rasters from 64 to 32 bit floats if necessary."""
    assert isinstance(band, int), "band must be an integer"

    if dirpath is None:
        dirpath = get_appdirs_path("raster-conversion")
    else:
        assert (os.path.isdir(dirpath) and os.access(dirpath, os.W_OK)), \
            "dirpath must be a writable directory"

    out_fp = os.path.join(dirpath, "{}.{}.geojson".format(sha256(filepath), band))
    if os.path.exists(out_fp):
        return out_fp

    _shapes(filepath, out_fp, band)
    return out_fp


def _shapes(in_fp, out_fp, bidx):
    """Code from rio CLI: https://github.com/mapbox/rasterio/blob/master/rasterio/rio/shapes.py
    All the click stuff is cut out, as well as some option which we don't need.

    Extracts shapes from one band or mask of a dataset and writes
    them out as GeoJSON. Shapes will be transformed to WGS 84 coordinates.

    The default action of this command is to extract shapes from the
    first band of the input dataset. The shapes are polygons bounding
    contiguous regions (or features) of the same raster value. This
    command performs poorly for int16 or float type datasets."""

    dump_kwds = {'sort_keys': True}

    # This is the generator for (feature, bbox) pairs.
    class Collection(object):

        def __init__(self):
            self._xs = []
            self._ys = []

        @property
        def bbox(self):
            return min(self._xs), min(self._ys), max(self._xs), max(self._ys)

        def __call__(self):
            with rasterio.open(in_fp) as src:
                if bidx > src.count:
                    raise ValueError('bidx is out of range for raster')

                # Adjust transforms.
                transform = src.transform

                # Most of the time, we'll use the valid data mask.
                # We skip reading it if we're extracting every possible
                # feature (even invalid data features) from a band.
                msk = src.read_masks(bidx)
                img = src.read(bidx, masked=False)

                # Transform the raster bounds.
                bounds = src.bounds
                xs = [bounds[0], bounds[2]]
                ys = [bounds[1], bounds[3]]
                xs, ys = rasterio.warp.transform(
                    src.crs, CRS({'init': 'epsg:4326'}), xs, ys)
                self._xs = xs
                self._ys = ys

                # Prepare keyword arguments for shapes().
                kwargs = {'transform': transform}
                kwargs['mask'] = msk

                src_basename = os.path.basename(src.name)

                # Yield GeoJSON features.
                for i, (g, val) in enumerate(
                        rasterio.features.shapes(img, **kwargs)):
                    g = rasterio.warp.transform_geom(
                        src.crs, 'EPSG:4326', g,
                        antimeridian_cutting=True, precision=-1)
                    xs, ys = zip(*coords(g))
                    yield {
                        'type': 'Feature',
                        'id': str(i),
                        'properties': {
                            'val': val,
                            'filename': src_basename,
                            'id': i
                        },
                        'bbox': [min(xs), min(ys), max(xs), max(ys)],
                        'geometry': g
                    }

    with open(out_fp, "w") as f:
        write_features(
            f, Collection(), sequence=False,
            geojson_type='collection', use_rs=False, **dump_kwds
        )


def clean_raster(fp, new_fp=None, band=1, nodata=None):
    """Clean raster data and metadata:
        * Delete invalid block sizes, and remove tiling
        * Set nodata to a reasonable value, if possible
        * Convert to 32 bit floats, if currently 64 bit floats and such conversion is possible

    ``fp``: String. Filepath of the input raster file.

    ``new_fp``: String, optional. Filepath of the raster to create. If not provided, the new raster will have the same name as the existing file, but will be created in a temporary directory.

    ``band``: Integer, default is ``1``. Raster band to clean and create in new file. Each band of a multiband raster would have to be cleaned separately.

    ``nodata``: Float, optional. Additional value to try when changing ``nodata`` value; must not be present in existing raster data.

    Returns the filepath of the new file as a compressed GeoTIFF. Can also return ``None`` if no new raster was written due to failing preconditions."""
    with rasterio.Env():
        with rasterio.open(fp) as src:
            profile = src.profile
            array = src.read(band)
            dtypes = src.dtypes

    profile.update(
        driver='GTiff',
        count=1,
        compress='lzw')

    # Set nodata to a reasonable value if possible
    if profile.get('nodata') is None and (array < -1e30).sum():
        warnings.warn("No `nodata` value set, but large negative numbers present. "
              "Please set a valid `nodata` value in raster file.")
        return
    elif profile.get('nodata') and profile['nodata'] < -1e30:
        nodatas = [-1, -99, -999, -9999]
        if nodata is not None:
            nodatas = [nodata] + nodatas
        found = False
        for value in nodatas:
            if not (array == value).sum():
                nodata, found = value, True
                break

        if found:
            array[np.isclose(array, profile['nodata'])] = nodata
            array[np.isnan(array)] = nodata
            profile['nodata'] = nodata
        else:
            warnings.warn((
                "`nodata` value is large and negative ({}), but no suitable "
                "replacement value found. Please specify a `nodata` value."
            ).format(profile['nodata']))
            return

    if dtypes[band - 1] == rasterio.float64:
        if not ((array < np.finfo('float32').min).sum() or
                (array > np.finfo('float32').max).sum()):
            array = array.astype(np.float32)
            profile['dtype'] = np.float32
        else:
            print("Not converting to 32 bit float; out of range values present.")

    profile['tiled'] = False
    profile.pop('blockysize', None)
    profile.pop('blockxsize', None)

    if new_fp is None:
        new_fp = os.path.join(tempfile.mkdtemp(), os.path.basename(fp))

    with rasterio.Env():
        with rasterio.open(new_fp, 'w', **profile) as dst:
            dst.write(array, 1)

    return new_fp


def round_to_x_significant_digits(array, sf=3):
    num_digits = sf - np.floor(np.log10(np.abs(array))).astype(int) - 1
    num_digits[np.where(array == 0)] = 0
    for value in np.unique(num_digits):
        indices = np.where(num_digits == value)
        array[indices] = np.round(array[indices], value)
    return array


def round_raster(in_fp, out_fp=None, band=1, sig_digits=3):
    """Round raster cell values to a certain number of significant digits in new raster file. For example, π rounded to 4 significant digits is 3.142.

        * ``in_fp``: String. Filepath of raster input file.
        * ``out_fp``: String, optional. Filepath of new raster to be created. Should not currently exist. If not provided, the new raster will have the same name as the existing file, but will be created in a temporary directory.
        * ``band``: Int, default is 1. Band to round. Band indices start at 1.
        * ``sig_digits``: Int, default is 3. Number of significant digits to round to.

    The created raster file will have the same ``dtype``, shape, and CRS as the input file. It will be a compressed GeoTIFF.

    Returns ``out_fp``, the filepath of the created file.

    """
    if out_fp is None:
        out_fp = os.path.join(
            tempfile.mkdtemp(),
            os.path.basename(in_fp)
        )

    with rasterio.Env():
        with rasterio.open(in_fp) as src:
            array = src.read(band)
            profile = src.profile

        profile.update(
            driver='GTiff',
            count=1,
            compress='lzw')

        with rasterio.open(out_fp, 'w', **profile) as dst:
            dst.write(round_to_x_significant_digits(array, sig_digits), 1)

    return out_fp
