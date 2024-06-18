#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from pymispgalaxies import Galaxies, Clusters, Cluster, UnableToRevertMachinetag
from glob import glob
import os
import json
from collections import Counter, defaultdict
import warnings
from uuid import UUID


class TestPyMISPGalaxies(unittest.TestCase):

    def setUp(self):
        self.galaxies = Galaxies()
        self.clusters = Clusters(skip_duplicates=False)
        self.maxDiff = None

    def test_searchable(self):
        for cluster in self.clusters.values():
            all_searchable = []
            for c_values in cluster.values():
                all_searchable += c_values.searchable
            count = Counter(all_searchable)
            for k, v in count.items():
                if v != 1:
                    warnings.warn('On search in {}: {} is present multiple times'.format(cluster.type, k))

    def test_duplicates(self):
        has_duplicates = False
        for name, c in self.clusters.items():
            if c.duplicates:
                has_duplicates = True
                to_print = Counter(c.duplicates)
                for entry, counter in to_print.items():
                    print(counter + 1, entry)
        self.assertFalse(has_duplicates)

    def test_dump_galaxies(self):
        galaxies_from_files = {}
        for galaxy_file in glob(os.path.join(self.galaxies.root_dir_galaxies, '*.json')):
            with open(galaxy_file, 'r') as f:
                galaxy = json.load(f)
            galaxies_from_files[galaxy['name']] = galaxy
        for name, g in self.galaxies.items():
            out = g.to_dict()
            self.assertDictEqual(out, galaxies_from_files[g.name])

    def test_dump_clusters(self):
        clusters_from_files = {}
        for cluster_file in glob(os.path.join(self.clusters.root_dir_clusters, '*.json')):
            with open(cluster_file, 'r') as f:
                cluster = json.load(f)
            clusters_from_files[cluster['name']] = cluster
        for name, c in self.clusters.items():
            out = c.to_dict()
            print(name, c.name)
            self.assertCountEqual(out, clusters_from_files[c.name])

    def test_validate_schema_clusters(self):
        self.clusters.validate_with_schema()

    def test_validate_schema_galaxies(self):
        self.galaxies.validate_with_schema()

    def test_meta_additional_properties(self):
        # All the properties in the meta key of the bundled-in clusters should be known
        for c in self.clusters.values():
            for cv in c.values():
                if cv.meta:
                    self.assertIsNot(cv.meta.additional_properties, {})
                    for key, value in cv.meta.to_dict().items():
                        self.assertTrue(isinstance(value, (str, list)), value)
                        if isinstance(value, list):
                            for v in value:
                                self.assertTrue(isinstance(v, str), f'Error in {c.name}: {json.dumps(value, indent=2)}')

    def test_machinetags(self):
        self.clusters.all_machinetags()

    def test_print(self):
        print(self.clusters)

    def test_search(self):
        self.assertIsNot(len(self.clusters.search('apt')), 0)

    def test_revert_machinetag(self):
        self.assertEqual(len(self.clusters.revert_machinetag('misp-galaxy:tool="Babar"')), 2)
        with self.assertRaises(UnableToRevertMachinetag):
            self.clusters.revert_machinetag('blah')

    def test_len(self):
        self.assertIsNot(len(self.clusters), 0)
        self.assertIsNot(len(self.galaxies), 0)
        for c in self.clusters.values():
            self.assertIsNot(len(c), 0)

    def test_json(self):
        for g in self.galaxies.values():
            g.to_json()
        for c in self.clusters.values():
            c.to_json()

    def test_uuids(self):
        all_uuids = defaultdict(list)
        for cluster in self.clusters.values():
            # Skip deprecated
            if self.galaxies[cluster.name].namespace == 'deprecated':
                continue
            try:
                self.assertIsInstance(UUID(cluster.uuid), UUID, f'{cluster.name} - {cluster.uuid}')
            except ValueError:
                raise Exception(f'{cluster.name} - {cluster.uuid}')
            all_uuids[cluster.uuid].append(cluster.name)
            for value in cluster.values():
                try:
                    self.assertIsInstance(UUID(value.uuid), UUID, f'{cluster.name} - {value.value} - {value.uuid}')
                except ValueError:
                    raise Exception(f'{cluster.name} - {value.value} - {value.uuid}')
                all_uuids[value.uuid].append(f'{cluster.name}|{value.value}')

        errors = {}
        for uuid, entries in all_uuids.items():
            if len(entries) != 1:
                errors[uuid] = entries
        print(json.dumps(errors, indent=2))
        self.assertFalse(errors)

    def test_get_by_external_id(self):
        cluster = Cluster(cluster='mitre-attack-pattern')
        self.assertIsNotNone(cluster)
        cluster_by_external_id = cluster.get_by_external_id('T1525')
        cluster_by_value = cluster.get('Implant Internal Image - T1525')
        self.assertEqual(cluster_by_external_id, cluster_by_value)

        with self.assertRaises(KeyError):
            cluster.get_by_external_id('XXXXXX')
