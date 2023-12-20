"""Filesystem utilities for Pandarus."""
import bz2
import hashlib
import json
import os
from typing import Dict, List, Union

import appdirs


def sha256(filepath: str, blocksize: int = 65536) -> str:
    """Generate SHA 256 hash for file at ``filepath``.
    ``blocksize`` (default is 65536) is block size to feed to hasher.
    Returns a ``str``."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as hfile:
        for buf in iter(lambda: hfile.read(blocksize), b""):
            hasher.update(buf)
    return hasher.hexdigest()


def json_exporter(
    data: Dict[str, Union[str, int, bool, List[str]]],
    filepath: str,
    compress: bool = True,
) -> str:
    """Export a file to JSON. Compressed with ``bz2`` is ``compress``.
    Returns the filepath of the JSON file. Returned filepath is not necessarily
    ``filepath``, if ``compress`` is ``True``."""
    if compress:
        filepath += ".bz2"
        with bz2.open(filepath, "wt", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    return filepath


def json_importer(filepath: str) -> Dict[str, Union[str, int, bool, List[str]]]:
    """Load a JSON file. Can be compressed with ``bz2`` - if so, it should have the
    extension ``.bz2``.
    Returns the data in the JSON file."""
    if filepath.endswith(".bz2"):
        with bz2.open(filepath, "rt", encoding="utf-8") as f:
            data = json.load(f)
    else:
        with open(filepath, "r", encoding="UTF-8") as f:
            data = json.load(f)
    return data


def get_appdirs_path(subdir: str) -> str:
    """Get path for an ``appdirs`` directory, with subdirectory ``subdir``.
    Returns the full directory path."""
    appdir = appdirs.user_data_dir("pandarus", "pandarus-cache")
    dirpath = os.path.join(appdir, subdir)
    os.makedirs(dirpath, exist_ok=True)
    return os.path.abspath(dirpath)
