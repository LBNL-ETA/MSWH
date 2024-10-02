#!/usr/bin/env python
# -*- coding : utf-8 -*-

from codecs import open
from os import path

from setuptools import setup, find_packages

long_description = """
# Multiscale Solar Water Heating Python Modeling Framework
"""

setup(
    name="mswh",
    version="1.1",
    description="Multiscale solar water heating",
    # The project's main homepage.
    url="https://github.com/LBNL-ETA/MSWH",
    # Author details
    author="Milica Grahovac/Robert Hosbach/"
    "Katie Coughlin/Mohan Ganeshalingam/Hannes Gerhart",
    classifiers=[
        "Programming Language :: Python :: 3.8",
    ],
    keywords="swh scale system model simulation",
    packages=find_packages(exclude=["docs", "scripts"]),
    # to run tests and use plotting capabilities one
    # also needs Orca (https://github.com/plotly/orca)
    install_requires=[
        "pandas==1.5.0",
        "numpy==1.20.3",
        "future",
        "plotly==3.2.0",
        "nbformat>=5.0.4",
        "psutil>=5.4.7",
        "django>=2.1.7",
        "sphinx_rtd_theme",
    ],
    package_data={},
    include_package_data=True,
    entry_points={},
)
