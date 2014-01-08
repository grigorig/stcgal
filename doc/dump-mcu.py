#!/usr/bin/env python3
# This curious script dumps all model info from STC-ISP.
# Data is directly read from the binary.
# Offsets are for STC-ISP 6.63, md5sum 62d465a196de26fa3fb4b22c7be4b882.

MCU_TABLE_OFFSET = 0x0004e270
MCU_TABLE_SIZE = 648
MCU_RECORD_SIZE = 32
MCU_NAMES_OFFSET = 0x00062dc8
MCU_NAMES_PTR_OFFSET = 0x00462dc8

import struct
import sys

inp = open(sys.argv[1], "rb")

for i in range(MCU_TABLE_SIZE):
    mcu_record_offset = MCU_TABLE_OFFSET + MCU_RECORD_SIZE * i
    inp.seek(mcu_record_offset)
    mcu_record = inp.read(MCU_RECORD_SIZE)
    flags, name_ptr, mcu_id, code_size, ee_size, _, total_size, _ = struct.unpack("<8I", mcu_record)
    
    mcu_name_offset = MCU_NAMES_OFFSET + (name_ptr - MCU_NAMES_PTR_OFFSET)
    inp.seek(mcu_name_offset)
    name_str = inp.read(16).split(b'\00')[0].decode("ascii")

    # 1 KB are reserved for some reason. in some cases even more. very odd.
    if ee_size > 0 and not name_str.startswith("IAP"):
        ee_size -= 1024

    print("MCUModel(name='%s', magic=0x%02x%02x, total=%d, code=%d, eeprom=%d)," %
        (name_str, mcu_id >> 8, mcu_id & 0xff, total_size, code_size, ee_size))

inp.close()

