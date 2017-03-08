# Pandarus

[![Build Status](https://travis-ci.org/cmutel/pandarus.svg?branch=master)](https://travis-ci.org/cmutel/pandarus) [![codecov](https://codecov.io/gh/cmutel/pandarus/branch/master/graph/badge.svg)](https://codecov.io/gh/cmutel/pandarus)
 [![Docs](https://readthedocs.org/projects/pandarus/badge/?version=latest)](http://pandarus.readthedocs.io/?badge=latest)


Pandarus is a GIS software toolkit for regionalized life cycle assessment. It is designed to work with [brightway LCA framework](https://brightwaylca.org), [brightway2-regional](), and [Constructive Geometries](https://bitbucket.org/cmutel/constructive-geometries).

For more information, see the [online documentation](https://pandarus.readthedocs.io/).

Pandarus provides the following functionality:

* Match two vector datasets
* Calculate area of each spatial unit in a vector dataset using the Mollweide projection
* Normalize raster datasets, including use of compatible `nodata` values
* Vectorization of raster datasets

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
