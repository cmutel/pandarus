"""Test cases for the __filesystem__ module."""

import os

from pandarus.utils.io import export_json, get_appdirs_path, import_json, sha256_file

from ... import PATH_DATA


def test_hashing() -> None:
    """Test hashing function."""
    if os.name == "nt":
        expected = "703734a71a2252ed9cabfeb5ddc4aeeb6c96becb720382f1edca0c87472bacef"
    else:
        expected = "d2adeda32326a6576b73f9f387d75798d5bd6f0b4d385d36684fdb7d205a0ab0"

    assert sha256_file(os.path.join(PATH_DATA, "testfile.hash")) == expected


def test_json_exporting_uncompressed(tmpdir) -> None:
    """Test exporting to JSON uncompressed."""
    new_file_path = os.path.join(tmpdir, "testfile")
    file_path = export_json(
        {"d": [1, 2, 3], "e": {"foo": "bar"}}, new_file_path, compress=False
    )
    assert file_path
    assert not file_path.endswith(".bz2")
    assert os.path.isfile(file_path)


def test_json_exporting_compressed(tmpdir) -> None:
    """Test exporting to JSON compressed."""
    new_file_path = os.path.join(tmpdir, "testfile")
    file_path = export_json([1, 2, 3], new_file_path, True)
    assert file_path
    assert file_path.endswith(".bz2")
    assert os.path.isfile(file_path)


def test_json_importing_uncompressed() -> None:
    """Test importing JSON uncompressed."""
    file_path = os.path.join(PATH_DATA, "json_test.json")
    assert import_json(file_path) == {"d": [1, 2, 3], "e": {"foo": "bar"}}


def test_json_importing_compressed() -> None:
    """Test importing JSON compressed."""
    file_path = os.path.join(PATH_DATA, "json_test.json.bz2")
    assert import_json(file_path) == {"d": [1, 2, 3], "e": {"foo": "bar"}}


def test_json_roundtrip_uncompressed(tmpdir) -> None:
    """Test roundtrip of exporting and import of JSON uncompressed."""
    data = {"d": [1, 2, 3], "e": {"foo": "bar"}}
    new_file_path = os.path.join(tmpdir, "testfile")

    file_path = export_json(data, new_file_path, compress=False)
    assert import_json(file_path) == data


def test_json_roundtrip_compressed(tmpdir) -> None:
    """Test roundtrip of exporting and import of JSON compressed."""
    data = {"d": [1, 2, 3], "e": {"foo": "bar"}}
    new_file_path = os.path.join(tmpdir, "testfile")

    file_path = export_json(data, new_file_path)
    assert import_json(file_path) == data


def test_appdirs_path() -> None:
    """Test getting appdirs path."""
    dir_path = get_appdirs_path("test-dir")
    assert os.path.exists(dir_path)
    assert os.path.isdir(dir_path)
    assert "test-dir" in dir_path
    assert "pandarus" in dir_path

    os.rmdir(dir_path)
    assert not os.path.exists(dir_path)
