# Pandarus

Pandarus is software for taking two geospatial data sets (either raster or vector), and calculating their combined intersected areas. Here is an example of two input maps, one in blue, the other in red:

![intersecting map](http://mutel.org/map.png)

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

For more information, see the [online documentation](https://pandarus.readthedocs.io/).

## Requirements

* [appdirs](https://pypi.python.org/pypi/appdirs)
* [docopt](http://docopt.org/)
* [fiona](https://pypi.python.org/pypi/Fiona)
* [pyprind](https://pypi.python.org/pypi/PyPrind/)
* [pyproj](https://pypi.python.org/pypi/pyproj)
* [rasterio](https://github.com/mapbox/rasterio)
* [rasterstats](https://pypi.python.org/pypi/rasterstats)
* [Rtree](https://pypi.python.org/pypi/Rtree/)
* [shapely](https://pypi.python.org/pypi/Shapely)

## Development

Pandarus is developed by [Chris Mutel](https://chris.mutel.org/) as part of his work at the [Technology Assessment Group](https://www.psi.ch/ta/technology-assessment) at the Paul Scherrer Institut and previously at the [Ecological Systems Design group](http://www.ifu.ethz.ch/ESD/index_EN) at ETH Zürich.

Source code is available on [GitHub](https://github.com/cmutel/pandarus).
