from pandarus.filesystem import sha256, json_exporter, get_appdirs_path, json_importer
import tempfile
import os

dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))


def test_hashing():
    assert sha256(os.path.join(dirpath, "testfile.hash")) == \
        'd2adeda32326a6576b73f9f387d75798d5bd6f0b4d385d36684fdb7d205a0ab0'


def test_json_exporting():
    with tempfile.TemporaryDirectory() as dirpath:
        new_fp = os.path.join(dirpath, 'testfile')
        fp = json_exporter({'d': [1,2,3], 'e': {'foo': 'bar'}}, new_fp, False)
        assert fp
        assert not fp.endswith(".bz2")
        assert os.path.isfile(fp)

        fp = json_exporter([1,2,3], new_fp, True)
        assert fp
        assert fp.endswith(".bz2")
        assert os.path.isfile(fp)

def test_json_importing():
    fp = os.path.join(dirpath, "json_test.json")
    assert json_importer(fp) == {'d': [1,2,3], 'e': {'foo': 'bar'}}

    fp = os.path.join(dirpath, "json_test.json.bz2")
    assert json_importer(fp) == {'d': [1,2,3], 'e': {'foo': 'bar'}}

def test_json_roundtrip():
    data = {'d': [1,2,3], 'e': {'foo': 'bar'}}

    with tempfile.TemporaryDirectory() as dirpath:
        new_fp = os.path.join(dirpath, 'testfile')

        fp = json_exporter(data, new_fp, False)
        assert json_importer(fp) == data

        fp = json_exporter(data, new_fp)
        assert json_importer(fp) == data

def test_appdirs_path():
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
