#
# Copyright (c) 2013-2015 Grigori Goronzy <greg@chown.ath.cx>
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

import sys, os, time, struct
import argparse
import stcgal
from stcgal.utils import Utils, BaudType
from stcgal.protocols import *
from stcgal.ihex import IHex

class StcGal:
    """STC ISP flash tool frontend"""

    def __init__(self, opts):
        self.opts = opts
        if opts.protocol == "stc89":
            self.protocol = Stc89Protocol(opts.port, opts.handshake, opts.baud)
        elif opts.protocol == "stc12a":
            self.protocol = Stc12AProtocol(opts.port, opts.handshake, opts.baud)
        elif opts.protocol == "stc12":
            self.protocol = Stc12Protocol(opts.port, opts.handshake, opts.baud)
        elif opts.protocol == "stc15a":
            self.protocol = Stc15AProtocol(opts.port, opts.handshake, opts.baud,
                                          round(opts.trim * 1000))
        else:
            self.protocol = Stc15Protocol(opts.port, opts.handshake, opts.baud,
                                          round(opts.trim * 1000))

        self.protocol.debug = opts.debug

    def emit_options(self, options):
        for o in options:
            try:
                kv = o.split("=", 1)
                if len(kv) < 2: raise ValueError("incorrect format")
                self.protocol.set_option(kv[0], kv[1])
            except ValueError as e:
                raise NameError("invalid option '%s' (%s)" % (kv[0], e))

    def load_file_auto(self, fileobj):
        """Load file with Intel Hex autodetection."""

        fname = fileobj.name.lower()
        if (fname.endswith(".hex") or fname.endswith(".ihx") or
                fname.endswith(".ihex")):
            try:
                hexfile = IHex.read(fileobj)
                binary = hexfile.extract_data()
                print("%d bytes (Intel HEX)" %len(binary))
                return binary
            except ValueError as e:
                raise IOError("invalid Intel HEX file (%s)" %e)
        else:
            binary = fileobj.read()
            print("%d bytes (Binary)" %len(binary))
            return binary

    def program_mcu(self):
        code_size = self.protocol.model.code
        ee_size = self.protocol.model.eeprom

        print("Loading flash: ", end="")
        sys.stdout.flush()
        bindata = self.load_file_auto(self.opts.code_binary)

        # warn if it overflows
        if len(bindata) > code_size:
            print("WARNING: code_binary overflows into eeprom segment!", file=sys.stderr)
        if len(bindata) > (code_size + ee_size):
            print("WARNING: code_binary truncated!", file=sys.stderr)
            bindata = bindata[0:code_size + ee_size]

        # add eeprom data if supplied
        if self.opts.eeprom_binary:
            print("Loading EEPROM: ", end="")
            sys.stdout.flush()
            eedata = self.load_file_auto(self.opts.eeprom_binary)
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

        if self.opts.option: self.emit_options(self.opts.option)

        self.protocol.handshake()
        self.protocol.erase_flash(len(bindata), code_size)
        self.protocol.program_flash(bindata)
        self.protocol.program_options()
        self.protocol.disconnect()

    def run(self):
        try: self.protocol.connect()
        except KeyboardInterrupt:
            sys.stdout.flush();
            print("interrupted")
            return 2
        except (StcFramingException, StcProtocolException) as e:
            sys.stdout.flush();
            print("Protocol error: %s" % e, file=sys.stderr)
            self.protocol.disconnect()
            return 1
        except serial.SerialException as e:
            sys.stdout.flush();
            print("Serial port error: %s" % e, file=sys.stderr)
            return 1

        try:
            if self.opts.code_binary:
                self.program_mcu()
                return 0
            else:
                self.protocol.disconnect()
                return 0
        except IOError as e:
            sys.stdout.flush();
            print("I/O error: %s" % e, file=sys.stderr)
            self.protocol.disconnect()
            return 1
        except NameError as e:
            sys.stdout.flush();
            print("Option error: %s" % e, file=sys.stderr)
            self.protocol.disconnect()
            return 1
        except (StcFramingException, StcProtocolException) as e:
            sys.stdout.flush();
            print("Protocol error: %s" % e, file=sys.stderr)
            self.protocol.disconnect()
            return 1
        except KeyboardInterrupt:
            sys.stdout.flush();
            print("interrupted", file=sys.stderr)
            self.protocol.disconnect()
            return 2
        except serial.SerialException as e:
            print("Serial port error: %s" % e, file=sys.stderr)
            return 1


def cli():
    # check arguments
    parser = argparse.ArgumentParser(description="stcgal %s - an STC MCU ISP flash tool" %stcgal.__version__)
    parser.add_argument("code_binary", help="code segment binary file to flash", type=argparse.FileType("rb"), nargs='?')
    parser.add_argument("eeprom_binary", help="eeprom segment binary file to flash", type=argparse.FileType("rb"), nargs='?')
    parser.add_argument("-P", "--protocol", help="protocol version", choices=["stc89", "stc12a", "stc12", "stc15a", "stc15"], default="stc12")
    parser.add_argument("-p", "--port", help="serial port device", default="/dev/ttyUSB0")
    parser.add_argument("-b", "--baud", help="transfer baud rate (default: 19200)", type=BaudType(), default=19200)
    parser.add_argument("-l", "--handshake", help="handshake baud rate (default: 1200)", type=BaudType(), default=1200)
    parser.add_argument("-o", "--option", help="set option (can be used multiple times)", action="append")
    parser.add_argument("-t", "--trim", help="RC oscillator frequency in kHz (STC15 series only)", type=float, default=0.0)
    parser.add_argument("-D", "--debug", help="enable debug output", action="store_true")
    opts = parser.parse_args()
    
    # run programmer
    gal = StcGal(opts)
    return gal.run()
