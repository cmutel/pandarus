.. _technical:

Technical Reference
===================

calculate
---------

.. autofunction:: pandarus.calculate.raster_statistics

.. autofunction:: pandarus.calculate.intersect

.. autofunction:: pandarus.calculate.intersections_from_intersection

.. autofunction:: pandarus.calculate.calculate_remaining

conversion
----------

.. autofunction:: pandarus.conversion.check_type

.. autofunction:: pandarus.conversion.convert_to_vector

.. autofunction:: pandarus.conversion.clean_raster

.. autofunction:: pandarus.conversion.round_raster

filesystem
----------

.. autofunction:: pandarus.filesystem.get_appdirs_path

.. autofunction:: pandarus.filesystem.sha256

.. autofunction:: pandarus.filesystem.json_exporter

.. autofunction:: pandarus.filesystem.json_importer

geometry
--------

.. autofunction:: pandarus.geometry.clean

.. autofunction:: pandarus.geometry.recursive_geom_finder

.. autofunction:: pandarus.geometry.get_intersection

.. autofunction:: pandarus.geometry.get_measure

.. autofunction:: pandarus.geometry.get_remaining

map
---

.. autoclass:: pandarus.maps.Map
    :members:

intersections
-------------

.. autofunction:: pandarus.intersections.intersection_dispatcher

.. autofunction:: pandarus.intersections.intersection_worker

projection
----------

.. automethod:: pandarus.projection.project

.. automethod:: pandarus.projection.wgs84
