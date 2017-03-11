# -*- coding: utf-8 -*-
import numpy as np
import warnings
from affine import Affine
from numpy import min_scalar_type
from rasterio import features
from rasterstats.io import read_features, Raster
from rasterstats.utils import (get_percentile, check_stats, remap_categories,
                    key_assoc_val, boxify_points)
from shapely.geometry import shape

# Code from https://github.com/perrygeo/python-rasterstats/pull/136
# Percent coverage selection and weighting
# Same license as rasterstats


def gen_zonal_stats(
        vectors, raster,
        layer=0,
        band=1,
        nodata=None,
        affine=None,
        stats=None,
        all_touched=True,
        percent_cover_selection=None,
        percent_cover_weighting=True,
        percent_cover_scale=20,
        categorical=False,
        category_map=None,
        add_stats=None,
        zone_func=None,
        raster_out=False,
        prefix=None,
        geojson_out=False, **kwargs):
    """Zonal statistics of raster values aggregated to vector geometries.

    Parameters

    vectors: path to an vector source or geo-like python objects

    raster: ndarray or path to a GDAL raster source
        If ndarray is passed, the ``affine`` kwarg is required.

    layer: int or string, optional
        If `vectors` is a path to an fiona source,
        specify the vector layer to use either by name or number.
        defaults to 0

    band: int, optional
        If `raster` is a GDAL source, the band number to use (counting from 1).
        defaults to 1.

    nodata: float, optional
        If `raster` is a GDAL source, this value overrides any NODATA value
        specified in the file's metadata.
        If `None`, the file's metadata's NODATA value (if any) will be used.
        defaults to `None`.

    affine: Affine instance
        required only for ndarrays, otherwise it is read from src

    stats:  list of str, or space-delimited str, optional
        Which statistics to calculate for each zone.
        All possible choices are listed in ``utils.VALID_STATS``.
        defaults to ``DEFAULT_STATS``, a subset of these.

    all_touched: bool, optional
        Whether to include every raster cell touched by a geometry, or only
        those having a center point within the polygon.
        defaults to `False`

    percent_cover_selection: float, optional
        Include only raster cells that have at least the given percent
        covered by the vector feature. Requires percent_cover_scale argument
        be used to specify scale at which to generate percent coverage
        estimates

    percent_cover_weighting: bool, optional
        whether or not to use percent coverage of cells during calculations
        to adjust stats (only applies to mean, count and sum)

    percent_cover_scale: int, optional
        Scale used when generating percent coverage estimates of each
        raster cell by vector feature. Percent coverage is generated by
        rasterizing the feature at a finer resolution than the raster
        (based on percent_cover_scale value) then using a summation to aggregate
        to the raster resolution and dividing by the square of percent_cover_scale
        to get percent coverage value for each cell. Increasing percent_cover_scale
        will increase the accuracy of percent coverage values; three orders
        magnitude finer resolution (percent_cover_scale=1000) is usually enough to
        get coverage estimates with <1% error in individual edge cells coverage
        estimates, though much smaller values (e.g., percent_cover_scale=10) are often
        sufficient (<10% error) and require less memory.

    categorical: bool, optional

    category_map: dict
        A dictionary mapping raster values to human-readable categorical names.
        Only applies when categorical is True

    add_stats: dict
        with names and functions of additional stats to compute, optional

    zone_func: callable
        function to apply to zone ndarray prior to computing stats

    raster_out: boolean
        Include the masked numpy array for each feature?, optional

        Each feature dictionary will have the following additional keys:
        mini_raster_array: The clipped and masked numpy array
        mini_raster_affine: Affine transformation
        mini_raster_nodata: NoData Value

    prefix: string
        add a prefix to the keys (default: None)

    geojson_out: boolean
        Return list of GeoJSON-like features (default: False)
        Original feature geometry and properties will be retained
        with zonal stats appended as additional properties.
        Use with `prefix` to ensure unique and meaningful property names.

    Returns

    generator of dicts (if geojson_out is False)
        Each item corresponds to a single vector feature and
        contains keys for each of the specified stats.

    generator of geojson features (if geojson_out is True)
        GeoJSON-like Feature as python dict
    """
    stats, run_count = check_stats(stats, categorical)

    # check inputs related to percent coverage
    percent_cover = False
    if percent_cover_weighting or percent_cover_selection is not None:
        percent_cover = True
        if percent_cover_scale is None:
            warnings.warn('No value for `percent_cover_scale` was given. '
                          'Using default value of 10.')
            percent_cover_scale = 10

        try:
            if percent_cover_scale != int(percent_cover_scale):
                warnings.warn('Value for `percent_cover_scale` given ({0}) '
                              'was converted to int ({1}) but does not '
                              'match original value'.format(
                                percent_cover_scale, int(percent_cover_scale)))

            percent_cover_scale = int(percent_cover_scale)

            if percent_cover_scale <= 1:
                raise Exception('Value for `percent_cover_scale` must be '
                                'greater than one ({0})'.format(
                                    percent_cover_scale))

        except:
            raise Exception('Invalid value for `percent_cover_scale` '
                            'provided ({0}). Must be type int.'.format(
                                percent_cover_scale))

        if percent_cover_selection is not None:
            try:
                percent_cover_selection = float(percent_cover_selection)
            except:
                raise Exception('Invalid value for `percent_cover_selection` '
                                'provided ({0}). Must be able to be converted '
                                'to a float.'.format(percent_cover_selection))

        # if not all_touched:
        #     warnings.warn('`all_touched` was not enabled but an option requiring '
        #                   'percent_cover calculations was selected. Automatically '
        #                   'enabling `all_touched`.')
        # all_touched = True

    with Raster(raster, affine, nodata, band) as rast:
        features_iter = read_features(vectors, layer)
        for _, feat in enumerate(features_iter):
            geom = shape(feat['geometry'])

            if 'Point' in geom.type:
                geom = boxify_points(geom, rast)
                percent_cover = False

            geom_bounds = tuple(geom.bounds)
            fsrc = rast.read(bounds=geom_bounds)

            if percent_cover:
                cover_weights = rasterize_pctcover_geom(
                    geom, shape=fsrc.shape, affine=fsrc.affine,
                    scale=percent_cover_scale,
                    all_touched=all_touched)
                rv_array = cover_weights > (percent_cover_selection or 0)
            else:
                rv_array = rasterize_geom(
                    geom, shape=fsrc.shape, affine=fsrc.affine,
                    all_touched=all_touched)

            # nodata mask
            isnodata = (fsrc.array == fsrc.nodata)

            # add nan mask (if necessary)
            if np.issubdtype(fsrc.array.dtype, float) and \
               np.isnan(fsrc.array.min()):
                isnodata = (isnodata | np.isnan(fsrc.array))

            # Mask the source data array
            # mask everything that is not a valid value or not within our geom
            masked = np.ma.MaskedArray(
                fsrc.array,
                mask=(isnodata | ~rv_array))

            # execute zone_func on masked zone ndarray
            if zone_func is not None:
                if not callable(zone_func):
                    raise TypeError(('zone_func must be a callable '
                                     'which accepts function a '
                                     'single `zone_array` arg.'))
                zone_func(masked)

            if masked.compressed().size == 0:
                # nothing here, fill with None and move on
                feature_stats = dict([(stat, None) for stat in stats])
                if 'count' in stats:  # special case, zero makes sense here
                    feature_stats['count'] = 0
            else:
                if run_count:
                    keys, counts = np.unique(masked.compressed(), return_counts=True)
                    pixel_count = dict(zip([np.asscalar(k) for k in keys],
                                           [np.asscalar(c) for c in counts]))

                if categorical:
                    feature_stats = dict(pixel_count)
                    if category_map:
                        feature_stats = remap_categories(category_map, feature_stats)
                else:
                    feature_stats = {}

                if 'min' in stats:
                    feature_stats['min'] = float(masked.min())
                if 'max' in stats:
                    feature_stats['max'] = float(masked.max())
                if 'mean' in stats:
                    if percent_cover:
                        feature_stats['mean'] = float(
                            np.sum(masked * cover_weights) /
                            np.sum(~masked.mask * cover_weights))
                    else:
                        feature_stats['mean'] = float(masked.mean())
                if 'count' in stats:
                    if percent_cover:
                        feature_stats['count'] = float(np.sum(~masked.mask * cover_weights))
                    else:
                        feature_stats['count'] = int(masked.count())
                # optional
                if 'sum' in stats:
                    if percent_cover:
                        feature_stats['sum'] = float(np.sum(masked * cover_weights))
                    else:
                        feature_stats['sum'] = float(masked.sum())
                if 'std' in stats:
                    feature_stats['std'] = float(masked.std())
                if 'median' in stats:
                    feature_stats['median'] = float(np.median(masked.compressed()))
                if 'majority' in stats:
                    feature_stats['majority'] = float(key_assoc_val(pixel_count, max))
                if 'minority' in stats:
                    feature_stats['minority'] = float(key_assoc_val(pixel_count, min))
                if 'unique' in stats:
                    feature_stats['unique'] = len(list(pixel_count.keys()))
                if 'range' in stats:
                    try:
                        rmin = feature_stats['min']
                    except KeyError:
                        rmin = float(masked.min())
                    try:
                        rmax = feature_stats['max']
                    except KeyError:
                        rmax = float(masked.max())
                    feature_stats['range'] = rmax - rmin

                for pctile in [s for s in stats if s.startswith('percentile_')]:
                    q = get_percentile(pctile)
                    pctarr = masked.compressed()
                    feature_stats[pctile] = np.percentile(pctarr, q)

            if 'nodata' in stats:
                featmasked = np.ma.MaskedArray(fsrc.array, mask=np.logical_not(rv_array))
                feature_stats['nodata'] = float((featmasked == fsrc.nodata).sum())

            if add_stats is not None:
                for stat_name, stat_func in add_stats.items():
                    feature_stats[stat_name] = stat_func(masked)

            if raster_out:
                feature_stats['mini_raster_array'] = masked
                feature_stats['mini_raster_affine'] = fsrc.affine
                feature_stats['mini_raster_nodata'] = fsrc.nodata

            if prefix is not None:
                prefixed_feature_stats = {}
                for key, val in feature_stats.items():
                    newkey = "{}{}".format(prefix, key)
                    prefixed_feature_stats[newkey] = val
                feature_stats = prefixed_feature_stats

            if geojson_out:
                for key, val in feature_stats.items():
                    if 'properties' not in feat:
                        feat['properties'] = {}
                    feat['properties'][key] = val
                yield feat
            else:
                yield feature_stats



def rasterize_geom(geom, shape, affine, all_touched=False):
    """
    Parameters
    ----------
    geom: GeoJSON geometry
    shape: desired shape
    affine: desired transform
    all_touched: rasterization strategy

    Returns
    -------
    ndarray: boolean
    """
    geoms = [(geom, 1)]
    rv_array = features.rasterize(
        geoms,
        out_shape=shape,
        transform=affine,
        fill=0,
        dtype='uint8',
        all_touched=all_touched)

    return rv_array.astype(bool)


# https://stackoverflow.com/questions/8090229/
#   resize-with-averaging-or-rebin-a-numpy-2d-array/8090605#8090605
def rebin_sum(a, shape, dtype):
    sh = shape[0],a.shape[0]//shape[0],shape[1],a.shape[1]//shape[1]
    return a.reshape(sh).sum(-1, dtype=dtype).sum(1, dtype=dtype)


def rasterize_pctcover_geom(geom, shape, affine, scale=None, all_touched=False):
    """
    Parameters
    ----------
    geom: GeoJSON geometry
    shape: desired shape
    affine: desired transform
    scale: scale at which to generate percent cover estimate

    Returns
    -------
    ndarray: float32
    """
    if scale is None:
        scale = 10

    min_dtype = min_scalar_type(scale ** 2)

    new_affine = Affine(affine[0]/scale, 0, affine[2],
                        0, affine[4]/scale, affine[5])

    new_shape = (shape[0] * scale, shape[1] * scale)

    rv_array = rasterize_geom(geom, new_shape, new_affine, all_touched=all_touched)

    rv_array = rebin_sum(rv_array, shape, min_dtype)

    return rv_array.astype('float32') / (scale**2)
