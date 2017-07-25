#!/usr/bin/env python
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
        try:
            return obj._json()
        except AttributeError:
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
        self.description = self.galaxy['description']
        self.version = self.galaxy['version']
        self.uuid = self.galaxy['uuid']

    def _json(self):
        return {'type': self.type, 'name': self.name, 'description': self.description,
                'version': self.version, 'uuid': self.uuid}


class Galaxies(collections.Mapping):

    def __init__(self):
        self.root_dir_galaxies = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)),
                                              'data', 'misp-galaxy', 'galaxies')
        self.galaxies = {}
        for galaxy_file in glob(os.path.join(self.root_dir_galaxies, '*.json')):
            with open(galaxy_file, 'r') as f:
                galaxy = json.load(f)
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

    def __str__(self):
        to_print = ''
        for galaxy in self.galaxies.values():
            to_print += '{}\n\n'.format(str(galaxy))
        return to_print


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

    def _json(self):
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
        self.value = v['value']
        self.description = v.get('description')
        self.meta = self.__init_meta(v.get('meta'))

    def __init_meta(self, m):
        if not m:
            return None
        return ClusterValueMeta(m)

    def _json(self):
        to_return = {'value': self.value}
        if self.description:
            to_return['description'] = self.description
        if self.meta:
            to_return['meta'] = self.meta._json()
        return to_return

    def __str__(self):
        to_print = '{}\n{}'.format(self.value, self.description)
        if self.meta:
            to_print += '\n'
            for k, v in self.meta._json().items():
                to_print += '- {}:\t{}'.format(k, v)
        return to_print


class Cluster():

    def __init__(self, cluster):
        self.cluster = cluster
        self.name = self.cluster['name']
        self.type = self.cluster['type']
        self.source = self.cluster['source']
        self.authors = self.cluster['authors']
        self.description = self.cluster['description']
        self.uuid = self.cluster['uuid']
        self.version = self.cluster['version']
        self.values = []
        for value in self.cluster['values']:
            self.values.append(ClusterValue(value))

    def machinetags(self):
        to_return = []
        for v in self.values:
            to_return.append('misp-galaxy:{}="{}"'.format(self.type, v.value))
        return to_return

    def __str__(self):
        return '\n'.join(self.machinetags())

    def _json(self):
        to_return = {'name': self.name, 'type': self.type, 'source': self.source,
                     'authors': self.authors, 'description': self.description,
                     'uuid': self.uuid, 'version': self.version, 'values': []}
        for v in self.values:
            to_return['values'].append(v._json())
        return to_return


class Clusters(collections.Mapping):

    def __init__(self):
        self.root_dir_clusters = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)),
                                              'data', 'misp-galaxy', 'clusters')
        self.clusters = {}
        for cluster_file in glob(os.path.join(self.root_dir_clusters, '*.json')):
            with open(cluster_file, 'r') as f:
                cluster = json.load(f)
            self.clusters[cluster['type']] = Cluster(cluster)

    def validate_with_schema(self):
        if not HAS_JSONSCHEMA:
            raise ImportError('jsonschema is required: pip install jsonschema')
        schema = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)),
                              'data', 'misp-galaxy', 'schema_clusters.json')
        with open(schema, 'r') as f:
            loaded_schema = json.load(f)
        for c in self.clusters.values():
            jsonschema.validate(c.cluster, loaded_schema)

    def all_machinetags(self):
        return [cluster.machinetags() for cluster in self.clusters.values()]

    def revert_machinetag(self, machinetag):
        _, cluster_type, cluster_value = re.findall('^([^:]*):([^=]*)="([^"]*)"$', machinetag)[0]
        cluster = self.clusters[cluster_type]
        for v in cluster.values:
            if v.value == cluster_value:
                return cluster, v
        raise UnableToRevertMachinetag('The machinetag {} could not be found.'.format(machinetag))

    def __getitem__(self, name):
        return self.clusters[name]

    def __iter__(self):
        return iter(self.clusters)

    def __len__(self):
        return len(self.clusters)

    def __str__(self):
        to_print = ''
        for cluster in self.clusters.values():
            to_print += '{}\n\n'.format(cluster)
        return to_print
