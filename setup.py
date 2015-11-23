#!/usr/bin/env python3

import stcgal
from setuptools import setup, find_packages

setup(
    name = "stcgal",
    version = "1.0",
    packages = find_packages(exclude=["doc"]),
    install_requires = ["pyserial"],
    entry_points = {
        "console_scripts": [
            "stcgal = stcgal.frontend:cli",
        ],
    }
)
