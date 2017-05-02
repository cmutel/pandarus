---
title: 'Pandarus: GIS toolkit for regionalized life cycle assessment'
tags:
 - Python
 - LCA
 - GIS
authors:
 - name: Chris Mutel
   orcid: 0000-0002-7898-9862
   affiliation: 1
affiliations:
 - name: Paul Scherrer Institut
   index: 1
date: 14 April 2017
bibliography: paper.bib
---

# Summary

Pandarus is a GIS toolkit for regionalized life cycle assessment (LCA). It is designed to work with brightway LCA framework [@homepage], brightway2-regional [@regional], and Constructive Geometries [@cg]. A separate library, pandarus-remote [@remote], provides a web API to run Pandarus on a server.

In the context of life cycle assessment, regionalization means the introduction of detailed spatial information for inventory activities and impact assessment characterization maps. As these will have different spatial scales, GIS functionality is required to match these two maps. Pandarus can do the following:

* Overlay two vector datasets, calculating the areas of each combination of features using the Mollweide projection.
* Calculate the area of the geometric difference (the areas present in one input file but not in the other) of one vector dataset with another vector dataset.
* Calculate statistics such as min, mean, and max when overlaying a raster dataset with a vector dataset.
* Normalize raster datasets, including use of compatible `nodata` values
* Vectorization of raster datasets

The outputs from Pandarus can be used in LCA software which does not include a GIS framework, thus speeding the integration of regionalization into the broader LCA community.

# References
