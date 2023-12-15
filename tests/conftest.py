"""Fixtures for __pandarus__."""
from typing import Dict

import pytest
from shapely.geometry import MultiPolygon


@pytest.fixture
def equal_intersections():
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
