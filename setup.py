#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name="Trapeza",
    version="0.1",
    description="Manipulate and combine spreadsheet files",
    url="https://bitbucket.org/davidreed/trapeza",
    author="David Reed",
    author_email="david@ktema.org",
    packages=["trapeza"],
    license="MIT",
    install_requires=["Python >= 2.7"],
    long_description=open("README.txt").read())
