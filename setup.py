#!/usr/bin/env python3
"""
Setup script for Maqro Dealership Backend
"""

from setuptools import setup, find_packages
import os

# Read requirements from requirements.txt
def read_requirements():
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="maqro-dealerships",
    version="0.1.0",
    description="Maqro Dealership Backend API",
    author="Maqro Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=read_requirements(),
    python_requires=">=3.8",
    include_package_data=True,
    zip_safe=False,
) 