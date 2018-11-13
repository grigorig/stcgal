[![Build Status](https://travis-ci.org/grigorig/stcgal.svg)](https://travis-ci.org/grigorig/stcgal)
[![Coverage Status](https://coveralls.io/repos/github/grigorig/stcgal/badge.svg?branch=coveralls)](https://coveralls.io/github/grigorig/stcgal?branch=coveralls)
[![PyPI version](https://badge.fury.io/py/stcgal.svg)](https://badge.fury.io/py/stcgal)

stcgal - STC MCU ISP flash tool
===============================

stcgal is a command line flash programming tool for [STC MCU Ltd](http://stcmcu.com/).
8051 compatible microcontrollers.

STC microcontrollers have an UART/USB based boot strap loader (BSL). It
utilizes a packet-based protocol to flash the code memory and IAP
memory over a serial link. This is referred to as in-system programming
(ISP).  The BSL is also used to configure various (fuse-like) device
options. Unfortunately, this protocol is not publicly documented and
STC only provide a (crude) Windows GUI application for programming.

stcgal is a full-featured Open Source replacement for STC's Windows
software; it supports a wide range of MCUs, it is very portable and
suitable for automation.

Features
--------

* Support for STC 89/90/10/11/12/15/8 series
* UART and USB BSL support
* Display part info
* Determine operating frequency
* Program flash memory
* Program IAP/EEPROM
* Set device options
* Read unique device ID (STC 10/11/12/15/8)
* Trim RC oscillator frequency (STC 15/8)
* Automatic power-cycling with DTR toggle or a custom shell command
* Automatic UART protocol detection

Quickstart
----------

Install stcgal (might need root/administrator privileges):
    
    pip3 install stcgal

Call stcgal and show usage:

    stcgal -h

Further information
-------------------

[Installation](doc/INSTALL.md)

[How to use stcgal](doc/USAGE.md)

[Frequently Asked Questions](doc/FAQ.md)

[List of tested MCU models](doc/MODELS.md)

License
-------

stcgal is published under the MIT license.
