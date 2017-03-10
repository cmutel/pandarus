Pandarus
========

Pandarus is a GIS software toolkit for regionalized life cycle assessment. It is designed to work with `brightway LCA framework <https://brightwaylca.org>`__, `brightway2-regional <https://bitbucket.org/cmutel/brightway2-regional>`__, and `Constructive Geometries <https://bitbucket.org/cmutel/constructive-geometries>`__. A separate library, `pandarus-remote <https://bitbucket.org/cmutel/pandarus_remote>`__, provides a web API to run Pandarus on a server.

Why Pandarus?
-------------

The software matches two different maps against each other, and `Pandarus was a bit of a matchmaker himself <http://en.wikipedia.org/wiki/Pandarus>`_. Plus, ancient names are 200% more science-y.

Calculating areas
-----------------

Because Pandarus was designed for global data sets, the `Mollweide projection <http://en.wikipedia.org/wiki/Mollweide_projection>`_ is used as the default equal-area projection for calculating areas (in square meters). Although no projection is perfect, the Mollweide has been found to be a reasonable compromise (e.g. [1]_)

.. [1] Usery, E.L., and Seong, J.C., (2000) `A comparison of equal-area map projections for regional and global raster data <http://cegis.usgs.gov/projection/pdf/nmdrs.usery.prn.pdf>`_

Capabilities
============

Matching two vector datasets
----------------------------

Pandarus can match two vector datasets, generating a new vector dataset which includes each possible combination of a spatial unit in the first dataset with a spatial unit in the second dataset. This functionality is used in calculating which characterization factors to apply to an emission in a given region.

In addition to

.. image:: images/map.png
    :align: center

.. automethod:: pandarus.calculate.Pandarus.intersect

Calculating the areas of spatial units
--------------------------------------

Pandarus can calculate the area of each spatial unit in a vector dataset. This functionality is used for normalization by total area when matching characterization factors to emissions in a given region.

.. image:: images/map.png
    :align: center

.. automethod:: pandarus.calculate.Pandarus.areas

Calculating raster statistics against a vector dataset
------------------------------------------------------

Pandarus can calculate mask a raster with each feature from a vector dataset, and calculate the min, max, and average values from the intersected raster cells. This functionality is provided by a patched version of `rasterstats <https://github.com/perrygeo/python-rasterstats>`__.

.. image:: images/map.png
    :align: center

.. automethod:: pandarus.calculate.Pandarus.rasterstats

Cleaning and vectorizing raster files
-------------------------------------

Pandarus provides some utility functions to help manage raster files, which are not always provided with rich and correct metadata.

.. autofunction:: pandarus.clean_raster

.. autofunction:: pandarus.round_raster

.. autofunction:: pandarus.convert_to_vector

Installation
============

Pandarus can be installed directly from `PyPi <https://pypi.python.org/pypi>`_ using `pip` or `easy_install`, e.g.

.. code-block:: bash

    pip install pandarus

However, it is easy to run into errors if libraries are compiled against different versions of GDAL. One way to get an installation that is almost guaranteed is to use `Conda <https://conda.io/miniconda.html>`__:

.. code-block:: bash

    conda config --add channels conda-forge cmutel
    conda create -n pandarus python=3.5
    source activate pandarus
    conda install pandarus

Pandarus source code is on `GitHub <https://github.com/cmutel/pandarus>`__.

Requirements
------------

Pandarus uses the following libraries:

    * `appdirs <https://pypi.python.org/pypi/appdirs>`__
    * `fiona <http://toblerity.org/fiona/index.html>`__
    * `pyprind <https://pypi.python.org/pypi/PyPrind>`__
    * `pyproj <https://code.google.com/p/pyproj/>`__
    * `Rtree <http://toblerity.org/rtree/>`__
    * `rasterio <https://github.com/mapbox/rasterio>`__
    * `rasterstats <https://pypi.python.org/pypi/rasterstats>`__
    * `shapely <https://pypi.python.org/pypi/Shapely>`__

Technical Reference
===================

.. toctree::
   :maxdepth: 2

   technical
