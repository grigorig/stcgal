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

"""Tests with fuzzing of input data"""

import random
import sys
import unittest
from unittest.mock import patch
import yaml
import stcgal.frontend
import stcgal.protocols
from tests.test_program import get_default_opts, convert_to_bytes

class ByteArrayFuzzer:
    """Fuzzer for byte arrays"""

    def __init__(self):
        self.rng = random.Random()
        self.cut_propability = 0.01 # probability for cutting off an array early
        self.cut_min = 0 # minimum cut amount
        self.cut_max = sys.maxsize # maximum cut amount
        self.bitflip_probability = 0.0001 # probability for flipping a bit
        self.randomize_probability = 0.001 # probability for randomizing a char

    def fuzz(self, inp):
        """Fuzz an array of bytes according to predefined settings"""
        arr = bytearray(inp)
        arr = self.cut_off(arr)
        self.randomize(arr)
        return bytes(arr)

    def randomize(self, arr):
        """Randomize array contents with bitflips and random bytes"""
        for i, _ in enumerate(arr):
            for j in range(8):
                if self.rng.random() < self.bitflip_probability:
                    arr[i] ^= (1 << j)
            if self.rng.random() < self.randomize_probability:
                arr[i] = self.rng.getrandbits(8)

    def cut_off(self, arr):
        """Cut off data from end of array"""
        if self.rng.random() < self.cut_propability:
            cut_limit = min(len(arr), self.cut_max)
            cut_len = self.rng.randrange(self.cut_min, cut_limit)
            arr = arr[0:len(arr) - cut_len]
        return arr

class TestProgramFuzzed(unittest.TestCase):
    """Special programming cycle tests that use a fuzzing approach"""

    @patch("stcgal.protocols.StcBaseProtocol.read_packet")
    @patch("stcgal.protocols.Stc89Protocol.write_packet")
    @patch("stcgal.protocols.serial.Serial", autospec=True)
    @patch("stcgal.protocols.time.sleep")
    @patch("sys.stdout")
    @patch("sys.stderr")
    def test_program_fuzz(self, err, out, sleep_mock, serial_mock, write_mock, read_mock):
        """Test programming cycles with fuzzing enabled"""
        yml = [
            "./tests/iap15f2k61s2.yml",
            "./tests/stc12c2052ad.yml",
            "./tests/stc15w4k56s4.yml",
            "./tests/stc12c5a60s2.yml",
            "./tests/stc89c52rc.yml",
            "./tests/stc15l104w.yml",
            "./tests/stc15f104e.yml",
            "./tests/stc8a8k64s4a12.yml",
        ]
        fuzzer = ByteArrayFuzzer()
        fuzzer.cut_propability = 0.01
        fuzzer.bitflip_probability = 0.005
        fuzzer.rng = random.Random(1)
        for y in yml:
            with self.subTest(msg="trace {}".format(y)):
                self.single_fuzz(y, serial_mock, fuzzer, read_mock, err, out,
                                 sleep_mock, write_mock)

    def single_fuzz(self, yml, serial_mock, fuzzer, read_mock, err, out, sleep_mock, write_mock):
        """Test a single programming cycle with fuzzing"""
        with open(yml) as test_file:
            test_data = yaml.load(test_file.read())
            for _ in range(1000):
                with self.subTest():
                    opts = get_default_opts()
                    opts.protocol = test_data["protocol"]
                    opts.code_image.read.return_value = bytes(test_data["code_data"])
                    serial_mock.return_value.inWaiting.return_value = 1
                    fuzzed_responses = []
                    for arr in convert_to_bytes(test_data["responses"]):
                        fuzzed_responses.append(fuzzer.fuzz(arr))
                    read_mock.side_effect = fuzzed_responses
                    gal = stcgal.frontend.StcGal(opts)
                    self.assertGreaterEqual(gal.run(), 0)
                    err.reset_mock()
                    out.reset_mock()
                    sleep_mock.reset_mock()
                    serial_mock.reset_mock()
                    write_mock.reset_mock()
                    read_mock.reset_mock()
