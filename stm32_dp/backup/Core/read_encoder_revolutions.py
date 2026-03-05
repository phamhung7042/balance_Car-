#!/usr/bin/env python3
"""Read encoder counters and calculate revolutions over SWD using pyOCD

Requires:
    pip install pyocd pyelftools

Usage:
    python read_encoder_revolutions.py /path/to/your_project.elf

This script extends read_encoder.py to also calculate revolutions based on:
- PPR: 11 pulses per revolution per channel
- Quadrature: x4
- Gear ratio: 30:1
- Total: 1320 ticks per revolution

Connect an ST-Link/v2 or CMSIS-DAP probe to the board and run the script.
"""

import sys
import time
from pyocd.core.helpers import ConnectHelper
from elftools.elf.elffile import ELFFile

import os

# Encoder specifications from robot_params.h
ENCODER_PPR = 11        # pulses per revolution per channel
QUAD_FACTOR = 4         # quadrature encoding x4
GEAR_RATIO = 30.0       # gear ratio
TICKS_PER_REV = ENCODER_PPR * QUAD_FACTOR * GEAR_RATIO  # 1320 ticks/rev

WHEEL_DIAMETER_M = 0.10  # 10cm wheel
WHEEL_CIRC_M = 3.1415926 * WHEEL_DIAMETER_M

if len(sys.argv) < 2:
    print("Usage: python read_encoder_revolutions.py <path_to_elf>")
    sys.exit(1)

elf_path = sys.argv[1]
if not os.path.isfile(elf_path):
    print(f"Error: ELF file not found: {elf_path}")
    # try to help by listing .elf files in current directory
    candidates = [f for f in os.listdir('.') if f.lower().endswith('.elf')]
    if candidates:
        print("Found the following ELF files in this directory:")
        for c in candidates:
            print('  ', c)
    sys.exit(1)

# open elf and locate symbols
with open(elf_path, 'rb') as f:
    elf = ELFFile(f)
    symtab = elf.get_section_by_name('.symtab')
    if symtab is None:
        raise RuntimeError('ELF has no symbol table')
    def find_addr(name):
        sym = symtab.get_symbol_by_name(name)
        if not sym:
            raise KeyError(f'symbol {name} not found in ELF')
        return sym[0]['st_value']

    addr_enc1 = find_addr('Debug_Enc1_Count')
    addr_enc2 = find_addr('Debug_Enc2_Count')

print(f'Encoder1 symbol at 0x{addr_enc1:08X}, Encoder2 at 0x{addr_enc2:08X}')
print(f'Encoder specs: {ENCODER_PPR} PPR, x{QUAD_FACTOR} quad, {GEAR_RATIO}:1 gear = {TICKS_PER_REV} ticks/rev')

# connect to target
session = ConnectHelper.session_with_chosen_probe()
with session:
    target = session.target
    target.resume()          # let CPU run
    print('Reading encoder data, press Ctrl-C to stop')
    print('Format: counts (revolutions) [distance_m]')
    try:
        while True:
            v1 = target.read32(addr_enc1)
            v2 = target.read32(addr_enc2)

            # Calculate revolutions
            rev1 = v1 / TICKS_PER_REV
            rev2 = v2 / TICKS_PER_REV

            # Calculate distance (approximate)
            dist1 = rev1 * WHEEL_CIRC_M
            dist2 = rev2 * WHEEL_CIRC_M

            print(f'enc1={v1:8d} ({rev1:7.3f} rev) [{dist1:6.3f}m]  '
                  f'enc2={v2:8d} ({rev2:7.3f} rev) [{dist2:6.3f}m]', end='\r')
            time.sleep(0.1)
    except KeyboardInterrupt:
        print('\nDone.')