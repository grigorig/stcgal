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

"""
TODO:
- Utils class?
- error/exception handling
- some more documentation / comments
- private member naming, other style issues

- MCU database
- Prepare for STC89/STC15 protocols
"""

import serial
import sys, os, time, struct
import argparse

DEBUG = False

class Utils:
    """make sensible boolean from string or other type value"""
    @classmethod
    def to_bool(self, val):
        if isinstance(val, bool): return val
        if isinstance(val, int): return bool(val)
        if len(val) == 0: return False
        return True if val[0].lower() == "t" or val[0] == "1" else False


class Stc12Option:
    """Manipulate STC10/11/12 series option bytes"""

    def __init__(self, msr):
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
        raise ValueError

    def get_option(self, name):
        for opt, get_func, _ in self.options:
            if opt == name:
                return get_func(name)
        raise ValueError

    def get_msr(self):
        return bytes(self.msr)

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
        val = int(val, 0)
        osc_vals = {4096: 0, 8192: 1, 16384: 2, 32768: 3}
        if val not in osc_vals.keys(): raise ValueError
        self.msr[0] &= 0x8f
        self.msr[0] |= osc_vals[val] << 4

    def get_por_delay(self):
        delay = not bool(self.msr[1] & 128)
        return "long" if delay else "short"

    def set_por_delay(self, val):
        delays = {"short": 1, "long": 0}
        if val not in delays.keys(): raise ValueError
        self.msr[1] &= 0x7f
        self.msr[1] |= delays[val] << 7

    def get_clock_gain(self):
        gain = bool(self.msr[1] & 64)
        return "high" if gain else "low"

    def set_clock_gain(self, val):
        gains = {"low": 0, "high": 1}
        if val not in gains.keys(): raise ValueError
        self.msr[1] &= 0xbf
        self.msr[1] |= gains[val] << 6

    def get_clock_source(self):
        source = bool(self.msr[1] & 2)
        return "external" if source else "internal"

    def set_clock_source(self, val):
        sources = {"internal": 0, "external": 1}
        if val not in sources.keys(): raise ValueError
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
        val = int(val, 0)
        wd_vals = {2: 0, 4: 1, 8: 2, 16: 3, 32: 4, 64: 5, 128: 6, 256: 7}
        if val not in wd_vals.keys(): raise ValueError
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

    def __init__(self, port, baud_handshake, baud_transfer):
        self.port = port
        self.baud_handshake = baud_handshake
        self.baud_transfer = baud_transfer

        self.mcu_magic = 0
        self.mcu_clock_hz = 0.0
        self.mcu_bsl_version = ""
        self.options = None

    def dump_packet(self, data, receive=True):
        if DEBUG:
            print("%s Packet data: " % ("<-" if receive else "->") +
                  " ".join(hex(x) for x in data), file=sys.stderr)

    def modular_sum(self, data):
        """modular 16-bit sum"""

        s = 0
        for b in data: s += b
        return s & 0xffff

    def read_packet(self):
        """Read and check packet from MCU.
        
        Reads a packet of data from the MCU and and do
        validity and checksum checks on it.

        Returns packet payload or None in case of an error.
        """

        # read and check frame start magic
        packet = bytes()
        packet += self.ser.read(2)
        if packet[0:2] != self.PACKET_START:
            print("Wrong magic (%s), discarding packet!" %
                  packet[0:2], file=sys.stderr)
            self.dump_packet(packet)
            return None

        # read direction and length
        packet += self.ser.read(3)
        if packet[2] != self.PACKET_MCU[0]:
            print("Wrong direction (%s), discarding packet!" %
                  hex(packet[3]), file=sys.stderr)
            self.dump_packet(packet)
            return None

        # read packet data
        packet_len, = struct.unpack(">H", packet[3:5])
        packet += self.ser.read(packet_len - 3)

        # verify end code
        if packet[packet_len+1] != self.PACKET_END[0]:
            print("Wrong end code (%s), discarding packet!" %
                  hex(packet[packet_len+1]), file=sys.stderr)
            self.dump_packet(packet)
            return None

        # verify checksum
        packet_csum, = struct.unpack(">H", packet[packet_len-1:packet_len+1])
        calc_csum = sum(packet[2:packet_len-1]) & 0xffff
        if packet_csum != calc_csum:
            print("Wrong checksum (%s, expected %s), discarding packet!" %
                  (hex(packet_csum), hex(calc_csum)), file=sys.stderr)
            self.dump_packet(packet)
            return None

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

    def decode_status_packet(self, packet):
        """Decode status packet"""

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
        baud_actual = (self.mcu_clock_hz) / (16 * (256 - brt))
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

        print("Target magic: %s" % hex(self.mcu_magic))
        print("Target frequency: %.3f MHz" % (self.mcu_clock_hz / 1E6))
        print("Target bootloader version: %s" % self.mcu_bsl_version)

    def connect(self):
        """Connect to MCU and initialize communication.

        Set up serial port, send sync sequence and get part info.
        """
        
        self.ser = serial.Serial(port=self.port, baudrate=self.baud_handshake,
                                 parity=serial.PARITY_EVEN)

        # send sync, and wait for MCU response
        print("Waiting for MCU, please cycle power...", end="")
        sys.stdout.flush()
        while True:
            self.ser.write(b"\x7f")
            self.ser.flush()
            time.sleep(0.015)
            if self.ser.inWaiting() > 0: break
        print("done")

        # read status packet
        status_packet = self.read_packet()
        if status_packet == None or status_packet[0] != 0x50:
            print("Error receiving status packet, aborting!", file=sys.stderr)
            return False
        self.decode_status_packet(status_packet)
        self.print_mcu_info()
        self.options = Stc12Option(status_packet[23:27])
        self.options.print()

        return True

    def handshake(self):
        """Do baudrate handshake

        Initate and do the (rather complicated) baudrate handshake.
        """

        # start baudrate handshake
        brt, brt_csum, iap, delay = self.calculate_baud()
        print("Switching to %d baud..." % self.baud_transfer, end="")
        sys.stdout.flush()
        packet = bytes([0x50, 0x00, 0x00, 0x36, 0x01])
        packet += struct.pack(">H", self.mcu_magic)
        self.write_packet(packet)
        response = self.read_packet()
        if response == None or response[0] != 0x8f:
            print("Error receiving handshake packet, aborting!", file=sys.stderr)
            return False

        # test new settings
        print("testing...", end="")
        sys.stdout.flush()
        packet = bytes([0x8f, 0xc0, brt, 0x3f, brt_csum, delay, iap])
        self.write_packet(packet)
        time.sleep(0.2)
        self.ser.baudrate = self.baud_transfer
        response = self.read_packet()
        self.ser.baudrate = self.baud_handshake
        if response == None or response[0] != 0x8f:
            print("Error receiving handshake packet, aborting!", file=sys.stderr)
            return False

        # switch to the settings
        print("setting...", end="")
        sys.stdout.flush()
        packet = bytes([0x8e, 0xc0, brt, 0x3f, brt_csum, delay])
        self.write_packet(packet)
        time.sleep(0.2)
        self.ser.baudrate = self.baud_transfer
        response = self.read_packet()
        if response == None or response[0] != 0x84:
            print("Error receiving handshake packet, aborting!", file=sys.stderr)
            return False
        print("done")

        return True

    def erase_flash(self, erase_size, flash_size):
        """Erase the MCU's flash memory.

        Erase the flash memory with a block-erase command.
        """

        blks = (erase_size + 255) // 256
        size = (flash_size + 255) // 256
        print("Erasing %d blocks..." % blks)
        packet = bytes([0x84, 0x00, 0x00, blks, 0x00, 0x00, size,
                        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0x00, 0x00, 0x00, 0x00])
        for i in range(0x80, 0x0d, -1): packet += bytes([i])
        self.write_packet(packet)
        response = self.read_packet()
        if response == None or response[0] != 0x00:
            print("Error receiving erase response, aborting!", file=sys.stderr)
            return False
        return True

    def program_flash(self, addr, data):
        """Program the MCU's flash memory.

        Write data into flash memory, starting at the given address. The address
        should be 128 byte aligned.
        """

        print("Writing %d bytes..." % len(data), end="")
        sys.stdout.flush()
        for i in range(addr, addr+len(data), 128):
            packet = bytes(3)
            packet += struct.pack(">H", i)
            packet += struct.pack(">H", self.PROGRAM_BLOCKSIZE)
            packet += data[i-addr:i-addr+128]
            while len(packet) < self.PROGRAM_BLOCKSIZE + 7: packet += b"\x00"
            csum = sum(packet[7:]) & 0xff
            self.write_packet(packet)
            response = self.read_packet()
            if response == None or response[0] != 0x00:
                print("Error receiving program response packet, aborting!", file=sys.stderr)
                return False
            elif response[1] != csum:
                print("Wrong checksum in program response (%s, expected %s), aborting!" %
                      (hex(response[1]), hex(csum)), file=sys.stderr)
            print(".", end="")
            sys.stdout.flush()
        print()

        packet = bytes([0x69, 0x00, 0x00, 0x36, 0x01])
        packet += struct.pack(">H", self.mcu_magic)
        self.write_packet(packet)
        response = self.read_packet()
        if response == None or response[0] != 0x8d:
            print("Error receiving program finish response packet, aborting!", file=sys.stderr)
            return False
        print("Finished writing flash!")

        return True

    def set_option(self, name, value):
        self.options.set_option(name, value)

    def program_options(self):
        #self.options.print()
        print("Setting options...")
        msr = self.options.get_msr()
        packet = bytes([0x8d, msr[0], msr[1], msr[2], msr[3],
                        0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
                        0xff, 0xff, 0xff, 0xff, 0xff, 0xff])

        packet += struct.pack(">I", int(self.mcu_clock_hz))
        self.write_packet(packet)
        response = self.read_packet()
        if response == None or response[0] != 0x50:
            print("Error receiving set options response packet, aborting!", file=sys.stderr)
            return False

        print("Target UID: %02x%02x%02x%02x%02x%02x%02x" %
              (response[18], response[19], response[20], response[21],
               response[22], response[23], response[24]))

        return True

    def disconnect(self):
        """Disconnect from MCU"""

        # reset mcu
        packet = bytes([0x82])
        self.write_packet(packet)
        self.ser.close()
        print("Disconnected!")

class StcGal:
    """STC ISP flash tool frontend"""

    def __init__(self, opts):
        self.opts = opts
        self.protocol = Stc12Protocol(opts.port, opts.handshake, opts.baud)

    def run(self):
        self.protocol.connect()

        if opts.binary:
            bindata = opts.binary.read()

            if opts.option:
                for o in opts.option:
                    k, v = o.split("=", 1)
                    self.protocol.set_option(k, v)

            self.protocol.handshake()
            self.protocol.erase_flash(len(bindata), 0xf0 * 256)
            self.protocol.program_flash(0, bindata)
            self.protocol.program_options()

        self.protocol.disconnect()

if __name__ == "__main__":
    # check arguments
    parser = argparse.ArgumentParser(description="STC10/11/12 series MCU ISP flash tool")
    parser.add_argument("binary", help="binary file to flash", type=argparse.FileType("rb"), nargs='?')
    parser.add_argument("-p", "--port", help="serial port device", default="/dev/ttyUSB0")
    parser.add_argument("-b", "--baud", help="transfer baud rate (default: 19200)", type=int, default=19200)
    parser.add_argument("-l", "--handshake", help="handshake baud rate (default: 2400)", type=int, default=2400)
    parser.add_argument("-o", "--option", help="set option (can be used multiple times)", action="append")
    opts = parser.parse_args()
    
    # run programmer
    gal = StcGal(opts)
    sys.exit(gal.run())
