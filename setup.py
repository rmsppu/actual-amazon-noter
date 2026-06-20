#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="actual-ecommerce-noter",
    version="2.2.0-fork.9",
    description="Update Actual Budget transaction notes with Amazon and PayPal order details",
    long_description="Update Actual Budget transaction notes with Amazon and PayPal order details",
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
            "actual-ecommerce-noter=actual-ecommerce-noter:main",
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