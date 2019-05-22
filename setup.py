#!/usr/bin/env python
# -*- coding : utf-8 -*-

from codecs import open
from os import path

from setuptools import setup, find_packages

long_description = \
"""
# Multiscale Solar Water Heating Python Modeling Framework
"""

setup(
    name='mswh',

    version='0.1',

    description='Multiscale solar water heating',

    # The project's main homepage.
    url='https://github.com/LBNL-ETA/MSWH',

    # Author details
    author='Milica Grahovac/Robert Hosbach/'\
           'Katie Coughlin/Mohan Ganeshalingam/Hannes Gerhart',


    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],

    keywords='swh scale system model simulation',

    packages=find_packages(exclude=['docs', 'scripts']),

    install_requires=[
        'pandas>=0.24.1',
        'numpy>=1.16.1'
        'future',
        'plotly>=3.2.0',
        'psutil>=5.4.7',
        'django>=2.1.7',
        'sphinx_rtd_theme'],

    package_data={},
    include_package_data=True,

    entry_points={}

    )
