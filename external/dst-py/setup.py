"""
Setup script for the Dempster-Shafer package.

This script configures the package for installation using setuptools.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dempster_shafer",
    version="0.1.0",
    author="Dempster-Shafer Project Team",
    author_email="author@example.com",
    description="A comprehensive Python package for Dempster-Shafer theory",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/dempster_shafer",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    python_requires=">=3.6",
    install_requires=[
        "numpy>=1.19.0",
        "matplotlib>=3.3.0",
    ],
)
