.. _technical:

Technical Reference
===================

core
----

.. autofunction:: pandarus.core.intersect

.. autofunction:: pandarus.core.intersections_from_intersection

.. autofunction:: pandarus.core.calculate_remaining

.. autofunction:: pandarus.core.raster_statistics

.. autofunction:: pandarus.core.convert_to_vector

.. autofunction:: pandarus.core.clean_raster

.. autofunction:: pandarus.core.round_raster

model
-----

.. autoclass:: pandarus.model.Map
    :members:

errors
------

.. autoexception:: pandarus.errors.PandarusError

.. autoexception:: pandarus.errors.IncompatibleTypesError

.. autoexception:: pandarus.errors.DuplicateFieldIDError

.. autoexception:: pandarus.errors.UnknownDatasetTypeError

.. autoexception:: pandarus.errors.MalformedMetaError

.. autoexception:: pandarus.errors.PoolTaskError

helpers
-------

.. autoclass:: pandarus.helpers.ExtractionHelper
    :members:

conversion
----------

.. autofunction:: pandarus.utils.conversion.check_dataset_type

.. autofunction:: pandarus.utils.conversion.dict_to_features

.. autofunction:: pandarus.utils.conversion.round_to_x_significant_digits

geometry
--------

.. autofunction:: pandarus.utils.geometry.clean_geom

.. autofunction:: pandarus.utils.geometry.recursive_geom_finder

.. autofunction:: pandarus.utils.geometry.get_intersection

.. autofunction:: pandarus.utils.geometry.get_geom_kind

.. autofunction:: pandarus.utils.geometry.get_geom_measure

.. autofunction:: pandarus.utils.geometry.get_geom_remaining_measure

io
--

.. autofunction:: pandarus.utils.io.sha256_file

.. autofunction:: pandarus.utils.io.get_appdirs_path

.. autofunction:: pandarus.utils.io.export_json

.. autofunction:: pandarus.utils.io.import_json

logger
------

.. autofunction:: pandarus.utils.logger.logger_init

multiprocess
------------

.. autofunction:: pandarus.utils.multiprocess.intersection_dispatcher

.. autofunction:: pandarus.utils.multiprocess.intersection_worker

projection
----------

.. autofunction:: pandarus.utils.projection.project_geom

.. autofunction:: pandarus.utils.projection.wgs84
