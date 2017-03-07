# -*- coding: utf-8 -*-
from .filesystem import json_exporter, get_appdirs_path
from .maps import Map
from .matching import MatchMaker, areal_calculation, intersection_calculation
from fiona.crs import from_string
import fiona
import os
from shapely.geometry import mapping


WGS84 = from_string("+datum=WGS84 +ellps=WGS84 +no_defs +proj=longlat")


class Pandarus(object):
    """Controller for all actions."""
    def __init__(self, from_filepath, to_filepath=None,
            from_metadata={}, to_metadata={}):
        self.from_map = Map(from_filepath, **from_metadata)
        self.metadata = {'first': {
            'sha256': self.from_map.hash,
            'filename': os.path.basename(from_filepath)
        }}
        self.metadata['first'].update(from_metadata)
        if to_filepath is not None:
            self.to_map = Map(to_filepath, **to_metadata)
            self.metadata['second'] = {
                'sha256': self.to_map.hash,
                'filename': os.path.basename(to_filepath)
            }
            self.metadata['second'].update(to_metadata)

    def intersect(self, cpus=None, to_meters=True):
        if cpus != 0:
            self.data = MatchMaker.intersect(
                self.from_map.filepath,
                self.to_map.filepath,
                cpus=cpus,
            )
        else:
            self.data = intersection_calculation(
                self.from_map.filepath,
                None,
                self.to_map.filepath,
                1,
                to_meters=to_meters,
            )
        return self.data

    def as_geojson(self, dct):
        mapping_from = self.from_map.get_fieldnames_dictionary(None)
        mapping_to = self.to_map.get_fieldnames_dictionary(None)
        for index, key in enumerate(dct):
            row = dct[key]
            gj = {
                'geometry': mapping(row['geom']),
                'properties': {
                    'id': index,
                    'from_label': mapping_from[key[0]],
                    'to_label': mapping_to[key[1]],
                    'measure': row['measure']},
            }
            yield gj

    def intersection_file(self, filepath=None, cpus=None, pool=True):
        if not hasattr(self, 'to_map'):
            raise ValueError("Need ``to_map`` for intersection")
        if not filepath:
            dirpath = get_appdirs_path("intersections")
            filepath = os.path.join(
                dirpath,
                "{}-{}.geojson".format(*sorted([self.from_map.hash, self.to_map.hash]))
            )

        if os.path.exists(filepath):
            os.remove(filepath)

        results = self.as_geojson(self.intersect(cpus, pool))

        schema = {
            'properties': {
                'id': 'int',
                'from_label': 'str',
                'to_label': 'str',
                'measure': 'float',
            },
            'geometry': 'MultiPolygon',
        }

        with fiona.drivers():
            with fiona.open(
                    filepath, 'w',
                    crs=WGS84,
                    driver='GeoJSON',
                    schema=schema,
                ) as sink:
                for f in results:
                    sink.write(f)

        return filepath

    def areas(self, cpus=None, to_meters=True):
        if cpus != 0:
            self.data = MatchMaker.areas(
                self.from_map.filepath,
                None,
                cpus=cpus,
            )
        else:
            self.data = areal_calculation(
                self.from_map.filepath,
                None,
                1,
                to_meters=to_meters,
            )
        return self.data

    def add_from_map_fieldname(self, fieldname=None):
        """Turn feature integer indices into actual field values using field `fieldname`"""
        if not self.data:
            raise ValueError("Must match maps first")
        mapping_dict = self.from_map.get_fieldnames_dictionary(fieldname)
        self.data = {
            (mapping_dict[k[0]], k[1]): v
            for k, v in self.data.items()
        }

    def add_to_map_fieldname(self, fieldname=None):
        """Turn feature integer indices into actual field values using field `fieldname`"""
        if not self.data:
            raise ValueError("Must match maps first")
        mapping_dict = self.to_map.get_fieldnames_dictionary(fieldname)
        self.data = {
            (k[0], mapping_dict[k[1]]): v
            for k, v in self.data.items()
        }

    def add_areas_map_fieldname(self, fieldname=None):
        """Turn feature integer indices into actual field values using field `fieldname`"""
        if not self.data:
            raise ValueError("Must match maps first")
        mapping_dict = self.from_map.get_fieldnames_dictionary(fieldname)
        self.data = {mapping_dict[k]: v for k, v in self.data.items()}

    def export(self, filepath, compress=True):
        if not filepath.endswith("json"):
            filepath += ".json"
        if isinstance(list(self.data.keys())[0], tuple):
            self.unpack_tuples()
        else:
            self.unpack_dictionary()
        return json_exporter(self.data, self.metadata, filepath, compressed=compress)

    def unpack_tuples(self):
        self.data = [(k[0], k[1], v) for k, v in self.data.items()]

    def unpack_dictionary(self):
        self.data = [(k, v) for k, v in self.data.items()]
