#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from pymispgalaxies import Galaxies, Clusters, Cluster


class TestPyMISPGalaxiesApi(unittest.TestCase):

    def setUp(self):
        self.galaxies = Galaxies()
        self.clusters = Clusters(skip_duplicates=True)
        self.maxDiff = None

    def test_get_by_external_id(self):
        cluster = Cluster(cluster='mitre-attack-pattern')
        self.assertIsNotNone(cluster)
        cluster_by_external_id = cluster.get_by_external_id('T1525')
        cluster_by_value = cluster.get('Implant Internal Image - T1525')
        self.assertEqual(cluster_by_external_id, cluster_by_value)

        with self.assertRaises(KeyError):
            cluster.get_by_external_id('XXXXXX')
