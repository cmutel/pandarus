"""Pandarus error classes."""


class PandarusError(Exception):
    """Base class for Pandarus exceptions"""


class IncompatibleTypesError(Exception):
    """Geometry comparison across geometry types is meaningless"""


class DuplicateFieldIDError(Exception):
    """Field ID value is duplicated and should be unique"""
