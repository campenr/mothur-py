#!/usr/bin/env python3

"""Setup.py for Rhea."""

from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="Rhea",
    version="0.1.0",
	#packages=['tests', 'examples'],
    description="Python wrapper for the bioinformatics tool mothur",
    long_description=long_description,
    url="https://github.com/campenr/rhea",
    author="Richard Campen",
    author_email="richard@campen.co",
    license="Modified BSD License",

    # TODO add more classifiers (e.g. platform)

    classifiers=[
        "Development Status :: 4 - Beta",
		"Environment :: Win32 (MS Windows)",
        "Intended Audience :: End Users/Desktop",
		"Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
		"Natural Language :: English",
		"Operating System :: Microsoft :: Windows :: Windows 10",
        "Programming Language :: Python :: 3.6",
		"Topic :: Scientific/Engineering :: Bio-Informatics"
    ],

    keywords="bioinformatics mothur",
    packages=find_packages(),
    include_package_data=True
)
