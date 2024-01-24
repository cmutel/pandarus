"""Test cases for the __raster_statistics__ feature."""
import json
import os
import sys

import pytest

from pandarus import raster_statistics

from .. import PATH_DEM, PATH_GRID, PATH_RANGE_RASTER, PATH_SQUARE


class ExactExtractMockModule:
    # pylint: disable=R0903
    """Mock module for exactextract."""

    @property
    def exact_extract(self) -> None:
        """Mock exact_extract function."""
        raise ImportError("No module named 'exact_extract'")


@pytest.mark.skipif(
    not pytest.importorskip("exactextract"), reason="exactextract not available"
)
def test_rasterstats_exactextract_invalid() -> None:
    """Test rasterstats using exactextract with invalid input."""
    with pytest.raises(ValueError):
        raster_statistics(PATH_GRID, "name", PATH_SQUARE)


def test_rasterstats_gen_zonal_stats_invalid(monkeypatch) -> None:
    """Test rasterstats using gen_zonal_stats with invalid input."""
    monkeypatch.setitem(sys.modules, "exactextract", ExactExtractMockModule())
    with pytest.raises(ValueError):
        raster_statistics(PATH_GRID, "name", PATH_SQUARE)


@pytest.mark.skipif(
    not pytest.importorskip("exactextract"), reason="exactextract not available"
)
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
                {
                    "min": 30.0,
                    "max": 47.0,
                    "mean": 38.29999923706055,
                    "count": 10.0,
                },
            ],
            [
                "grid cell 1",
                {
                    "min": 0.0,
                    "max": 17.0,
                    "mean": 8.300000190734863,
                    "count": 10.0,
                },
            ],
            [
                "grid cell 2",
                {
                    "min": 32.0,
                    "max": 49.0,
                    "mean": 40.70000076293945,
                    "count": 10.0,
                },
            ],
            [
                "grid cell 3",
                {
                    "min": 2.0,
                    "max": 19.0,
                    "mean": 10.699999809265137,
                    "count": 10.0,
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


@pytest.mark.skipif(
    not pytest.importorskip("exactextract"), reason="exactextract not available"
)
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


@pytest.mark.skipif(
    not pytest.importorskip("exactextract"), reason="exactextract not available"
)
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
