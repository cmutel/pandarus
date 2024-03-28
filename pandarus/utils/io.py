"""IO utilities for Pandarus."""

import bz2
import hashlib
import json
import os
from typing import Any, Dict

import appdirs


def sha256_file(filepath: str, blocksize: int = 65536) -> str:
    """Generate SHA 256 hash for file at ``filepath``.
    ``blocksize`` (default is 65536) is block size to feed to hasher.
    Returns a ``str``."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as hfile:
        for buf in iter(lambda: hfile.read(blocksize), b""):
            hasher.update(buf)
    return hasher.hexdigest()


def export_json(
    data: Dict[str, Any],
    filepath: str,
    compress: bool = True,
) -> str:
    """Export a file to JSON. Compressed with ``bz2`` if ``compress`` is ``True``.
    Returns the filepath of the JSON file. Returned filepath is not necessarily
    ``filepath``, if ``compress`` is ``True``."""
    filepath = filepath + ".bz2" if compress else filepath
    with (
        bz2.open(filepath, "wt", encoding="utf-8")
        if compress
        else open(filepath, "w", encoding="utf-8")
    ) as f:
        json.dump(data, f, ensure_ascii=False)
    return filepath


def import_json(filepath: str) -> Dict[str, Any]:
    """Load a JSON file. Can be compressed with ``bz2`` - if so, it should have the
    extension ``.bz2``.
    Returns the data in the JSON file."""
    with (
        bz2.open(filepath, "rt", encoding="utf-8")
        if filepath.endswith(".bz2")
        else open(filepath, "r", encoding="UTF-8")
    ) as f:
        data = json.load(f)
    return data


def get_appdirs_path(subdir: str) -> str:
    """Get path for an ``appdirs`` directory, with subdirectory ``subdir``.
    Returns the full directory path."""
    appdir = appdirs.user_data_dir("pandarus", "pandarus-cache")
    dirpath = os.path.join(appdir, subdir)
    os.makedirs(dirpath, exist_ok=True)
    return dirpath
