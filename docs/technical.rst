.. _technical:

Technical Reference
===================

calculate
---------

.. autoclass:: pandarus.calculate.Pandarus
    :members:

conversion
----------

.. automethod:: pandarus.conversion.check_type

.. automethod:: pandarus.conversion.convert_to_vector

filesystem
----------

.. automethod:: pandarus.filesystem.get_appdirs_path

.. automethod:: pandarus.filesystem.sha256

geometry
--------

.. automethod:: pandarus.geometry.clean

.. automethod:: pandarus.geometry.measure_area

.. automethod:: pandarus.geometry.measure_line

.. automethod:: pandarus.geometry.get_intersection

.. automethod:: pandarus.geometry.normalize_dictionary_values

.. automethod:: pandarus.geometry.recursive_geom_finder

map
---

.. autoclass:: pandarus.maps.Map
    :members:

matching
--------

.. autofunction:: pandarus.matching.intersect

.. autofunction:: pandarus.matching.intersection_calculation

projection
----------

.. automethod:: pandarus.projection.project

.. automethod:: pandarus.projection.wgs84
