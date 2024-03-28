"""Fixtures for __pandarus__."""

from typing import Any, Callable, Dict

import pytest
from shapely.geometry import MultiPolygon


@pytest.fixture
def equal_intersections() -> Callable[[Dict, Dict], bool]:
    """Return a function that checks if two intersections are equal."""

    def _equal_intersections(intersections1: Dict, intersections2: Dict) -> bool:
        for intersection1, intersection2 in zip(
            intersections1.values(), intersections2.values()
        ):
            intersection1_shape = MultiPolygon(intersection1["geom"]["coordinates"])
            intersection2_shape = MultiPolygon(intersection2["geom"]["coordinates"])
            if not intersection1_shape.equals(intersection2_shape):
                return False
        return True

    return _equal_intersections


@pytest.fixture
def remaining_schema() -> Dict[str, Any]:
    """Return a function that returns the schema of the remaining file."""
    return {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "measure": 3096540361.3696108,
                    "to_label": "grid cell 1",
                    "from_label": "by-myself",
                    "id": 0,
                },
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [
                                [0.5, 1.5],
                                [0.5, 2.0],
                                [1.0, 2.0],
                                [1.0, 1.5],
                                [0.5, 1.5],
                            ]
                        ]
                    ],
                },
            },
        ],
    }
