#
# Copyright (c) 2017 Grigori Goronzy <greg@chown.ath.cx>
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

"""Tests for utility functions and other misc parts"""

import argparse
import unittest
from stcgal.utils import Utils, BaudType

class TestUtils(unittest.TestCase):
    """Test for utility functions in the Utils class"""

    def test_to_bool(self):
        """Test special utility function for bool conversion"""
        self.assertTrue(Utils.to_bool(True))
        self.assertTrue(Utils.to_bool("true"))
        self.assertTrue(Utils.to_bool("True"))
        self.assertTrue(Utils.to_bool("t"))
        self.assertTrue(Utils.to_bool("T"))
        self.assertTrue(Utils.to_bool(1))
        self.assertTrue(Utils.to_bool(-1))
        self.assertFalse(Utils.to_bool(0))
        self.assertFalse(Utils.to_bool(None))
        self.assertFalse(Utils.to_bool("false"))
        self.assertFalse(Utils.to_bool("False"))
        self.assertFalse(Utils.to_bool("f"))
        self.assertFalse(Utils.to_bool("F"))
        self.assertFalse(Utils.to_bool(""))

    def test_to_int(self):
        """Test wrapped integer conversion"""
        self.assertEqual(Utils.to_int("2"), 2)
        self.assertEqual(Utils.to_int("0x10"), 16)
        with self.assertRaises(ValueError):
            Utils.to_int("a")
        with self.assertRaises(ValueError):
            Utils.to_int("")
        with self.assertRaises(ValueError):
            Utils.to_int(None)

    def test_hexstr(self):
        """Test byte array formatter"""
        self.assertEqual(Utils.hexstr([10]), "0A")
        self.assertEqual(Utils.hexstr([1, 2, 3]), "010203")
        with self.assertRaises(Exception):
            Utils.hexstr([400, 500])

    def test_decode_packed_bcd(self):
        """Test packed BCD decoder"""
        self.assertEqual(Utils.decode_packed_bcd(0x01), 1)
        self.assertEqual(Utils.decode_packed_bcd(0x10), 10)
        self.assertEqual(Utils.decode_packed_bcd(0x11), 11)
        self.assertEqual(Utils.decode_packed_bcd(0x25), 25)
        self.assertEqual(Utils.decode_packed_bcd(0x99), 99)

class TestBaudType(unittest.TestCase):
    """Test BaudType class"""

    def test_create_baud_type(self):
        """Test creation of BaudType instances"""
        baud_type = BaudType()
        self.assertEqual(baud_type("2400"), 2400)
        self.assertEqual(baud_type("115200"), 115200)
        with self.assertRaises(argparse.ArgumentTypeError):
            baud_type("2374882")
