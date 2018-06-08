
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="metadata_updater",
    version="dev",
    description="Edit Data Service metadata",
    author="splanzer",
    author_email="splanzer@linz.govt.nz",
    url="https://github.com/linz/lds-metadata-updater",
    packages=find_packages(),
    package_data={
        # Include .yml files in dist-packaging
        "lds-metadata-updater": ["*.yml"],
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "metadata_updater=metadata_updater:main"
        ],
    },
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: LDS Data Admins",
        "Natural Language :: English",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
    ],
)
