"""Conversion utilities for Pandarus."""
from typing import Any, Dict, Generator, List

import fiona
import numpy as np
import rasterio
from fiona.errors import DataIOError, DriverError
from numpy.typing import NDArray
from shapely.geometry import mapping

from ..errors import MalformedMetaError, UnknownDatasetTypeError


def dict_to_features(
    data_dict: Dict[str, Dict[str, Any]]
) -> Generator[Dict[str, Any], None, None]:
    """Convert a dictionary of dictionaries to a generator of GeoJSON features."""
    for index, (key, row) in enumerate(data_dict.items()):
        gj = {
            "geometry": mapping(row["geom"]),
            "properties": {
                "id": index,
                "from_label": key[0],
                "to_label": key[1],
                "measure": row["measure"],
            },
        }
        yield gj


def check_dataset_type(file_path: str) -> str:
    """Determine if a GIS dataset is raster or vector.

    ``file_path`` is a file path of a GIS dataset file.

    Returns ``'vector'`` or ``'raster'``.

    Raises:
    * ``MalformedMetaError`` if the file is a vector but the geometry type is unknown.
    * ``UnknownDatasetTypeError`` if the file can't be opened with fiona or rasterio."""
    try:
        with fiona.open(file_path) as ds:
            if ds.meta["schema"]["geometry"] != "Unknown":
                return "vector"
            raise MalformedMetaError
    except (DataIOError, DriverError):
        try:
            with rasterio.open(file_path) as ds:
                return "raster"
        except Exception as exc:
            raise UnknownDatasetTypeError(file_path) from exc


def round_to_x_significant_digits(array: NDArray, x: int = 3) -> NDArray:
    """Round array to a certain number of significant digits"""
    num_digits = x - np.floor(np.log10(np.abs(array))).astype(int) - 1
    num_digits[array == 0] = 0
    for value in np.unique(num_digits):
        indices = np.where(num_digits == value)
        array[indices] = np.round(array[indices], value)
    return array


def unwrap_exact_extract_stats(results: List[List[Dict]]) -> List[Dict[str, float]]:
    """The default return format from `exact_extract` is
    `[{'properties': {'foo': 'bar'}}]`. We need `{'foo': 'bar'}`."""
    return [result[0]["properties"] for result in results]
