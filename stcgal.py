#!/usr/bin/env python3
#
# Copyright (c) 2013 Grigori Goronzy
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

# stcgal - STC MCU serial bootloader flash programmer

import serial
import sys, os, time, struct
import argparse
import collections

DEBUG = False

class Utils:
    @classmethod
    def to_bool(self, val):
        """make sensible boolean from string or other type value"""

        if isinstance(val, bool): return val
        if isinstance(val, int): return bool(val)
        if len(val) == 0: return False
        return True if val[0].lower() == "t" or val[0] == "1" else False

    @classmethod
    def to_int(self, val):
        """make int from any value, nice error message if not possible"""

        try: return int(val, 0)
        except: raise ValueError("invalid integer")

    @classmethod
    def hexstr(self, bytestr, sep=""):
        """make formatted hex string output from byte sequence"""

        return sep.join(["%02X" % x for x in bytestr])


class BaudType:
    """Check baud rate for validity"""

    def __call__(self, string):
        baud = int(string)
        if baud not in serial.Serial.BAUDRATES:
            raise argparse.ArgumentTypeError("illegal baudrate")
        return baud

    def __repr__(self): return "baudrate"

class MCUModelDatabase:
    """Database that holds basic MCU information.

    This database holds the most basic information about MCU models:
    name, identification code and flash memory sizes.
    """

    MCUModel = collections.namedtuple("MCUModel", ["name", "magic", "total", "code", "eeprom"])

    models = (
        MCUModel(name='STC15F2K08S2', magic=0xf401, total=65536, code=8192, eeprom=54272),
        MCUModel(name='STC15F2K16S2', magic=0xf402, total=65536, code=16384, eeprom=46080),
        MCUModel(name='STC15F2K24S2', magic=0xf403, total=65536, code=24576, eeprom=37888),
        MCUModel(name='STC15F2K32S2', magic=0xf404, total=65536, code=32768, eeprom=29696),
        MCUModel(name='STC15F2K40S2', magic=0xf405, total=65536, code=40960, eeprom=21504),
        MCUModel(name='STC15F2K48S2', magic=0xf406, total=65536, code=49152, eeprom=13312),
        MCUModel(name='STC15F2K56S2', magic=0xf407, total=65536, code=57344, eeprom=5120),
        MCUModel(name='STC15F2K60S2', magic=0xf408, total=65536, code=61440, eeprom=1024),
        MCUModel(name='IAP15F2K61S2', magic=0xf449, total=65536, code=62464, eeprom=0),
        MCUModel(name='STC15L2K08S2', magic=0xf481, total=65536, code=8192, eeprom=54272),
        MCUModel(name='STC15L2K16S2', magic=0xf482, total=65536, code=16384, eeprom=46080),
        MCUModel(name='STC15L2K24S2', magic=0xf483, total=65536, code=24576, eeprom=37888),
        MCUModel(name='STC15L2K32S2', magic=0xf484, total=65536, code=32768, eeprom=29696),
        MCUModel(name='STC15L2K40S2', magic=0xf485, total=65536, code=40960, eeprom=21504),
        MCUModel(name='STC15L2K48S2', magic=0xf486, total=65536, code=49152, eeprom=13312),
        MCUModel(name='STC15L2K56S2', magic=0xf487, total=65536, code=57344, eeprom=5120),
        MCUModel(name='STC15L2K60S2', magic=0xf488, total=65536, code=61440, eeprom=1024),
        MCUModel(name='IAP15L2K61S2', magic=0xf4c9, total=65536, code=62464, eeprom=0),
        MCUModel(name='STC15F404AD', magic=0xf40a, total=65536, code=4096, eeprom=9216),
        MCUModel(name='STC15F408AD', magic=0xf40b, total=65536, code=8192, eeprom=5120),
        MCUModel(name='STC15F412AD', magic=0xf40c, total=65536, code=12288, eeprom=1024),
        MCUModel(name='IAP15F413AD', magic=0xf44d, total=65536, code=13312, eeprom=0),
        MCUModel(name='STC15L404AD', magic=0xf48a, total=65536, code=4096, eeprom=9216),
        MCUModel(name='STC15L408AD', magic=0xf48b, total=65536, code=8192, eeprom=5120),
        MCUModel(name='STC15L412AD', magic=0xf48c, total=65536, code=12288, eeprom=1024),
        MCUModel(name='IAP15L413AD', magic=0xf4cd, total=65536, code=13312, eeprom=0),
        MCUModel(name='STC15W101SW', magic=0xf501, total=8192, code=1024, eeprom=4096),
        MCUModel(name='STC15W102SW', magic=0xf502, total=8192, code=2048, eeprom=3072),
        MCUModel(name='STC15W103SW', magic=0xf503, total=8192, code=3072, eeprom=2048),
        MCUModel(name='STC15W104SW', magic=0xf504, total=8192, code=4096, eeprom=1024),
        MCUModel(name='IAP15W105SW', magic=0xf545, total=8192, code=5120, eeprom=0),
        MCUModel(name='STC15W101S', magic=0xf508, total=8192, code=1024, eeprom=4096),
        MCUModel(name='STC15W102S', magic=0xf50a, total=8192, code=2048, eeprom=3072),
        MCUModel(name='STC15W103S', magic=0xf50b, total=8192, code=3072, eeprom=2048),
        MCUModel(name='STC15W104S', magic=0xf50c, total=8192, code=4096, eeprom=1024),
        MCUModel(name='IAP15W105S', magic=0xf54d, total=8192, code=5120, eeprom=0),
        MCUModel(name='STC15W201S', magic=0xf511, total=8192, code=1024, eeprom=4096),
        MCUModel(name='STC15W202S', magic=0xf512, total=8192, code=2048, eeprom=3072),
        MCUModel(name='STC15W203S', magic=0xf513, total=8192, code=3072, eeprom=2048),
        MCUModel(name='STC15W204S', magic=0xf514, total=8192, code=4096, eeprom=1024),
        MCUModel(name='IAP15W205S', magic=0xf555, total=8192, code=5120, eeprom=0),
        MCUModel(name='STC15F100W', magic=0xf290, total=8192, code=512, eeprom=0),
        MCUModel(name='STC15F101W', magic=0xf291, total=8192, code=1024, eeprom=4096),
        MCUModel(name='STC15F102W', magic=0xf292, total=8192, code=2048, eeprom=3072),
        MCUModel(name='STC15F103W', magic=0xf293, total=8192, code=3072, eeprom=2048),
        # XXX: same magic as STC15F104E!
        MCUModel(name='STC15F104W', magic=0xf294, total=8192, code=4096, eeprom=1024),
        MCUModel(name='IAP15F105W', magic=0xf2b5, total=8192, code=5120, eeprom=0),
        MCUModel(name='STC15F100', magic=0xf298, total=8192, code=512, eeprom=0),
        MCUModel(name='STC15F101', magic=0xf299, total=8192, code=1024, eeprom=4096),
        MCUModel(name='STC15F102', magic=0xf29a, total=8192, code=2048, eeprom=3072),
        MCUModel(name='STC15F103', magic=0xf29b, total=8192, code=3072, eeprom=2048),
        MCUModel(name='STC15F104', magic=0xf29c, total=8192, code=4096, eeprom=1024),
        MCUModel(name='IAP15F105', magic=0xf2bd, total=8192, code=5120, eeprom=0),
        MCUModel(name='STC15L100W', magic=0xf2d0, total=8192, code=512, eeprom=0),
        MCUModel(name='STC15L101W', magic=0xf2d1, total=8192, code=1024, eeprom=4096),
        MCUModel(name='STC15L102W', magic=0xf2d2, total=8192, code=2048, eeprom=3072),
        MCUModel(name='STC15L103W', magic=0xf2d3, total=8192, code=3072, eeprom=2048),
        # XXX: same magic as STC15L104E!
        MCUModel(name='STC15L104W', magic=0xf2d4, total=8192, code=4096, eeprom=1024),
        MCUModel(name='IAP15L105W', magic=0xf2f5, total=8192, code=5120, eeprom=0),
        MCUModel(name='STC15L100', magic=0xf2d8, total=8192, code=512, eeprom=0),
        MCUModel(name='STC15L101', magic=0xf2d9, total=8192, code=1024, eeprom=4096),
        MCUModel(name='STC15L102', magic=0xf2da, total=8192, code=2048, eeprom=3072),
        MCUModel(name='STC15L103', magic=0xf2db, total=8192, code=3072, eeprom=2048),
        MCUModel(name='STC15L104', magic=0xf2dc, total=8192, code=4096, eeprom=1024),
        MCUModel(name='IAP15L105', magic=0xf2fd, total=8192, code=5120, eeprom=0),
        MCUModel(name='STC15F104E', magic=0xf294, total=8192, code=4096, eeprom=1024),
        MCUModel(name='STC15L104E', magic=0xf2d4, total=8192, code=4096, eeprom=1024),
        MCUModel(name='STC15F204EA', magic=0xf394, total=8192, code=4096, eeprom=1024),
        MCUModel(name='IAP15F205EA', magic=0xf3b5, total=8192, code=5120, eeprom=0),
        MCUModel(name='STC15L204EA', magic=0xf3d4, total=8192, code=4096, eeprom=1024),
        MCUModel(name='IAP15L205EA', magic=0xf3f5, total=8192, code=5120, eeprom=0),
        MCUModel(name='STC12C5A08S2', magic=0xd164, total=65536, code=8192, eeprom=55296),
        MCUModel(name='STC12C5A16S2', magic=0xd168, total=65536, code=16384, eeprom=47104),
        MCUModel(name='STC12C5A32S2', magic=0xd170, total=65536, code=32768, eeprom=30720),
        MCUModel(name='STC12C5A40S2', magic=0xd174, total=65536, code=40960, eeprom=22528),
        MCUModel(name='STC12C5A48S2', magic=0xd178, total=65536, code=49152, eeprom=14336),
        MCUModel(name='STC12C5A52S2', magic=0xd17a, total=65536, code=53248, eeprom=10240),
        MCUModel(name='STC12C5A56S2', magic=0xd17c, total=65536, code=57344, eeprom=6144),
        MCUModel(name='STC12C5A60S2', magic=0xd17e, total=65536, code=61440, eeprom=2048),
        MCUModel(name='STC12C5A08AD', magic=0xd144, total=65536, code=8192, eeprom=55296),
        MCUModel(name='STC12C5A16AD', magic=0xd148, total=65536, code=16384, eeprom=47104),
        MCUModel(name='STC12C5A32AD', magic=0xd150, total=65536, code=32768, eeprom=30720),
        MCUModel(name='STC12C5A40AD', magic=0xd154, total=65536, code=40960, eeprom=22528),
        MCUModel(name='STC12C5A48AD', magic=0xd158, total=65536, code=49152, eeprom=14336),
        MCUModel(name='STC12C5A52AD', magic=0xd15a, total=65536, code=53248, eeprom=10240),
        MCUModel(name='STC12C5A56AD', magic=0xd15c, total=65536, code=57344, eeprom=6144),
        MCUModel(name='STC12C5A60AD', magic=0xd15e, total=65536, code=61440, eeprom=2048),
        MCUModel(name='STC12C5A08CCP', magic=0xd124, total=65536, code=8192, eeprom=55296),
        MCUModel(name='STC12C5A16CCP', magic=0xd128, total=65536, code=16384, eeprom=47104),
        MCUModel(name='STC12C5A32CCP', magic=0xd130, total=65536, code=32768, eeprom=30720),
        MCUModel(name='STC12C5A40CCP', magic=0xd134, total=65536, code=40960, eeprom=22528),
        MCUModel(name='STC12C5A48CCP', magic=0xd138, total=65536, code=49152, eeprom=14336),
        MCUModel(name='STC12C5A52CCP', magic=0xd13a, total=65536, code=53248, eeprom=10240),
        MCUModel(name='STC12C5A56CCP', magic=0xd13c, total=65536, code=57344, eeprom=6144),
        MCUModel(name='STC12C5A60CCP', magic=0xd13e, total=65536, code=61440, eeprom=2048),
        MCUModel(name='STC12C5A08X', magic=0xd104, total=65536, code=8192, eeprom=0),
        MCUModel(name='STC12C5A16X', magic=0xd108, total=65536, code=16384, eeprom=0),
        MCUModel(name='STC12C5A32X', magic=0xd110, total=65536, code=32768, eeprom=0),
        MCUModel(name='STC12C5A40X', magic=0xd114, total=65536, code=40960, eeprom=0),
        MCUModel(name='STC12C5A48X', magic=0xd118, total=65536, code=49152, eeprom=0),
        MCUModel(name='STC12C5A52X', magic=0xd11a, total=65536, code=53248, eeprom=0),
        MCUModel(name='STC12C5A56X', magic=0xd11c, total=65536, code=57344, eeprom=0),
        MCUModel(name='STC12C5A60X', magic=0xd11e, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP12C5A08S2', magic=0xd163, total=65536, code=8192, eeprom=0),
        MCUModel(name='IAP12C5A16S2', magic=0xd167, total=65536, code=16384, eeprom=0),
        MCUModel(name='IAP12C5A32S2', magic=0xd16f, total=65536, code=32768, eeprom=0),
        MCUModel(name='IAP12C5A40S2', magic=0xd173, total=65536, code=40960, eeprom=0),
        MCUModel(name='IAP12C5A48S2', magic=0xd177, total=65536, code=49152, eeprom=0),
        MCUModel(name='IAP12C5A52S2', magic=0xd179, total=65536, code=53248, eeprom=0),
        MCUModel(name='IAP12C5A56S2', magic=0xd17b, total=65536, code=57344, eeprom=0),
        MCUModel(name='IAP12C5A60S2', magic=0xd17d, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP12C5A62S2', magic=0xd17f, total=65536, code=63488, eeprom=0),
        MCUModel(name='IAP12C5A08AD', magic=0xd143, total=65536, code=8192, eeprom=0),
        MCUModel(name='IAP12C5A16AD', magic=0xd147, total=65536, code=16384, eeprom=0),
        MCUModel(name='IAP12C5A32AD', magic=0xd14f, total=65536, code=32768, eeprom=0),
        MCUModel(name='IAP12C5A40AD', magic=0xd153, total=65536, code=40960, eeprom=0),
        MCUModel(name='IAP12C5A48AD', magic=0xd157, total=65536, code=49152, eeprom=0),
        MCUModel(name='IAP12C5A52AD', magic=0xd159, total=65536, code=53248, eeprom=0),
        MCUModel(name='IAP12C5A56AD', magic=0xd15b, total=65536, code=57344, eeprom=0),
        MCUModel(name='IAP12C5A60AD', magic=0xd15d, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP12C5A62AD', magic=0xd15f, total=65536, code=63488, eeprom=0),
        MCUModel(name='IAP12C5A08CCP', magic=0xd123, total=65536, code=8192, eeprom=0),
        MCUModel(name='IAP12C5A16CCP', magic=0xd127, total=65536, code=16384, eeprom=0),
        MCUModel(name='IAP12C5A32CCP', magic=0xd12f, total=65536, code=32768, eeprom=0),
        MCUModel(name='IAP12C5A40CCP', magic=0xd133, total=65536, code=40960, eeprom=0),
        MCUModel(name='IAP12C5A48CCP', magic=0xd137, total=65536, code=49152, eeprom=0),
        MCUModel(name='IAP12C5A52CCP', magic=0xd139, total=65536, code=53248, eeprom=0),
        MCUModel(name='IAP12C5A56CCP', magic=0xd13b, total=65536, code=57344, eeprom=0),
        MCUModel(name='IAP12C5A60CCP', magic=0xd13d, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP12C5A62CCP', magic=0xd13f, total=65536, code=63488, eeprom=0),
        MCUModel(name='IAP12C5A08', magic=0xd103, total=65536, code=8192, eeprom=0),
        MCUModel(name='IAP12C5A16', magic=0xd107, total=65536, code=16384, eeprom=0),
        MCUModel(name='IAP12C5A32', magic=0xd10f, total=65536, code=32768, eeprom=0),
        MCUModel(name='IAP12C5A40', magic=0xd113, total=65536, code=40960, eeprom=0),
        MCUModel(name='IAP12C5A48', magic=0xd117, total=65536, code=49152, eeprom=0),
        MCUModel(name='IAP12C5A52', magic=0xd119, total=65536, code=53248, eeprom=0),
        MCUModel(name='IAP12C5A56', magic=0xd11b, total=65536, code=57344, eeprom=0),
        MCUModel(name='IAP12C5A60', magic=0xd11d, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP12C5A62', magic=0xd11f, total=65536, code=63488, eeprom=0),
        MCUModel(name='STC12LE5A08S2', magic=0xd1e4, total=65536, code=8192, eeprom=55296),
        MCUModel(name='STC12LE5A16S2', magic=0xd1e8, total=65536, code=16384, eeprom=47104),
        MCUModel(name='STC12LE5A32S2', magic=0xd1f0, total=65536, code=32768, eeprom=30720),
        MCUModel(name='STC12LE5A40S2', magic=0xd1f4, total=65536, code=40960, eeprom=22528),
        MCUModel(name='STC12LE5A48S2', magic=0xd1f8, total=65536, code=49152, eeprom=14336),
        MCUModel(name='STC12LE5A52S2', magic=0xd1fa, total=65536, code=53248, eeprom=10240),
        MCUModel(name='STC12LE5A56S2', magic=0xd1fc, total=65536, code=57344, eeprom=6144),
        MCUModel(name='STC12LE5A60S2', magic=0xd1fe, total=65536, code=61440, eeprom=2048),
        MCUModel(name='STC12LE5A08AD', magic=0xd1c4, total=65536, code=8192, eeprom=55296),
        MCUModel(name='STC12LE5A16AD', magic=0xd1c8, total=65536, code=16384, eeprom=47104),
        MCUModel(name='STC12LE5A32AD', magic=0xd1d0, total=65536, code=32768, eeprom=30720),
        MCUModel(name='STC12LE5A40AD', magic=0xd1d4, total=65536, code=40960, eeprom=22528),
        MCUModel(name='STC12LE5A48AD', magic=0xd1d8, total=65536, code=49152, eeprom=14336),
        MCUModel(name='STC12LE5A52AD', magic=0xd1da, total=65536, code=53248, eeprom=10240),
        MCUModel(name='STC12LE5A56AD', magic=0xd1dc, total=65536, code=57344, eeprom=6144),
        MCUModel(name='STC12LE5A60AD', magic=0xd1de, total=65536, code=61440, eeprom=2048),
        MCUModel(name='STC12LE5A08CCP', magic=0xd1a4, total=65536, code=8192, eeprom=55296),
        MCUModel(name='STC12LE5A16CCP', magic=0xd1a8, total=65536, code=16384, eeprom=47104),
        MCUModel(name='STC12LE5A32CCP', magic=0xd1b0, total=65536, code=32768, eeprom=30720),
        MCUModel(name='STC12LE5A40CCP', magic=0xd1b4, total=65536, code=40960, eeprom=22528),
        MCUModel(name='STC12LE5A48CCP', magic=0xd1b8, total=65536, code=49152, eeprom=14336),
        MCUModel(name='STC12LE5A52CCP', magic=0xd1ba, total=65536, code=53248, eeprom=10240),
        MCUModel(name='STC12LE5A56CCP', magic=0xd1bc, total=65536, code=57344, eeprom=6144),
        MCUModel(name='STC12LE5A60CCP', magic=0xd1be, total=65536, code=61440, eeprom=2048),
        MCUModel(name='STC12LE5A08X', magic=0xd184, total=65536, code=8192, eeprom=0),
        MCUModel(name='STC12LE5A16X', magic=0xd188, total=65536, code=16384, eeprom=0),
        MCUModel(name='STC12LE5A32X', magic=0xd190, total=65536, code=32768, eeprom=0),
        MCUModel(name='STC12LE5A40X', magic=0xd194, total=65536, code=40960, eeprom=0),
        MCUModel(name='STC12LE5A48X', magic=0xd198, total=65536, code=49152, eeprom=0),
        MCUModel(name='STC12LE5A52X', magic=0xd19a, total=65536, code=53248, eeprom=0),
        MCUModel(name='STC12LE5A56X', magic=0xd19c, total=65536, code=57344, eeprom=0),
        MCUModel(name='STC12LE5A60X', magic=0xd19e, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP12LE5A08S2', magic=0xd1e3, total=65536, code=8192, eeprom=0),
        MCUModel(name='IAP12LE5A16S2', magic=0xd1e7, total=65536, code=16384, eeprom=0),
        MCUModel(name='IAP12LE5A32S2', magic=0xd1ef, total=65536, code=32768, eeprom=0),
        MCUModel(name='IAP12LE5A40S2', magic=0xd1f3, total=65536, code=40960, eeprom=0),
        MCUModel(name='IAP12LE5A48S2', magic=0xd1f7, total=65536, code=49152, eeprom=0),
        MCUModel(name='IAP12LE5A52S2', magic=0xd1f9, total=65536, code=53248, eeprom=0),
        MCUModel(name='IAP12LE5A56S2', magic=0xd1fb, total=65536, code=57344, eeprom=0),
        MCUModel(name='IAP12LE5A60S2', magic=0xd1fd, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP12LE5A62S2', magic=0xd1ff, total=65536, code=63488, eeprom=0),
        MCUModel(name='IAP12LE5A08AD', magic=0xd1c3, total=65536, code=8192, eeprom=0),
        MCUModel(name='IAP12LE5A16AD', magic=0xd1c7, total=65536, code=16384, eeprom=0),
        MCUModel(name='IAP12LE5A32AD', magic=0xd1cf, total=65536, code=32768, eeprom=0),
        MCUModel(name='IAP12LE5A40AD', magic=0xd1d3, total=65536, code=40960, eeprom=0),
        MCUModel(name='IAP12LE5A48AD', magic=0xd1d7, total=65536, code=49152, eeprom=0),
        MCUModel(name='IAP12LE5A52AD', magic=0xd1d9, total=65536, code=53248, eeprom=0),
        MCUModel(name='IAP12LE5A56AD', magic=0xd1db, total=65536, code=57344, eeprom=0),
        MCUModel(name='IAP12LE5A60AD', magic=0xd1dd, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP12LE5A62AD', magic=0xd1df, total=65536, code=63488, eeprom=0),
        MCUModel(name='IAP12LE5A08CCP', magic=0xd1a3, total=65536, code=8192, eeprom=0),
        MCUModel(name='IAP12LE5A16CCP', magic=0xd1a7, total=65536, code=16384, eeprom=0),
        MCUModel(name='IAP12LE5A32CCP', magic=0xd1af, total=65536, code=32768, eeprom=0),
        MCUModel(name='IAP12LE5A40CCP', magic=0xd1b3, total=65536, code=40960, eeprom=0),
        MCUModel(name='IAP12LE5A48CCP', magic=0xd1b7, total=65536, code=49152, eeprom=0),
        MCUModel(name='IAP12LE5A52CCP', magic=0xd1b9, total=65536, code=53248, eeprom=0),
        MCUModel(name='IAP12LE5A56CCP', magic=0xd1bb, total=65536, code=57344, eeprom=0),
        MCUModel(name='IAP12LE5A60CCP', magic=0xd1bd, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP12LE5A62CCP', magic=0xd1bf, total=65536, code=63488, eeprom=0),
        MCUModel(name='IAP12LE5A08', magic=0xd183, total=65536, code=8192, eeprom=0),
        MCUModel(name='IAP12LE5A16', magic=0xd187, total=65536, code=16384, eeprom=0),
        MCUModel(name='IAP12LE5A32', magic=0xd18f, total=65536, code=32768, eeprom=0),
        MCUModel(name='IAP12LE5A40', magic=0xd193, total=65536, code=40960, eeprom=0),
        MCUModel(name='IAP12LE5A48', magic=0xd197, total=65536, code=49152, eeprom=0),
        MCUModel(name='IAP12LE5A52', magic=0xd199, total=65536, code=53248, eeprom=0),
        MCUModel(name='IAP12LE5A56', magic=0xd19b, total=65536, code=57344, eeprom=0),
        MCUModel(name='IAP12LE5A60', magic=0xd19d, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP12LE5A62', magic=0xd19f, total=65536, code=63488, eeprom=0),
        MCUModel(name='STC10F02XE', magic=0xd262, total=16384, code=2048, eeprom=12288),
        MCUModel(name='STC10F04XE', magic=0xd264, total=16384, code=4096, eeprom=10240),
        MCUModel(name='STC10F06XE', magic=0xd266, total=16384, code=6144, eeprom=8192),
        MCUModel(name='STC10F08XE', magic=0xd268, total=16384, code=8192, eeprom=6144),
        MCUModel(name='STC10F10XE', magic=0xd26a, total=16384, code=10240, eeprom=4096),
        MCUModel(name='STC10F12XE', magic=0xd26c, total=16384, code=12288, eeprom=2048),
        MCUModel(name='STC10F02X', magic=0xd242, total=16384, code=2048, eeprom=0),
        MCUModel(name='STC10F04X', magic=0xd244, total=16384, code=4096, eeprom=0),
        MCUModel(name='STC10F06X', magic=0xd246, total=16384, code=6144, eeprom=0),
        MCUModel(name='STC10F08X', magic=0xd248, total=16384, code=8192, eeprom=0),
        MCUModel(name='STC10F10X', magic=0xd24a, total=16384, code=10240, eeprom=0),
        MCUModel(name='STC10F12X', magic=0xd24c, total=16384, code=12288, eeprom=0),
        MCUModel(name='STC10F02', magic=0xd202, total=16384, code=2048, eeprom=0),
        MCUModel(name='STC10F04', magic=0xd204, total=16384, code=4096, eeprom=0),
        MCUModel(name='STC10F06', magic=0xd206, total=16384, code=6144, eeprom=0),
        MCUModel(name='STC10F08', magic=0xd208, total=16384, code=8192, eeprom=0),
        MCUModel(name='STC10F10', magic=0xd20a, total=16384, code=10240, eeprom=0),
        MCUModel(name='STC10F12', magic=0xd20c, total=16384, code=12288, eeprom=0),
        MCUModel(name='IAP10F02XE', magic=0xd272, total=16384, code=2048, eeprom=0),
        MCUModel(name='IAP10F04XE', magic=0xd274, total=16384, code=4096, eeprom=0),
        MCUModel(name='IAP10F06XE', magic=0xd276, total=16384, code=6144, eeprom=0),
        MCUModel(name='IAP10F08XE', magic=0xd278, total=16384, code=8192, eeprom=0),
        MCUModel(name='IAP10F10XE', magic=0xd27a, total=16384, code=10240, eeprom=0),
        MCUModel(name='IAP10F12XE', magic=0xd27c, total=16384, code=12288, eeprom=0),
        MCUModel(name='IAP10F14X', magic=0xd27e, total=16384, code=14336, eeprom=0),
        MCUModel(name='IAP10F02', magic=0xd232, total=16384, code=2048, eeprom=0),
        MCUModel(name='IAP10F04', magic=0xd234, total=16384, code=4096, eeprom=0),
        MCUModel(name='IAP10F06', magic=0xd236, total=16384, code=6144, eeprom=0),
        MCUModel(name='IAP10F08', magic=0xd238, total=16384, code=8192, eeprom=0),
        MCUModel(name='IAP10F10', magic=0xd23a, total=16384, code=10240, eeprom=0),
        MCUModel(name='IAP10F12', magic=0xd23c, total=16384, code=12288, eeprom=0),
        MCUModel(name='IAP10F14', magic=0xd23e, total=16384, code=14336, eeprom=0),
        MCUModel(name='STC10L02XE', magic=0xd2e2, total=16384, code=2048, eeprom=12288),
        MCUModel(name='STC10L04XE', magic=0xd2e4, total=16384, code=4096, eeprom=10240),
        MCUModel(name='STC10L06XE', magic=0xd2e6, total=16384, code=6144, eeprom=8192),
        MCUModel(name='STC10L08XE', magic=0xd2e8, total=16384, code=8192, eeprom=6144),
        MCUModel(name='STC10L10XE', magic=0xd2ea, total=16384, code=10240, eeprom=4096),
        MCUModel(name='STC10L12XE', magic=0xd2ec, total=16384, code=12288, eeprom=2048),
        MCUModel(name='STC10L02X', magic=0xd2c2, total=16384, code=2048, eeprom=0),
        MCUModel(name='STC10L04X', magic=0xd2c4, total=16384, code=4096, eeprom=0),
        MCUModel(name='STC10L06X', magic=0xd2c6, total=16384, code=6144, eeprom=0),
        MCUModel(name='STC10L08X', magic=0xd2c8, total=16384, code=8192, eeprom=0),
        MCUModel(name='STC10L10X', magic=0xd2ca, total=16384, code=10240, eeprom=0),
        MCUModel(name='STC10L12X', magic=0xd2cc, total=16384, code=12288, eeprom=0),
        MCUModel(name='STC10L02', magic=0xd282, total=16384, code=2048, eeprom=0),
        MCUModel(name='STC10L04', magic=0xd284, total=16384, code=4096, eeprom=0),
        MCUModel(name='STC10L06', magic=0xd286, total=16384, code=6144, eeprom=0),
        MCUModel(name='STC10L08', magic=0xd288, total=16384, code=8192, eeprom=0),
        MCUModel(name='STC10L10', magic=0xd28a, total=16384, code=10240, eeprom=0),
        MCUModel(name='STC10L12', magic=0xd28c, total=16384, code=12288, eeprom=0),
        MCUModel(name='IAP10L02XE', magic=0xd2f2, total=16384, code=2048, eeprom=0),
        MCUModel(name='IAP10L04XE', magic=0xd2f4, total=16384, code=4096, eeprom=0),
        MCUModel(name='IAP10L06XE', magic=0xd2f6, total=16384, code=6144, eeprom=0),
        MCUModel(name='IAP10L08XE', magic=0xd2f8, total=16384, code=8192, eeprom=0),
        MCUModel(name='IAP10L10XE', magic=0xd2fa, total=16384, code=10240, eeprom=0),
        MCUModel(name='IAP10L12XE', magic=0xd2fc, total=16384, code=12288, eeprom=0),
        MCUModel(name='IAP10L14X', magic=0xd2fe, total=16384, code=14336, eeprom=0),
        MCUModel(name='IAP10L02', magic=0xd2b2, total=16384, code=2048, eeprom=0),
        MCUModel(name='IAP10L04', magic=0xd2b4, total=16384, code=4096, eeprom=0),
        MCUModel(name='IAP10L06', magic=0xd2b6, total=16384, code=6144, eeprom=0),
        MCUModel(name='IAP10L08', magic=0xd2b8, total=16384, code=8192, eeprom=0),
        MCUModel(name='IAP10L10', magic=0xd2ba, total=16384, code=10240, eeprom=0),
        MCUModel(name='IAP10L12', magic=0xd2bc, total=16384, code=12288, eeprom=0),
        MCUModel(name='IAP10L14', magic=0xd2be, total=16384, code=14336, eeprom=0),
        MCUModel(name='STC11F01E', magic=0xe221, total=8192, code=1024, eeprom=5120),
        MCUModel(name='STC11F02E', magic=0xe222, total=8192, code=2048, eeprom=4096),
        MCUModel(name='STC11F03E', magic=0xe223, total=8192, code=3072, eeprom=3072),
        MCUModel(name='STC11F04E', magic=0xe224, total=8192, code=4096, eeprom=2048),
        MCUModel(name='STC11F05E', magic=0xe265, total=8192, code=5120, eeprom=1024),
        MCUModel(name='STC11F01', magic=0xe201, total=8192, code=1024, eeprom=0),
        MCUModel(name='STC11F02', magic=0xe202, total=8192, code=2048, eeprom=0),
        MCUModel(name='STC11F03', magic=0xe203, total=8192, code=3072, eeprom=0),
        MCUModel(name='STC11F04', magic=0xe204, total=8192, code=4096, eeprom=0),
        MCUModel(name='STC11F05', magic=0xe245, total=8192, code=5120, eeprom=0),
        MCUModel(name='IAP11F01E', magic=0xe231, total=8192, code=1024, eeprom=0),
        MCUModel(name='IAP11F02E', magic=0xe232, total=8192, code=2048, eeprom=0),
        MCUModel(name='IAP11F03E', magic=0xe233, total=8192, code=3072, eeprom=0),
        MCUModel(name='IAP11F04E', magic=0xe234, total=8192, code=4096, eeprom=0),
        MCUModel(name='IAP11F05E', magic=0xe275, total=8192, code=5120, eeprom=0),
        MCUModel(name='IAP11F01', magic=0xe211, total=8192, code=1024, eeprom=0),
        MCUModel(name='IAP11F02', magic=0xe212, total=8192, code=2048, eeprom=0),
        MCUModel(name='IAP11F03', magic=0xe213, total=8192, code=3072, eeprom=0),
        MCUModel(name='IAP11F04', magic=0xe214, total=8192, code=4096, eeprom=0),
        MCUModel(name='IAP11F05', magic=0xe255, total=8192, code=5120, eeprom=0),
        MCUModel(name='IAP11F06', magic=0xe276, total=8192, code=6144, eeprom=0),
        MCUModel(name='STC11L01E', magic=0xe2a1, total=8192, code=1024, eeprom=5120),
        MCUModel(name='STC11L02E', magic=0xe2a2, total=8192, code=2048, eeprom=4096),
        MCUModel(name='STC11L03E', magic=0xe2a3, total=8192, code=3072, eeprom=3072),
        MCUModel(name='STC11L04E', magic=0xe2a4, total=8192, code=4096, eeprom=2048),
        MCUModel(name='STC11L05E', magic=0xe2e5, total=8192, code=5120, eeprom=1024),
        MCUModel(name='STC11L01', magic=0xe281, total=8192, code=1024, eeprom=0),
        MCUModel(name='STC11L02', magic=0xe282, total=8192, code=2048, eeprom=0),
        MCUModel(name='STC11L03', magic=0xe283, total=8192, code=3072, eeprom=0),
        MCUModel(name='STC11L04', magic=0xe284, total=8192, code=4096, eeprom=0),
        MCUModel(name='STC11L05', magic=0xe2c5, total=8192, code=5120, eeprom=0),
        MCUModel(name='IAP11L01E', magic=0xe2b1, total=8192, code=1024, eeprom=0),
        MCUModel(name='IAP11L02E', magic=0xe2b2, total=8192, code=2048, eeprom=0),
        MCUModel(name='IAP11L03E', magic=0xe2b3, total=8192, code=3072, eeprom=0),
        MCUModel(name='IAP11L04E', magic=0xe2b4, total=8192, code=4096, eeprom=0),
        MCUModel(name='IAP11L05E', magic=0xe2f5, total=8192, code=5120, eeprom=0),
        MCUModel(name='IAP11L01', magic=0xe291, total=8192, code=1024, eeprom=0),
        MCUModel(name='IAP11L02', magic=0xe292, total=8192, code=2048, eeprom=0),
        MCUModel(name='IAP11L03', magic=0xe293, total=8192, code=3072, eeprom=0),
        MCUModel(name='IAP11L04', magic=0xe294, total=8192, code=4096, eeprom=0),
        MCUModel(name='IAP11L05', magic=0xe2d5, total=8192, code=5120, eeprom=0),
        MCUModel(name='IAP11L06', magic=0xe2f6, total=8192, code=6144, eeprom=0),
        MCUModel(name='STC11F08XE', magic=0xd364, total=65536, code=8192, eeprom=55296),
        MCUModel(name='STC11F16XE', magic=0xd368, total=65536, code=16384, eeprom=47104),
        MCUModel(name='STC11F20XE', magic=0xd36a, total=65536, code=20480, eeprom=30720),
        MCUModel(name='STC11F32XE', magic=0xd370, total=65536, code=32768, eeprom=30720),
        MCUModel(name='STC11F40XE', magic=0xd374, total=65536, code=40960, eeprom=22528),
        MCUModel(name='STC11F48XE', magic=0xd378, total=65536, code=49152, eeprom=14336),
        MCUModel(name='STC11F52XE', magic=0xd37a, total=65536, code=53248, eeprom=10240),
        MCUModel(name='STC11F56XE', magic=0xd37c, total=65536, code=57344, eeprom=6144),
        MCUModel(name='STC11F60XE', magic=0xd37e, total=65536, code=61440, eeprom=2048),
        MCUModel(name='STC11F08X', magic=0xd344, total=65536, code=8192, eeprom=0),
        MCUModel(name='STC11F16X', magic=0xd348, total=65536, code=16384, eeprom=0),
        MCUModel(name='STC11F20X', magic=0xd34a, total=65536, code=20480, eeprom=0),
        MCUModel(name='STC11F32X', magic=0xd350, total=65536, code=32768, eeprom=0),
        MCUModel(name='STC11F40X', magic=0xd354, total=65536, code=40960, eeprom=0),
        MCUModel(name='STC11F48X', magic=0xd358, total=65536, code=49152, eeprom=0),
        MCUModel(name='STC11F52X', magic=0xd35a, total=65536, code=53248, eeprom=0),
        MCUModel(name='STC11F56X', magic=0xd35c, total=65536, code=57344, eeprom=0),
        MCUModel(name='STC11F60X', magic=0xd35e, total=65536, code=61440, eeprom=0),
        MCUModel(name='STC11F08', magic=0xd304, total=65536, code=8192, eeprom=0),
        MCUModel(name='STC11F16', magic=0xd308, total=65536, code=16384, eeprom=0),
        MCUModel(name='STC11F20', magic=0xd30a, total=65536, code=20480, eeprom=0),
        MCUModel(name='STC11F32', magic=0xd310, total=65536, code=32768, eeprom=0),
        MCUModel(name='STC11F40', magic=0xd314, total=65536, code=40960, eeprom=0),
        MCUModel(name='STC11F48', magic=0xd318, total=65536, code=49152, eeprom=0),
        MCUModel(name='STC11F52', magic=0xd31a, total=65536, code=53248, eeprom=0),
        MCUModel(name='STC11F56', magic=0xd31c, total=65536, code=57344, eeprom=0),
        MCUModel(name='STC11F60', magic=0xd31e, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP11F08XE', magic=0xd363, total=65536, code=8192, eeprom=0),
        MCUModel(name='IAP11F16XE', magic=0xd367, total=65536, code=16384, eeprom=0),
        MCUModel(name='IAP11F20XE', magic=0xd369, total=65536, code=20480, eeprom=0),
        MCUModel(name='IAP11F32XE', magic=0xd36f, total=65536, code=32768, eeprom=0),
        MCUModel(name='IAP11F40XE', magic=0xd373, total=65536, code=40960, eeprom=0),
        MCUModel(name='IAP11F48XE', magic=0xd377, total=65536, code=49152, eeprom=0),
        MCUModel(name='IAP11F52XE', magic=0xd379, total=65536, code=53248, eeprom=0),
        MCUModel(name='IAP11F56XE', magic=0xd37b, total=65536, code=57344, eeprom=0),
        MCUModel(name='IAP11F60XE', magic=0xd37d, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP11F08X', magic=0xd343, total=65536, code=8192, eeprom=0),
        MCUModel(name='IAP11F16X', magic=0xd347, total=65536, code=16384, eeprom=0),
        MCUModel(name='IAP11F20X', magic=0xd349, total=65536, code=20480, eeprom=0),
        MCUModel(name='IAP11F32X', magic=0xd34f, total=65536, code=32768, eeprom=0),
        MCUModel(name='IAP11F40X', magic=0xd353, total=65536, code=40960, eeprom=0),
        MCUModel(name='IAP11F48X', magic=0xd357, total=65536, code=49152, eeprom=0),
        MCUModel(name='IAP11F52X', magic=0xd359, total=65536, code=53248, eeprom=0),
        MCUModel(name='IAP11F56X', magic=0xd35b, total=65536, code=57344, eeprom=0),
        MCUModel(name='IAP11F60X', magic=0xd35d, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP11F62X', magic=0xd35f, total=65536, code=63488, eeprom=0),
        MCUModel(name='IAP11F08', magic=0xd303, total=65536, code=8192, eeprom=0),
        MCUModel(name='IAP11F16', magic=0xd307, total=65536, code=16384, eeprom=0),
        MCUModel(name='IAP11F20', magic=0xd309, total=65536, code=20480, eeprom=0),
        MCUModel(name='IAP11F32', magic=0xd30f, total=65536, code=32768, eeprom=0),
        MCUModel(name='IAP11F40', magic=0xd313, total=65536, code=40960, eeprom=0),
        MCUModel(name='IAP11F48', magic=0xd317, total=65536, code=49152, eeprom=0),
        MCUModel(name='IAP11F52', magic=0xd319, total=65536, code=53248, eeprom=0),
        MCUModel(name='IAP11F56', magic=0xd31b, total=65536, code=57344, eeprom=0),
        MCUModel(name='IAP11F60', magic=0xd31d, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP11F62', magic=0xd31f, total=65536, code=63488, eeprom=0),
        MCUModel(name='STC11L08XE', magic=0xd3e4, total=65536, code=8192, eeprom=55296),
        MCUModel(name='STC11L16XE', magic=0xd3e8, total=65536, code=16384, eeprom=47104),
        MCUModel(name='STC11L20XE', magic=0xd3ea, total=65536, code=20480, eeprom=30720),
        MCUModel(name='STC11L32XE', magic=0xd3f0, total=65536, code=32768, eeprom=30720),
        MCUModel(name='STC11L40XE', magic=0xd3f4, total=65536, code=40960, eeprom=22528),
        MCUModel(name='STC11L48XE', magic=0xd3f8, total=65536, code=49152, eeprom=14336),
        MCUModel(name='STC11L52XE', magic=0xd3fa, total=65536, code=53248, eeprom=10240),
        MCUModel(name='STC11L56XE', magic=0xd3fc, total=65536, code=57344, eeprom=6144),
        MCUModel(name='STC11L60XE', magic=0xd3fe, total=65536, code=61440, eeprom=2048),
        MCUModel(name='STC11L08X', magic=0xd3c4, total=65536, code=8192, eeprom=0),
        MCUModel(name='STC11L16X', magic=0xd3c8, total=65536, code=16384, eeprom=0),
        MCUModel(name='STC11L20X', magic=0xd3ca, total=65536, code=20480, eeprom=0),
        MCUModel(name='STC11L32X', magic=0xd3d0, total=65536, code=32768, eeprom=0),
        MCUModel(name='STC11L40X', magic=0xd3d4, total=65536, code=40960, eeprom=0),
        MCUModel(name='STC11L48X', magic=0xd3d8, total=65536, code=49152, eeprom=0),
        MCUModel(name='STC11L52X', magic=0xd3da, total=65536, code=53248, eeprom=0),
        MCUModel(name='STC11L56X', magic=0xd3dc, total=65536, code=57344, eeprom=0),
        MCUModel(name='STC11L60X', magic=0xd3de, total=65536, code=61440, eeprom=0),
        MCUModel(name='STC11L08', magic=0xd384, total=65536, code=8192, eeprom=0),
        MCUModel(name='STC11L16', magic=0xd388, total=65536, code=16384, eeprom=0),
        MCUModel(name='STC11L20', magic=0xd38a, total=65536, code=20480, eeprom=0),
        MCUModel(name='STC11L32', magic=0xd390, total=65536, code=32768, eeprom=0),
        MCUModel(name='STC11L40', magic=0xd394, total=65536, code=40960, eeprom=0),
        MCUModel(name='STC11L48', magic=0xd398, total=65536, code=49152, eeprom=0),
        MCUModel(name='STC11L52', magic=0xd39a, total=65536, code=53248, eeprom=0),
        MCUModel(name='STC11L56', magic=0xd39c, total=65536, code=57344, eeprom=0),
        MCUModel(name='STC11L60', magic=0xd39e, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP11L08XE', magic=0xd3e3, total=65536, code=8192, eeprom=0),
        MCUModel(name='IAP11L16XE', magic=0xd3e7, total=65536, code=16384, eeprom=0),
        MCUModel(name='IAP11L20XE', magic=0xd3e9, total=65536, code=20480, eeprom=0),
        MCUModel(name='IAP11L32XE', magic=0xd3ef, total=65536, code=32768, eeprom=0),
        MCUModel(name='IAP11L40XE', magic=0xd3f3, total=65536, code=40960, eeprom=0),
        MCUModel(name='IAP11L48XE', magic=0xd3f7, total=65536, code=49152, eeprom=0),
        MCUModel(name='IAP11L52XE', magic=0xd3f9, total=65536, code=53248, eeprom=0),
        MCUModel(name='IAP11L56XE', magic=0xd3fb, total=65536, code=57344, eeprom=0),
        MCUModel(name='IAP11L60XE', magic=0xd3fd, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP11L08X', magic=0xd3c3, total=65536, code=8192, eeprom=0),
        MCUModel(name='IAP11L16X', magic=0xd3c7, total=65536, code=16384, eeprom=0),
        MCUModel(name='IAP11L20X', magic=0xd3c9, total=65536, code=20480, eeprom=0),
        MCUModel(name='IAP11L32X', magic=0xd3cf, total=65536, code=32768, eeprom=0),
        MCUModel(name='IAP11L40X', magic=0xd3d3, total=65536, code=40960, eeprom=0),
        MCUModel(name='IAP11L48X', magic=0xd3d7, total=65536, code=49152, eeprom=0),
        MCUModel(name='IAP11L52X', magic=0xd3d9, total=65536, code=53248, eeprom=0),
        MCUModel(name='IAP11L56X', magic=0xd3db, total=65536, code=57344, eeprom=0),
        MCUModel(name='IAP11L60X', magic=0xd3dd, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP11L62X', magic=0xd3df, total=65536, code=63488, eeprom=0),
        MCUModel(name='IAP11L08', magic=0xd383, total=65536, code=8192, eeprom=0),
        MCUModel(name='IAP11L16', magic=0xd387, total=65536, code=16384, eeprom=0),
        MCUModel(name='IAP11L20', magic=0xd389, total=65536, code=20480, eeprom=0),
        MCUModel(name='IAP11L32', magic=0xd38f, total=65536, code=32768, eeprom=0),
        MCUModel(name='IAP11L40', magic=0xd393, total=65536, code=40960, eeprom=0),
        MCUModel(name='IAP11L48', magic=0xd397, total=65536, code=49152, eeprom=0),
        MCUModel(name='IAP11L52', magic=0xd399, total=65536, code=53248, eeprom=0),
        MCUModel(name='IAP11L56', magic=0xd39b, total=65536, code=57344, eeprom=0),
        MCUModel(name='IAP11L60', magic=0xd39d, total=65536, code=61440, eeprom=0),
        MCUModel(name='IAP11L62', magic=0xd39f, total=65536, code=63488, eeprom=0),
        MCUModel(name='STC12C5201AD', magic=0xe161, total=8192, code=1024, eeprom=5120),
        MCUModel(name='STC12C5202AD', magic=0xe162, total=8192, code=2048, eeprom=4096),
        MCUModel(name='STC12C5203AD', magic=0xe163, total=8192, code=3072, eeprom=3072),
        MCUModel(name='STC12C5204AD', magic=0xe164, total=8192, code=4096, eeprom=2048),
        MCUModel(name='STC12C5205AD', magic=0xe165, total=8192, code=5120, eeprom=1024),
        MCUModel(name='STC12C5206AD', magic=0xe166, total=8192, code=6144, eeprom=0),
        MCUModel(name='STC12C5201PWM', magic=0xe121, total=8192, code=1024, eeprom=5120),
        MCUModel(name='STC12C5202PWM', magic=0xe122, total=8192, code=2048, eeprom=4096),
        MCUModel(name='STC12C5203PWM', magic=0xe123, total=8192, code=3072, eeprom=3072),
        MCUModel(name='STC12C5204PWM', magic=0xe124, total=8192, code=4096, eeprom=2048),
        MCUModel(name='STC12C5205PWM', magic=0xe125, total=8192, code=5120, eeprom=1024),
        MCUModel(name='STC12C5206PWM', magic=0xe126, total=8192, code=6144, eeprom=0),
        MCUModel(name='STC12C5201', magic=0xe101, total=8192, code=1024, eeprom=5120),
        MCUModel(name='STC12C5202', magic=0xe102, total=8192, code=2048, eeprom=4096),
        MCUModel(name='STC12C5203', magic=0xe103, total=8192, code=3072, eeprom=3072),
        MCUModel(name='STC12C5204', magic=0xe104, total=8192, code=4096, eeprom=2048),
        MCUModel(name='STC12C5205', magic=0xe105, total=8192, code=5120, eeprom=1024),
        MCUModel(name='STC12C5206', magic=0xe106, total=8192, code=6144, eeprom=0),
        MCUModel(name='STC12LE5201AD', magic=0xe1e1, total=8192, code=1024, eeprom=5120),
        MCUModel(name='STC12LE5202AD', magic=0xe1e2, total=8192, code=2048, eeprom=4096),
        MCUModel(name='STC12LE5203AD', magic=0xe1e3, total=8192, code=3072, eeprom=3072),
        MCUModel(name='STC12LE5204AD', magic=0xe1e4, total=8192, code=4096, eeprom=2048),
        MCUModel(name='STC12LE5205AD', magic=0xe1e5, total=8192, code=5120, eeprom=1024),
        MCUModel(name='STC12LE5206AD', magic=0xe1e6, total=8192, code=6144, eeprom=0),
        MCUModel(name='STC12LE5201PWM', magic=0xe1a1, total=8192, code=1024, eeprom=5120),
        MCUModel(name='STC12LE5202PWM', magic=0xe1a2, total=8192, code=2048, eeprom=4096),
        MCUModel(name='STC12LE5203PWM', magic=0xe1a3, total=8192, code=3072, eeprom=3072),
        MCUModel(name='STC12LE5204PWM', magic=0xe1a4, total=8192, code=4096, eeprom=2048),
        MCUModel(name='STC12LE5205PWM', magic=0xe1a5, total=8192, code=5120, eeprom=1024),
        MCUModel(name='STC12LE5206PWM', magic=0xe1a6, total=8192, code=6144, eeprom=0),
        MCUModel(name='STC12LE5201', magic=0xe181, total=8192, code=1024, eeprom=5120),
        MCUModel(name='STC12LE5202', magic=0xe182, total=8192, code=2048, eeprom=4096),
        MCUModel(name='STC12LE5203', magic=0xe183, total=8192, code=3072, eeprom=3072),
        MCUModel(name='STC12LE5204', magic=0xe184, total=8192, code=4096, eeprom=2048),
        MCUModel(name='STC12LE5205', magic=0xe185, total=8192, code=5120, eeprom=1024),
        MCUModel(name='STC12LE5206', magic=0xe186, total=8192, code=6144, eeprom=0),
        MCUModel(name='STC12C5601AD', magic=0xe661, total=32768, code=1024, eeprom=29696),
        MCUModel(name='STC12C5602AD', magic=0xe662, total=32768, code=2048, eeprom=28672),
        MCUModel(name='STC12C5603AD', magic=0xe663, total=32768, code=3072, eeprom=27648),
        MCUModel(name='STC12C5604AD', magic=0xe664, total=32768, code=4096, eeprom=26624),
        MCUModel(name='STC12C5605AD', magic=0xe665, total=32768, code=5120, eeprom=25600),
        MCUModel(name='STC12C5606AD', magic=0xe666, total=32768, code=6144, eeprom=24576),
        MCUModel(name='STC12C5608AD', magic=0xe668, total=32768, code=8192, eeprom=22528),
        MCUModel(name='STC12C5612AD', magic=0xe66c, total=32768, code=12288, eeprom=18432),
        MCUModel(name='STC12C5616AD', magic=0xe670, total=32768, code=16384, eeprom=14336),
        MCUModel(name='STC12C5620AD', magic=0xe674, total=32768, code=20480, eeprom=10240),
        MCUModel(name='STC12C5624AD', magic=0xe678, total=32768, code=24576, eeprom=6144),
        MCUModel(name='STC12C5628AD', magic=0xe67c, total=32768, code=28672, eeprom=2048),
        MCUModel(name='STC12C5630AD', magic=0xe67e, total=32768, code=30720, eeprom=0),
        MCUModel(name='STC12C5601', magic=0xe601, total=32768, code=1024, eeprom=29696),
        MCUModel(name='STC12C5602', magic=0xe602, total=32768, code=2048, eeprom=28672),
        MCUModel(name='STC12C5603', magic=0xe603, total=32768, code=3072, eeprom=27648),
        MCUModel(name='STC12C5604', magic=0xe604, total=32768, code=4096, eeprom=26624),
        MCUModel(name='STC12C5605', magic=0xe605, total=32768, code=5120, eeprom=25600),
        MCUModel(name='STC12C5606', magic=0xe606, total=32768, code=6144, eeprom=24576),
        MCUModel(name='STC12C5608', magic=0xe608, total=32768, code=8192, eeprom=22528),
        MCUModel(name='STC12C5612', magic=0xe60c, total=32768, code=12288, eeprom=18432),
        MCUModel(name='STC12C5616', magic=0xe610, total=32768, code=16384, eeprom=14336),
        MCUModel(name='STC12C5620', magic=0xe614, total=32768, code=20480, eeprom=10240),
        MCUModel(name='STC12C5624', magic=0xe618, total=32768, code=24576, eeprom=6144),
        MCUModel(name='STC12C5628', magic=0xe61c, total=32768, code=28672, eeprom=2048),
        MCUModel(name='STC12C5630', magic=0xe61e, total=32768, code=30720, eeprom=0),
        MCUModel(name='STC12LE5601AD', magic=0xe6e1, total=32768, code=1024, eeprom=29696),
        MCUModel(name='STC12LE5602AD', magic=0xe6e2, total=32768, code=2048, eeprom=28672),
        MCUModel(name='STC12LE5603AD', magic=0xe6e3, total=32768, code=3072, eeprom=27648),
        MCUModel(name='STC12LE5604AD', magic=0xe6e4, total=32768, code=4096, eeprom=26624),
        MCUModel(name='STC12LE5605AD', magic=0xe6e5, total=32768, code=5120, eeprom=25600),
        MCUModel(name='STC12LE5606AD', magic=0xe6e6, total=32768, code=6144, eeprom=24576),
        MCUModel(name='STC12LE5608AD', magic=0xe6e8, total=32768, code=8192, eeprom=22528),
        MCUModel(name='STC12LE5612AD', magic=0xe6ec, total=32768, code=12288, eeprom=18432),
        MCUModel(name='STC12LE5616AD', magic=0xe6f0, total=32768, code=16384, eeprom=14336),
        MCUModel(name='STC12LE5620AD', magic=0xe6f4, total=32768, code=20480, eeprom=10240),
        MCUModel(name='STC12LE5624AD', magic=0xe6f8, total=32768, code=24576, eeprom=6144),
        MCUModel(name='STC12LE5628AD', magic=0xe6fc, total=32768, code=28672, eeprom=2048),
        MCUModel(name='STC12LE5630AD', magic=0xe6fe, total=32768, code=30720, eeprom=0),
        MCUModel(name='STC12LE5601', magic=0xe681, total=32768, code=1024, eeprom=29696),
        MCUModel(name='STC12LE5602', magic=0xe682, total=32768, code=2048, eeprom=28672),
        MCUModel(name='STC12LE5603', magic=0xe683, total=32768, code=3072, eeprom=27648),
        MCUModel(name='STC12LE5604', magic=0xe684, total=32768, code=4096, eeprom=26624),
        MCUModel(name='STC12LE5605', magic=0xe685, total=32768, code=5120, eeprom=25600),
        MCUModel(name='STC12LE5606', magic=0xe686, total=32768, code=6144, eeprom=24576),
        MCUModel(name='STC12LE5608', magic=0xe688, total=32768, code=8192, eeprom=22528),
        MCUModel(name='STC12LE5612', magic=0xe68c, total=32768, code=12288, eeprom=18432),
        MCUModel(name='STC12LE5616', magic=0xe690, total=32768, code=16384, eeprom=14336),
        MCUModel(name='STC12LE5620', magic=0xe694, total=32768, code=20480, eeprom=10240),
        MCUModel(name='STC12LE5624', magic=0xe698, total=32768, code=24576, eeprom=6144),
        MCUModel(name='STC12LE5628', magic=0xe69c, total=32768, code=28672, eeprom=2048),
        MCUModel(name='STC12LE5630', magic=0xe69e, total=32768, code=30720, eeprom=0),
        MCUModel(name='STC12C5401AD', magic=0xe061, total=32768, code=1024, eeprom=12288),
        MCUModel(name='STC12C5402AD', magic=0xe062, total=32768, code=2048, eeprom=12288),
        MCUModel(name='STC12C5404AD', magic=0xe064, total=32768, code=4096, eeprom=12288),
        MCUModel(name='STC12C5406AD', magic=0xe066, total=32768, code=6144, eeprom=12288),
        MCUModel(name='STC12C5408AD', magic=0xe068, total=32768, code=8192, eeprom=12288),
        MCUModel(name='STC12C5410AD', magic=0xe06a, total=32768, code=10240, eeprom=12288),
        MCUModel(name='STC12C5412AD', magic=0xe06c, total=32768, code=12288, eeprom=12288),
        MCUModel(name='STC12C5416AD', magic=0xe070, total=32768, code=16384, eeprom=12288),
        MCUModel(name='STC12C5420AD', magic=0xe074, total=32768, code=20480, eeprom=12288),
        MCUModel(name='STC12C5424AD', magic=0xe078, total=32768, code=24576, eeprom=12288),
        MCUModel(name='STC12C5428AD', magic=0xe07c, total=32768, code=28672, eeprom=12288),
        MCUModel(name='STC12C5401', magic=0xe001, total=32768, code=1024, eeprom=12288),
        MCUModel(name='STC12C5402', magic=0xe002, total=32768, code=2048, eeprom=12288),
        MCUModel(name='STC12C5404', magic=0xe004, total=32768, code=4096, eeprom=12288),
        MCUModel(name='STC12C5406', magic=0xe006, total=32768, code=6144, eeprom=12288),
        MCUModel(name='STC12C5408', magic=0xe008, total=32768, code=8192, eeprom=12288),
        MCUModel(name='STC12C5410', magic=0xe00a, total=32768, code=10240, eeprom=12288),
        MCUModel(name='STC12C5412', magic=0xe00c, total=32768, code=12288, eeprom=12288),
        MCUModel(name='STC12C5416', magic=0xe010, total=32768, code=16384, eeprom=12288),
        MCUModel(name='STC12C5420', magic=0xe014, total=32768, code=20480, eeprom=12288),
        MCUModel(name='STC12C5424', magic=0xe018, total=32768, code=24576, eeprom=12288),
        MCUModel(name='STC12C5428', magic=0xe01c, total=32768, code=28672, eeprom=12288),
        MCUModel(name='STC12LE5401AD', magic=0xe0e1, total=32768, code=1024, eeprom=22016),
        MCUModel(name='STC12LE5402AD', magic=0xe0e2, total=32768, code=2048, eeprom=20992),
        MCUModel(name='STC12LE5404AD', magic=0xe0e4, total=32768, code=4096, eeprom=18944),
        MCUModel(name='STC12LE5406AD', magic=0xe0e6, total=32768, code=6144, eeprom=16896),
        MCUModel(name='STC12LE5408AD', magic=0xe0e8, total=32768, code=8192, eeprom=10752),
        MCUModel(name='STC12LE5410AD', magic=0xe0ea, total=32768, code=10240, eeprom=4608),
        MCUModel(name='STC12LE5412AD', magic=0xe0ec, total=32768, code=12288, eeprom=11776),
        MCUModel(name='STC12LE5416AD', magic=0xe0f0, total=32768, code=16384, eeprom=12288),
        MCUModel(name='STC12LE5420AD', magic=0xe0f4, total=32768, code=20480, eeprom=8192),
        MCUModel(name='STC12LE5424AD', magic=0xe0f8, total=32768, code=24576, eeprom=4096),
        MCUModel(name='STC12LE5428AD', magic=0xe0fc, total=32768, code=28672, eeprom=0),
        MCUModel(name='STC12LE5401', magic=0xe081, total=32768, code=1024, eeprom=22016),
        MCUModel(name='STC12LE5402', magic=0xe082, total=32768, code=2048, eeprom=20992),
        MCUModel(name='STC12LE5404', magic=0xe084, total=32768, code=4096, eeprom=18944),
        MCUModel(name='STC12LE5406', magic=0xe086, total=32768, code=6144, eeprom=16896),
        MCUModel(name='STC12LE5408', magic=0xe088, total=32768, code=8192, eeprom=10752),
        MCUModel(name='STC12LE5410', magic=0xe08a, total=32768, code=10240, eeprom=4608),
        MCUModel(name='STC12LE5412', magic=0xe08c, total=32768, code=12288, eeprom=11776),
        MCUModel(name='STC12LE5416', magic=0xe090, total=32768, code=16384, eeprom=12288),
        MCUModel(name='STC12LE5420', magic=0xe094, total=32768, code=20480, eeprom=8192),
        MCUModel(name='STC12LE5424', magic=0xe098, total=32768, code=24576, eeprom=4096),
        MCUModel(name='STC12LE5428', magic=0xe09c, total=32768, code=28672, eeprom=0),
        MCUModel(name='STC12C1052AD', magic=0xf211, total=8192, code=1024, eeprom=4096),
        MCUModel(name='STC12C2052AD', magic=0xf212, total=8192, code=2048, eeprom=3072),
        MCUModel(name='STC12C3052AD', magic=0xf213, total=8192, code=3072, eeprom=2048),
        MCUModel(name='STC12C4052AD', magic=0xf214, total=8192, code=4096, eeprom=1024),
        MCUModel(name='STC12C5052AD', magic=0xf215, total=8192, code=5120, eeprom=0),
        MCUModel(name='STC12C1052', magic=0xf201, total=8192, code=1024, eeprom=4096),
        MCUModel(name='STC12C2052', magic=0xf202, total=8192, code=2048, eeprom=3072),
        MCUModel(name='STC12C3052', magic=0xf203, total=8192, code=3072, eeprom=2048),
        MCUModel(name='STC12C4052', magic=0xf204, total=8192, code=4096, eeprom=1024),
        MCUModel(name='STC12C5052', magic=0xf205, total=8192, code=5120, eeprom=0),
        MCUModel(name='STC12LE1052AD', magic=0xf231, total=8192, code=1024, eeprom=4096),
        MCUModel(name='STC12LE2052AD', magic=0xf232, total=8192, code=2048, eeprom=3072),
        MCUModel(name='STC12LE3052AD', magic=0xf233, total=8192, code=3072, eeprom=2048),
        MCUModel(name='STC12LE4052AD', magic=0xf234, total=8192, code=4096, eeprom=1024),
        MCUModel(name='STC12LE5052AD', magic=0xf235, total=8192, code=5120, eeprom=0),
        MCUModel(name='STC12LE1052', magic=0xf221, total=8192, code=1024, eeprom=4096),
        MCUModel(name='STC12LE2052', magic=0xf222, total=8192, code=2048, eeprom=3072),
        MCUModel(name='STC12LE3052', magic=0xf223, total=8192, code=3072, eeprom=2048),
        MCUModel(name='STC12LE4052', magic=0xf224, total=8192, code=4096, eeprom=1024),
        MCUModel(name='STC12LE5052', magic=0xf225, total=8192, code=5120, eeprom=0),
        MCUModel(name='STC90C51RC', magic=0xf021, total=16384, code=4096, eeprom=9216),
        MCUModel(name='STC90C52RC', magic=0xf022, total=16384, code=8192, eeprom=5120),
        MCUModel(name='STC90C53RC', magic=0xf024, total=16384, code=14336, eeprom=0),
        MCUModel(name='STC90C06RC', magic=0xf026, total=16384, code=6144, eeprom=7168),
        MCUModel(name='STC90C07RC', magic=0xf027, total=16384, code=7168, eeprom=6144),
        MCUModel(name='STC90C10RC', magic=0xf02a, total=16384, code=10240, eeprom=3072),
        MCUModel(name='STC90C12RC', magic=0xf02c, total=16384, code=12288, eeprom=1024),
        MCUModel(name='STC90LE51RC', magic=0xf041, total=16384, code=4096, eeprom=9216),
        MCUModel(name='STC90LE52RC', magic=0xf042, total=16384, code=8192, eeprom=5120),
        MCUModel(name='STC90LE53RC', magic=0xf044, total=16384, code=14336, eeprom=0),
        MCUModel(name='STC90LE06RC', magic=0xf046, total=16384, code=6144, eeprom=7168),
        MCUModel(name='STC90LE07RC', magic=0xf047, total=16384, code=7168, eeprom=6144),
        MCUModel(name='STC90LE10RC', magic=0xf04a, total=16384, code=10240, eeprom=3072),
        MCUModel(name='STC90LE12RC', magic=0xf04c, total=16384, code=12288, eeprom=1024),
        MCUModel(name='STC90C51RD+', magic=0xf121, total=65536, code=4096, eeprom=58368),
        MCUModel(name='STC90C52RD+', magic=0xf122, total=65536, code=8192, eeprom=54272),
        MCUModel(name='STC90C54RD+', magic=0xf124, total=65536, code=16384, eeprom=46080),
        MCUModel(name='STC90C55RD+', magic=0xf125, total=65536, code=20480, eeprom=41984),
        MCUModel(name='STC90C58RD+', magic=0xf128, total=65536, code=32768, eeprom=29696),
        MCUModel(name='STC90C510RD+', magic=0xf12a, total=65536, code=40960, eeprom=21504),
        MCUModel(name='STC90C512RD+', magic=0xf12c, total=65536, code=49152, eeprom=13312),
        MCUModel(name='STC90C513RD+', magic=0xf12d, total=65536, code=53248, eeprom=9216),
        MCUModel(name='STC90C514RD+', magic=0xf12e, total=65536, code=57344, eeprom=5120),
        MCUModel(name='STC90C516RD+', magic=0xf130, total=65536, code=62464, eeprom=0),
        MCUModel(name='STC90LE51RD+', magic=0xf141, total=65536, code=4096, eeprom=58368),
        MCUModel(name='STC90LE52RD+', magic=0xf142, total=65536, code=8192, eeprom=54272),
        MCUModel(name='STC90LE54RD+', magic=0xf144, total=65536, code=16384, eeprom=46080),
        MCUModel(name='STC90LE55RD+', magic=0xf145, total=65536, code=20480, eeprom=41984),
        MCUModel(name='STC90LE58RD+', magic=0xf148, total=65536, code=32768, eeprom=29696),
        MCUModel(name='STC90LE510RD+', magic=0xf14a, total=65536, code=40960, eeprom=21504),
        MCUModel(name='STC90LE512RD+', magic=0xf14c, total=65536, code=49152, eeprom=13312),
        MCUModel(name='STC90LE513RD+', magic=0xf14d, total=65536, code=53248, eeprom=9216),
        MCUModel(name='STC90LE514RD+', magic=0xf14e, total=65536, code=57344, eeprom=5120),
        MCUModel(name='STC90LE516RD+', magic=0xf150, total=65536, code=62464, eeprom=0),
        MCUModel(name='STC90C51AD', magic=0xf161, total=65536, code=4096, eeprom=58368),
        MCUModel(name='STC90C52AD', magic=0xf162, total=65536, code=8192, eeprom=54272),
        MCUModel(name='STC90C54AD', magic=0xf164, total=65536, code=16384, eeprom=46080),
        MCUModel(name='STC90C55AD', magic=0xf165, total=65536, code=20480, eeprom=41984),
        MCUModel(name='STC90C58AD', magic=0xf168, total=65536, code=32768, eeprom=29696),
        MCUModel(name='STC90C510AD', magic=0xf16a, total=65536, code=40960, eeprom=21504),
        MCUModel(name='STC90C512AD', magic=0xf16c, total=65536, code=49152, eeprom=13312),
        MCUModel(name='STC90C513AD', magic=0xf16d, total=65536, code=53248, eeprom=9216),
        MCUModel(name='STC90C514AD', magic=0xf16e, total=65536, code=57344, eeprom=5120),
        MCUModel(name='STC90C516AD', magic=0xf170, total=65536, code=62464, eeprom=0),
        MCUModel(name='STC90LE51AD', magic=0xf181, total=65536, code=4096, eeprom=58368),
        MCUModel(name='STC90LE52AD', magic=0xf182, total=65536, code=8192, eeprom=54272),
        MCUModel(name='STC90LE54AD', magic=0xf184, total=65536, code=16384, eeprom=46080),
        MCUModel(name='STC90LE55AD', magic=0xf185, total=65536, code=20480, eeprom=41984),
        MCUModel(name='STC90LE58AD', magic=0xf188, total=65536, code=32768, eeprom=29696),
        MCUModel(name='STC90LE510AD', magic=0xf18a, total=65536, code=40960, eeprom=21504),
        MCUModel(name='STC90LE512AD', magic=0xf18c, total=65536, code=49152, eeprom=13312),
        MCUModel(name='STC90LE513AD', magic=0xf18d, total=65536, code=53248, eeprom=9216),
        MCUModel(name='STC90LE514AD', magic=0xf18e, total=65536, code=57344, eeprom=5120),
        MCUModel(name='STC90LE516AD', magic=0xf190, total=65536, code=62464, eeprom=0),
        MCUModel(name='STC89C/LE51RC', magic=0xf001, total=16384, code=4096, eeprom=10240),
        MCUModel(name='STC89C/LE52RC', magic=0xf002, total=16384, code=8192, eeprom=6144),
        MCUModel(name='STC89C/LE53RC', magic=0xf004, total=16384, code=14336, eeprom=0),
        MCUModel(name='STC89C/LE06RC', magic=0xf006, total=16384, code=6144, eeprom=8192),
        MCUModel(name='STC89C/LE07RC', magic=0xf007, total=16384, code=7168, eeprom=7168),
        MCUModel(name='STC89C/LE10RC', magic=0xf00a, total=16384, code=10240, eeprom=4096),
        MCUModel(name='STC89C/LE12RC', magic=0xf00c, total=16384, code=12288, eeprom=2048),
        MCUModel(name='STC89C/LE51RD+', magic=0xf101, total=65536, code=4096, eeprom=59392),
        MCUModel(name='STC89C/LE52RD+', magic=0xf102, total=65536, code=8192, eeprom=55296),
        MCUModel(name='STC89C/LE54RD+', magic=0xf104, total=65536, code=16384, eeprom=47104),
        MCUModel(name='STC89C/LE55RD+', magic=0xf105, total=65536, code=20480, eeprom=43008),
        MCUModel(name='STC89C/LE58RD+', magic=0xf108, total=65536, code=32768, eeprom=30720),
        MCUModel(name='STC89C/LE510RD+', magic=0xf10a, total=65536, code=40960, eeprom=22528),
        MCUModel(name='STC89C/LE512RD+', magic=0xf10c, total=65536, code=49152, eeprom=14336),
        MCUModel(name='STC89C/LE513RD+', magic=0xf10d, total=65536, code=53248, eeprom=10240),
        MCUModel(name='STC89C/LE514RD+', magic=0xf10e, total=65536, code=57344, eeprom=6144),
        MCUModel(name='STC89C/LE516RD+', magic=0xf110, total=65536, code=63488, eeprom=0),
    )

    @classmethod
    def find_model(self, magic):
        for model in self.models:
            if model.magic == magic: return model
        raise NameError

    @classmethod
    def print_model_info(self, model):
        print("Target model:")
        print("  Name: %s" % model.name)
        print("  Magic: %02X%02X" % (model.magic >> 8, model.magic & 0xff))
        print("  Code flash: %.1f KB" % (model.code / 1024.0))
        print("  EEPROM flash: %.1f KB" % (model.eeprom / 1024.0))


class BaseOption:
    def print(self):
        print("Target options:")
        for name, get_func, _ in self.options:
            print("  %s=%s" % (name, get_func()))

    def set_option(self, name, value):
        for opt, _, set_func in self.options:
            if opt == name:
                print("Option %s=%s" % (name, value))
                set_func(value)
                return
        raise ValueError("unknown")

    def get_option(self, name):
        for opt, get_func, _ in self.options:
            if opt == name:
                return get_func(name)
        raise ValueError("unknown")

    def get_msr(self):
        return bytes(self.msr)


class Stc12Option(BaseOption):
    """Manipulate STC10/11/12 series option bytes"""

    def __init__(self, msr):
        assert len(msr) == 4
        self.msr = bytearray(msr)

        """list of options and their handlers"""
        self.options = (
            ("reset_pin_enabled", self.get_reset_pin_enabled, self.set_reset_pin_enabled),
            ("low_voltage_detect", self.get_low_voltage_detect, self.set_low_voltage_detect),
            ("oscillator_stable_delay", self.get_osc_stable_delay, self.set_osc_stable_delay),
            ("power_on_reset_delay", self.get_por_delay, self.set_por_delay),
            ("clock_gain", self.get_clock_gain, self.set_clock_gain),
            ("clock_source", self.get_clock_source, self.set_clock_source),
            ("watchdog_por_enabled", self.get_watchdog, self.set_watchdog),
            ("watchdog_stop_idle", self.get_watchdog_idle, self.set_watchdog_idle),
            ("watchdog_prescale", self.get_watchdog_prescale, self.set_watchdog_prescale),
            ("eeprom_erase_enabled", self.get_ee_erase, self.set_ee_erase),
            ("bsl_pindetect_enabled", self.get_pindetect, self.set_pindetect),
        )

    def get_reset_pin_enabled(self):
        return bool(self.msr[0] & 1)

    def set_reset_pin_enabled(self, val):
        val = Utils.to_bool(val);
        self.msr[0] &= 0xfe
        self.msr[0] |= 0x01 if bool(val) else 0x00

    def get_low_voltage_detect(self):
        return not bool(self.msr[0] & 64)

    def set_low_voltage_detect(self, val):
        val = Utils.to_bool(val);
        self.msr[0] &= 0xbf
        self.msr[0] |= 0x40 if not val else 0x00

    def get_osc_stable_delay(self):
        return 2 ** (((self.msr[0] >> 4) & 0x03) + 12)

    def set_osc_stable_delay(self, val):
        val = Utils.to_int(val)
        osc_vals = {4096: 0, 8192: 1, 16384: 2, 32768: 3}
        if val not in osc_vals.keys():
            raise ValueError("must be one of %s" % list(osc_vals.keys()))
        self.msr[0] &= 0xcf
        self.msr[0] |= osc_vals[val] << 4

    def get_por_delay(self):
        delay = not bool(self.msr[1] & 128)
        return "long" if delay else "short"

    def set_por_delay(self, val):
        delays = {"short": 1, "long": 0}
        if val not in delays.keys():
            raise ValueError("must be one of %s" % list(delays.keys()))
        self.msr[1] &= 0x7f
        self.msr[1] |= delays[val] << 7

    def get_clock_gain(self):
        gain = bool(self.msr[1] & 64)
        return "high" if gain else "low"

    def set_clock_gain(self, val):
        gains = {"low": 0, "high": 1}
        if val not in gains.keys():
            raise ValueError("must be one of %s" % list(gains.keys()))
        self.msr[1] &= 0xbf
        self.msr[1] |= gains[val] << 6

    def get_clock_source(self):
        source = bool(self.msr[1] & 2)
        return "external" if source else "internal"

    def set_clock_source(self, val):
        sources = {"internal": 0, "external": 1}
        if val not in sources.keys():
            raise ValueError("must be one of %s" % list(sources.keys()))
        self.msr[1] &= 0xfd
        self.msr[1] |= sources[val] << 1

    def get_watchdog(self):
        return not bool(self.msr[2] & 32)

    def set_watchdog(self, val):
        val = Utils.to_bool(val);
        self.msr[2] &= 0xdf
        self.msr[2] |= 0x20 if not val else 0x00

    def get_watchdog_idle(self):
        return not bool(self.msr[2] & 8)

    def set_watchdog_idle(self, val):
        val = Utils.to_bool(val);
        self.msr[2] &= 0xf7
        self.msr[2] |= 0x08 if not val else 0x00

    def get_watchdog_prescale(self):
        return 2 ** (((self.msr[2]) & 0x07) + 1)

    def set_watchdog_prescale(self, val):
        val = Utils.to_int(val)
        wd_vals = {2: 0, 4: 1, 8: 2, 16: 3, 32: 4, 64: 5, 128: 6, 256: 7}
        if val not in wd_vals.keys():
            raise ValueError("must be one of %s" % list(wd_vals.keys()))
        self.msr[2] &= 0xf8
        self.msr[2] |= wd_vals[val]

    def get_ee_erase(self):
        return not bool(self.msr[3] & 2)

    def set_ee_erase(self, val):
        val = Utils.to_bool(val);
        self.msr[3] &= 0xfd
        self.msr[3] |= 0x02 if not val else 0x00

    def get_pindetect(self):
        return not bool(self.msr[3] & 1)

    def set_pindetect(self, val):
        val = Utils.to_bool(val);
        self.msr[3] &= 0xfe
        self.msr[3] |= 0x01 if not val else 0x00


class Stc15Option(BaseOption):
    def __init__(self, msr):
        assert len(msr) == 13
        self.msr = bytearray(msr)

        self.options = (
            ("reset_pin_enabled", self.get_reset_pin_enabled, self.set_reset_pin_enabled),
            ("watchdog_por_enabled", self.get_watchdog, self.set_watchdog),
            ("watchdog_stop_idle", self.get_watchdog_idle, self.set_watchdog_idle),
            ("watchdog_prescale", self.get_watchdog_prescale, self.set_watchdog_prescale),
            ("low_voltage_reset", self.get_lvrs, self.set_lvrs),
            ("low_voltage_threshold", self.get_low_voltage, self.set_low_voltage),
            ("eeprom_lvd_inhibit", self.get_eeprom_lvd, self.set_eeprom_lvd),
            ("eeprom_erase_enabled", self.get_ee_erase, self.set_ee_erase),
            ("bsl_pindetect_enabled", self.get_pindetect, self.set_pindetect),
        )

    def set_trim(self, val):
        self.msr[3:5] = struct.pack(">H", val)

    def get_reset_pin_enabled(self):
        return bool(self.msr[0] & 16)

    def set_reset_pin_enabled(self, val):
        val = Utils.to_bool(val);
        self.msr[0] &= 0xef
        self.msr[0] |= 0x10 if bool(val) else 0x00

    def get_watchdog(self):
        return not bool(self.msr[2] & 32)

    def set_watchdog(self, val):
        val = Utils.to_bool(val);
        self.msr[2] &= 0xdf
        self.msr[2] |= 0x20 if not val else 0x00

    def get_watchdog_idle(self):
        return not bool(self.msr[2] & 8)

    def set_watchdog_idle(self, val):
        val = Utils.to_bool(val);
        self.msr[2] &= 0xf7
        self.msr[2] |= 0x08 if not val else 0x00

    def get_watchdog_prescale(self):
        return 2 ** (((self.msr[2]) & 0x07) + 1)

    def set_watchdog_prescale(self, val):
        val = Utils.to_int(val)
        wd_vals = {2: 0, 4: 1, 8: 2, 16: 3, 32: 4, 64: 5, 128: 6, 256: 7}
        if val not in wd_vals.keys():
            raise ValueError("must be one of %s" % list(wd_vals.keys()))
        self.msr[2] &= 0xf8
        self.msr[2] |= wd_vals[val]

    def get_lvrs(self):
        return bool(self.msr[1] & 64)

    def set_lvrs(self, val):
        val = Utils.to_bool(val);
        self.msr[1] &= 0xbf
        self.msr[1] |= 0x40 if val else 0x00

    def get_eeprom_lvd(self):
        return bool(self.msr[1] & 128)

    def set_eeprom_lvd(self, val):
        val = Utils.to_bool(val);
        self.msr[1] &= 0x7f
        self.msr[1] |= 0x80 if val else 0x00

    def get_low_voltage(self):
        return self.msr[1] & 0x07

    def set_low_voltage(self, val):
        val = Utils.to_int(val)
        if val not in range(0, 8):
            raise ValueError("must be one of %s" % list(range(0, 8)))
        self.msr[1] &= 0xf8
        self.msr[1] |= val

    def get_ee_erase(self):
        return not bool(self.msr[12] & 2)

    def set_ee_erase(self, val):
        val = Utils.to_bool(val);
        self.msr[12] &= 0xfd
        self.msr[12] |= 0x02 if not val else 0x00

    def get_pindetect(self):
        return not bool(self.msr[12] & 1)

    def set_pindetect(self, val):
        val = Utils.to_bool(val);
        self.msr[12] &= 0xfe
        self.msr[12] |= 0x01 if not val else 0x00


class Stc12Protocol:
    """Protocol handler for STC 10/11/12 series"""

    """magic word that starts a packet"""
    PACKET_START = bytes([0x46, 0xb9])

    """magic byte that ends a packet"""
    PACKET_END = bytes([0x16])

    """magic byte for packets received from MCU"""
    PACKET_MCU = bytes([0x68])

    """magic byte for packets sent by host"""
    PACKET_HOST = bytes([0x6a])

    """block size for programming flash"""
    PROGRAM_BLOCKSIZE = 128

    """countdown value for flash erase"""
    ERASE_COUNTDOWN = 0x0d

    def __init__(self, port, baud_handshake, baud_transfer):
        self.port = port
        self.baud_handshake = baud_handshake
        self.baud_transfer = baud_transfer

        self.mcu_magic = 0
        self.mcu_clock_hz = 0.0
        self.mcu_bsl_version = ""
        self.options = None
        self.model = None
        self.uid = None

    def dump_packet(self, data, receive=True):
        if DEBUG:
            print("%s Packet data: %s" % (("<-" if receive else "->"),
                  Utils.hexstr(data, " ")))

    def modular_sum(self, data):
        """modular 16-bit sum"""

        s = 0
        for b in data: s += b
        return s & 0xffff

    def read_bytes_safe(self, num):
        """Read data from serial port with timeout handling

        Read timeouts should raise an exception, that is the Python way."""

        data = self.ser.read(num)
        if len(data) != num:
            raise serial.SerialException("read timeout")

        return data

    def read_packet(self):
        """Read and check packet from MCU.
        
        Reads a packet of data from the MCU and and do
        validity and checksum checks on it.

        Returns packet payload or None in case of an error.
        """

        # read and check frame start magic
        packet = bytes()
        packet += self.read_bytes_safe(2)
        if packet[0:2] != self.PACKET_START:
            self.dump_packet(packet)
            raise RuntimeError("incorrect frame start")

        # read direction and length
        packet += self.read_bytes_safe(3)
        if packet[2] != self.PACKET_MCU[0]:
            self.dump_packet(packet)
            raise RuntimeError("incorrect packet direction magic")

        # read packet data
        packet_len, = struct.unpack(">H", packet[3:5])
        packet += self.read_bytes_safe(packet_len - 3)

        # verify end code
        if packet[packet_len+1] != self.PACKET_END[0]:
            self.dump_packet(packet)
            raise RuntimeError("incorrect frame end")

        # verify checksum
        packet_csum, = struct.unpack(">H", packet[packet_len-1:packet_len+1])
        calc_csum = sum(packet[2:packet_len-1]) & 0xffff
        if packet_csum != calc_csum:
            self.dump_packet(packet)
            raise RuntimeError("packet checksum mismatch")

        self.dump_packet(packet, receive=True)

        # payload only is returned
        return packet[5:packet_len-1]

    def write_packet(self, data):
        """Send packet to MCU.

        Constructs a packet with supplied payload and sends it to the MCU.
        """

        # frame start and direction magic
        packet = bytes()
        packet += self.PACKET_START
        packet += self.PACKET_HOST

        # packet length and payload
        packet += struct.pack(">H", len(data) + 6)
        packet += data

        # checksum and end code
        packet += struct.pack(">H", sum(packet[2:]) & 0xffff)
        packet += self.PACKET_END

        self.dump_packet(packet, receive=False)
        self.ser.write(packet)
        self.ser.flush()

    def initialize_status(self, packet):
        """Decode status packet and store basic MCU info"""

        self.mcu_magic, = struct.unpack(">H", packet[20:22])

        freq_counter = 0
        for i in range(8):
            freq_counter += struct.unpack(">H", packet[1+2*i:3+2*i])[0]
        freq_counter /= 8.0
        self.mcu_clock_hz = (self.baud_handshake * freq_counter * 12.0) / 7.0

        bl_version, bl_stepping = struct.unpack("BB", packet[17:19])
        self.mcu_bsl_version = "%d.%d%s" % (bl_version >> 4, bl_version & 0x0f,
                                           chr(bl_stepping))

    def calculate_baud(self):
        """Calculate MCU baudrate setting.

        Calculate appropriate baudrate settings for the MCU's UART,
        according to clock frequency and requested baud rate.
        """

        # baudrate is directly controlled by programming the MCU's BRT register
        brt = 256 - round((self.mcu_clock_hz) / (self.baud_transfer * 16))
        brt_csum = (2 * (256 - brt)) & 0xff
        try: baud_actual = (self.mcu_clock_hz) / (16 * (256 - brt))
        except ZeroDivisionError: raise RuntimeError("baudrate too high")
        baud_error = (abs(self.baud_transfer - baud_actual) * 100.0) / self.baud_transfer
        if baud_error > 5.0:
            print("WARNING: baud rate error is %.2f%%. You may need to set a slower rate." %
                  baud_error, file=sys.stderr)

        # IAP wait states (according to datasheet(s))
        iap_wait = 0x80
        if self.mcu_clock_hz < 1E6: iap_wait = 0x87
        elif self.mcu_clock_hz < 2E6: iap_wait = 0x86
        elif self.mcu_clock_hz < 3E6: iap_wait = 0x85
        elif self.mcu_clock_hz < 6E6: iap_wait = 0x84
        elif self.mcu_clock_hz < 12E6: iap_wait = 0x83
        elif self.mcu_clock_hz < 20E6: iap_wait = 0x82
        elif self.mcu_clock_hz < 24E6: iap_wait = 0x81

        # MCU delay after switching baud rates
        delay = 0x80

        return brt, brt_csum, iap_wait, delay
        
    def print_mcu_info(self):
        """Print MCU status information"""

        MCUModelDatabase.print_model_info(self.model)
        print("Target frequency: %.3f MHz" % (self.mcu_clock_hz / 1E6))
        print("Target BSL version: %s" % self.mcu_bsl_version)

    def pulse(self):
        """Send a sequence of 0x7f bytes for synchronization"""

        while True:
            self.ser.write(b"\x7f")
            self.ser.flush()
            time.sleep(0.015)
            if self.ser.inWaiting() > 0: break

    def initialize_model(self):
        """Initialize model-specific information"""

        try:
            self.model = MCUModelDatabase.find_model(self.mcu_magic)
        except NameError:
            msg = ("WARNING: Unknown model %02X%02X!" %
                (self.mcu_magic >> 8, self.mcu_magic & 0xff))
            print(msg, file=sys.stderr)
            self.model = MCUModelDatabase.MCUModel(name="UNKNOWN",
                magic=self.mcu_magic, total=63488, code=63488, eeprom=0)
        self.print_mcu_info()

    def get_status_packet(self):
        """Read and decode status packet"""

        status_packet = self.read_packet()
        if status_packet[0] != 0x50:
            raise RuntimeError("incorrect magic in status packet")
        return status_packet

    def initialize_options(self, status_packet):
        """Initialize options"""

        # create option state
        self.options = Stc12Option(status_packet[23:27])
        self.options.print()

    def connect(self):
        """Connect to MCU and initialize communication.

        Set up serial port, send sync sequence and get part info.
        """

        self.ser = serial.Serial(port=self.port, baudrate=self.baud_handshake,
                                 parity=serial.PARITY_EVEN)

        # conservative timeout values
        self.ser.timeout = 10.0
        self.ser.interCharTimeout = 1.0

        print("Waiting for MCU, please cycle power: ", end="")
        sys.stdout.flush()

        # send sync, and wait for MCU response
        # ignore errors until we see a valid response
        status_packet = None
        while not status_packet:
            try:
                self.pulse()
                status_packet = self.get_status_packet()
            except (RuntimeError, serial.SerialException): pass
        print("done")

        self.initialize_status(status_packet)
        self.initialize_model()
        self.initialize_options(status_packet)

    def handshake(self):
        """Do baudrate handshake

        Initate and do the (rather complicated) baudrate handshake.
        """

        # start baudrate handshake
        brt, brt_csum, iap, delay = self.calculate_baud()
        print("Switching to %d baud: " % self.baud_transfer, end="")
        sys.stdout.flush()
        packet = bytes([0x50, 0x00, 0x00, 0x36, 0x01])
        packet += struct.pack(">H", self.mcu_magic)
        self.write_packet(packet)
        response = self.read_packet()
        if response[0] != 0x8f:
            raise RuntimeError("incorrect magic in handshake packet")

        # test new settings
        print("testing ", end="")
        sys.stdout.flush()
        packet = bytes([0x8f, 0xc0, brt, 0x3f, brt_csum, delay, iap])
        self.write_packet(packet)
        time.sleep(0.2)
        self.ser.baudrate = self.baud_transfer
        response = self.read_packet()
        self.ser.baudrate = self.baud_handshake
        if response[0] != 0x8f:
            raise RuntimeError("incorrect magic in handshake packet")

        # switch to the settings
        print("setting ", end="")
        sys.stdout.flush()
        packet = bytes([0x8e, 0xc0, brt, 0x3f, brt_csum, delay])
        self.write_packet(packet)
        time.sleep(0.2)
        self.ser.baudrate = self.baud_transfer
        response = self.read_packet()
        if response[0] != 0x84:
            raise RuntimeError("incorrect magic in handshake packet")

        print("done")

    def erase_flash(self, erase_size, flash_size):
        """Erase the MCU's flash memory.

        Erase the flash memory with a block-erase command.
        """

        blks = ((erase_size + 511) // 512) * 2
        size = ((flash_size + 511) // 512) * 2
        print("Erasing %d blocks: " % blks, end="")
        sys.stdout.flush()
        packet = bytes([0x84, 0xff, 0x00, blks, 0x00, 0x00, size,
                        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0x00, 0x00, 0x00, 0x00])
        for i in range(0x80, self.ERASE_COUNTDOWN, -1): packet += bytes([i])
        self.write_packet(packet)
        response = self.read_packet()
        if response[0] != 0x00:
            raise RuntimeError("incorrect magic in erase packet")
        print("done")

        # UID, only sent with this packet by some BSLs
        if len(response) >= 8:
            self.uid = response[1:8]

    def program_flash(self, data):
        """Program the MCU's flash memory.

        Write data into flash memory, using the PROGRAM_BLOCKSIZE
        as the block size (depends on MCU's RAM size).
        """

        print("Writing %d bytes: " % len(data), end="")
        sys.stdout.flush()
        for i in range(0, len(data), self.PROGRAM_BLOCKSIZE):
            packet = bytes(3)
            packet += struct.pack(">H", i)
            packet += struct.pack(">H", self.PROGRAM_BLOCKSIZE)
            packet += data[i:i+self.PROGRAM_BLOCKSIZE]
            while len(packet) < self.PROGRAM_BLOCKSIZE + 7: packet += b"\x00"
            csum = sum(packet[7:]) & 0xff
            self.write_packet(packet)
            response = self.read_packet()
            if response[0] != 0x00:
                raise RuntimeError("incorrect magic in write packet")
            elif response[1] != csum:
                raise RuntimeError("verification checksum mismatch")
            print(".", end="")
            sys.stdout.flush()
        print(" done")

        print("Finishing write: ", end="")
        sys.stdout.flush()
        packet = bytes([0x69, 0x00, 0x00, 0x36, 0x01])
        packet += struct.pack(">H", self.mcu_magic)
        self.write_packet(packet)
        response = self.read_packet()
        if response[0] != 0x8d:
            raise RuntimeError("incorrect magic in finish packet")
        print("done")

    def set_option(self, name, value):
        self.options.set_option(name, value)

    def program_options(self):
        print("Setting options: ", end="")
        sys.stdout.flush()
        msr = self.options.get_msr()
        packet = bytes([0x8d, msr[0], msr[1], msr[2], msr[3],
                        0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
                        0xff, 0xff, 0xff, 0xff, 0xff, 0xff])

        packet += struct.pack(">I", int(self.mcu_clock_hz))
        self.write_packet(packet)
        response = self.read_packet()
        if response[0] != 0x50:
            raise RuntimeError("incorrect magic in option packet")
        print("done")

        # If UID wasn't sent with erase acknowledge, it should be in this packet
        if not self.uid:
            self.uid = response[18:25]

        print("Target UID: %s" % Utils.hexstr(self.uid))

    def disconnect(self):
        """Disconnect from MCU"""

        # reset mcu
        packet = bytes([0x82])
        self.write_packet(packet)
        self.ser.close()
        print("Disconnected!")


class Stc15Protocol(Stc12Protocol):
    """Protocol handler for STC 15 series"""

    ERASE_COUNTDOWN = 0x5e
    PROGRAM_BLOCKSIZE = 64

    def __init__(self, port, handshake, baud, trim):
        Stc12Protocol.__init__(self, port, handshake, baud)

        self.trim_frequency = trim
        self.trim_data = None
        self.frequency_counter = 0

    def initialize_options(self, status_packet):
        """Initialize options"""

        # create option state
        self.options = Stc15Option(status_packet[23:36])
        self.options.print()

    def get_status_packet(self):
        """Read and decode status packet"""

        status_packet = self.read_packet()
        if status_packet[0] == 0x80:
            # need to re-ack
            packet = bytes([0x80])
            self.write_packet(packet)
            self.pulse()
            status_packet = self.read_packet()
        if status_packet[0] != 0x50:
            raise RuntimeError("incorrect magic in status packet")
        return status_packet

    def initialize_status(self, packet):
        """Decode status packet and store basic MCU info"""

        self.mcu_magic, = struct.unpack(">H", packet[20:22])

        freq_counter = 0
        for i in range(4):
            freq_counter += struct.unpack(">H", packet[1+2*i:3+2*i])[0]
        freq_counter /= 4.0
        self.mcu_clock_hz = (self.baud_handshake * freq_counter * 12.0) / 7.0

        bl_version, bl_stepping = struct.unpack("BB", packet[17:19])
        self.mcu_bsl_version = "%d.%d%s" % (bl_version >> 4, bl_version & 0x0f,
                                           chr(bl_stepping))

        self.trim_data = packet[51:58]
        self.freq_counter = freq_counter

    def get_trim_sequence(self, frequency):
        """Return frequency-specific coarse trim sequence"""

        packet = bytes()
        if frequency < 7.5E6:
            packet += bytes([0x18, 0x00, 0x02, 0x00])
            packet += bytes([0x18, 0x80, 0x02, 0x00])
            packet += bytes([0x18, 0x80, 0x02, 0x00])
            packet += bytes([0x18, 0xff, 0x02, 0x00])
        elif frequency < 10E6:
            packet += bytes([0x18, 0x80, 0x02, 0x00])
            packet += bytes([0x18, 0xff, 0x02, 0x00])
            packet += bytes([0x58, 0x00, 0x02, 0x00])
            packet += bytes([0x58, 0xff, 0x02, 0x00])
        elif frequency < 15E6:
            packet += bytes([0x58, 0x00, 0x02, 0x00])
            packet += bytes([0x58, 0x80, 0x02, 0x00])
            packet += bytes([0x58, 0x80, 0x02, 0x00])
            packet += bytes([0x58, 0xff, 0x02, 0x00])
        elif frequency < 21E6:
            packet += bytes([0x58, 0x80, 0x02, 0x00])
            packet += bytes([0x58, 0xff, 0x02, 0x00])
            packet += bytes([0x98, 0x00, 0x02, 0x00])
            packet += bytes([0x98, 0x80, 0x02, 0x00])
        elif frequency < 31E6:
            packet += bytes([0x98, 0x00, 0x02, 0x00])
            packet += bytes([0x98, 0x80, 0x02, 0x00])
            packet += bytes([0x98, 0x80, 0x02, 0x00])
            packet += bytes([0x98, 0xff, 0x02, 0x00])
        else:
            packet += bytes([0xd8, 0x00, 0x02, 0x00])
            packet += bytes([0xd8, 0x80, 0x02, 0x00])
            packet += bytes([0xd8, 0x80, 0x02, 0x00])
            packet += bytes([0xd8, 0xb4, 0x02, 0x00])

        return packet

    def handshake(self):
        """Initiate and do the frequency adjustment and baudrate
        switch handshake.

        This rather complicated handshake trims the MCU's calibrated RC
        frequency and switches the baud rate at the same time.

        Flash programming uses a fixed frequency and that frequency is
        calibrated along with the frequency specified by the user.
        """

        user_speed = self.trim_frequency
        if user_speed <= 0: user_speed = self.mcu_clock_hz
        program_speed = 22118400

        user_count = int(self.freq_counter * (user_speed / self.mcu_clock_hz))
        program_count = int(self.freq_counter * (program_speed / self.mcu_clock_hz))

        # Initiate handshake
        print("Trimming frequency: ", end="")
        sys.stdout.flush()
        packet = bytes([0x50, 0x00, 0x00, 0x36, 0x01])
        packet += struct.pack(">H", self.mcu_magic)
        self.write_packet(packet)
        response = self.read_packet()
        if response[0] != 0x8f:
            raise RuntimeError("incorrect magic in handshake packet")

        # trim challenge-response, first round
        packet = bytes([0x65])
        packet += self.trim_data
        packet += bytes([0xff, 0xff, 0x06, 0x06])
        # add trim challenges for target frequency
        packet += self.get_trim_sequence(user_speed)
        # add trim challenge for program frequency
        packet += bytes([0x98, 0x00, 0x02, 0x00])
        packet += bytes([0x98, 0x80, 0x02, 0x00])
        self.write_packet(packet)
        self.pulse()
        response = self.read_packet()
        if response[0] != 0x65:
            raise RuntimeError("incorrect magic in handshake packet")

        # determine programming speed trim value
        target_trim_a, target_count_a = struct.unpack(">HH", response[28:32])
        target_trim_b, target_count_b = struct.unpack(">HH", response[32:36])
        m = (target_trim_b - target_trim_a) / (target_count_b - target_count_a)
        n = target_trim_a - m * target_count_a
        program_trim = round(m * program_count + n)

        # determine trim trials for second round
        trim_a, count_a = struct.unpack(">HH", response[12:16])
        trim_b, count_b = struct.unpack(">HH", response[16:20])
        trim_c, count_c = struct.unpack(">HH", response[20:24])
        trim_d, count_d = struct.unpack(">HH", response[24:28])
        # select suitable coarse trim range
        if count_c <= user_count and count_d >= user_count:
            target_trim_a = trim_c
            target_trim_b = trim_d
            target_count_a = count_c
            target_count_b = count_d
        else:
            target_trim_a = trim_a
            target_trim_b = trim_b
            target_count_a = count_a
            target_count_b = count_b
        # linear interpolate to find range to try next
        m = (target_trim_b - target_trim_a) / (target_count_b - target_count_a)
        n = target_trim_a - m * target_count_a
        target_trim = round(m * user_count + n)
        target_trim_start = min(max(target_trim - 5, target_trim_a), target_trim_b)

        # trim challenge-response, second round
        packet = bytes([0x65])
        packet += self.trim_data
        packet += bytes([0xff, 0xff, 0x06, 0x0B])
        for i in range(11):
            packet += struct.pack(">H", target_trim_start + i)
            packet += bytes([0x02, 0x00])
        self.write_packet(packet)
        self.pulse()
        response = self.read_packet()
        if response[0] != 0x65:
            raise RuntimeError("incorrect magic in handshake packet")

        # determine best trim value
        best_trim = 0
        best_count = 65535
        for i in range(11):
            trim, count = struct.unpack(">HH", response[12+4*i:16+4*i])
            if abs(count - user_count) < abs(best_count - user_count):
                best_trim = trim
                best_count = count
        final_freq = (best_count / self.freq_counter) * self.mcu_clock_hz
        print("%.03f MHz" % (final_freq / 1E6))
        self.options.set_trim(best_trim)

        # finally, switch baudrate
        print("Switching to %d baud: " % self.baud_transfer, end="")
        packet = bytes([0x8e])
        packet += struct.pack(">H", program_trim)
        packet += struct.pack(">B", 230400 // self.baud_transfer)
        packet += bytes([0xa1, 0x64, 0xb8, 0x00, 0x81, 0x20, 0xff, 0x00])
        self.write_packet(packet)
        time.sleep(0.2)
        self.ser.baudrate = self.baud_transfer
        response = self.read_packet()
        if response[0] != 0x84:
            raise RuntimeError("incorrect magic in handshake packet")
        print("done")

    def program_options(self):
        print("Setting options: ", end="")
        sys.stdout.flush()
        msr = self.options.get_msr()
        packet = bytes([0x8d])
        packet += msr
        packet += bytes([0xff, 0xff, 0xff, 0xff, 0xff, 0xff])

        self.write_packet(packet)
        response = self.read_packet()
        if response[0] != 0x50:
            raise RuntimeError("incorrect magic in option packet")
        print("done")

        print("Target UID: %s" % Utils.hexstr(self.uid))


class StcGal:
    """STC ISP flash tool frontend"""

    def __init__(self, opts):
        self.opts = opts
        if opts.protocol == "stc12":
            self.protocol = Stc12Protocol(opts.port, opts.handshake, opts.baud)
        else:
            self.protocol = Stc15Protocol(opts.port, opts.handshake, opts.baud,
                                          round(opts.trim * 1000))

    def emit_options(self, options):
        for o in options:
            try:
                kv = o.split("=", 1)
                if len(kv) < 2: raise ValueError("incorrect format")
                self.protocol.set_option(kv[0], kv[1])
            except ValueError as e:
                raise NameError("invalid option '%s' (%s)" % (kv[0], e))

    def program_mcu(self):
        code_size = self.protocol.model.code
        ee_size = self.protocol.model.eeprom

        bindata = opts.code_binary.read()

        # warn if it overflows
        if len(bindata) > code_size:
            print("WARNING: code_binary overflows into eeprom segment!", file=sys.stderr)
        if len(bindata) > (code_size + ee_size):
            print("WARNING: code_binary truncated!", file=sys.stderr)
            bindata = bindata[0:code_size + ee_size]

        # add eeprom data if supplied
        if opts.eeprom_binary:
            eedata = opts.eeprom_binary.read()
            if len(eedata) > ee_size:
                print("WARNING: eeprom_binary truncated!", file=sys.stderr)
                eedata = eedata[0:ee_size]
            if len(bindata) < code_size:
                bindata += bytes(code_size - len(bindata))
            elif len(bindata) > code_size:
                print("WARNING: eeprom_binary overlaps code_binary!", file=sys.stderr)
                bindata = bindata[0:code_size]
            bindata += eedata

        # pad to 256 byte boundary
        if len(bindata) % 256:
            bindata += bytes(256 - len(bindata) % 256)

        if opts.option: self.emit_options(opts.option)

        self.protocol.handshake()
        self.protocol.erase_flash(len(bindata), code_size)
        self.protocol.program_flash(bindata)
        self.protocol.program_options()
        self.protocol.disconnect()

    def run(self):
        try: self.protocol.connect()
        except KeyboardInterrupt:
            print("interrupted")
            return 2
        except RuntimeError as e:
            print("Communication error: %s" % e, file=sys.stderr)
            self.protocol.disconnect()
            return 1
        except serial.SerialException as e:
            print("Serial communication error: %s" % e, file=sys.stderr)
            return 1

        try:
            if opts.code_binary:
                self.program_mcu()
                return 0
            else:
                self.protocol.disconnect()
                return 0
        except NameError as e:
            print("Option error: %s" % e, file=sys.stderr)
            self.protocol.disconnect()
            return 1
        except RuntimeError as e:
            print("Communication error: %s" % e, file=sys.stderr)
            self.protocol.disconnect()
            return 1
        except KeyboardInterrupt:
            print("interrupted")
            self.protocol.disconnect()
            return 2
        except serial.SerialException as e:
            print("Serial communication error: %s" % e, file=sys.stderr)
            return 1


if __name__ == "__main__":
    # check arguments
    parser = argparse.ArgumentParser(description="STC MCU ISP flash tool")
    parser.add_argument("code_binary", help="code segment binary file to flash", type=argparse.FileType("rb"), nargs='?')
    parser.add_argument("eeprom_binary", help="eeprom segment binary file to flash", type=argparse.FileType("rb"), nargs='?')
    parser.add_argument("-P", "--protocol", help="protocol version", choices=["stc12", "stc15"], default="stc12")
    parser.add_argument("-p", "--port", help="serial port device", default="/dev/ttyUSB0")
    parser.add_argument("-b", "--baud", help="transfer baud rate (default: 19200)", type=BaudType(), default=19200)
    parser.add_argument("-l", "--handshake", help="handshake baud rate (default: 2400)", type=BaudType(), default=2400)
    parser.add_argument("-o", "--option", help="set option (can be used multiple times)", action="append")
    parser.add_argument("-t", "--trim", help="RC oscillator frequency in kHz (STC15 series only)", type=float, default=0.0)
    opts = parser.parse_args()
    
    # run programmer
    gal = StcGal(opts)
    sys.exit(gal.run())
