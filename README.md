# Pandarus

[![Build Status](https://travis-ci.org/cmutel/pandarus.svg?branch=master)](https://travis-ci.org/cmutel/pandarus) [![codecov](https://codecov.io/gh/cmutel/pandarus/branch/master/graph/badge.svg)](https://codecov.io/gh/cmutel/pandarus) [![Docs](https://readthedocs.org/projects/pandarus/badge/?version=latest)](http://pandarus.readthedocs.io/?badge=latest) [![status](http://joss.theoj.org/papers/99cd637f2eac0ffaba0be09fd3f0d75c/status.svg)](http://joss.theoj.org/papers/99cd637f2eac0ffaba0be09fd3f0d75c)

Pandarus is a GIS software toolkit for regionalized life cycle assessment. It is designed to work with [brightway LCA framework](https://brightwaylca.org), [brightway2-regional](https://bitbucket.org/cmutel/brightway2-regional), and [Constructive Geometries](https://bitbucket.org/cmutel/constructive-geometries).

For more information, including installation instructions, see the [online documentation](https://pandarus.readthedocs.io/), including a [usage example](https://github.com/cmutel/pandarus/blob/master/docs/usage_example.ipynb). Pandarus is only compatible with >= Python 3.8.

Pandarus provides the following functionality:

* [Overlay two vector datasets](https://pandarus.readthedocs.io/#intersecting-two-vector-datasets), calculating the areas of each combination of features using the Mollweide projection.
* Calculate the [area of the geometric difference](https://pandarus.readthedocs.io/#calculating-area-outside-of-intersections) (the areas present in one input file but not in the other) of one vector dataset with another vector dataset.
* [Calculate statistics](https://pandarus.readthedocs.io/#calculating-raster-statistics-against-a-vector-dataset) such as min, mean, and max when overlaying a raster dataset with a vector dataset.
* [Normalize raster datasets](https://pandarus.readthedocs.io/#manipulating-raster-files), including use of compatible `nodata` values
* Vectorization of raster datasets

## Requirements

* [appdirs](https://pypi.python.org/pypi/appdirs)
* [exactextract](https://github.com/isciences/exactextract.git)
* [fiona](https://pypi.python.org/pypi/Fiona)
* [numpy](http://www.numpy.org/)
* [pyproj](https://pypi.python.org/pypi/pyproj)
* [rasterio](https://github.com/mapbox/rasterio)
* [rasterstats](https://pypi.python.org/pypi/rasterstats)
* [Rtree](https://pypi.python.org/pypi/Rtree/)
* [shapely](https://pypi.python.org/pypi/Shapely)

## Development

Pandarus is developed by [Chris Mutel](https://chris.mutel.org/) as part of his work at the [Technology Assessment Group](https://www.psi.ch/ta/technology-assessment) at the Paul Scherrer Institut and previously at the [Ecological Systems Design group](http://www.ifu.ethz.ch/ESD/index_EN) at ETH Zürich.

Source code is available on [GitHub](https://github.com/cmutel/pandarus).
