"""Test cases for the __calculate__ module."""
import json
import os
import shutil

import fiona
import numpy as np
import pytest
from fiona.model import Feature

from pandarus import (
    Map,
    calculate_remaining,
    intersect,
    intersections_from_intersection,
    raster_statistics,
)
from pandarus.calculate import as_features
from pandarus.filesystem import json_importer

from . import (
    PATH_DEM,
    PATH_GRID,
    PATH_INTER_RES,
    PATH_INTER_RES_DECOMP,
    PATH_INTER_RES_MD,
    PATH_OUTSIDE,
    PATH_RANGE_RASTER,
    PATH_REMAIN_RESULT,
    PATH_SQUARE,
)


def fake_zonal_stats(vector, *_, **__) -> int:
    """Fake zonal stats function."""
    for i, _ in enumerate(Map(vector, "name")):
        yield i


def fake_intersection(first, second, indices=None, cpus=None, log_dir=None):
    # pylint: disable=unused-argument
    """Fake intersection function."""
    _, geom = next(Map(second).iter_latlong())
    return {(0, 0): {"measure": 42, "geom": geom}}


def test_rasterstats_invalid() -> None:
    """Test rasterstats with invalid input."""
    with pytest.raises(AssertionError):
        raster_statistics(PATH_GRID, "name", PATH_SQUARE)


def test_rasterstats_new_path(monkeypatch) -> None:
    """Test rasterstats with new path."""
    monkeypatch.setattr("pandarus.calculate.gen_zonal_stats", fake_zonal_stats)

    fp = raster_statistics(PATH_GRID, "name", PATH_RANGE_RASTER, compress=False)
    assert "rasterstats" in fp
    assert ".json" in fp
    assert os.path.isfile(fp)
    os.remove(fp)


def test_rasterstats(monkeypatch, tmpdir) -> None:
    """Test rasterstats with output path."""
    monkeypatch.setattr("pandarus.calculate.gen_zonal_stats", fake_zonal_stats)

    fp = os.path.join(tmpdir, "test.json")
    result = raster_statistics(
        PATH_GRID, "name", PATH_RANGE_RASTER, output=fp, compress=False
    )
    assert result == fp

    with open(fp, encoding="UTF-8") as f:
        result = json.load(f)

        expected = [
            ["grid cell 0", 0],
            ["grid cell 1", 1],
            ["grid cell 2", 2],
            ["grid cell 3", 3],
        ]

        assert result["metadata"].keys() == {"vector", "raster", "when"}
        assert result["metadata"]["vector"].keys() == {
            "field",
            "filename",
            "path",
            "sha256",
        }
        assert result["metadata"]["raster"].keys() == {
            "band",
            "filename",
            "path",
            "sha256",
        }
        assert result["data"] == expected


def test_rasterstats_overwrite_existing(monkeypatch, tmpdir) -> None:
    """Test rasterstats overwriting existing file."""
    monkeypatch.setattr("pandarus.calculate.gen_zonal_stats", fake_zonal_stats)

    fp = os.path.join(tmpdir, "test.json")

    with open(fp, "w", encoding="UTF-8") as f:
        f.write("Original content")

    result = raster_statistics(
        PATH_GRID, "name", PATH_RANGE_RASTER, output=fp, compress=False
    )

    assert result == fp

    with open(result, encoding="UTF-8") as f:
        content = f.read()
        assert content != "Original content"


def test_rasterstats_mismatched_crs(monkeypatch, tmpdir) -> None:
    """Test rasterstats with mismatched CRS."""
    monkeypatch.setattr("pandarus.calculate.gen_zonal_stats", fake_zonal_stats)

    fp = os.path.join(tmpdir, "test.json")
    with pytest.warns(UserWarning):
        raster_statistics(PATH_GRID, "name", PATH_DEM, output=fp)


def test_as_features(monkeypatch) -> None:
    """Test as_features function."""
    monkeypatch.setattr("pandarus.calculate.mapping", lambda x: x)

    expected = {
        "geometry": "Foo",
        "properties": {"id": 0, "from_label": 1, "to_label": 2, "measure": 42},
    }
    dct = {(1, 2): {"measure": 42, "geom": "Foo"}}
    assert next(as_features(dct)) == expected


def test_intersect(monkeypatch, tmpdir) -> None:
    """Test intersect function."""
    monkeypatch.setattr("pandarus.calculate.intersection_dispatcher", fake_intersection)

    vector_fp, data_fp = intersect(
        PATH_GRID,
        "name",
        PATH_SQUARE,
        "name",
        dirpath=tmpdir,
        compress=False,
        cpus=None,
    )

    with open(data_fp, encoding="UTF-8") as f:
        data = json.load(f)
        assert data["data"] == [["grid cell 0", "single", 42]]
        assert data["metadata"].keys() == {"first", "second", "when"}
        assert data["metadata"]["first"].keys() == {
            "field",
            "filename",
            "path",
            "sha256",
        }
        assert data["metadata"]["second"].keys() == {
            "field",
            "filename",
            "path",
            "sha256",
        }

        expected = {
            "id": "0",
            "type": "Feature",
            "geometry": {
                "coordinates": [
                    [(0.5, 0.5), (0.5, 1.5), (1.5, 1.5), (1.5, 0.5), (0.5, 0.5)]
                ],
                "type": "Polygon",
            },
            "properties": dict(
                [
                    ("id", 0),
                    ("to_label", "single"),
                    ("from_label", "grid cell 0"),
                    ("measure", 42.0),
                ]
            ),
        }
        assert next(iter(fiona.open(vector_fp))) == Feature.from_dict(expected)


def test_intersect_default_path(monkeypatch) -> None:
    """Test intersect function with default path."""
    monkeypatch.setattr("pandarus.calculate.intersection_dispatcher", fake_intersection)

    vector_fp, data_fp = intersect(PATH_GRID, "name", PATH_SQUARE, "name", cpus=None)

    print(vector_fp)
    print(data_fp)

    assert os.path.isfile(vector_fp)
    os.remove(vector_fp)
    assert os.path.isfile(data_fp)
    os.remove(data_fp)


def test_intersect_overwrite_existing(monkeypatch, tmpdir) -> None:
    """Test intersect function overwriting existing file."""
    monkeypatch.setattr("pandarus.calculate.intersection_dispatcher", fake_intersection)

    vector_fp, data_fp = intersect(
        PATH_GRID,
        "name",
        PATH_SQUARE,
        "name",
        dirpath=tmpdir,
        compress=False,
        cpus=None,
    )

    with open(vector_fp, "w", encoding="UTF-8") as f:
        f.write("Weeeee!")
    with open(data_fp, "w", encoding="UTF-8") as f:
        f.write("Wooooo!")

    vector_fp, data_fp = intersect(
        PATH_GRID,
        "name",
        PATH_SQUARE,
        "name",
        dirpath=tmpdir,
        compress=False,
        cpus=None,
    )

    with open(data_fp, encoding="UTF-8") as f:
        data = json.load(f)
        assert data["data"] == [["grid cell 0", "single", 42]]

    assert len(fiona.open(vector_fp)) == 1


def test_calculate_remaining(tmpdir) -> None:
    """Test calculate_remaining function."""
    # Remaining area is 0.5°  by 1°.
    # Circumference of earth is 40.000 km
    # We are close to equator
    # So area should be 1/2 * (4e7 / 360) ** 2 m2
    area = 1 / 2 * (4e7 / 360) ** 2

    data_fp = calculate_remaining(
        PATH_OUTSIDE, "name", PATH_REMAIN_RESULT, dirpath=tmpdir, compress=False
    )

    with open(data_fp, encoding="UTF-8") as f:
        data = json.load(f)

        assert data["data"][0][0] == "by-myself"
        assert np.isclose(area, data["data"][0][1], rtol=1e-2)
        assert data["metadata"].keys() == {"intersections", "source", "when"}
        assert data["metadata"]["intersections"].keys() == {
            "field",
            "filename",
            "path",
            "sha256",
        }
        assert data["metadata"]["source"].keys() == {
            "field",
            "filename",
            "path",
            "sha256",
        }


def test_calculate_remaining_copmressed_fp(tmpdir) -> None:
    """Test calculate_remaining with compressed fp."""
    data_fp = calculate_remaining(
        PATH_OUTSIDE, "name", PATH_REMAIN_RESULT, dirpath=tmpdir, compress=False
    )
    assert os.path.isfile(data_fp)


def test_calculate_remaining_default_path() -> None:
    """Test calculate_remaining with default path."""
    data_fp = calculate_remaining(
        PATH_OUTSIDE, "name", PATH_REMAIN_RESULT, compress=False
    )
    assert "intersections" in data_fp
    os.remove(data_fp)


def test_intersections_from_intersection(tmpdir) -> None:
    """Test intersections_from_intersection function."""
    fp1, fp2 = intersections_from_intersection(PATH_INTER_RES, dirpath=tmpdir)
    data = json_importer(fp1)
    result = [
        # Order from geojson file
        [0, "grid cell 3", 3097248058.207057],
        [1, "grid cell 2", 3097719886.041353],
        [2, "grid cell 0", 3097719886.0413523],
        [3, "grid cell 1", 3097248058.207055],
    ]
    assert data["data"] == result
    assert data["metadata"].keys() == {"first", "second", "when"}
    assert data["metadata"]["first"].keys() == {"field", "filename", "path", "sha256"}
    assert data["metadata"]["second"].keys() == {"field", "filename", "path", "sha256"}

    data = json_importer(fp2)
    result = [
        [0, "single", 3097248058.207057],
        [1, "single", 3097719886.041353],
        [2, "single", 3097719886.0413523],
        [3, "single", 3097248058.207055],
    ]
    assert data["data"] == result
    assert data["metadata"].keys() == {"first", "second", "when"}
    assert data["metadata"]["first"].keys() == {"field", "filename", "path", "sha256"}
    assert data["metadata"]["second"].keys() == {"field", "filename", "path", "sha256"}


def test_intersections_from_intersection_default_path() -> None:
    """Test intersections_from_intersection with default path."""
    f1, f2 = intersections_from_intersection(PATH_INTER_RES)
    assert "intersections" in f1
    os.remove(f1)
    os.remove(f2)


def test_intersections_from_intersection_specify_md(tmpdir) -> None:
    """Test intersections_from_intersection with specified metadata."""
    fp1, _ = intersections_from_intersection(
        PATH_INTER_RES, PATH_INTER_RES_MD, dirpath=tmpdir
    )
    data = json_importer(fp1)
    result = [
        # Order from geojson file
        [0, "grid cell 3", 3097248058.207057],
        [1, "grid cell 2", 3097719886.041353],
        [2, "grid cell 0", 3097719886.0413523],
        [3, "grid cell 1", 3097248058.207055],
    ]
    assert data["data"] == result

    fp1, _ = intersections_from_intersection(
        PATH_INTER_RES, PATH_INTER_RES_DECOMP, dirpath=tmpdir
    )
    data = json_importer(fp1)
    result = [
        # Order from geojson file
        [0, "grid cell 3", 3097248058.207057],
        [1, "grid cell 2", 3097719886.041353],
        [2, "grid cell 0", 3097719886.0413523],
        [3, "grid cell 1", 3097248058.207055],
    ]
    assert data["data"] == result

    shutil.copy(PATH_INTER_RES, tmpdir)
    new_fp = os.path.join(tmpdir, "intersection_result.geojson")

    fp1, _ = intersections_from_intersection(
        new_fp, PATH_INTER_RES_DECOMP, dirpath=tmpdir
    )
    data = json_importer(fp1)
    result = [
        # Order from geojson file
        [0, "grid cell 3", 3097248058.207057],
        [1, "grid cell 2", 3097719886.041353],
        [2, "grid cell 0", 3097719886.0413523],
        [3, "grid cell 1", 3097248058.207055],
    ]
    assert data["data"] == result


def test_intersections_from_intersection_not_filepath(tmpdir) -> None:
    """Test intersections_from_intersection with invalid filepath."""
    with pytest.raises(AssertionError):
        intersections_from_intersection("")

    shutil.copy(PATH_INTER_RES, tmpdir)
    new_fp = os.path.join(tmpdir, "intersection_result.geojson")
    with pytest.raises(ValueError):
        intersections_from_intersection(new_fp, dirpath=tmpdir)


def test_intersections_from_intersection_find_metadata(tmpdir) -> None:
    """Test intersections_from_intersection with metadata in same dir."""
    shutil.copy(PATH_INTER_RES, tmpdir)
    new_fp = os.path.join(tmpdir, "intersection_result.geojson")

    shutil.copy(PATH_INTER_RES_MD, tmpdir)

    fp1, _ = intersections_from_intersection(new_fp, dirpath=tmpdir)
    data = json_importer(fp1)
    result = [
        # Order from geojson file
        [0, "grid cell 3", 3097248058.207057],
        [1, "grid cell 2", 3097719886.041353],
        [2, "grid cell 0", 3097719886.0413523],
        [3, "grid cell 1", 3097248058.207055],
    ]
    assert data["data"] == result

    shutil.copy(PATH_INTER_RES, tmpdir)
    new_fp = os.path.join(tmpdir, "intersection_result.geojson")

    shutil.copy(PATH_INTER_RES_DECOMP, os.path.join(tmpdir, "intersection_result.json"))

    fp1, _ = intersections_from_intersection(new_fp, dirpath=tmpdir)
    data = json_importer(fp1)
    result = [
        # Order from geojson file
        [0, "grid cell 3", 3097248058.207057],
        [1, "grid cell 2", 3097719886.041353],
        [2, "grid cell 0", 3097719886.0413523],
        [3, "grid cell 1", 3097248058.207055],
    ]
    assert data["data"] == result
