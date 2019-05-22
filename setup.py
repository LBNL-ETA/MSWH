#!/usr/bin/env python
# -*- coding : utf-8 -*-

# To use a consistent encoding
from codecs import open
from os import path
# Always prefer setuptools over distutils
from setuptools import setup, find_packages

long_description = \
"""
# Introduction

"""

setup(
    name='mswh',

    version='0.1',

    description='Multiscale solar water heating',

    # The project's main homepage.
    url='https://github.com/milicag/mswh',

    # Author details
    author='Milica Grahovac/Robert Hosbach/Mohoan Ganeshalingam/Hannes Bohnengel/Katie Coughlin',


    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],

    keywords='swh scale system model simulation',

    # package_dir = {'lcc': 'src'}

    packages=find_packages(exclude=['docs', 'analysis_scripts']),

    install_requires=[
        'pandas>=0.24.1',
        'numpy>=1.16.1'
        'future',
        'plotly>=3.2.0',
        'psutil>=5.4.7',
        'django>=2.1.7',
        'sphinx_rtd_theme'],

    # # If there are data files included in your packages that need to be
    # # installed, specify them here.  If using Python 2.6 or less, then these
    # # have to be included in MANIFEST.in as well.
    package_data={},
    include_package_data=True,
    # # Although 'package_data' is the preferred approach, in some case you may
    # # need to place data files outside of your packages. See:
    # # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],

    # # To provide executable scripts, use entry points in preference to the
    # # "scripts" keyword. Entry points provide cross-platform support and allow
    # # pip to create the appropriate form of executable for the target platform.
    entry_points={}
)
