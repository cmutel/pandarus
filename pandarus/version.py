"""Utility module containing pandarus version and retrieval methods."""
import importlib.metadata
from typing import Union


def get_version_tuple() -> tuple:
    """Returns version as (major, minor, micro)."""

    def as_integer(version: str) -> Union[int, str]:
        """Tries parsing version else returns as is."""
        try:
            return int(version)
        except ValueError:  # pragma: no cover
            return version  # pragma: no cover

    return tuple(
        as_integer(v)
        for v in importlib.metadata.version("pandarus").strip().split(".")
    )


__version__ = get_version_tuple()