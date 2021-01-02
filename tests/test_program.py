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

"""Tests that simulate a whole programming cycle"""

import unittest
from unittest.mock import patch
import yaml
import stcgal.frontend
import stcgal.protocols
from stcgal.protocols import StcProtocolException

def convert_to_bytes(list_of_lists):
    """Convert lists of integer lists to list of byte lists"""
    return [bytes(x) for x in list_of_lists]

def get_default_opts():
    """Get a default preconfigured option object"""
    opts = unittest.mock.MagicMock()
    opts.protocol = "stc89"
    opts.autoreset = False
    opts.port = ""
    opts.baud = 19200
    opts.handshake = 9600
    opts.trim = 22118
    opts.eeprom_image = None
    opts.debug = False
    opts.version = False
    opts.code_image.name = "test.bin"
    opts.code_image.read.return_value = b"123456789"
    return opts

class ProgramTests(unittest.TestCase):
    """Test MCU programming cycles for different families, based on traces"""

    @patch("stcgal.protocols.StcBaseProtocol.read_packet")
    @patch("stcgal.protocols.Stc89Protocol.write_packet")
    @patch("stcgal.protocols.serial.Serial", autospec=True)
    @patch("stcgal.protocols.time.sleep")
    @patch("sys.stdout")
    def test_program_stc89(self, out, sleep_mock, serial_mock, write_mock, read_mock):
        """Test a programming cycle with STC89 protocol"""
        self._program_yml("./tests/stc89c52rc.yml", serial_mock, read_mock)

    @patch("stcgal.protocols.StcBaseProtocol.read_packet")
    @patch("stcgal.protocols.Stc89Protocol.write_packet")
    @patch("stcgal.protocols.serial.Serial", autospec=True)
    @patch("stcgal.protocols.time.sleep")
    @patch("sys.stdout")
    def test_program_stc12(self, out, sleep_mock, serial_mock, write_mock, read_mock):
        """Test a programming cycle with STC12 protocol"""
        self._program_yml("./tests/stc12c5a60s2.yml", serial_mock, read_mock)

    @patch("stcgal.protocols.StcBaseProtocol.read_packet")
    @patch("stcgal.protocols.Stc89Protocol.write_packet")
    @patch("stcgal.protocols.serial.Serial", autospec=True)
    @patch("stcgal.protocols.time.sleep")
    @patch("sys.stdout")
    def test_program_stc12a(self, out, sleep_mock, serial_mock, write_mock, read_mock):
        """Test a programming cycle with STC12A protocol"""
        self._program_yml("./tests/stc12c2052ad.yml", serial_mock, read_mock)

    def test_program_stc12b(self):
        """Test a programming cycle with STC12B protocol"""
        self.skipTest("trace missing")

    @patch("stcgal.protocols.StcBaseProtocol.read_packet")
    @patch("stcgal.protocols.Stc89Protocol.write_packet")
    @patch("stcgal.protocols.serial.Serial", autospec=True)
    @patch("stcgal.protocols.time.sleep")
    @patch("sys.stdout")
    def test_program_stc15f2(self, out, sleep_mock, serial_mock, write_mock, read_mock):
        """Test a programming cycle with STC15 protocol, F2 series"""
        self._program_yml("./tests/iap15f2k61s2.yml", serial_mock, read_mock)

    @patch("stcgal.protocols.StcBaseProtocol.read_packet")
    @patch("stcgal.protocols.Stc89Protocol.write_packet")
    @patch("stcgal.protocols.serial.Serial", autospec=True)
    @patch("stcgal.protocols.time.sleep")
    @patch("sys.stdout")
    def test_program_stc15w4(self, out, sleep_mock, serial_mock, write_mock, read_mock):
        """Test a programming cycle with STC15 protocol, W4 series"""
        self._program_yml("./tests/stc15w4k56s4.yml", serial_mock, read_mock)

    @patch("stcgal.protocols.StcBaseProtocol.read_packet")
    @patch("stcgal.protocols.Stc89Protocol.write_packet")
    @patch("stcgal.protocols.serial.Serial", autospec=True)
    @patch("stcgal.protocols.time.sleep")
    @patch("sys.stdout")
    def test_program_stc8a8(self, out, sleep_mock, serial_mock, write_mock, read_mock):
        """Test a programming cycle with STC8 protocol, STC8A8 series"""
        self._program_yml("./tests/stc8a8k64s4a12.yml", serial_mock, read_mock)

    @unittest.skip("trace is broken")
    @patch("stcgal.protocols.StcBaseProtocol.read_packet")
    @patch("stcgal.protocols.Stc89Protocol.write_packet")
    @patch("stcgal.protocols.serial.Serial", autospec=True)
    @patch("stcgal.protocols.time.sleep")
    @patch("sys.stdout")
    def test_program_stc15a(self, out, sleep_mock, serial_mock, write_mock, read_mock):
        """Test a programming cycle with STC15A protocol"""
        self._program_yml("./tests/stc15f104e.yml", serial_mock, read_mock)

    @patch("stcgal.protocols.StcBaseProtocol.read_packet")
    @patch("stcgal.protocols.Stc89Protocol.write_packet")
    @patch("stcgal.protocols.serial.Serial", autospec=True)
    @patch("stcgal.protocols.time.sleep")
    @patch("sys.stdout")
    def test_program_stc15l1(self, out, sleep_mock, serial_mock, write_mock, read_mock):
        """Test a programming cycle with STC15 protocol, L1 series"""
        self._program_yml("./tests/stc15l104w.yml", serial_mock, read_mock)

    @patch("stcgal.protocols.StcBaseProtocol.read_packet")
    @patch("stcgal.protocols.Stc89Protocol.write_packet")
    @patch("stcgal.protocols.serial.Serial", autospec=True)
    @patch("stcgal.protocols.time.sleep")
    @patch("sys.stdout")
    def test_program_stc8_untrimmed(self, out, sleep_mock, serial_mock, write_mock, read_mock):
        """Test error with untrimmed MCU"""
        with open("./tests/stc8f2k08s2-untrimmed.yml") as test_file:
            test_data = yaml.load(test_file.read(), Loader=yaml.SafeLoader)
            opts = get_default_opts()
            opts.trim = 0.0
            opts.protocol = test_data["protocol"]
            opts.code_image.read.return_value = bytes(test_data["code_data"])
            serial_mock.return_value.inWaiting.return_value = 1
            read_mock.side_effect = convert_to_bytes(test_data["responses"])
            gal = stcgal.frontend.StcGal(opts)
            self.assertEqual(gal.run(), 1)

    def test_program_stc15w4_usb(self):
        """Test a programming cycle with STC15W4 USB protocol"""
        self.skipTest("USB not supported yet, trace missing")

    def _program_yml(self, yml, serial_mock, read_mock):
        """Program MCU with data from YAML file"""
        with open(yml) as test_file:
            test_data = yaml.load(test_file.read(), Loader=yaml.SafeLoader)
            opts = get_default_opts()
            opts.protocol = test_data["protocol"]
            opts.code_image.read.return_value = bytes(test_data["code_data"])
            serial_mock.return_value.inWaiting.return_value = 1
            read_mock.side_effect = convert_to_bytes(test_data["responses"])
            gal = stcgal.frontend.StcGal(opts)
            self.assertEqual(gal.run(), 0)
