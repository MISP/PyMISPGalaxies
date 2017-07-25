#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name='pymispgalaxies',
    version='0.1',
    author='Raphaël Vinot',
    author_email='raphael.vinot@circl.lu',
    maintainer='Raphaël Vinot',
    url='https://github.com/MISP/PyMISPGalaxies',
    description='Python API for the MISP Galaxies.',
    packages=['pymispgalaxies'],
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Telecommunications Industry',
        'Programming Language :: Python',
        'Topic :: Security',
        'Topic :: Internet',
    ],
    tests_requires=['nose'],
    test_suite='nose.collector',
    package_data={'pymispgalaxies': ['data/misp-galaxy/schema_*.json',
                                     'data/misp-galaxy/clusters/*.json',
                                     'data/misp-galaxy/galaxies/*.json',
                                     'data/misp-galaxy/misp/*.json',
                                     'data/misp-galaxy/vocabularies/common/*.json',
                                     'data/misp-galaxy/vocabularies/threat-actor/*.json']}
)
