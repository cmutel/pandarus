# Changes

### 2.0.0 (2023-12-24)

- Upgrade to python 3.8+
- Refactor pandarus
- Use extactextract for raster stats
- Add new Exceptions
- Switch to GitHub Actions

### 1.0.4 (2017-05-04)

- Include LICENSE file in manifest

### 1.0.3 (2017-05-04)

- Small doc changes for peer review from JOSS

### 1.0.2 (2017-04-17)

- Fix license text

## 1.0 (2017-03-22)

Major rewrite of most functionality to support lines and points, not just polygons.

- Convert rasters to vector datasets before calculations
- Tests and CI
- Removed raster map wrapper
- Unwrap Multi geometries in rtree indices

## 0.7 (2016-06-01)

- Try to fix invalid inputs with ``buffer(0)``.
- Use actual logs.

## 0.6 (2016-04-20)

- Backwards incompatible change: Output for JSON and pickle is now: ``{'metadata': metadata for processed spatial datasets, 'data': data as before}``.
- New multiprocessing control flow.
- New command line parsing requires either `intersect` or `area`.

### 0.5.2 (2016-04-10)

- Bugfix: Add filename extensions when exporting

### 0.5.1 (2016-04-08)

- Bugfix: Remove a comma

## 0.5 (2016-04-07)

- Python >= 3.4 compatibility
- New functionality and command `pandarus areas` to calculate areas of features in a single map
- Removed nonfunctional `with-global` options
- Export now produces lists for all export options, instead of a mix of lists and dictionaries
- Add test geospatial datasets

### 0.4.1 (2015-04-30)

- More than 100x performance increase against raster maps by caching location indices
- Correct specifying raster band

## 0.4 (2014-08-15)

- Move script from ``pandarus-cli.py`` to ``pandarus``.

### 0.3.1 (2014-08-15)

- Raise ValueError if Map can't load any data

## 0.3 (2014-03-10)

- Properly handle band information throughout calculation
- Add with_global option, calculating areas of each spatial unit in each map

### 0.2.1 (2014-01-24)

- Include raster data values when iterating

## 0.2 (2014-01-21)

- Changed specification of field names in CLI

## 0.1 (2014-01-21)

- Initial release
