"""setup.py for mothur_py."""

from setuptools import setup, find_packages

# Get the long description from the README.md, converted to .rst if possible
try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
    print('using README.rst for long description')
except(IOError, ImportError):
    long_description = open('README.md').read()
    print('using README.md for long description')

setup(
    name="mothur_py",
    version="0.4.0",
    description="Python wrapper for the bioinformatics tool mothur",
    long_description=long_description,
    url="https://github.com/campenr/mothur-py",
    author="Richard Campen",
    author_email="richard@campen.co",
    license="Modified BSD License",

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Bio-Informatics"
    ],

    keywords="mothur bioinformatics",
    packages=find_packages(),
    include_package_data=True
)
