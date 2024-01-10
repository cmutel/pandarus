"""Test cases for the __calculate__ module."""
import json
import os
import shutil
import sys

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
from pandarus.utils.io import import_json

from ... import (
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


# pylint: disable=R0903
class ExactExtractMockModule:
    """Mock module for exactextract."""

    @property
    def exact_extract(self):
        """Mock exact_extract function."""
        raise ImportError("No module named 'exact_extract'")


def fake_intersection(first, second, indices=None, cpus=None, log_dir=None):
    # pylint: disable=unused-argument
    """Fake intersection function."""
    _, geom = next(Map(second).iter_latlong())
    return {(0, 0): {"measure": 42, "geom": geom}}


def test_rasterstats_exactextract_invalid() -> None:
    """Test rasterstats using exactextract with invalid input."""
    with pytest.raises(ValueError):
        raster_statistics(PATH_GRID, "name", PATH_SQUARE)


def test_rasterstats_gen_zonal_stats_invalid(monkeypatch) -> None:
    """Test rasterstats using gen_zonal_stats with invalid input."""
    monkeypatch.setitem(sys.modules, "exactextract", ExactExtractMockModule())
    with pytest.raises(ValueError):
        raster_statistics(PATH_GRID, "name", PATH_SQUARE)


def test_rasterstats_exactextract_new_path() -> None:
    """Test rasterstats using exactextract with new path."""
    fp = raster_statistics(PATH_GRID, "name", PATH_RANGE_RASTER, compress=False)
    assert "rasterstats" in fp
    assert ".json" in fp
    assert os.path.isfile(fp)
    os.remove(fp)


def test_rasterstats_gen_zonal_stats_new_path(monkeypatch) -> None:
    """Test rasterstats using gen_zonal_stats with new path."""
    monkeypatch.setitem(sys.modules, "exactextract", ExactExtractMockModule())
    with pytest.warns(UserWarning):
        fp = raster_statistics(PATH_GRID, "name", PATH_RANGE_RASTER, compress=False)
        assert "rasterstats" in fp
        assert ".json" in fp
        assert os.path.isfile(fp)
        os.remove(fp)


def test_rasterstats_exactextract(tmpdir) -> None:
    """Test rasterstats using exactextract with output path."""
    fp = os.path.join(tmpdir, "test.json")
    result = raster_statistics(
        PATH_GRID, "name", PATH_RANGE_RASTER, output_file_path=fp, compress=False
    )
    assert result == fp

    with open(fp, encoding="UTF-8") as f:
        result = json.load(f)

        expected = [
            [
                "grid cell 0",
                [
                    {
                        "properties": {
                            "min": 30.0,
                            "max": 47.0,
                            "mean": 38.29999923706055,
                            "count": 10.0,
                        }
                    },
                ],
            ],
            [
                "grid cell 1",
                [
                    {
                        "properties": {
                            "min": 0.0,
                            "max": 17.0,
                            "mean": 8.300000190734863,
                            "count": 10.0,
                        }
                    },
                ],
            ],
            [
                "grid cell 2",
                [
                    {
                        "properties": {
                            "min": 32.0,
                            "max": 49.0,
                            "mean": 40.70000076293945,
                            "count": 10.0,
                        }
                    },
                ],
            ],
            [
                "grid cell 3",
                [
                    {
                        "properties": {
                            "min": 2.0,
                            "max": 19.0,
                            "mean": 10.699999809265137,
                            "count": 10.0,
                        }
                    },
                ],
            ],
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


def test_rasterstats_gen_zonal_stats(tmpdir, monkeypatch) -> None:
    """Test rasterstats using gen_zonal_stats with output path."""
    monkeypatch.setitem(sys.modules, "exactextract", ExactExtractMockModule())

    with pytest.warns(UserWarning):
        fp = os.path.join(tmpdir, "test.json")
        result = raster_statistics(
            PATH_GRID, "name", PATH_RANGE_RASTER, output_file_path=fp, compress=False
        )
        assert result == fp

        with open(fp, encoding="UTF-8") as f:
            result = json.load(f)

            expected = [
                [
                    "grid cell 0",
                    {
                        "min": 30.0,
                        "max": 47.0,
                        "mean": 38.5,
                        "count": 12,
                    },
                ],
                [
                    "grid cell 1",
                    {
                        "min": 0.0,
                        "max": 17.0,
                        "mean": 8.5,
                        "count": 12,
                    },
                ],
                [
                    "grid cell 2",
                    {
                        "min": 33.0,
                        "max": 49.0,
                        "mean": 41.0,
                        "count": 8,
                    },
                ],
                [
                    "grid cell 3",
                    {
                        "min": 3.0,
                        "max": 19.0,
                        "mean": 11.0,
                        "count": 8,
                    },
                ],
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


def test_rasterstats_exactextract_overwrite_existing(tmpdir) -> None:
    """Test rasterstats using exactextract overwriting existing file."""
    fp = os.path.join(tmpdir, "test.json")

    with open(fp, "w", encoding="UTF-8") as f:
        f.write("Original content")

    result = raster_statistics(
        PATH_GRID, "name", PATH_RANGE_RASTER, output_file_path=fp, compress=False
    )

    assert result == fp

    with open(result, encoding="UTF-8") as f:
        content = f.read()
        assert content != "Original content"


def test_rasterstats_gen_zonal_stats_overwrite_existing(tmpdir, monkeypatch) -> None:
    """Test rasterstats using gen_zonal_stats overwriting existing file."""
    monkeypatch.setitem(sys.modules, "exactextract", ExactExtractMockModule())

    with pytest.warns(UserWarning):
        fp = os.path.join(tmpdir, "test.json")

        with open(fp, "w", encoding="UTF-8") as f:
            f.write("Original content")

        result = raster_statistics(
            PATH_GRID, "name", PATH_RANGE_RASTER, output_file_path=fp, compress=False
        )

        assert result == fp

        with open(result, encoding="UTF-8") as f:
            content = f.read()
            assert content != "Original content"


def test_rasterstats_exactextract_mismatched_crs(tmpdir) -> None:
    """Test rasterstats using exactextract with mismatched CRS."""
    fp = os.path.join(tmpdir, "test.json")
    with pytest.warns(UserWarning):
        raster_statistics(PATH_GRID, "name", PATH_DEM, output_file_path=fp)


def test_rasterstats_gen_zonal_stats_mismatched_crs(tmpdir, monkeypatch) -> None:
    """Test rasterstats using gen_zonal_stats with mismatched CRS."""
    monkeypatch.setitem(sys.modules, "exactextract", ExactExtractMockModule())
    fp = os.path.join(tmpdir, "test.json")
    with pytest.warns(UserWarning):
        raster_statistics(PATH_GRID, "name", PATH_DEM, output_file_path=fp)


def test_intersect(monkeypatch, tmpdir) -> None:
    """Test intersect function."""
    monkeypatch.setattr("pandarus.core.intersection_dispatcher", fake_intersection)

    vector_fp, data_fp = intersect(
        PATH_GRID,
        "name",
        PATH_SQUARE,
        "name",
        out_dir=tmpdir,
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
    monkeypatch.setattr(
        "pandarus.utils.multiprocess.intersection_dispatcher", fake_intersection
    )

    vector_fp, data_fp = intersect(PATH_GRID, "name", PATH_SQUARE, "name", cpus=None)

    print(vector_fp)
    print(data_fp)

    assert os.path.isfile(vector_fp)
    os.remove(vector_fp)
    assert os.path.isfile(data_fp)
    os.remove(data_fp)


def test_intersect_overwrite_existing(monkeypatch, tmpdir) -> None:
    """Test intersect function overwriting existing file."""
    monkeypatch.setattr("pandarus.core.intersection_dispatcher", fake_intersection)

    vector_fp, data_fp = intersect(
        PATH_GRID,
        "name",
        PATH_SQUARE,
        "name",
        out_dir=tmpdir,
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
        out_dir=tmpdir,
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
        PATH_OUTSIDE, "name", PATH_REMAIN_RESULT, out_dir=tmpdir, compress=False
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
        PATH_OUTSIDE, "name", PATH_REMAIN_RESULT, out_dir=tmpdir, compress=False
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
    fp1, fp2 = intersections_from_intersection(PATH_INTER_RES, out_dir=tmpdir)
    data = import_json(fp1)
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

    data = import_json(fp2)
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
        PATH_INTER_RES, PATH_INTER_RES_MD, out_dir=tmpdir
    )
    data = import_json(fp1)
    result = [
        # Order from geojson file
        [0, "grid cell 3", 3097248058.207057],
        [1, "grid cell 2", 3097719886.041353],
        [2, "grid cell 0", 3097719886.0413523],
        [3, "grid cell 1", 3097248058.207055],
    ]
    assert data["data"] == result

    fp1, _ = intersections_from_intersection(
        PATH_INTER_RES, PATH_INTER_RES_DECOMP, out_dir=tmpdir
    )
    data = import_json(fp1)
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
        new_fp, PATH_INTER_RES_DECOMP, out_dir=tmpdir
    )
    data = import_json(fp1)
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
    with pytest.raises(FileNotFoundError):
        intersections_from_intersection("")

    shutil.copy(PATH_INTER_RES, tmpdir)
    new_fp = os.path.join(tmpdir, "intersection_result.geojson")
    with pytest.raises(ValueError):
        intersections_from_intersection(new_fp, out_dir=tmpdir)


def test_intersections_from_intersection_find_metadata(tmpdir) -> None:
    """Test intersections_from_intersection with metadata in same dir."""
    shutil.copy(PATH_INTER_RES, tmpdir)
    new_fp = os.path.join(tmpdir, "intersection_result.geojson")

    shutil.copy(PATH_INTER_RES_MD, tmpdir)

    fp1, _ = intersections_from_intersection(new_fp, out_dir=tmpdir)
    data = import_json(fp1)
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

    fp1, _ = intersections_from_intersection(new_fp, out_dir=tmpdir)
    data = import_json(fp1)
    result = [
        # Order from geojson file
        [0, "grid cell 3", 3097248058.207057],
        [1, "grid cell 2", 3097719886.041353],
        [2, "grid cell 0", 3097719886.0413523],
        [3, "grid cell 1", 3097248058.207055],
    ]
    assert data["data"] == result
