#!/usr/bin/env python3
"""
Setup script for actual-amazon-noter

This script installs the actual-amazon-noter executable and its dependencies.

Usage:
    pip install .
    python setup.py install
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the long description from README.txt
readme_path = Path(__file__).parent / "README.txt"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

setup(
    name="actual-amazon-noter",
    version="1.0.0",
    description="Update Actual Budget transaction notes with Amazon order details",
    long_description=long_description,
    long_description_content_type="text/plain",
    author="",
    author_email="",
    url="",
    packages=find_packages(),
    include_package_data=False,
    install_requires=[
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "actual-amazon-noter=actual-amazon-noter:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)