# IHex by Kier Davis, modified for Python 3
# Public Domain
# https://github.com/kierdavis/IHex

import struct
import codecs


class IHex:
    """Intel HEX parser and writer"""

    @classmethod
    def read(cls, lines):
        """Read Intel HEX data from string or lines"""
        ihex = cls()

        segbase = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue

            t, a, d = ihex.parse_line(line)
            if t == 0x00:
                ihex.insert_data(segbase + a, d)

            elif t == 0x01:
                break  # Should we check for garbage after this?

            elif t == 0x02:
                ihex.set_mode(16)
                segbase = struct.unpack(">H", d[0:2])[0] << 4

            elif t == 0x03:
                ihex.set_mode(16)

                cs, ip = struct.unpack(">2H", d[0:2])
                ihex.set_start((cs, ip))

            elif t == 0x04:
                ihex.set_mode(32)
                segbase = struct.unpack(">H", d[0:2])[0] << 16

            elif t == 0x05:
                ihex.set_mode(32)
                ihex.set_start(struct.unpack(">I", d[0:4])[0])

            else:
                raise ValueError("Invalid type byte")

        return ihex

    @classmethod
    def read_file(cls, fname):
        """Read Intel HEX data from file"""
        f = open(fname, "rb")
        ihex = cls.read(f)
        f.close()
        return ihex

    def __init__(self):
        self.areas = {}
        self.start = None
        self.mode = 8
        self.row_bytes = 16

    def set_row_bytes(self, row_bytes):
        """Set output hex file row width (bytes represented per row)."""
        if row_bytes < 1 or row_bytes > 0xff:
            raise ValueError("Value out of range: (%r)" % row_bytes)
        self.row_bytes = row_bytes

    def extract_data(self, start=None, end=None):
        """Extract binary data"""
        if start is None:
            start = 0

        if end is None:
            result = bytearray()

            for addr, data in self.areas.items():
                if addr >= start:
                    if len(result) < (addr - start):
                        result[len(result):addr - start] = bytes(
                            addr - start - len(result))
                    result[addr - start:addr - start + len(data)] = data

            return bytes(result)

        result = bytearray()

        for addr, data in self.areas.items():
            if addr >= start and addr < end:
                data = data[:end - addr]
                if len(result) < (addr - start):
                    result[len(result):addr - start] = bytes(
                        addr - start - len(result))
                result[addr - start:addr - start + len(data)] = data

        return bytes(result)

    def set_start(self, start=None):
        self.start = start

    def set_mode(self, mode):
        self.mode = mode

    def get_area(self, addr):
        for start, data in self.areas.items():
            end = start + len(data)
            if addr >= start and addr <= end:
                return start

        return None

    def insert_data(self, istart, idata):
        iend = istart + len(idata)

        area = self.get_area(istart)
        if area is None:
            self.areas[istart] = idata

        else:
            data = self.areas[area]
            # istart - iend + len(idata) + len(data)
            self.areas[area] = data[
                :istart - area] + idata + data[iend - area:]

    def calc_checksum(self, data):
        total = sum(data)
        return (-total) & 0xFF

    def parse_line(self, rawline):
        if rawline[0:1] != b":":
            raise ValueError("Invalid line start character (%r)" % rawline[0])

        try:
            line = codecs.decode(rawline[1:], "hex_codec")
        except ValueError:
            raise ValueError("Invalid hex data")

        length, addr, line_type = struct.unpack(">BHB", line[:4])

        dataend = length + 4
        data = line[4:dataend]

        cs1 = line[dataend]
        cs2 = self.calc_checksum(line[:dataend])

        if cs1 != cs2:
            raise ValueError("Checksums do not match")

        return (line_type, addr, data)

    def make_line(self, line_type, addr, data):
        line = struct.pack(">BHB", len(data), addr, line_type)
        line += data
        line += chr(self.calc_checksum(line))
        return ":" + line.encode("hex").upper() + "\r\n"

    def write(self):
        """Write Intel HEX data to string"""
        output = ""

        for start, data in sorted(self.areas.items()):
            i = 0
            segbase = 0

            while i < len(data):
                chunk = data[i:i + self.row_bytes]

                addr = start
                newsegbase = segbase

                if self.mode == 8:
                    addr = addr & 0xFFFF

                elif self.mode == 16:
                    t = addr & 0xFFFF
                    newsegbase = (addr - t) >> 4
                    addr = t

                    if newsegbase != segbase:
                        output += self.make_line(
                            0x02, 0, struct.pack(">H", newsegbase))
                        segbase = newsegbase

                elif self.mode == 32:
                    newsegbase = addr >> 16
                    addr = addr & 0xFFFF

                    if newsegbase != segbase:
                        output += self.make_line(
                            0x04, 0, struct.pack(">H", newsegbase))
                        segbase = newsegbase

                output += self.make_line(0x00, addr, chunk)

                i += self.row_bytes
                start += self.row_bytes

        if self.start is not None:
            if self.mode == 16:
                output += self.make_line(
                    0x03, 0, struct.pack(">2H", self.start[0], self.start[1]))
            elif self.mode == 32:
                output += self.make_line(
                    0x05, 0, struct.pack(">I", self.start))

        output += self.make_line(0x01, 0, "")
        return output

    def write_file(self, fname):
        """Write Intel HEX data to file"""
        f = open(fname, "w")
        f.write(self.write())
        f.close()
