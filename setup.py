#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import re

from setuptools import setup, find_packages

with io.open("kubeb/__init__.py", "rt", encoding="utf8") as f:
    version = re.search(r"__version__ = \'(.*?)\'", f.read()).group(1)

with open("Readme.md", "r") as fh:
    long_description = fh.read()

setup(
    name='kubeb',
    version=version,
    author="podder-ai",
    description=" Kubeb (Cubeba) provide CLI to build and deploy a application to Kubernetes environment",
    packages=find_packages(exclude=['tests', '*.tests', '*.tests.*']),
    package_data={
        'kubeb': ['**/*.py', '**/**/*'],
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/podder-ai/kubeb",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'click',
        'jinja2',
        'pyyaml',
        'python-dotenv',
        'click-spinner',
    ],
    entry_points={
        'console_scripts': ['kubeb=kubeb.main:cli'],
    }
)