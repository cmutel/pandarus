========
Pandarus
========

Pandarus is software for taking two geospatial data sets (either raster or vector), and calculating their combined intersected areas. Here is an example of two input maps, one in blue, the other in red:

.. image:: http://mutel.org/map.png
   :width: 457
   :height: 454

Pandarus would calculate the intersected areas of each spatial unit of both maps, and output the following:

.. code-block:: python

    {(0, 0): 0.25,
     (0, 1): 0.25,
     (0, 3): 0.25,
     (0, 4): 0.25,
     (1, 1): 0.25,
     (1, 2): 0.25,
     (1, 4): 0.25,
     (1, 5): 0.25,
     (2, 3): 0.25,
     (2, 4): 0.25,
     (2, 6): 0.25,
     (2, 7): 0.25,
     (3, 4): 0.25,
     (3, 5): 0.25,
     (3, 7): 0.25,
     (3, 8): 0.25}

For more information, see the `online documentation <http://pandarus.readthedocs.io/>`_.

Requirements
============

    * `docopt <http://docopt.org/>`__
    * `eight <https://pypi.python.org/pypi/eight>`__
    * `fiona <http://toblerity.org/fiona/index.html>`__
    * `GDAL <https://pypi.python.org/pypi/GDAL/>`__
    * `pyprind <https://pypi.python.org/pypi/PyPrind/>`__
    * `pyproj <https://code.google.com/p/pyproj/>`__
    * `Rtree <http://toblerity.org/rtree/>`__
    * `shapely <https://pypi.python.org/pypi/Shapely>`__

Development
===========

Pandarus is developed by `Chris Mutel <http://chris.mutel.org/>`_ as part of his work at the `Technology Assessment Group <https://www.psi.ch/ta/technology-assessment>`__ at the Paul Scherrer Institut and previously at the `Ecological Systems Design group <http://www.ifu.ethz.ch/ESD/index_EN>`_ at ETH Zürich.

Source code is available on `bitbucket <https://bitbucket.org/cmutel/pandarus>`_.
