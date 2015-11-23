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

import serial
import sys, os, time, struct
import argparse
import collections
from stcgal.models import MCUModelDatabase
from stcgal.utils import Utils

class StcFramingException(Exception):
    """Something wrong with packet framing or checksum"""
    pass


class StcProtocolException(Exception):
    """High-level protocol issue, like wrong packet type"""
    pass


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


class Stc89Option(BaseOption):
    """Manipulation STC89 series option byte"""

    def __init__(self, msr):
        self.msr = msr
        self.options = (
            ("cpu_6t_enabled", self.get_t6, self.set_t6),
            ("bsl_pindetect_enabled", self.get_pindetect, self.set_pindetect),
            ("eeprom_erase_enabled", self.get_ee_erase, self.set_ee_erase),
            ("clock_gain", self.get_clock_gain, self.set_clock_gain),
            ("ale_enabled", self.get_ale, self.set_ale),
            ("xram_enabled", self.get_xram, self.set_xram),
            ("watchdog_por_enabled", self.get_watchdog, self.set_watchdog),
        )

    def get_msr(self):
        return self.msr

    def get_t6(self):
        return not bool(self.msr & 1)

    def set_t6(self, val):
        val = Utils.to_bool(val);
        self.msr &= 0xfe
        self.msr |= 0x01 if not bool(val) else 0x00

    def get_pindetect(self):
        return not bool(self.msr & 4)

    def set_pindetect(self, val):
        val = Utils.to_bool(val);
        self.msr &= 0xfb
        self.msr |= 0x04 if not bool(val) else 0x00

    def get_ee_erase(self):
        return not bool(self.msr & 8)

    def set_ee_erase(self, val):
        val = Utils.to_bool(val);
        self.msr &= 0xf7
        self.msr |= 0x08 if not bool(val) else 0x00

    def get_clock_gain(self):
        gain = bool(self.msr & 16)
        return "high" if gain else "low"

    def set_clock_gain(self, val):
        gains = {"low": 0, "high": 0x10}
        if val not in gains.keys():
            raise ValueError("must be one of %s" % list(gains.keys()))
        self.msr &= 0xef
        self.msr |= gains[val]

    def get_ale(self):
        return bool(self.msr & 32)

    def set_ale(self, val):
        val = Utils.to_bool(val);
        self.msr &= 0xdf
        self.msr |= 0x20 if bool(val) else 0x00

    def get_xram(self):
        return bool(self.msr & 64)

    def set_xram(self, val):
        val = Utils.to_bool(val);
        self.msr &= 0xbf
        self.msr |= 0x40 if bool(val) else 0x00

    def get_watchdog(self):
        return not bool(self.msr & 128)

    def set_watchdog(self, val):
        val = Utils.to_bool(val);
        self.msr &= 0x7f
        self.msr |= 0x80 if not bool(val) else 0x00


class Stc12AOption(BaseOption):
    """Manipulate STC12A series option bytes"""

    def __init__(self, msr):
        assert len(msr) == 5
        self.msr = bytearray(msr)

        """list of options and their handlers"""
        self.options = (
            ("low_voltage_detect", self.get_low_voltage_detect, self.set_low_voltage_detect),
            ("clock_source", self.get_clock_source, self.set_clock_source),
            ("watchdog_por_enabled", self.get_watchdog, self.set_watchdog),
            ("watchdog_stop_idle", self.get_watchdog_idle, self.set_watchdog_idle),
            ("watchdog_prescale", self.get_watchdog_prescale, self.set_watchdog_prescale),
            ("eeprom_erase_enabled", self.get_ee_erase, self.set_ee_erase),
            ("bsl_pindetect_enabled", self.get_pindetect, self.set_pindetect),
        )

    def get_low_voltage_detect(self):
        return not bool(self.msr[4] & 64)

    def set_low_voltage_detect(self, val):
        val = Utils.to_bool(val);
        self.msr[4] &= 0xbf
        self.msr[4] |= 0x40 if not val else 0x00

    def get_clock_source(self):
        source = bool(self.msr[0] & 2)
        return "external" if source else "internal"

    def set_clock_source(self, val):
        sources = {"internal": 0, "external": 1}
        if val not in sources.keys():
            raise ValueError("must be one of %s" % list(sources.keys()))
        self.msr[0] &= 0xfd
        self.msr[0] |= sources[val] << 1

    def get_watchdog(self):
        return not bool(self.msr[1] & 32)

    def set_watchdog(self, val):
        val = Utils.to_bool(val);
        self.msr[1] &= 0xdf
        self.msr[1] |= 0x20 if not val else 0x00

    def get_watchdog_idle(self):
        return not bool(self.msr[1] & 8)

    def set_watchdog_idle(self, val):
        val = Utils.to_bool(val);
        self.msr[1] &= 0xf7
        self.msr[1] |= 0x08 if not val else 0x00

    def get_watchdog_prescale(self):
        return 2 ** (((self.msr[1]) & 0x07) + 1)

    def set_watchdog_prescale(self, val):
        val = Utils.to_int(val)
        wd_vals = {2: 0, 4: 1, 8: 2, 16: 3, 32: 4, 64: 5, 128: 6, 256: 7}
        if val not in wd_vals.keys():
            raise ValueError("must be one of %s" % list(wd_vals.keys()))
        self.msr[1] &= 0xf8
        self.msr[1] |= wd_vals[val]

    def get_ee_erase(self):
        return not bool(self.msr[2] & 2)

    def set_ee_erase(self, val):
        val = Utils.to_bool(val);
        self.msr[2] &= 0xfd
        self.msr[2] |= 0x02 if not val else 0x00

    def get_pindetect(self):
        return not bool(self.msr[2] & 1)

    def set_pindetect(self, val):
        val = Utils.to_bool(val);
        self.msr[2] &= 0xfe
        self.msr[2] |= 0x01 if not val else 0x00


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


class Stc15AOption(BaseOption):
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


class Stc15Option(BaseOption):
    def __init__(self, msr):
        assert len(msr) == 4
        self.msr = bytearray(msr)

        self.options = (
            ("reset_pin_enabled", self.get_reset_pin_enabled, self.set_reset_pin_enabled),
            ("clock_source", self.get_clock_source, self.set_clock_source),
            ("clock_gain", self.get_clock_gain, self.set_clock_gain),
            ("watchdog_por_enabled", self.get_watchdog, self.set_watchdog),
            ("watchdog_stop_idle", self.get_watchdog_idle, self.set_watchdog_idle),
            ("watchdog_prescale", self.get_watchdog_prescale, self.set_watchdog_prescale),
            ("low_voltage_reset", self.get_lvrs, self.set_lvrs),
            ("low_voltage_threshold", self.get_low_voltage, self.set_low_voltage),
            ("eeprom_lvd_inhibit", self.get_eeprom_lvd, self.set_eeprom_lvd),
            ("eeprom_erase_enabled", self.get_ee_erase, self.set_ee_erase),
            ("bsl_pindetect_enabled", self.get_pindetect, self.set_pindetect),
            ("power_on_reset_delay", self.get_por_delay, self.set_por_delay),
            ("rstout_por_state", self.get_p33_state, self.set_p33_state),
            ("uart_passthrough", self.get_uart_passthrough, self.set_uart_passthrough),
            ("uart_pin_mode", self.get_uart_pin_mode, self.set_uart_pin_mode),
        )

    def get_reset_pin_enabled(self):
        return not bool(self.msr[2] & 16)

    def set_reset_pin_enabled(self, val):
        val = Utils.to_bool(val);
        self.msr[2] &= 0xef
        self.msr[2] |= 0x10 if not bool(val) else 0x00

    def get_clock_source(self):
        source = bool(self.msr[2] & 0x01)
        return "internal" if source else "external"

    def set_clock_source(self, val):
        sources = {"internal": 1, "external": 0}
        if val not in sources.keys():
            raise ValueError("must be one of %s" % list(sources.keys()))
        self.msr[2] &= 0xfe
        self.msr[2] |= sources[val]

    def get_clock_gain(self):
        gain = bool(self.msr[2] & 0x02)
        return "high" if gain else "low"

    def set_clock_gain(self, val):
        gains = {"low": 0, "high": 1}
        if val not in gains.keys():
            raise ValueError("must be one of %s" % list(gains.keys()))
        self.msr[2] &= 0xfd
        self.msr[2] |= gains[val] << 1

    def get_watchdog(self):
        return not bool(self.msr[0] & 32)

    def set_watchdog(self, val):
        val = Utils.to_bool(val);
        self.msr[0] &= 0xdf
        self.msr[0] |= 0x20 if not val else 0x00

    def get_watchdog_idle(self):
        return not bool(self.msr[0] & 8)

    def set_watchdog_idle(self, val):
        val = Utils.to_bool(val);
        self.msr[0] &= 0xf7
        self.msr[0] |= 0x08 if not val else 0x00

    def get_watchdog_prescale(self):
        return 2 ** (((self.msr[0]) & 0x07) + 1)

    def set_watchdog_prescale(self, val):
        val = Utils.to_int(val)
        wd_vals = {2: 0, 4: 1, 8: 2, 16: 3, 32: 4, 64: 5, 128: 6, 256: 7}
        if val not in wd_vals.keys():
            raise ValueError("must be one of %s" % list(wd_vals.keys()))
        self.msr[0] &= 0xf8
        self.msr[0] |= wd_vals[val]

    def get_lvrs(self):
        return not bool(self.msr[1] & 64)

    def set_lvrs(self, val):
        val = Utils.to_bool(val);
        self.msr[1] &= 0xbf
        self.msr[1] |= 0x40 if not val else 0x00

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
        return bool(self.msr[3] & 2)

    def set_ee_erase(self, val):
        val = Utils.to_bool(val);
        self.msr[3] &= 0xfd
        self.msr[3] |= 0x02 if val else 0x00

    def get_pindetect(self):
        return not bool(self.msr[3] & 1)

    def set_pindetect(self, val):
        val = Utils.to_bool(val);
        self.msr[3] &= 0xfe
        self.msr[3] |= 0x01 if not val else 0x00

    def get_por_delay(self):
        delay = bool(self.msr[2] & 128)
        return "long" if delay else "short"

    def set_por_delay(self, val):
        delays = {"short": 0, "long": 1}
        if val not in delays.keys():
            raise ValueError("must be one of %s" % list(delays.keys()))
        self.msr[2] &= 0x7f
        self.msr[2] |= delays[val] << 7

    def get_p33_state(self):
        return "high" if self.msr[2] & 0x08 else "low"

    def set_p33_state(self, val):
        val = Utils.to_bool(val)
        self.msr[2] &= 0xf7
        self.msr[2] |= 0x08 if val else 0x00

    def get_uart_passthrough(self):
        return bool(self.msr[2] & 0x40)

    def set_uart_passthrough(self, val):
        val = Utils.to_bool(val)
        self.msr[2] &= 0xbf
        self.msr[2] |= 0x40 if val else 0x00

    def get_uart_pin_mode(self):
        return "push-pull" if bool(self.msr[2] & 0x20) else "normal"

    def set_uart_pin_mode(self, val):
        delays = {"normal": 0, "push-pull": 1}
        if val not in delays.keys():
            raise ValueError("must be one of %s" % list(delays.keys()))
        self.msr[2] &= 0xdf
        self.msr[2] |= 0x20 if val else 0x00


class StcBaseProtocol:
    """Basic functionality for STC BSL protocols"""

    """magic word that starts a packet"""
    PACKET_START = bytes([0x46, 0xb9])

    """magic byte that ends a packet"""
    PACKET_END = bytes([0x16])

    """magic byte for packets received from MCU"""
    PACKET_MCU = bytes([0x68])

    """magic byte for packets sent by host"""
    PACKET_HOST = bytes([0x6a])

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
        self.debug = False

    def dump_packet(self, data, receive=True):
        if self.debug:
            print("%s Packet data: %s" % (("<-" if receive else "->"),
                  Utils.hexstr(data, " ")), file=sys.stderr)

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
            raise serial.SerialTimeoutException("read timeout")

        return data

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
            raise StcProtocolException("incorrect magic in status packet")
        return status_packet

    def set_option(self, name, value):
        self.options.set_option(name, value)

    def connect(self):
        """Connect to MCU and initialize communication.

        Set up serial port, send sync sequence and get part info.
        """

        self.ser = serial.Serial(port=self.port, baudrate=self.baud_handshake,
                                 parity=self.PARITY)

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
            except (StcFramingException, serial.SerialTimeoutException): pass
        print("done")

        self.initialize_status(status_packet)
        self.initialize_model()
        self.initialize_options(status_packet)

    def disconnect(self):
        """Disconnect from MCU"""

        # reset mcu
        packet = bytes([0x82])
        self.write_packet(packet)
        self.ser.close()
        print("Disconnected!")


class Stc89Protocol(StcBaseProtocol):
    """Protocol handler for STC 89/90 series"""

    """These don't use any parity"""
    PARITY = serial.PARITY_NONE

    """block size for programming flash"""
    PROGRAM_BLOCKSIZE = 128

    def __init__(self, port, baud_handshake, baud_transfer):
        StcBaseProtocol.__init__(self, port, baud_handshake, baud_transfer)

        self.cpu_6t = None

    def read_packet(self):
        """Read and check packet from MCU.

        Reads a packet of data from the MCU and and do
        validity and checksum checks on it.

        Returns packet payload or None in case of an error.
        """

        # read and check frame start magic
        packet = bytes()
        packet += self.read_bytes_safe(1)
        # Some (?) BSL versions don't send a frame start with the status
        # packet. Let's be liberal and accept that always, just in case.
        if packet[0] == self.PACKET_MCU[0]:
            packet = self.PACKET_START + self.PACKET_MCU
        else:
            if packet[0] != self.PACKET_START[0]:
                self.dump_packet(packet)
                raise StcFramingException("incorrect frame start")
            packet += self.read_bytes_safe(1)
            if packet[1] != self.PACKET_START[1]:
                self.dump_packet(packet)
                raise StcFramingException("incorrect frame start")

            # read direction
            packet += self.read_bytes_safe(1)
            if packet[2] != self.PACKET_MCU[0]:
                self.dump_packet(packet)
                raise StcFramingException("incorrect packet direction magic")

        # read length
        packet += self.read_bytes_safe(2)

        # read packet data
        packet_len, = struct.unpack(">H", packet[3:5])
        packet += self.read_bytes_safe(packet_len - 3)

        # verify end code
        if packet[packet_len+1] != self.PACKET_END[0]:
            self.dump_packet(packet)
            raise StcFramingException("incorrect frame end")

        # verify checksum
        packet_csum = packet[packet_len]
        calc_csum = sum(packet[2:packet_len]) & 0xff
        if packet_csum != calc_csum:
            self.dump_packet(packet)
            raise StcFramingException("packet checksum mismatch")

        self.dump_packet(packet, receive=True)

        # payload only is returned
        return packet[5:packet_len]

    def write_packet(self, data):
        """Send packet to MCU.

        Constructs a packet with supplied payload and sends it to the MCU.
        """

        # frame start and direction magic
        packet = bytes()
        packet += self.PACKET_START
        packet += self.PACKET_HOST

        # packet length and payload
        packet += struct.pack(">H", len(data) + 5)
        packet += data

        # checksum and end code
        packet += bytes([sum(packet[2:]) & 0xff])
        packet += self.PACKET_END

        self.dump_packet(packet, receive=False)
        self.ser.write(packet)
        self.ser.flush()

    def get_status_packet(self):
        """Read and decode status packet"""

        status_packet = self.read_packet()
        if status_packet[0] != 0x00:
            raise StcProtocolException("incorrect magic in status packet")
        return status_packet

    def initialize_options(self, status_packet):
        """Initialize options"""

        self.options = Stc89Option(status_packet[19])
        self.options.print()

    def calculate_baud(self):
        """Calculate MCU baudrate setting.

        Calculate appropriate baudrate settings for the MCU's UART,
        according to clock frequency and requested baud rate.
        """

        # timing is different in 6T mode
        sample_rate = 16 if self.cpu_6t else 32
        # baudrate is directly controlled by programming the MCU's BRT register
        brt = 65536 - round((self.mcu_clock_hz) / (self.baud_transfer * sample_rate))
        brt_csum = (2 * (256 - brt)) & 0xff
        baud_actual = (self.mcu_clock_hz) / (sample_rate * (65536 - brt))
        baud_error = (abs(self.baud_transfer - baud_actual) * 100.0) / self.baud_transfer
        if baud_error > 5.0:
            print("WARNING: baudrate error is %.2f%%. You may need to set a slower rate." %
                  baud_error, file=sys.stderr)

        # IAP wait states (according to datasheet(s))
        iap_wait = 0x80
        if self.mcu_clock_hz < 5E6: iap_wait = 0x83
        elif self.mcu_clock_hz < 10E6: iap_wait = 0x82
        elif self.mcu_clock_hz < 20E6: iap_wait = 0x81

        # MCU delay after switching baud rates
        delay = 0xa0

        return brt, brt_csum, iap_wait, delay

    def initialize_status(self, packet):
        """Decode status packet and store basic MCU info"""

        self.mcu_magic, = struct.unpack(">H", packet[20:22])
        self.cpu_6t = not bool(packet[19] & 1)

        cpu_t = 6.0 if self.cpu_6t else 12.0
        freq_counter = 0
        for i in range(8):
            freq_counter += struct.unpack(">H", packet[1+2*i:3+2*i])[0]
        freq_counter /= 8.0
        self.mcu_clock_hz = (self.baud_handshake * freq_counter * cpu_t) / 7.0

        bl_version, bl_stepping = struct.unpack("BB", packet[17:19])
        self.mcu_bsl_version = "%d.%d%s" % (bl_version >> 4, bl_version & 0x0f,
                                           chr(bl_stepping))

    def handshake(self):
        """Switch to transfer baudrate

        Switches to transfer baudrate and verifies that the setting works with
        a ping-pong exchange of packets."""

        # check new baudrate
        print("Switching to %d baud: " % self.baud_transfer, end="")
        brt, brt_csum, iap, delay = self.calculate_baud()
        print("checking ", end="")
        sys.stdout.flush()
        packet = bytes([0x8f])
        packet += struct.pack(">H", brt)
        packet += bytes([0xff - (brt >> 8), brt_csum, delay, iap])
        self.write_packet(packet)
        time.sleep(0.2)
        self.ser.baudrate = self.baud_transfer
        response = self.read_packet()
        self.ser.baudrate = self.baud_handshake
        if response[0] != 0x8f:
            raise StcProtocolException("incorrect magic in handshake packet")

        # switch to baudrate
        print("setting ", end="")
        sys.stdout.flush()
        packet = bytes([0x8e])
        packet += struct.pack(">H", brt)
        packet += bytes([0xff - (brt >> 8), brt_csum, delay])
        self.write_packet(packet)
        time.sleep(0.2)
        self.ser.baudrate = self.baud_transfer
        response = self.read_packet()
        if response[0] != 0x8e:
            raise StcProtocolException("incorrect magic in handshake packet")

        # ping-pong test
        print("testing ", end="")
        sys.stdout.flush()
        packet = bytes([0x80, 0x00, 0x00, 0x36, 0x01])
        packet += struct.pack(">H", self.mcu_magic)
        for i in range(4):
            self.write_packet(packet)
            response = self.read_packet()
            if response[0] != 0x80:
                raise StcProtocolException("incorrect magic in handshake packet")

        print("done")

    def erase_flash(self, erase_size, flash_size):
        """Erase the MCU's flash memory.

        Erase the flash memory with a block-erase command.
        flash_size is ignored; not used on STC 89 series.
        """

        blks = ((erase_size + 511) // 512) * 2
        print("Erasing %d blocks: " % blks, end="")
        sys.stdout.flush()
        packet = bytes([0x84, blks, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33])
        self.write_packet(packet)
        response = self.read_packet()
        if response[0] != 0x80:
            raise StcProtocolException("incorrect magic in erase packet")
        print("done")

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
            if response[0] != 0x80:
                raise StcProtocolException("incorrect magic in write packet")
            elif response[1] != csum:
                raise StcProtocolException("verification checksum mismatch")
            print(".", end="")
            sys.stdout.flush()
        print(" done")

    def program_options(self):
        """Program option byte into flash"""

        print("Setting options: ", end="")
        sys.stdout.flush()
        msr = self.options.get_msr()
        packet = bytes([0x8d, msr, 0xff, 0xff, 0xff])
        self.write_packet(packet)
        response = self.read_packet()
        if response[0] != 0x8d:
            raise StcProtocolException("incorrect magic in option packet")
        print("done")


class Stc12AProtocol(Stc89Protocol):

    """countdown value for flash erase"""
    ERASE_COUNTDOWN = 0x0d

    def __init__(self, port, baud_handshake, baud_transfer):
        Stc89Protocol.__init__(self, port, baud_handshake, baud_transfer)

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
        if brt <= 1 or brt > 255:
            raise StcProtocolException("requested baudrate cannot be set")
        brt_csum = (2 * (256 - brt)) & 0xff
        baud_actual = (self.mcu_clock_hz) / (16 * (256 - brt))
        baud_error = (abs(self.baud_transfer - baud_actual) * 100.0) / self.baud_transfer
        if baud_error > 5.0:
            print("WARNING: baudrate error is %.2f%%. You may need to set a slower rate." %
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

    def initialize_options(self, status_packet):
        """Initialize options"""

        # create option state
        self.options = Stc12AOption(status_packet[23:28])
        self.options.print()

    def handshake(self):
        """Do baudrate handshake

        Initate and do the (rather complicated) baudrate handshake.
        """

        # start baudrate handshake
        print("Switching to %d baud: " % self.baud_transfer, end="")
        sys.stdout.flush()
        brt, brt_csum, iap, delay = self.calculate_baud()
        print("checking ", end="")
        sys.stdout.flush()
        packet = bytes([0x8f, 0xc0, brt, 0x3f, brt_csum, delay, iap])
        self.write_packet(packet)
        time.sleep(0.2)
        self.ser.baudrate = self.baud_transfer
        response = self.read_packet()
        self.ser.baudrate = self.baud_handshake
        if response[0] != 0x8f:
            raise StcProtocolException("incorrect magic in handshake packet")

        # switch to the settings
        print("setting ", end="")
        sys.stdout.flush()
        packet = bytes([0x8e, 0xc0, brt, 0x3f, brt_csum, delay])
        self.write_packet(packet)
        time.sleep(0.2)
        self.ser.baudrate = self.baud_transfer
        response = self.read_packet()
        if response[0] != 0x8e:
            raise StcProtocolException("incorrect magic in handshake packet")

        # ping-pong test
        print("testing ", end="")
        sys.stdout.flush()
        packet = bytes([0x80, 0x00, 0x00, 0x36, 0x01])
        packet += struct.pack(">H", self.mcu_magic)
        for i in range(4):
            self.write_packet(packet)
            response = self.read_packet()
            if response[0] != 0x80:
                raise StcProtocolException("incorrect magic in handshake packet")

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
        if response[0] != 0x80:
            raise StcProtocolException("incorrect magic in erase packet")
        print("done")

    def program_options(self):
        print("Setting options: ", end="")
        sys.stdout.flush()
        msr = self.options.get_msr()
        packet = bytes([0x8d, msr[0], msr[1], msr[2], msr[3],
                        msr[4]])

        packet += struct.pack(">I", int(self.mcu_clock_hz))
        self.write_packet(packet)
        response = self.read_packet()
        if response[0] != 0x80:
            raise StcProtocolException("incorrect magic in option packet")
        print("done")


class Stc12Protocol(StcBaseProtocol):
    """Protocol handler for STC 10/11/12 series"""

    """block size for programming flash"""
    PROGRAM_BLOCKSIZE = 128

    """countdown value for flash erase"""
    ERASE_COUNTDOWN = 0x0d

    """Parity for error correction was introduced with STC12"""
    PARITY = serial.PARITY_EVEN

    def __init__(self, port, baud_handshake, baud_transfer):
        StcBaseProtocol.__init__(self, port, baud_handshake, baud_transfer)

    def read_packet(self):
        """Read and check packet from MCU.
        
        Reads a packet of data from the MCU and and do
        validity and checksum checks on it.

        Returns packet payload or None in case of an error.
        """

        # read and check frame start magic
        packet = bytes()
        packet += self.read_bytes_safe(1)
        if packet[0] != self.PACKET_START[0]:
            raise StcFramingException("incorrect frame start")
        packet += self.read_bytes_safe(1)
        if packet[1] != self.PACKET_START[1]:
            raise StcFramingException("incorrect frame start")

        # read direction and length
        packet += self.read_bytes_safe(3)
        if packet[2] != self.PACKET_MCU[0]:
            self.dump_packet(packet)
            raise StcFramingException("incorrect packet direction magic")

        # read packet data
        packet_len, = struct.unpack(">H", packet[3:5])
        packet += self.read_bytes_safe(packet_len - 3)

        # verify end code
        if packet[packet_len+1] != self.PACKET_END[0]:
            self.dump_packet(packet)
            raise StcFramingException("incorrect frame end")

        # verify checksum
        packet_csum, = struct.unpack(">H", packet[packet_len-1:packet_len+1])
        calc_csum = sum(packet[2:packet_len-1]) & 0xffff
        if packet_csum != calc_csum:
            self.dump_packet(packet)
            raise StcFramingException("packet checksum mismatch")

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
        if brt <= 1 or brt > 255:
            raise StcProtocolException("requested baudrate cannot be set")
        brt_csum = (2 * (256 - brt)) & 0xff
        baud_actual = (self.mcu_clock_hz) / (16 * (256 - brt))
        baud_error = (abs(self.baud_transfer - baud_actual) * 100.0) / self.baud_transfer
        if baud_error > 5.0:
            print("WARNING: baudrate error is %.2f%%. You may need to set a slower rate." %
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
        
    def initialize_options(self, status_packet):
        """Initialize options"""

        # create option state
        self.options = Stc12Option(status_packet[23:27])
        self.options.print()

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
            raise StcProtocolException("incorrect magic in handshake packet")

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
            raise StcProtocolException("incorrect magic in handshake packet")

        # switch to the settings
        print("setting ", end="")
        sys.stdout.flush()
        packet = bytes([0x8e, 0xc0, brt, 0x3f, brt_csum, delay])
        self.write_packet(packet)
        time.sleep(0.2)
        self.ser.baudrate = self.baud_transfer
        response = self.read_packet()
        if response[0] != 0x84:
            raise StcProtocolException("incorrect magic in handshake packet")

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
            raise StcProtocolException("incorrect magic in erase packet")
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
                raise StcProtocolException("incorrect magic in write packet")
            elif response[1] != csum:
                raise StcProtocolException("verification checksum mismatch")
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
            raise StcProtocolException("incorrect magic in finish packet")
        print("done")

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
            raise StcProtocolException("incorrect magic in option packet")
        print("done")

        # If UID wasn't sent with erase acknowledge, it should be in this packet
        if not self.uid:
            self.uid = response[18:25]

        print("Target UID: %s" % Utils.hexstr(self.uid))


class Stc15AProtocol(Stc12Protocol):
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
        self.options = Stc15AOption(status_packet[23:36])
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
            raise StcProtocolException("incorrect magic in status packet")
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
            raise StcProtocolException("incorrect magic in handshake packet")

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
            raise StcProtocolException("incorrect magic in handshake packet")

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
            raise StcProtocolException("incorrect magic in handshake packet")

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
            raise StcProtocolException("incorrect magic in handshake packet")
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
            raise StcProtocolException("incorrect magic in option packet")
        print("done")

        print("Target UID: %s" % Utils.hexstr(self.uid))

class Stc15Protocol(Stc15AProtocol):
    """Protocol handler for later STC 15 series"""

    def __init__(self, port, handshake, baud, trim):
        Stc15AProtocol.__init__(self, port, handshake, baud, trim)

        self.trim_value = None

    def initialize_options(self, status_packet):
        """Initialize options"""

        # create option state
        self.options = Stc15Option(status_packet[5:8] + status_packet[12:13])
        self.options.print()

    def initialize_status(self, packet):
        """Decode status packet and store basic MCU info"""

        self.mcu_magic, = struct.unpack(">H", packet[20:22])

        # check bit that control internal vs. external clock source
        # get frequency either stored from calibration or from
        # frequency counter
        self.external_clock = (packet[7] & 0x01) == 0
        if self.external_clock:
            count, = struct.unpack(">H", packet[13:15])
            self.mcu_clock_hz = self.baud_handshake * count
        else:
            self.mcu_clock_hz, = struct.unpack(">I", packet[8:12])

        # pre-calibrated trim adjust for 24 MHz, range 0x40
        self.freq_count_24 = packet[4]

        # wakeup timer factory value
        self.wakeup_freq, = struct.unpack(">H", packet[1:3])

        bl_version, bl_stepping = struct.unpack("BB", packet[17:19])
        self.mcu_bsl_version = "%d.%d%s" % (bl_version >> 4, bl_version & 0x0f,
                                           chr(bl_stepping))
        self.bsl_version = bl_version

    def print_mcu_info(self):
        """Print additional STC15 info"""

        StcBaseProtocol.print_mcu_info(self)
        print("Target wakeup frequency: %.3f KHz" %(self.wakeup_freq / 1000))

    def choose_range(self, packet, response, target_count):
        """Choose appropriate trim value mean for next round from challenge
        responses."""

        calib_data = response[2:]
        challenge_data = packet[2:]
        calib_len = response[1]

        for i in range(calib_len - 1):
            count_a, count_b = struct.unpack(">HH", calib_data[2*i:2*i+4])
            trim_a, trim_b, trim_range = struct.unpack(">BxBB", challenge_data[2*i:2*i+4])
            if ((count_a <= target_count and count_b >= target_count) or
                    (count_b <= target_count and count_a >= target_count)):
                m = (trim_b - trim_a) / (count_b - count_a)
                n = trim_a - m * count_a
                target_trim = round(m * target_count + n)
                return (target_trim, trim_range)

        return None

    def choose_trim(self, packet, response, target_count):
        """Choose best trim for given target count from challenge
        responses."""

        calib_data = response[2:]
        challenge_data = packet[2:]
        calib_len = response[1]

        best = None
        best_count = sys.maxsize
        for i in range(calib_len):
            count, = struct.unpack(">H", calib_data[2*i:2*i+2])
            trim_adj, trim_range = struct.unpack(">BB", challenge_data[2*i:2*i+2])
            if abs(count - target_count) < best_count:
                best_count = abs(count - target_count)
                best = (trim_adj, trim_range), count

        return best

    def calibrate(self):
        """Calibrate selected user frequency and the high-speed program
        frequency and switch to selected baudrate."""

        # determine target counters
        user_speed = self.trim_frequency
        if user_speed <= 0: user_speed = self.mcu_clock_hz
        program_speed = 22118400
        target_user_count = round(user_speed / (self.baud_handshake/2))
        target_prog_count = round(program_speed / (self.baud_handshake/2))

        # calibration, round 1
        print("Trimming frequency: ", end="")
        packet = bytes([0x00])
        packet += struct.pack(">B", 12)
        packet += bytes([0x00, 0xc0, 0x80, 0xc0, 0xff, 0xc0])
        packet += bytes([0x00, 0x80, 0x80, 0x80, 0xff, 0x80])
        packet += bytes([0x00, 0x40, 0x80, 0x40, 0xff, 0x40])
        packet += bytes([0x00, 0x00, 0x80, 0x00, 0xc0, 0x00])
        self.write_packet(packet)
        self.ser.write(bytes([0x92, 0x92, 0x92, 0x92]))
        self.ser.flush()
        response = self.read_packet()
        if response[0] != 0x00:
            raise StcProtocolException("incorrect magic in handshake packet")

        # select ranges and trim values
        user_trim = self.choose_range(packet, response, target_user_count)
        prog_trim = self.choose_range(packet, response, target_prog_count)
        if user_trim == None or prog_trim == None:
            raise StcProtocolException("frequency trimming unsuccessful")

        # calibration, round 2
        packet = bytes([0x00])
        packet += struct.pack(">B", 12)
        for i in range(user_trim[0] - 3, user_trim[0] + 3):
            packet += bytes([i & 0xff, user_trim[1]])
        for i in range(prog_trim[0] - 3, prog_trim[0] + 3):
            packet += bytes([i & 0xff, prog_trim[1]])
        self.write_packet(packet)
        self.ser.write(bytes([0x92, 0x92, 0x92, 0x92]))
        self.ser.flush()
        response = self.read_packet()
        if response[0] != 0x00:
            raise StcProtocolException("incorrect magic in handshake packet")

        # select final values
        user_trim, user_count = self.choose_trim(packet, response, target_user_count)
        prog_trim, prog_count = self.choose_trim(packet, response, target_prog_count)
        self.trim_value = user_trim
        self.trim_frequency = round(user_count * (self.baud_handshake / 2))
        print("%.03f MHz" % (self.trim_frequency / 1E6))

        # switch to programming frequency
        print("Switching to %d baud: " % self.baud_transfer, end="")
        packet = bytes([0x01])
        packet += bytes(prog_trim)
        # XXX: baud rate calculation is different between MCUs with and without
        # hardware UART. Only one family of models seems to lack a hardware
        # UART, and we can isolate those with a check on the magic.
        # This is a bit of a hack, but it works.
        bauds = self.baud_transfer if (self.mcu_magic >> 8) == 0xf2 else self.baud_transfer * 4
        packet += struct.pack(">H", int(65535 - program_speed / bauds))
        packet += struct.pack(">H", int(65535 - (program_speed / bauds) * 1.5))
        packet += bytes([0x83])
        self.write_packet(packet)
        response = self.read_packet()
        if response[0] != 0x01:
            raise StcProtocolException("incorrect magic in handshake packet")
        time.sleep(0.2)
        self.ser.baudrate = self.baud_transfer

    def switch_baud_ext(self):
        """Switch baudrate using external clock source"""

        print("Switching to %d baud: " % self.baud_transfer, end="")
        packet = bytes([0x01])
        packet += bytes([self.freq_count_24, 0x40])
        packet += struct.pack(">H", int(65535 - self.mcu_clock_hz / self.baud_transfer / 4))
        packet += bytes([0x00, 0x00, 0x83])
        self.write_packet(packet)
        response = self.read_packet()
        if response[0] != 0x01:
            raise StcProtocolException("incorrect magic in handshake packet")
        time.sleep(0.2)
        self.ser.baudrate = self.baud_transfer

        # for switching back to RC, program factory values
        self.trim_value = (self.freq_count_24, 0x40)
        self.trim_frequency = int(24E6)

    def handshake(self):
        """Do the handshake to calibrate frequencies and switch to
        programming baudrate. Complicated by the fact that programming
        can also use the external clock."""

        # external clock needs special handling
        if self.external_clock:
            self.switch_baud_ext()
        else:
            self.calibrate()

        # test/prepare
        packet = bytes([0x05])
        if self.bsl_version >= 0x72:
            packet += bytes([0x00, 0x00, 0x5a, 0xa5])
        self.write_packet(packet)
        response = self.read_packet()
        if response[0] != 0x05:
            raise StcProtocolException("incorrect magic in handshake packet")

        print("done")

    def erase_flash(self, erase_size, flash_size):
        """Erase the MCU's flash memory.

        Erase the flash memory with a block-erase command.
        Note that this protocol always seems to erase everything.
        """

        # XXX: how does partial erase work?

        print("Erasing flash: ", end="")
        packet = bytes([0x03, 0x00])
        if self.bsl_version >= 0x72:
            packet += bytes([0x00, 0x5a, 0xa5])
        self.write_packet(packet)
        response = self.read_packet()
        if response[0] != 0x03:
            raise StcProtocolException("incorrect magic in handshake packet")
        print("done")

        if len(response) >= 8:
            self.uid = response[1:8]

    def program_flash(self, data):
        """Program the MCU's flash memory."""

        print("Writing %d bytes: " % len(data), end="")
        sys.stdout.flush()
        for i in range(0, len(data), self.PROGRAM_BLOCKSIZE):
            packet = bytes([0x22]) if i == 0 else bytes([0x02])
            packet += struct.pack(">H", i)
            if self.bsl_version >= 0x72:
                packet += bytes([0x5a, 0xa5])
            packet += data[i:i+self.PROGRAM_BLOCKSIZE]
            while len(packet) < self.PROGRAM_BLOCKSIZE + 3: packet += b"\x00"
            self.write_packet(packet)
            response = self.read_packet()
            if response[0] != 0x02 or response[1] != 0x54:
                raise StcProtocolException("incorrect magic in write packet")
            print(".", end="")
            sys.stdout.flush()
        print(" done")

    def program_options(self):
        print("Setting options: ", end="")
        sys.stdout.flush()
        msr = self.options.get_msr()

        packet = bytes([0x04, 0x00, 0x00])
        if self.bsl_version >= 0x72:
            packet += bytes([0x5a, 0xa5])
        packet += bytes([0xff] * 23)
        packet += bytes([(self.trim_frequency >> 24) & 0xff,
                         0xff,
                         (self.trim_frequency >> 16) & 0xff,
                         0xff,
                         (self.trim_frequency >> 8) & 0xff,
                         0xff,
                         (self.trim_frequency >> 0) & 0xff,
                         0xff])
        packet += bytes([msr[3]])
        packet += bytes([0xff] * 27)
        packet += bytes([self.trim_value[0], self.trim_value[1] + 0x3f])
        packet += msr[0:3]
        self.write_packet(packet)
        response = self.read_packet()
        if response[0] != 0x04 or response[1] != 0x54:
            raise StcProtocolException("incorrect magic in option packet")
        print("done")

        print("Target UID: %s" % Utils.hexstr(self.uid))


