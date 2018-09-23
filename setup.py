#!/usr/bin/env python3
#
# Copyright (c) 2016 Grigori Goronzy <greg@chown.ath.cx>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import stcgal
from setuptools import setup, find_packages

with open("doc/PyPI.md", "r") as fh:
    long_description = fh.read()

setup(
    name = "stcgal",
    version = stcgal.__version__,
    packages = find_packages(exclude=["doc", "tests"]),
    install_requires = ["pyserial>=3.0", "tqdm>=4.0.0"],
    extras_require = {
        "usb": ["pyusb>=1.0.0"]
    },
    entry_points = {
        "console_scripts": [
            "stcgal = stcgal.frontend:cli",
        ],
    },
    description = "STC MCU ISP flash tool",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    keywords = "stc mcu microcontroller 8051 mcs-51",
    url = "https://github.com/grigorig/stcgal",
    author = "Grigori Goronzy",
    author_email = "greg@kinoho.net",
    license = "MIT License",
    platforms = "any",
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development",
    ],
    test_suite = "tests",
    tests_require = ["PyYAML"],
)
