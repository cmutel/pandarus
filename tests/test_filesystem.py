"""Test cases for the __filesystem__ module."""
import os

from pandarus.filesystem import get_appdirs_path, json_exporter, json_importer, sha256

from . import PATH_DATA


def test_hashing() -> None:
    """Test hashing function."""
    if os.name == "nt":
        expected = "703734a71a2252ed9cabfeb5ddc4aeeb6c96becb720382f1edca0c87472bacef"
    else:
        expected = "d2adeda32326a6576b73f9f387d75798d5bd6f0b4d385d36684fdb7d205a0ab0"

    assert sha256(os.path.join(PATH_DATA, "testfile.hash")) == expected


def test_json_exporting_uncompressed(tmpdir) -> None:
    """Test exporting to JSON uncompressed."""
    new_fp = os.path.join(tmpdir, "testfile")
    fp = json_exporter({"d": [1, 2, 3], "e": {"foo": "bar"}}, new_fp, compress=False)
    assert fp
    assert not fp.endswith(".bz2")
    assert os.path.isfile(fp)


def test_json_exporting_compressed(tmpdir) -> None:
    """Test exporting to JSON compressed."""
    new_fp = os.path.join(tmpdir, "testfile")
    fp = json_exporter([1, 2, 3], new_fp, True)
    assert fp
    assert fp.endswith(".bz2")
    assert os.path.isfile(fp)


def test_json_importing_uncompressed() -> None:
    """Test importing JSON uncompressed."""
    fp = os.path.join(PATH_DATA, "json_test.json")
    assert json_importer(fp) == {"d": [1, 2, 3], "e": {"foo": "bar"}}


def test_json_importing_compressed() -> None:
    """Test importing JSON compressed."""
    fp = os.path.join(PATH_DATA, "json_test.json.bz2")
    assert json_importer(fp) == {"d": [1, 2, 3], "e": {"foo": "bar"}}


def test_json_roundtrip_uncompressed(tmpdir) -> None:
    """Test roundtrip of exporting and import of JSON uncompressed."""
    data = {"d": [1, 2, 3], "e": {"foo": "bar"}}
    new_fp = os.path.join(tmpdir, "testfile")

    fp = json_exporter(data, new_fp, compress=False)
    assert json_importer(fp) == data


def test_json_roundtrip_compressed(tmpdir) -> None:
    """Test roundtrip of exporting and import of JSON compressed."""
    data = {"d": [1, 2, 3], "e": {"foo": "bar"}}
    new_fp = os.path.join(tmpdir, "testfile")

    fp = json_exporter(data, new_fp)
    assert json_importer(fp) == data


def test_appdirs_path() -> None:
    """Test getting appdirs path."""
    dp = get_appdirs_path("test-dir")
    assert os.path.exists(dp)
    assert os.path.isdir(dp)
    assert "test-dir" in dp
    assert "pandarus" in dp

    os.rmdir(dp)
    assert not os.path.exists(dp)
    dp = get_appdirs_path("test-dir")
    assert os.path.exists(dp)
    os.rmdir(dp)
