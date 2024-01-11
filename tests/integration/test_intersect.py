"""Test cases for the __intersect__ feature."""
import json
import os
from math import sqrt
from typing import Any, Dict, Tuple

import fiona
import numpy as np
from fiona import Feature
from shapely import MultiPolygon

from pandarus import Map, intersect
from pandarus.utils.conversion import round_to_x_significant_digits

from .. import (
    PATH_GRID,
    PATH_GRID_INTS,
    PATH_GRID_PROJ,
    PATH_LINES,
    PATH_LINES_PROJ,
    PATH_OUTSIDE,
    PATH_POINTS,
    PATH_POINTS_PROJ,
    PATH_SQUARE,
    PATH_SQUARE_PROJ,
)


def fake_intersection(
    first,
    second,
    indices=None,
    cpus=None,
    log_dir=None,
) -> Dict[Tuple[int, int], Dict[str, Any]]:
    # pylint: disable=unused-argument
    """Fake intersection function."""
    _, geom = next(Map(second).iter_latlong())
    return {(0, 0): {"measure": 42, "geom": geom}}


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


def test_intersection_polygon(tmpdir) -> None:
    """Test the intersection function with a polygon input."""
    area = 1 / 4 * (4e7 / 360) ** 2

    vector_fp, data_fp = intersect(
        PATH_OUTSIDE,
        "name",
        PATH_GRID,
        "name",
        out_dir=tmpdir,
        compress=False,
        log_dir=tmpdir,
    )
    with open(data_fp, encoding="utf-8") as f:
        data = json.load(f)

        assert len(data["data"]) == 2
        for x, y, z in data["data"]:
            assert x == "by-myself"
            assert y in ("grid cell 1", "grid cell 3")
            assert np.isclose(z, area, rtol=1e-2)

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

    with fiona.open(vector_fp) as src:
        meta = src.meta

        assert meta["driver"] == "GeoJSON"
        assert meta["schema"] == {
            "geometry": "MultiPolygon",
            "properties": dict(
                [
                    ("measure", "float"),
                    ("from_label", "str"),
                    ("id", "int"),
                    ("to_label", "str"),
                ]
            ),
        }
        assert meta["crs"] == {"init": "epsg:4326"}

        coords = MultiPolygon(
            [[[(0.5, 1.5), (0.5, 2.0), (1.0, 2.0), (1.0, 1.5), (0.5, 1.5)]]]
        )

        for feature in src:
            feature_mp = MultiPolygon(feature["geometry"]["coordinates"])
            feature_mp.equals_exact(coords, 1e-5)
            assert feature["geometry"]["type"] == "MultiPolygon"
            assert feature["properties"].keys() == {
                "measure",
                "from_label",
                "to_label",
                "id",
            }
            assert np.isclose(feature["properties"]["measure"], area, rtol=1e-2)


def test_intersection_polygon_integer_indices(tmpdir) -> None:
    """Test the intersection function with a polygon input and integer indices."""
    area = 1 / 4 * (4e7 / 360) ** 2

    vector_fp, data_fp = intersect(
        PATH_OUTSIDE,
        "name",
        PATH_GRID_INTS,
        "name",
        out_dir=tmpdir,
        compress=False,
        log_dir=tmpdir,
    )

    with open(data_fp, encoding="utf-8") as f:
        data = json.load(f)

        assert len(data["data"]) == 2
        for x, y, z in data["data"]:
            assert x == "by-myself"
            assert y in (1, 3)
            assert np.isclose(z, area, rtol=1e-2)

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

    with fiona.open(vector_fp) as src:
        meta = src.meta

        assert meta["driver"] == "GeoJSON"
        assert meta["schema"] == {
            "geometry": "MultiPolygon",
            "properties": dict(
                [
                    ("measure", "float"),
                    ("from_label", "str"),
                    ("id", "int"),
                    ("to_label", "int"),
                ]
            ),
        }
        assert meta["crs"] == {"init": "epsg:4326"}

        coords = MultiPolygon(
            [[[(0.5, 1.5), (0.5, 2.0), (1.0, 2.0), (1.0, 1.5), (0.5, 1.5)]]],
        )

        for feature in src:
            feature_mp = MultiPolygon(feature["geometry"]["coordinates"])
            feature_mp.equals_exact(coords, 1e-5)
            assert feature["geometry"]["type"] == "MultiPolygon"
            assert feature["properties"].keys() == {
                "measure",
                "from_label",
                "to_label",
                "id",
            }
            assert np.isclose(feature["properties"]["measure"], area, rtol=1e-2)


def test_intersection_polygon_projection(tmpdir) -> None:
    """Test the intersection function with a polygon input and projection."""
    area = 1 / 4 * (4e7 / 360) ** 2

    vector_fp, data_fp = intersect(
        PATH_GRID_PROJ,
        "name",
        PATH_SQUARE_PROJ,
        "name",
        out_dir=tmpdir,
        compress=False,
        log_dir=tmpdir,
    )

    with open(data_fp, encoding="utf-8") as f:
        data = json.load(f)

        assert len(data["data"]) == 4
        for x, y, z in data["data"]:
            assert x in [f"grid cell {x}" for x in range(4)]
            assert y == "single"
            assert np.isclose(z, area, rtol=1e-2)

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

    with fiona.open(vector_fp) as src:
        meta = src.meta

        assert meta["driver"] == "GeoJSON"
        assert meta["schema"] == {
            "geometry": "MultiPolygon",
            "properties": dict(
                [
                    ("measure", "float"),
                    ("from_label", "str"),
                    ("id", "int"),
                    ("to_label", "str"),
                ]
            ),
        }
        assert meta["crs"] == {"init": "epsg:4326"}

        coords = MultiPolygon(
            [[[(0.5, 1.0), (1.0, 1.0), (1.0, 0.5), (0.5, 0.5), (0.5, 1.0)]]],
        )

        for feature in src:
            feature_mp = MultiPolygon(feature["geometry"]["coordinates"])
            feature_mp.equals_exact(coords, 1e-5)
            assert feature["geometry"]["type"] == "MultiPolygon"
            assert feature["properties"].keys() == {
                "measure",
                "from_label",
                "to_label",
                "id",
            }
            assert np.isclose(feature["properties"]["measure"], area, rtol=1e-2)


def test_intersection_line(tmpdir) -> None:
    """Test the intersection function with a line input."""
    one_degree = 4e7 / 360

    vector_fp, data_fp = intersect(
        PATH_LINES,
        "name",
        PATH_GRID,
        "name",
        out_dir=tmpdir,
        compress=False,
        log_dir=tmpdir,
    )

    with open(data_fp, encoding="utf-8") as f:
        data = json.load(f)
        data_dct = {(x, y): z for x, y, z in data["data"]}

        assert len(data["data"]) == 4
        assert np.isclose(data_dct[("A", "grid cell 0")], 62000, rtol=1e-2)
        assert np.isclose(data_dct[("A", "grid cell 1")], one_degree, rtol=1e-2)
        assert np.isclose(data_dct[("A", "grid cell 3")], 50000, rtol=1e-2)
        assert np.isclose(
            data_dct[("B", "grid cell 2")], sqrt(2) * one_degree / 2, rtol=2e-2
        )

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

    with fiona.open(vector_fp) as src:
        meta = src.meta

        assert meta["driver"] == "GeoJSON"
        assert meta["schema"] == {
            "geometry": "MultiLineString",
            "properties": dict(
                [
                    ("measure", "float"),
                    ("from_label", "str"),
                    ("id", "int"),
                    ("to_label", "str"),
                ]
            ),
        }
        assert meta["crs"] == {"init": "epsg:4326"}

        coords = [
            [[(1.0, 1.5), (1.5, 1.5)]],
            [[(0.5, 1.0), (0.5, 1.5), (1.0, 1.5)]],
            [[(0.5, 0.5), (0.5, 1.0)]],
            [[(1.0, 1.0), (1.5, 0.5)]],
        ]

        for feature in src:
            assert feature["geometry"]["coordinates"] in coords
            assert feature["geometry"]["type"] == "MultiLineString"
            assert feature["properties"].keys() == {
                "measure",
                "from_label",
                "to_label",
                "id",
            }


def test_intersection_line_projection(tmpdir) -> None:
    """Test the intersection function with a line input and projection."""
    one_degree = 4e7 / 360

    vector_fp, data_fp = intersect(
        PATH_LINES_PROJ,
        "name",
        PATH_GRID_PROJ,
        "name",
        out_dir=tmpdir,
        compress=False,
        log_dir=tmpdir,
    )

    with fiona.open(vector_fp, encoding="utf-8") as vf:
        with open(data_fp, encoding="utf-8") as f:
            data = json.load(f)
            data_dct = {(x, y): z for x, y, z in data["data"]}

            assert len(data["data"]) == len(vf)
            assert np.isclose(data_dct[("A", "grid cell 0")], 62000, rtol=1e-2)
            assert np.isclose(data_dct[("A", "grid cell 1")], one_degree, rtol=1e-2)
            assert np.isclose(data_dct[("A", "grid cell 3")], 50000, rtol=1e-2)
            assert np.isclose(
                data_dct[("B", "grid cell 2")], sqrt(2) * one_degree / 2, rtol=2e-2
            )

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

    with fiona.open(vector_fp) as src:
        meta = src.meta

        assert meta["driver"] == "GeoJSON"
        assert meta["schema"] == {
            "geometry": "MultiLineString",
            "properties": dict(
                [
                    ("measure", "float"),
                    ("from_label", "str"),
                    ("id", "int"),
                    ("to_label", "str"),
                ]
            ),
        }
        assert meta["crs"] == {"init": "epsg:4326"}

        coords = [
            np.array(x)
            for x in [
                [[[1.0, 1.0], [1.0, 1.0]]],
                [[(1.0, 1.5), (1.5, 1.5)]],
                [[(0.5, 1.0), (0.5, 1.5), (1.0, 1.5)]],
                [[(0.5, 0.5), (0.5, 1.0)]],
                [[(1.0, 1.0), (1.5, 0.5)]],
            ]
        ]

        arrays = [
            round_to_x_significant_digits(np.array(x["geometry"]["coordinates"]))
            for x in src
        ]

        for array in arrays:
            print(array)
            assert any(
                np.allclose(array, obj) for obj in coords if array.shape == obj.shape
            )

        for feature in src:
            assert feature["geometry"]["type"] == "MultiLineString"
            assert feature["properties"].keys() == {
                "measure",
                "from_label",
                "to_label",
                "id",
            }


def test_intersection_point(tmpdir) -> None:
    """Test the intersection function with a point input."""
    vector_fp, data_fp = intersect(
        PATH_POINTS,
        "name",
        PATH_GRID,
        "name",
        out_dir=tmpdir,
        compress=False,
        log_dir=tmpdir,
    )

    with open(data_fp, encoding="utf-8") as f:
        data = json.load(f)

        assert sorted(data["data"]) == sorted(
            [["point 1", "grid cell 0", 1.0], ["point 2", "grid cell 3", 1.0]]
        )

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

    with fiona.open(vector_fp) as src:
        meta = src.meta

        assert meta["driver"] == "GeoJSON"
        assert meta["schema"] == {
            "geometry": "MultiPoint",
            "properties": dict(
                [
                    ("measure", "float"),
                    ("from_label", "str"),
                    ("id", "int"),
                    ("to_label", "str"),
                ]
            ),
        }
        assert meta["crs"] == {"init": "epsg:4326"}

        coords = [[(0.5, 0.5)], [(1.5, 1.5)]]

        for feature in src:
            assert feature["geometry"]["coordinates"] in coords
            assert feature["geometry"]["type"] == "MultiPoint"
            assert feature["properties"].keys() == {
                "measure",
                "from_label",
                "to_label",
                "id",
            }


def test_intersection_point_projection(tmpdir) -> None:
    """Test the intersection function with a point input and projection."""
    vector_fp, data_fp = intersect(
        PATH_POINTS_PROJ,
        "name",
        PATH_GRID_PROJ,
        "name",
        out_dir=tmpdir,
        compress=False,
        log_dir=tmpdir,
    )

    with open(data_fp, encoding="utf-8") as f:
        data = json.load(f)
        data_dct = {(x, y): z for x, y, z in data["data"]}

        assert len(data["data"]) == 2
        assert data_dct[("point 1", "grid cell 0")] == 1
        assert data_dct[("point 2", "grid cell 3")] == 1
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

    with fiona.open(vector_fp) as src:
        meta = src.meta

        assert meta["driver"] == "GeoJSON"
        assert meta["schema"] == {
            "geometry": "MultiPoint",
            "properties": dict(
                [
                    ("measure", "float"),
                    ("from_label", "str"),
                    ("id", "int"),
                    ("to_label", "str"),
                ]
            ),
        }
        assert meta["crs"] == {"init": "epsg:4326"}

        coords = [[(0.5, 0.5)], [(1.5, 1.5)]]

        for feature in src:
            print(feature)
            assert feature["geometry"]["coordinates"] in coords
            assert feature["geometry"]["type"] == "MultiPoint"
            assert feature["properties"].keys() == {
                "measure",
                "from_label",
                "to_label",
                "id",
            }
