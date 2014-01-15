stcgal - STC MCU flash tool
===========================

stcgal is a command line flash programming tool for STC MCU Ltd. [1]
8051 compatible microcontrollers. The name was inspired by avrdude [2].

STC microcontrollers have a UART-based boot strap loader (BSL). It
utilizes a packet-based protocol to flash the code memory and IAP
memory. The BSL is also used to configure various (fuse-like) device
options. Unfortunately, this protocol is not publicly documented and
STC only provide a (crude) Windows GUI application for programming.

stcgal is a full-featured replacement for STC's Windows software;
it is very portable and suitable for automation.

[1] http://stcmcu.com/
[2] http://www.nongnu.org/avrdude/

Supported MCU models
--------------------

stcgal should fully support STC 10/11/12 series MCUs. STC 15 series
support is unfinished, but should support all STC15F10x/STC15F20x
series MCU models. STC 89/90 series support is work in progress.

So far, stcgal was tested with the following MCU models:

* STC12C5A60S2 (BSL version: 6.2L)
* STC11F08XE (BSL version: 6.5M)
* STC15F104E (BSL version: 6.7Q)

More compatibility testing is going to happen soon.

Features
--------

* Display part info
* Program flash memory
* Program IAP/EEPROM
* Set device options
* Read unique device ID
* Trim RC oscillator frequency (on STC 15 series)

Installation
------------

stcgal requires Python 3.2 (or later) and pySerial.

Usage
-----

See ```stcgal.py -h``` for usage information.

BSL Protocol
------------

The text files in the doc/ subdirectory provide an overview over
the reverse engineered protocols used by the BSLs. For more details,
please read the source code.

License
-------

stcgal is published under the MIT license.
