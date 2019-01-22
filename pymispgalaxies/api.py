#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from json import JSONEncoder
import os
import sys
import collections
from glob import glob
import re

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


class EncodeGalaxies(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Galaxy):
            return obj.to_dict()
        return JSONEncoder.default(self, obj)


class EncodeClusters(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (Cluster, ClusterValue, ClusterValueMeta)):
            return obj.to_dict()
        return JSONEncoder.default(self, obj)


class PyMISPGalaxiesError(Exception):
    def __init__(self, message):
        super(PyMISPGalaxiesError, self).__init__(message)
        self.message = message


class UnableToRevertMachinetag(PyMISPGalaxiesError):
    pass


class Galaxy():

    def __init__(self, galaxy):
        self.galaxy = galaxy
        self.type = self.galaxy['type']
        self.name = self.galaxy['name']
        self.icon = self.galaxy['icon']
        self.description = self.galaxy['description']
        self.version = self.galaxy['version']
        self.uuid = self.galaxy['uuid']
        self.namespace = self.galaxy.pop('namespace', None)

    def to_json(self):
        return json.dumps(self, cls=EncodeGalaxies)

    def to_dict(self):
        to_return = {'type': self.type, 'name': self.name, 'description': self.description,
                     'version': self.version, 'uuid': self.uuid, 'icon': self.icon}
        if self.namespace:
            to_return['namespace'] = self.namespace
        return to_return


class Galaxies(collections.Mapping):

    def __init__(self, galaxies=[]):
        if not galaxies:
            galaxies = []
            self.root_dir_galaxies = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)),
                                                  'data', 'misp-galaxy', 'galaxies')
            for galaxy_file in glob(os.path.join(self.root_dir_galaxies, '*.json')):
                with open(galaxy_file, 'r') as f:
                    galaxies.append(json.load(f))

        self.galaxies = {}
        for galaxy in galaxies:
            self.galaxies[galaxy['name']] = Galaxy(galaxy)

    def validate_with_schema(self):
        if not HAS_JSONSCHEMA:
            raise ImportError('jsonschema is required: pip install jsonschema')
        schema = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)),
                              'data', 'misp-galaxy', 'schema_galaxies.json')
        with open(schema, 'r') as f:
            loaded_schema = json.load(f)
        for g in self.galaxies.values():
            jsonschema.validate(g.galaxy, loaded_schema)

    def __getitem__(self, name):
        return self.galaxies[name]

    def __iter__(self):
        return iter(self.galaxies)

    def __len__(self):
        return len(self.galaxies)


class ClusterValueMeta():

    def __init__(self, m):
        self.type = m.pop('type', None)
        self.complexity = m.pop('complexity', None)
        self.effectiveness = m.pop('effectiveness', None)
        self.country = m.pop('country', None)
        self.possible_issues = m.pop('possible_issues', None)
        self.colour = m.pop('colour', None)
        self.motive = m.pop('motive', None)
        self.impact = m.pop('impact', None)
        self.refs = m.pop('refs', None)
        self.synonyms = m.pop('synonyms', None)
        self.derivated_from = m.pop('derivated_from', None)
        self.status = m.pop('status', None)
        self.date = m.pop('date', None)
        self.encryption = m.pop('encryption', None)
        self.extensions = m.pop('extensions', None)
        self.ransomnotes = m.pop('ransomnotes', None)
        # NOTE: meta can have aditional properties. We only load the ones
        # defined on the schema
        self.additional_properties = m

    def to_json(self):
        return json.dumps(self, cls=EncodeClusters)

    def to_dict(self):
        to_return = {}
        if self.type:
            to_return['type'] = self.type
        if self.complexity:
            to_return['complexity'] = self.complexity
        if self.effectiveness:
            to_return['effectiveness'] = self.effectiveness
        if self.country:
            to_return['country'] = self.country
        if self.possible_issues:
            to_return['possible_issues'] = self.possible_issues
        if self.colour:
            to_return['colour'] = self.colour
        if self.motive:
            to_return['motive'] = self.motive
        if self.impact:
            to_return['impact'] = self.impact
        if self.refs:
            to_return['refs'] = self.refs
        if self.synonyms:
            to_return['synonyms'] = self.synonyms
        if self.derivated_from:
            to_return['derivated_from'] = self.derivated_from
        if self.status:
            to_return['status'] = self.status
        if self.date:
            to_return['date'] = self.date
        if self.encryption:
            to_return['encryption'] = self.encryption
        if self.extensions:
            to_return['extensions'] = self.extensions
        if self.ransomnotes:
            to_return['ransomnotes'] = self.ransomnotes
        if self.additional_properties:
            to_return.update(self.additional_properties)
        return to_return


class ClusterValue():

    def __init__(self, v):
        if not v['value']:
            raise PyMISPGalaxiesError("Invalid cluster (no value): {}".format(v))
        self.uuid = v.get('uuid', None)
        self.value = v['value']
        self.description = v.get('description')
        self.meta = self.__init_meta(v.get('meta'))
        self.searchable = [self.value]
        if self.uuid:
            self.searchable.append(self.uuid)
        if self.meta and self.meta.synonyms:
            self.searchable += self.meta.synonyms
        self.searchable = list(set(self.searchable))

    def __init_meta(self, m):
        if not m:
            return None
        return ClusterValueMeta(m)

    def to_json(self):
        return json.dumps(self, cls=EncodeClusters)

    def to_dict(self):
        to_return = {'value': self.value}
        if self.uuid:
            to_return['uuid'] = self.uuid
        if self.description:
            to_return['description'] = self.description
        if self.meta:
            to_return['meta'] = self.meta
        return to_return


class Cluster(collections.Mapping):

    def __init__(self, cluster, skip_duplicates=False):
        self.cluster = cluster
        self.name = self.cluster['name']
        self.type = self.cluster['type']
        self.source = self.cluster['source']
        self.authors = self.cluster['authors']
        self.description = self.cluster['description']
        self.uuid = self.cluster['uuid']
        self.version = self.cluster['version']
        self.category = self.cluster['category']
        self.cluster_values = {}
        self.duplicates = []
        for value in self.cluster['values']:
            new_cluster_value = ClusterValue(value)
            if self.get(new_cluster_value.value):
                if skip_duplicates:
                    self.duplicates.append((self.name, new_cluster_value.value))
                else:
                    raise PyMISPGalaxiesError("Duplicate value ({}) in cluster: {}".format(new_cluster_value.value, self.name))
            self.cluster_values[new_cluster_value.value] = new_cluster_value

    def search(self, query, return_tags=False):
        matching = []
        for v in self.values():
            if [s for s in v.searchable if query.lower() in s.lower()]:
                if return_tags:
                    matching.append('misp-galaxy:{}="{}"'.format(self.type, v.value))
                    pass
                else:
                    matching.append(v)
        return matching

    def machinetags(self):
        to_return = []
        for v in self.values():
            to_return.append('misp-galaxy:{}="{}"'.format(self.type, v.value))
        return to_return

    def __str__(self):
        return '\n'.join(self.machinetags())

    def __getitem__(self, name):
        return self.cluster_values[name]

    def __len__(self):
        return len(self.cluster_values)

    def __iter__(self):
        return iter(self.cluster_values)

    def to_json(self):
        return json.dumps(self, cls=EncodeClusters)

    def to_dict(self):
        to_return = {'name': self.name, 'type': self.type, 'source': self.source,
                     'authors': self.authors, 'description': self.description,
                     'uuid': self.uuid, 'version': self.version, 'category': self.category,
                     'values': []}
        to_return['values'] = [v for v in self.values()]
        return to_return


class Clusters(collections.Mapping):

    def __init__(self, clusters=[], skip_duplicates=False):
        if not clusters:
            clusters = []
            self.root_dir_clusters = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)),
                                                  'data', 'misp-galaxy', 'clusters')
            for cluster_file in glob(os.path.join(self.root_dir_clusters, '*.json')):
                with open(cluster_file, 'r') as f:
                    clusters.append(json.load(f))
        self.clusters = {}
        for cluster in clusters:
            self.clusters[cluster['type']] = Cluster(cluster, skip_duplicates=skip_duplicates)

    def validate_with_schema(self):
        if not HAS_JSONSCHEMA:
            raise ImportError('jsonschema is required: pip install jsonschema')
        schema = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)),
                              'data', 'misp-galaxy', 'schema_clusters.json')
        with open(schema, 'r') as f:
            loaded_schema = json.load(f)
        for c in self.values():
            jsonschema.validate(c.cluster, loaded_schema)

    def all_machinetags(self):
        return [cluster.machinetags() for cluster in self.values()]

    def revert_machinetag(self, machinetag):
        try:
            _, cluster_type, cluster_value = re.findall('^([^:]*):([^=]*)="([^"]*)"$', machinetag)[0]
            cluster = self.get(cluster_type)
            value = cluster[cluster_value]
            return cluster, value
        except Exception:
            raise UnableToRevertMachinetag('The machinetag {} could not be found.'.format(machinetag))

    def search(self, query, return_tags=False):
        to_return = []
        for cluster in self.values():
            values = cluster.search(query, return_tags)
            if not values:
                continue
            to_return.append((cluster, values))
        return to_return

    def __getitem__(self, name):
        return self.clusters[name]

    def __iter__(self):
        return iter(self.clusters)

    def __len__(self):
        return len(self.clusters)

    def __str__(self):
        to_print = ''
        for cluster in self.values():
            to_print += '{}\n\n'.format(cluster)
        return to_print
