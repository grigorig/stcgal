#!/usr/bin/env python3
# This curious script dumps all model info from STC-ISP.
# Data is directly read from the binary.
# Offsets are for stc-isp-15xx-v6.87P.exe, sha256sum d5413728d87cf5d7a6e036348ade5b38cce13113ae3bb090cfac7a232ba82a53

MCU_TABLE_OFFSET = 0x00071c30
MCU_TABLE_SIZE = 1068
MCU_RECORD_SIZE = 32
MCU_NAMES_OFFSET = 0x000924E8
MCU_NAMES_PTR_OFFSET = 0x004924e8

import struct
import sys

inp = open(sys.argv[1], "rb")

for i in range(MCU_TABLE_SIZE):
    mcu_record_offset = MCU_TABLE_OFFSET + MCU_RECORD_SIZE * i
    inp.seek(mcu_record_offset)
    mcu_record = inp.read(MCU_RECORD_SIZE)
    flags, name_ptr, mcu_id, code_size, ee_size, _, total_size, _ = struct.unpack("<8I", mcu_record)
    mcu_id &= 0xffff
    
    mcu_name_offset = MCU_NAMES_OFFSET + (name_ptr - MCU_NAMES_PTR_OFFSET)
    inp.seek(mcu_name_offset)
    name_str = inp.read(16).split(b'\00')[0].decode("ascii")

    # TODO: With some MCUs, the amount of available EEPROM depends on the BSL version.
    # Generally, newer BSLs free up a KB of additional EEPROM. Currently, always the
    # maximum amount (with newer BSL) is reported.

    # STC12x54xx always have 12 KB eeprom
    if name_str.startswith("STC12C54") or name_str.startswith("STC12LE54"):
        ee_size = 12 * 1024

    print("MCUModel(name='%s', magic=0x%02x%02x, total=%d, code=%d, eeprom=%d)," %
        (name_str, mcu_id >> 8, mcu_id & 0xff, total_size, code_size, ee_size))

inp.close()

