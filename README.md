# Pandarus

[![PyPI](https://img.shields.io/pypi/v/pandarus.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/pandarus.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/pandarus)][pypi status]
[![License](https://img.shields.io/pypi/l/pandarus)][license]

[![Read the documentation at https://pandarus.readthedocs.io/](https://img.shields.io/readthedocs/pandarus/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/cmutel/pandarus/actions/workflows/python-test.yml/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/cmutel/pandarus/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi status]: https://pypi.org/project/pandarus/
[read the docs]: https://pandarus.readthedocs.io/
[tests]: https://github.com/cmutel/pandarus/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/cmutel/pandarus
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

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

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide][Contributor Guide].

## License

Distributed under the terms of the [BSD-2-Clause][License],
_pyilcd_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue][Issue Tracker] along with a detailed description.


<!-- github-only -->

[command-line reference]: https://pandarus.readthedocs.io/en/latest/usage.html
[License]: https://github.com/cmutel/pandarus/blob/main/LICENSE
[Contributor Guide]: https://github.com/cmutel/pandarus/blob/main/CONTRIBUTING.md
[Issue Tracker]: https://github.com/cmutel/pandarus/issues
