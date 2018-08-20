#
# Copyright (c) 2013-2016 Grigori Goronzy <greg@chown.ath.cx>
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

import struct
from abc import ABC
from stcgal.utils import Utils

class BaseOption(ABC):
    """Base class for options"""

    def __init__(self):
        self.options = ()
        self.msr = None

    def print(self):
        """Print current configuration to standard output"""
        print("Target options:")
        for name, get_func, _ in self.options:
            print("  %s=%s" % (name, get_func()))

    def set_option(self, name, value):
        """Set value of a specific option"""
        for opt, _, set_func in self.options:
            if opt == name:
                print("Option %s=%s" % (name, value))
                set_func(value)
                return
        raise ValueError("unknown")

    def get_option(self, name):
        """Get option value for a specific option"""
        for opt, get_func, _ in self.options:
            if opt == name:
                return get_func(name)
        raise ValueError("unknown")

    def get_msr(self):
        """Get array of model-specific configuration registers"""
        return bytes(self.msr)


class Stc89Option(BaseOption):
    """Manipulation STC89 series option byte"""

    def __init__(self, msr):
        super().__init__()
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
        val = Utils.to_bool(val)
        self.msr &= 0xfe
        self.msr |= 0x01 if not bool(val) else 0x00

    def get_pindetect(self):
        return not bool(self.msr & 4)

    def set_pindetect(self, val):
        val = Utils.to_bool(val)
        self.msr &= 0xfb
        self.msr |= 0x04 if not bool(val) else 0x00

    def get_ee_erase(self):
        return not bool(self.msr & 8)

    def set_ee_erase(self, val):
        val = Utils.to_bool(val)
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
        val = Utils.to_bool(val)
        self.msr &= 0xdf
        self.msr |= 0x20 if bool(val) else 0x00

    def get_xram(self):
        return bool(self.msr & 64)

    def set_xram(self, val):
        val = Utils.to_bool(val)
        self.msr &= 0xbf
        self.msr |= 0x40 if bool(val) else 0x00

    def get_watchdog(self):
        return not bool(self.msr & 128)

    def set_watchdog(self, val):
        val = Utils.to_bool(val)
        self.msr &= 0x7f
        self.msr |= 0x80 if not bool(val) else 0x00


class Stc12AOption(BaseOption):
    """Manipulate STC12A series option bytes"""

    def __init__(self, msr):
        super().__init__()
        assert len(msr) == 4
        self.msr = bytearray(msr)

        """list of options and their handlers"""
        self.options = (
            ("low_voltage_reset", self.get_low_voltage_detect, self.set_low_voltage_detect),
            ("clock_source", self.get_clock_source, self.set_clock_source),
            ("watchdog_por_enabled", self.get_watchdog, self.set_watchdog),
            ("watchdog_stop_idle", self.get_watchdog_idle, self.set_watchdog_idle),
            ("watchdog_prescale", self.get_watchdog_prescale, self.set_watchdog_prescale),
            ("eeprom_erase_enabled", self.get_ee_erase, self.set_ee_erase),
            ("bsl_pindetect_enabled", self.get_pindetect, self.set_pindetect),
        )

    def get_low_voltage_detect(self):
        lvd = bool(self.msr[3] & 64)
        return "high" if not lvd else "low"

    def set_low_voltage_detect(self, val):
        lvds = {"low": 1, "high": 0}
        if val not in lvds.keys():
            raise ValueError("must be one of %s" % list(lvds.keys()))
        self.msr[3] &= 0xbf
        self.msr[3] |= lvds[val] << 6

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
        val = Utils.to_bool(val)
        self.msr[1] &= 0xdf
        self.msr[1] |= 0x20 if not val else 0x00

    def get_watchdog_idle(self):
        return not bool(self.msr[1] & 8)

    def set_watchdog_idle(self, val):
        val = Utils.to_bool(val)
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
        val = Utils.to_bool(val)
        self.msr[2] &= 0xfd
        self.msr[2] |= 0x02 if not val else 0x00

    def get_pindetect(self):
        return not bool(self.msr[2] & 1)

    def set_pindetect(self, val):
        val = Utils.to_bool(val)
        self.msr[2] &= 0xfe
        self.msr[2] |= 0x01 if not val else 0x00


class Stc12Option(BaseOption):
    """Manipulate STC10/11/12 series option bytes"""

    def __init__(self, msr):
        super().__init__()
        assert len(msr) == 4
        self.msr = bytearray(msr)

        """list of options and their handlers"""
        self.options = (
            ("reset_pin_enabled", self.get_reset_pin_enabled, self.set_reset_pin_enabled),
            ("low_voltage_reset", self.get_low_voltage_detect, self.set_low_voltage_detect),
            ("oscillator_stable_delay", self.get_osc_stable_delay, self.set_osc_stable_delay),
            ("por_reset_delay", self.get_por_delay, self.set_por_delay),
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
        val = Utils.to_bool(val)
        self.msr[0] &= 0xfe
        self.msr[0] |= 0x01 if bool(val) else 0x00

    def get_low_voltage_detect(self):
        return not bool(self.msr[0] & 64)

    def set_low_voltage_detect(self, val):
        val = Utils.to_bool(val)
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
        val = Utils.to_bool(val)
        self.msr[2] &= 0xdf
        self.msr[2] |= 0x20 if not val else 0x00

    def get_watchdog_idle(self):
        return not bool(self.msr[2] & 8)

    def set_watchdog_idle(self, val):
        val = Utils.to_bool(val)
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
        val = Utils.to_bool(val)
        self.msr[3] &= 0xfd
        self.msr[3] |= 0x02 if not val else 0x00

    def get_pindetect(self):
        return not bool(self.msr[3] & 1)

    def set_pindetect(self, val):
        val = Utils.to_bool(val)
        self.msr[3] &= 0xfe
        self.msr[3] |= 0x01 if not val else 0x00


class Stc15AOption(BaseOption):
    def __init__(self, msr):
        super().__init__()
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
        val = Utils.to_bool(val)
        self.msr[0] &= 0xef
        self.msr[0] |= 0x10 if bool(val) else 0x00

    def get_watchdog(self):
        return not bool(self.msr[2] & 32)

    def set_watchdog(self, val):
        val = Utils.to_bool(val)
        self.msr[2] &= 0xdf
        self.msr[2] |= 0x20 if not val else 0x00

    def get_watchdog_idle(self):
        return not bool(self.msr[2] & 8)

    def set_watchdog_idle(self, val):
        val = Utils.to_bool(val)
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
        val = Utils.to_bool(val)
        self.msr[1] &= 0xbf
        self.msr[1] |= 0x40 if val else 0x00

    def get_eeprom_lvd(self):
        return bool(self.msr[1] & 128)

    def set_eeprom_lvd(self, val):
        val = Utils.to_bool(val)
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
        val = Utils.to_bool(val)
        self.msr[12] &= 0xfd
        self.msr[12] |= 0x02 if not val else 0x00

    def get_pindetect(self):
        return not bool(self.msr[12] & 1)

    def set_pindetect(self, val):
        val = Utils.to_bool(val)
        self.msr[12] &= 0xfe
        self.msr[12] |= 0x01 if not val else 0x00


class Stc15Option(BaseOption):
    def __init__(self, msr):
        super().__init__()
        assert len(msr) >= 4
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
            ("por_reset_delay", self.get_por_delay, self.set_por_delay),
            ("rstout_por_state", self.get_p33_state, self.set_p33_state),
            ("uart2_passthrough", self.get_uart_passthrough, self.set_uart_passthrough),
            ("uart2_pin_mode", self.get_uart_pin_mode, self.set_uart_pin_mode),
        )

        if len(msr) > 4:
            self.options += (("cpu_core_voltage", self.get_core_voltage, self.set_core_voltage),)

    def get_reset_pin_enabled(self):
        return not bool(self.msr[2] & 16)

    def set_reset_pin_enabled(self, val):
        val = Utils.to_bool(val)
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
        val = Utils.to_bool(val)
        self.msr[0] &= 0xdf
        self.msr[0] |= 0x20 if not val else 0x00

    def get_watchdog_idle(self):
        return not bool(self.msr[0] & 8)

    def set_watchdog_idle(self, val):
        val = Utils.to_bool(val)
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
        val = Utils.to_bool(val)
        self.msr[1] &= 0xbf
        self.msr[1] |= 0x40 if not val else 0x00

    def get_eeprom_lvd(self):
        return bool(self.msr[1] & 128)

    def set_eeprom_lvd(self, val):
        val = Utils.to_bool(val)
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
        val = Utils.to_bool(val)
        self.msr[3] &= 0xfd
        self.msr[3] |= 0x02 if val else 0x00

    def get_pindetect(self):
        return not bool(self.msr[3] & 1)

    def set_pindetect(self, val):
        val = Utils.to_bool(val)
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

    def get_core_voltage(self):
        if self.msr[4] == 0xea: return "low"
        elif self.msr[4] == 0xf7: return "mid"
        elif self.msr[4] == 0xfd: return "high"
        return "unknown"

    def set_core_voltage(self, val):
        volt_vals = {"low": 0xea, "mid": 0xf7, "high": 0xfd}
        if val not in volt_vals.keys():
            raise ValueError("must be one of %s" % list(volt_vals.keys()))
        self.msr[4] = volt_vals[val]

class Stc8Option(BaseOption):
    def __init__(self, msr):
        super().__init__()
        assert len(msr) >= 5
        self.msr = bytearray(msr)

        self.options = (
            ("reset_pin_enabled", self.get_reset_pin_enabled, self.set_reset_pin_enabled),
            ("clock_gain", self.get_clock_gain, self.set_clock_gain),
            ("watchdog_por_enabled", self.get_watchdog, self.set_watchdog),
            ("watchdog_stop_idle", self.get_watchdog_idle, self.set_watchdog_idle),
            ("watchdog_prescale", self.get_watchdog_prescale, self.set_watchdog_prescale),
            ("low_voltage_reset", self.get_lvrs, self.set_lvrs),
            ("low_voltage_threshold", self.get_low_voltage, self.set_low_voltage),
            ("eeprom_erase_enabled", self.get_ee_erase, self.set_ee_erase),
            ("bsl_pindetect_enabled", self.get_pindetect, self.set_pindetect),
            ("por_reset_delay", self.get_por_delay, self.set_por_delay),
            ("rstout_por_state", self.get_p20_state, self.set_p20_state),
            ("uart1_remap", self.get_uart1_remap, self.set_uart1_remap),
            ("uart2_passthrough", self.get_uart_passthrough, self.set_uart_passthrough),
            ("uart2_pin_mode", self.get_uart_pin_mode, self.set_uart_pin_mode),
            ("epwm_open_drain", self.get_epwm_pp, self.set_epwm_pp),
            ("program_eeprom_split", self.get_flash_split, self.set_flash_split),
        )

    def get_reset_pin_enabled(self):
        return not bool(self.msr[2] & 16)

    def set_reset_pin_enabled(self, val):
        val = Utils.to_bool(val)
        self.msr[2] &= 0xef
        self.msr[2] |= 0x10 if not bool(val) else 0x00

    def get_clock_gain(self):
        gain = bool(self.msr[1] & 0x02)
        return "high" if gain else "low"

    def set_clock_gain(self, val):
        gains = {"low": 0, "high": 1}
        if val not in gains.keys():
            raise ValueError("must be one of %s" % list(gains.keys()))
        self.msr[1] &= 0xfd
        self.msr[1] |= gains[val] << 1

    def get_watchdog(self):
        return not bool(self.msr[3] & 32)

    def set_watchdog(self, val):
        val = Utils.to_bool(val)
        self.msr[3] &= 0xdf
        self.msr[3] |= 0x20 if not val else 0x00

    def get_watchdog_idle(self):
        return not bool(self.msr[3] & 8)

    def set_watchdog_idle(self, val):
        val = Utils.to_bool(val)
        self.msr[3] &= 0xf7
        self.msr[3] |= 0x08 if not val else 0x00

    def get_watchdog_prescale(self):
        return 2 ** (((self.msr[3]) & 0x07) + 1)

    def set_watchdog_prescale(self, val):
        val = Utils.to_int(val)
        wd_vals = {2: 0, 4: 1, 8: 2, 16: 3, 32: 4, 64: 5, 128: 6, 256: 7}
        if val not in wd_vals.keys():
            raise ValueError("must be one of %s" % list(wd_vals.keys()))
        self.msr[3] &= 0xf8
        self.msr[3] |= wd_vals[val]

    def get_lvrs(self):
        return not bool(self.msr[2] & 64)

    def set_lvrs(self, val):
        val = Utils.to_bool(val)
        self.msr[2] &= 0xbf
        self.msr[2] |= 0x40 if not val else 0x00

    def get_low_voltage(self):
        return 3 - self.msr[2] & 0x03

    def set_low_voltage(self, val):
        val = Utils.to_int(val)
        if val not in range(0, 4):
            raise ValueError("must be one of %s" % list(range(0, 4)))
        self.msr[2] &= 0xfc
        self.msr[2] |= 3 - val

    def get_ee_erase(self):
        return bool(self.msr[0] & 2)

    def set_ee_erase(self, val):
        val = Utils.to_bool(val)
        self.msr[0] &= 0xfd
        self.msr[0] |= 0x02 if val else 0x00

    def get_pindetect(self):
        return not bool(self.msr[0] & 1)

    def set_pindetect(self, val):
        val = Utils.to_bool(val)
        self.msr[0] &= 0xfe
        self.msr[0] |= 0x01 if not val else 0x00

    def get_por_delay(self):
        delay = bool(self.msr[1] & 128)
        return "long" if delay else "short"

    def set_por_delay(self, val):
        delays = {"short": 0, "long": 1}
        if val not in delays.keys():
            raise ValueError("must be one of %s" % list(delays.keys()))
        self.msr[1] &= 0x7f
        self.msr[1] |= delays[val] << 7

    def get_p20_state(self):
        return "high" if self.msr[1] & 0x08 else "low"

    def set_p20_state(self, val):
        val = Utils.to_bool(val)
        self.msr[1] &= 0xf7
        self.msr[1] |= 0x08 if val else 0x00

    def get_uart_passthrough(self):
        return bool(self.msr[1] & 0x10)

    def set_uart_passthrough(self, val):
        val = Utils.to_bool(val)
        self.msr[1] &= 0xef
        self.msr[1] |= 0x10 if val else 0x00

    def get_uart_pin_mode(self):
        return "push-pull" if bool(self.msr[1] & 0x20) else "normal"

    def set_uart_pin_mode(self, val):
        modes = {"normal": 0, "push-pull": 1}
        if val not in modes.keys():
            raise ValueError("must be one of %s" % list(modes.keys()))
        self.msr[1] &= 0xdf
        self.msr[1] |= 0x20 if modes[val] else 0x00

    def get_epwm_pp(self):
        return bool(self.msr[1] & 0x04)

    def set_epwm_pp(self, val):
        val = Utils.to_bool(val)
        self.msr[1] &= 0xfb
        self.msr[1] |= 0x04 if val else 0x00

    def get_uart1_remap(self):
        return bool(self.msr[1] & 0x40)

    def set_uart1_remap(self, val):
        val = Utils.to_bool(val)
        self.msr[1] &= 0xbf
        self.msr[1] |= 0x40 if val else 0x00

    def get_flash_split(self):
        return self.msr[4] * 256

    def set_flash_split(self, val):
        num_val = Utils.to_int(val)
        if num_val < 512 or num_val > 65024 or (num_val % 512) != 0:
            raise ValueError("must be between 512 and 65024 bytes and a multiple of 512 bytes")
        self.msr[4] = num_val // 256