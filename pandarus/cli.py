#!/usr/bin/env python
# encoding: utf-8
"""Pandarus command line controller.

This program does one of:
* Calculates the area of each spatial unit in a map.
* Match two geospatial datasets, and calculates the area of each intersecting spatial unit in map1 and map2.

Usage:
  pandarus area <map> [--field=<field>|--band=<band>] <output> [csv|json|pickle] [options]
  pandarus intersect <map1> [--field1=<field1>|--band1=<band1>] <map2> [--field2=<field2>|--band2=<band2>] <output> [csv|json|pickle] [options]

Options:
  --no-bz2          Don't compress output with BZip2
  --cpus=<cpus>     Number of cpus to use (default is all)
  --no-projection   Compute areas in CRS of `map2`, don't use Mollweide projection
  -h --help         Show this screen.
  --version         Show version.

"""
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from docopt import docopt
from pandarus import *
import os
import sys


def main():
    arguments = docopt(__doc__, version='Pandarus CLI 0.3')
    # if arguments['info']:
    #     print(Map(arguments['<map>']).info)
    if arguments['area']:
        format = ('csv' if arguments['csv'] else 0) or ('pickle' if arguments['pickle'] else 0) or 'json'
        output = os.path.abspath(arguments['<output>']) + '.' + format

        # Don't overwrite existing output
        if os.path.exists(output) or os.path.exists(output + ".bz2"):
            sys.exit("ERROR: Output file `%s` already exists" % output)

        kwargs = {
            'from_filepath': arguments['<map>'],
        }
        if arguments.get('--field'):
            kwargs['from_metadata'] = {'field': arguments['--field']}
        elif arguments.get('--band'):
            kwargs['from_metadata'] = {'band': arguments['--band']}

        controller = Pandarus(**kwargs)
        controller.areas(cpus=int(arguments['--cpus'] or 0))

        if kwargs.get('from_metadata') or controller.from_map.raster:
            controller.add_areas_map_fieldname()

        exported = controller.export(
            output,
            format,
            compress=not arguments['--no-bz2']
        )
        print("Finished Pandarus areas job; created `%s`" % exported)
    elif arguments['intersect']:
        format = ('csv' if arguments['csv'] else 0) or ('pickle' if arguments['pickle'] else 0) or 'json'
        output = os.path.abspath(arguments['<output>']) + '.' + format

        # Don't overwrite existing output
        if os.path.exists(output) or os.path.exists(output + ".bz2"):
            sys.exit("ERROR: Output file `%s` already exists" % output)

        kwargs = {
            'from_filepath': arguments['<map1>'],
            'to_filepath': arguments['<map2>'],
        }
        if arguments.get('--field1'):
            kwargs['from_metadata'] = {'field': arguments['--field1']}
        elif arguments.get('--band1'):
            kwargs['from_metadata'] = {'band': arguments['--band1']}
        if arguments.get('--field2'):
            kwargs['to_metadata'] = {'field': arguments['--field2']}
        elif arguments.get('--band2'):
            kwargs['from_metadata'] = {'band': arguments['--band2']}

        controller = Pandarus(**kwargs)
        controller.match(cpus=int(arguments['--cpus'] or 0))

        if kwargs.get('from_metadata') or controller.from_map.raster:
            controller.add_from_map_fieldname()
        if kwargs.get('to_metadata') or controller.to_map.raster:
            controller.add_to_map_fieldname()

        exported = controller.export(
            output,
            format,
            compress=not arguments['--no-bz2']
        )
        print("Finished Pandarus intersection job; created `%s`" % exported)


if __name__ == '__main__':
    main()
