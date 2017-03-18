import os
import appdirs
import bz2
import codecs
import hashlib
import json


def sha256(filepath, blocksize=65536):
    """Generate SHA 256 hash for file at ``filepath``.

    ``blocksize`` (default is 65536) is block size to feed to hasher.

    Returns a ``str``."""
    hasher = hashlib.sha256()
    fo = open(filepath, 'rb')
    buf = fo.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = fo.read(blocksize)
    return hasher.hexdigest()


def json_exporter(data, filepath, compress=True):
    """Export a file to JSON. Compressed with ``bz2`` is ``compress``.

    Returns the filepath of the JSON file. Returned filepath is not necessarily ``filepath``, if ``compress`` is ``True``."""
    if compress:
        filepath += ".bz2"
        with bz2.BZ2File(filepath, "w") as f:
            f.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    else:
        with codecs.open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    return filepath


def json_importer(fp):
    """Load a JSON file. Can be compressed with ``bz2`` - if so, it should have the extension ``.bz2``.

    Returns the data in the JSON file."""
    if fp.endswith(".bz2"):
        with bz2.open(fp, "rb") as f:
            data = json.loads(f.read().decode("utf-8"))
    else:
        with open(fp, "r") as f:
            data = json.load(f)
    return data


def get_appdirs_path(subdir):
    """Get path for an ``appdirs`` directory, with subdirectory ``subdir``.

    Returns the full directory path."""
    dirpath = os.path.join(
        appdirs.user_data_dir("pandarus", "pandarus-cache"),
        subdir
    )
    if not os.path.isdir(dirpath):
        os.makedirs(dirpath)
    return os.path.abspath(dirpath)
