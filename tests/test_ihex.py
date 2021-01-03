#
# Copyright (c) 2021 Grigori Goronzy <greg@chown.ath.cx>
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

import unittest
import stcgal.ihex

class IHEXTests(unittest.TestCase):
    """Tests for IHEX reader"""

    def test_simple(self):
        """Test reading a basic, valid file"""
        lines = [
            b":0B00000068656C6C6F5F776F726C645A",
            b":00000001FF"
        ]
        bindata = stcgal.ihex.IHex.read(lines).extract_data()
        self.assertEqual(bindata, b"hello_world")

    def test_empty(self):
        """Test reading an empty file"""
        lines = []
        bindata = stcgal.ihex.IHex.read(lines).extract_data()
        self.assertEqual(bindata, b"")

    def test_invalid(self):
        """Test invalid encoded data"""
        lines = [
            ":abc"
        ]
        with self.assertRaises(ValueError):
            stcgal.ihex.IHex.read(lines)

    def test_roundtrip(self):
        """Test round-trip through encoder/decoder"""
        bindata = b"12345678"
        for mode in (8, 16, 32):
            with self.subTest(mode):
                hexer = stcgal.ihex.IHex()
                hexer.set_mode(mode)
                hexer.insert_data(0, bindata)
                encoded = hexer.write().encode("ASCII").splitlines()
                decoded = stcgal.ihex.IHex.read(encoded).extract_data()
                self.assertEqual(decoded, bindata)
