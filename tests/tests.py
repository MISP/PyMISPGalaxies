#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pymispgalaxies import Galaxies, Clusters, UnableToRevertMachinetag
from glob import glob
import os
import json
from collections import Counter


class TestPyMISPGalaxies(unittest.TestCase):

    def setUp(self):
        self.galaxies = Galaxies()
        self.clusters = Clusters(skip_duplicates=True)
        self.maxDiff = None

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
