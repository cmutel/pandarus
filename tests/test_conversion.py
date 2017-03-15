from pandarus.conversion import *
from affine import Affine
from rasterio.crs import CRS
import fiona
import numpy as np
import os
import pytest
import rasterio
import tempfile

dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
grid = os.path.join(dirpath, "grid.geojson")
sixty_four = os.path.join(dirpath, "test_raster_cfs.tif")
cfs = os.path.join(dirpath, "raster_cfs_32bit.tif")
dem = os.path.join(dirpath, "DEM.tif")
invalid = os.path.join(dirpath, "invalid.txt")


def create_raster(name, array, dirpath, nodata=-1, **kwargs):
    profile = {
        'count': 1,
        'nodata': nodata,
        'dtype': 'float32',
        'width': array.shape[1],
        'height': array.shape[0],
        'affine': Affine(0.1, 0, 10, 0, -0.1, 10),
        'driver': 'GTiff',
        'compress': 'lzw',
        'crs': CRS.from_epsg(4326)
    }
    profile.update(kwargs)
    fp = os.path.join(dirpath, name)

    with rasterio.Env():
        with rasterio.open(fp, 'w', **profile) as dst:
            dst.write(array, 1)

    return fp

def test_create_raster():
    with tempfile.TemporaryDirectory() as dirpath:
        fp = create_raster(
            'foo.tif',
            np.random.random(size=(10,10)).astype(np.float32),
            dirpath
        )
        assert os.path.isfile(fp)
        assert check_type(fp) == 'raster'
        with rasterio.open(fp) as f:
            assert f.read(1).shape == (10, 10)
            assert f.read(1).dtype == np.float32

def test_check_type():
    assert check_type(grid) == 'vector'
    assert check_type(cfs) == 'raster'
    with pytest.raises(ValueError):
        check_type(invalid)

def test_convert_to_vector():
    with pytest.raises(AssertionError):
        convert_to_vector(cfs, band='1')

    with tempfile.TemporaryDirectory() as dirpath:
        out = convert_to_vector(cfs, dirpath)
        assert check_type(out) == 'vector'

        # Second time should be a no-op
        out = convert_to_vector(cfs, dirpath)
        assert check_type(out) == 'vector'

        with fiona.open(out) as src:
            meta = src.meta

            assert meta['crs'] == {'init': 'epsg:4326'}
            assert meta['schema']['properties'].keys() == {'filename', 'id', 'val'}
            assert meta['schema']['geometry'] in ('Polygon', 'MultiPolygon')

    out = convert_to_vector(cfs)
    assert check_type(out) == 'vector'
    os.remove(out)

def test_rounding():
    given = np.array([3.14159358979, 2.718281828459045235360, 325796139])
    expected = (3.142, 2.718, 3.258e8)
    for x, y in zip(round_to_x_significant_digits(given, 4), expected):
        assert x == y

def test_round_raster():
    with tempfile.TemporaryDirectory() as dirpath:
        out = os.path.join(dirpath, "test.tif")

        assert round_raster(cfs, out) == out

        with rasterio.open(out) as src:
            array = src.read(1)
            profile = src.profile

    assert profile['driver'] == 'GTiff'
    assert profile['compress'] == 'lzw'
    assert profile['count'] == 1
    assert profile['height'] == 16
    assert np.unique(array[:3, :3]).shape == (1,)
    assert np.isclose(array[0, 0], 1.47e-7)

def test_clean_raster():
    out = clean_raster(sixty_four)

    with rasterio.open(out) as src:
        array = src.read(1)
        profile = src.profile

    assert array.dtype == np.float32
    assert profile['driver'] == 'GTiff'
    assert profile['compress'] == 'lzw'
    assert profile['count'] == 1
    assert profile['nodata'] == -1
    assert not profile['tiled']
    assert 'blockysize' not in profile
    assert 'blockxsize' not in profile
    os.remove(out)

def test_clean_raster_null_nodata():
    with tempfile.TemporaryDirectory() as dirpath:
        out = os.path.join(dirpath, "test.tif")
        result = clean_raster(dem, out)

        with rasterio.open(out) as src:
            profile = src.profile

    assert profile['nodata'] is None

def test_clean_raster_filepath():
    with tempfile.TemporaryDirectory() as dirpath:
        out = os.path.join(dirpath, "test.tif")
        result = clean_raster(sixty_four, out)
        assert result == out

def test_clean_raster_64bit():
    array = np.array([[0, -1, 1e100]])

    with tempfile.TemporaryDirectory() as dirpath:
        fp = create_raster('foo.tif', array, dirpath, dtype='float64', nodata=42)

        with rasterio.open(fp) as f:
            assert f.profile['nodata'] == 42
            assert f.read(1).dtype == np.float64

        out_fp = os.path.join(dirpath, 'clean.tif')
        out = clean_raster(fp, out_fp)

        with rasterio.open(fp) as f:
            assert f.read(1).dtype == np.float64

def test_clean_raster_out_of_bounds():
    array = np.array([[0, 1.5, 42, -1e50]])
    with tempfile.TemporaryDirectory() as dirpath:
        fp = create_raster('foo.tif', array, dirpath, dtype='float64', nodata=None)
        out = clean_raster(fp)
        assert out is None

def test_clean_raster_dont_change():
    array = np.array([[0, 1.5, 42, -1e7]])
    with tempfile.TemporaryDirectory() as dirpath:
        fp = create_raster('foo.tif', array, dirpath, dtype='float64', nodata=-1e7)
        out = clean_raster(fp)
        with rasterio.open(out) as f:
            assert f.profile['nodata'] == -1e7
    os.remove(out)

def test_clean_raster_nodata():
    array = np.array([[0, 1.5, 42, -1e50]])
    with tempfile.TemporaryDirectory() as dirpath:
        fp = create_raster('foo.tif', array, dirpath, dtype='float64', nodata=-1e50)
        out = clean_raster(fp)
        with rasterio.open(out) as f:
            assert f.profile['nodata'] == -1
    os.remove(out)

    array = np.array([[0, -1., -99., 6/7]])
    with tempfile.TemporaryDirectory() as dirpath:
        fp = create_raster('foo.tif', array, dirpath, dtype='float64', nodata=-1e50)
        out = clean_raster(fp)
    with rasterio.open(out) as f:
        assert f.profile['nodata'] == -999
    os.remove(out)

    array = np.array([[0, -1., -99., -999., -9999.]])
    with tempfile.TemporaryDirectory() as dirpath:
        fp = create_raster('foo.tif', array, dirpath, dtype='float64', nodata=-1e50)
        assert clean_raster(fp) is None

def test_clean_raster_try_given_nodata():
    array = np.array([[0, -1., -99., -999., -9999]])
    with tempfile.TemporaryDirectory() as dirpath:
        fp = create_raster('foo.tif', array, dirpath, dtype='float64', nodata=-1e50)
        out = clean_raster(fp, nodata=42)
        with rasterio.open(out) as f:
            assert f.profile['nodata'] == 42
    os.remove(out)
