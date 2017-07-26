#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pymispgalaxies import Galaxies, Clusters
from glob import glob
import os
import json


class TestPyMISPGalaxies(unittest.TestCase):

    def setUp(self):
        self.galaxies = Galaxies()
        self.clusters = Clusters()
        self.maxDiff = None

    def test_dump_galaxies(self):
        galaxies_from_files = {}
        for galaxy_file in glob(os.path.join(self.galaxies.root_dir_galaxies, '*.json')):
            with open(galaxy_file, 'r') as f:
                galaxy = json.load(f)
            galaxies_from_files[galaxy['name']] = galaxy
        for name, g in self.galaxies.items():
            out = g._json()
            self.assertDictEqual(out, galaxies_from_files[g.name])

    def test_dump_clusters(self):
        clusters_from_files = {}
        for cluster_file in glob(os.path.join(self.clusters.root_dir_clusters, '*.json')):
            with open(cluster_file, 'r') as f:
                cluster = json.load(f)
            clusters_from_files[cluster['name']] = cluster
        for name, c in self.clusters.items():
            out = c._json()
            self.assertCountEqual(out, clusters_from_files[c.name])

    def test_validate_schema_clusters(self):
        self.clusters.validate_with_schema()

    def test_validate_schema_galaxies(self):
        self.galaxies.validate_with_schema()

    def test_meta_additional_properties(self):
        # All the properties in the meta key of the bundled-in clusters should be known
        for c in self.clusters.values():
            for cv in c.values.values():
                if cv.meta:
                    self.assertIsNot(cv.meta.additional_properties, {})

    def test_machinetags(self):
        self.clusters.all_machinetags()

    def test_print(self):
        print(self.clusters)

    def test_search(self):
        self.assertIsNot(len(self.clusters.search('apt')), 0)
