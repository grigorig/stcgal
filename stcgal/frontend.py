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

import sys
import argparse
import stcgal
import serial
from stcgal.utils import BaudType
from stcgal.protocols import Stc89Protocol
from stcgal.protocols import Stc12AProtocol
from stcgal.protocols import Stc12BProtocol
from stcgal.protocols import Stc12Protocol
from stcgal.protocols import Stc15Protocol
from stcgal.protocols import Stc15AProtocol
from stcgal.protocols import StcUsb15Protocol
from stcgal.protocols import Stc8Protocol
from stcgal.protocols import StcAutoProtocol
from stcgal.protocols import StcProtocolException
from stcgal.protocols import StcFramingException
from stcgal.ihex import IHex

class StcGal:
    """STC ISP flash tool frontend"""

    def __init__(self, opts):
        self.opts = opts
        self.initialize_protocol(opts)

    def initialize_protocol(self, opts):
        """Initialize protocol backend"""
        if opts.protocol == "stc89":
            self.protocol = Stc89Protocol(opts.port, opts.handshake, opts.baud)
        elif opts.protocol == "stc12a":
            self.protocol = Stc12AProtocol(opts.port, opts.handshake, opts.baud)
        elif opts.protocol == "stc12b":
            self.protocol = Stc12BProtocol(opts.port, opts.handshake, opts.baud)
        elif opts.protocol == "stc12":
            self.protocol = Stc12Protocol(opts.port, opts.handshake, opts.baud)
        elif opts.protocol == "stc15a":
            self.protocol = Stc15AProtocol(opts.port, opts.handshake, opts.baud,
                                           round(opts.trim * 1000))
        elif opts.protocol == "stc15":
            self.protocol = Stc15Protocol(opts.port, opts.handshake, opts.baud,
                                          round(opts.trim * 1000))
        elif opts.protocol == "stc8":
            self.protocol = Stc8Protocol(opts.port, opts.handshake, opts.baud,
                                         round(opts.trim * 1000))
        elif opts.protocol == "usb15":
            self.protocol = StcUsb15Protocol()
        else:
            self.protocol = StcAutoProtocol(opts.port, opts.handshake, opts.baud)
        self.protocol.debug = opts.debug

    def emit_options(self, options):
        """Set options from command line to protocol handler."""

        for opt in options:
            try:
                kv = opt.split("=", 1)
                if len(kv) < 2:
                    raise ValueError("incorrect format")
                self.protocol.set_option(kv[0], kv[1])
            except ValueError as ex:
                raise NameError("invalid option '%s' (%s)" % (kv[0], ex))

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
            except ValueError as ex:
                raise IOError("invalid Intel HEX file (%s)" %ex)
        else:
            binary = fileobj.read()
            print("%d bytes (Binary)" %len(binary))
            return binary

    def program_mcu(self):
        """Execute the standard programming flow."""

        code_size = self.protocol.model.code
        ee_size = self.protocol.model.eeprom

        print("Loading flash: ", end="")
        sys.stdout.flush()
        bindata = self.load_file_auto(self.opts.code_image)

        # warn if it overflows
        if len(bindata) > code_size:
            print("WARNING: code_image overflows into eeprom segment!", file=sys.stderr)
        if len(bindata) > (code_size + ee_size):
            print("WARNING: code_image truncated!", file=sys.stderr)
            bindata = bindata[0:code_size + ee_size]

        # add eeprom data if supplied
        if self.opts.eeprom_image:
            print("Loading EEPROM: ", end="")
            sys.stdout.flush()
            eedata = self.load_file_auto(self.opts.eeprom_image)
            if len(eedata) > ee_size:
                print("WARNING: eeprom_image truncated!", file=sys.stderr)
                eedata = eedata[0:ee_size]
            if len(bindata) < code_size:
                bindata += bytes(code_size - len(bindata))
            elif len(bindata) > code_size:
                print("WARNING: eeprom_image overlaps code_image!", file=sys.stderr)
                bindata = bindata[0:code_size]
            bindata += eedata

        # pad to 512 byte boundary
        if len(bindata) % 512:
            bindata += b'\xff' * (512 - len(bindata) % 512)

        if self.opts.option: self.emit_options(self.opts.option)

        self.protocol.handshake()
        self.protocol.erase_flash(len(bindata), code_size)
        self.protocol.program_flash(bindata)
        self.protocol.program_options()
        self.protocol.disconnect()

    def run(self):
        """Run programmer, main entry point."""

        if self.opts.version:
            print("stcgal {}".format(stcgal.__version__))
            return 0

        try:
            self.protocol.connect(autoreset=self.opts.autoreset, resetcmd=self.opts.resetcmd)
            if isinstance(self.protocol, StcAutoProtocol):
                if not self.protocol.protocol_name:
                    raise StcProtocolException("cannot detect protocol")
                base_protocol = self.protocol
                self.opts.protocol = self.protocol.protocol_name
                print("Protocol detected: %s" % self.opts.protocol)
                # recreate self.protocol with proper protocol class
                self.initialize_protocol(self.opts)
            else:
                base_protocol = None

            self.protocol.initialize(base_protocol)
        except KeyboardInterrupt:
            sys.stdout.flush()
            print("interrupted")
            return 2
        except (StcFramingException, StcProtocolException) as ex:
            sys.stdout.flush()
            print("Protocol error: %s" % ex, file=sys.stderr)
            self.protocol.disconnect()
            return 1
        except serial.SerialException as ex:
            sys.stdout.flush()
            print("Serial port error: %s" % ex, file=sys.stderr)
            return 1
        except IOError as ex:
            sys.stdout.flush()
            print("I/O error: %s" % ex, file=sys.stderr)
            return 1
        except Exception as ex:
            sys.stdout.flush()
            print("Unexpected error: %s" % ex, file=sys.stderr)
            return 1

        try:
            if self.opts.code_image:
                self.program_mcu()
                return 0
            self.protocol.disconnect()
            return 0
        except NameError as ex:
            sys.stdout.flush()
            print("Option error: %s" % ex, file=sys.stderr)
            self.protocol.disconnect()
            return 1
        except (StcFramingException, StcProtocolException) as ex:
            sys.stdout.flush()
            print("Protocol error: %s" % ex, file=sys.stderr)
            self.protocol.disconnect()
            return 1
        except KeyboardInterrupt:
            sys.stdout.flush()
            print("interrupted", file=sys.stderr)
            self.protocol.disconnect()
            return 2
        except serial.SerialException as ex:
            print("Serial port error: %s" % ex, file=sys.stderr)
            return 1
        except IOError as ex:
            sys.stdout.flush()
            print("I/O error: %s" % ex, file=sys.stderr)
            self.protocol.disconnect()
            return 1


def cli():
    # check arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="stcgal {} - an STC MCU ISP flash tool\n".format(stcgal.__version__) +
                                                 "(C) 2014-2018 Grigori Goronzy and others\nhttps://github.com/grigorig/stcgal")
    parser.add_argument("code_image", help="code segment file to flash (BIN/HEX)", type=argparse.FileType("rb"), nargs='?')
    parser.add_argument("eeprom_image", help="eeprom segment file to flash (BIN/HEX)", type=argparse.FileType("rb"), nargs='?')
    parser.add_argument("-a", "--autoreset", help="cycle power automatically by asserting DTR", action="store_true")
    parser.add_argument("-r", "--resetcmd",  help="shell command for board power-cycling (instead of DTR assertion)", action="store")
    parser.add_argument("-P", "--protocol", help="protocol version (default: auto)",
                        choices=["stc89", "stc12a", "stc12b", "stc12", "stc15a", "stc15", "stc8", "usb15", "auto"], default="auto")
    parser.add_argument("-p", "--port", help="serial port device", default="/dev/ttyUSB0")
    parser.add_argument("-b", "--baud", help="transfer baud rate (default: 19200)", type=BaudType(), default=19200)
    parser.add_argument("-l", "--handshake", help="handshake baud rate (default: 2400)", type=BaudType(), default=2400)
    parser.add_argument("-o", "--option", help="set option (can be used multiple times, see documentation)", action="append")
    parser.add_argument("-t", "--trim", help="RC oscillator frequency in kHz (STC15+ series only)", type=float, default=0.0)
    parser.add_argument("-D", "--debug", help="enable debug output", action="store_true")
    parser.add_argument("-V", "--version", help="print version info and exit", action="store_true")
    opts = parser.parse_args()

    # run programmer
    gal = StcGal(opts)
    return gal.run()
