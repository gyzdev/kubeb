#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from setuptools import setup, find_packages
from setuptools.command.install import install

# circleci.py version
VERSION = "0.0.8"

with open("Readme.md", "r") as fh:
    long_description = fh.read()


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv('CIRCLE_TAG')

        if tag != VERSION:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION
            )
            sys.exit(info)

setup(
    name='kubeb',
    version=VERSION,
    author="podder-ai",
    description=" Kubeb (Cubeba) provide CLI to build and deploy a application to Kubernetes environment",
    packages=find_packages(),
    include_package_data=True,
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
    },
    cmdclass={
        'verify': VerifyVersionCommand,
    }
)