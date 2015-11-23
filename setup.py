#!/usr/bin/env python3

import stcgal
from setuptools import setup, find_packages

setup(
    name = "stcgal",
    version = stcgal.__version__,
    packages = find_packages(exclude=["doc"]),
    install_requires = ["pyserial"],
    entry_points = {
        "console_scripts": [
            "stcgal = stcgal.frontend:cli",
        ],
    },
    description = "STC MCU ISP flash tool",
    url = "https://github.com/grigorig/stcgal",
    author = "Grigori Goronzy",
    author_email = "greg@kinoho.net",
    license = "MIT License",
    platforms = "any",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development",
    ],
)
