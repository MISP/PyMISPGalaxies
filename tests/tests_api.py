#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from pymispgalaxies import Galaxies, Clusters, Cluster, ClusterValue


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

    def test_merge_cv(self):
        cv_1 = ClusterValue({
            'uuid': '1234',
            'value': 'old value',
            'description': 'old description',
            'related': [
                {
                    'dest-uuid': '1',
                    'type': 'subtechnique-of'
                },
                {
                    'dest-uuid': '2',
                    'type': 'old-type'
                }
            ]
        })

        cv_2 = ClusterValue({
            'uuid': '1234',
            'value': 'new value',
            'description': 'new description',
            'related': [
                {
                    'dest-uuid': '2',
                    'type': 'new-type'
                },
                {
                    'dest-uuid': '3',
                    'type': 'similar-to'
                }
            ]
        })

        cv_1.merge(cv_2)
        self.assertEqual(cv_1.value, 'new value')
        self.assertEqual(cv_1.description, 'new description')
        for rel in cv_1.related:
            if rel['dest-uuid'] == '1':
                self.assertEqual(rel['type'], 'subtechnique-of')
            elif rel['dest-uuid'] == '2':
                self.assertEqual(rel['type'], 'new-type')
            elif rel['dest-uuid'] == '3':
                self.assertEqual(rel['type'], 'similar-to')
            else:
                self.fail(f"Unexpected related: {rel}")

    def test_cluster_has_changed(self):
        cluster = Cluster(cluster='backdoor')
        cv = cluster.get('WellMess')
        self.assertFalse(cluster.has_changed())

        cv.description = 'new description'
        self.assertTrue(cluster.has_changed())

    def test_galaxy_has_changed(self):
        galaxy = self.galaxies.get('backdoor')
        self.assertFalse(galaxy.has_changed())

        galaxy.description = 'new description'
        self.assertTrue(galaxy.has_changed())
