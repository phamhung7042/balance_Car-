#!/usr/bin/env python3
"""Read encoder counters over SWD using pyOCD

Requires:
    pip install pyocd pyelftools

Usage:
    python read_encoder.py /path/to/your_project.elf

Connect an ST-Link/v2 or CMSIS-DAP probe to the board and run the script; it
will print encoder counts continuously. This avoids UART and uses the debug
interface, which is what STM32CubeIDE's Live Expressions already uses.

Make sure the firmware is built and the ELF file path is correct.

"""
import sys
import time
from pyocd.core.helpers import ConnectHelper
from elftools.elf.elffile import ELFFile

if len(sys.argv) < 2:
    print("Usage: python read_encoder.py <path_to_elf>")
    sys.exit(1)

elf_path = sys.argv[1]

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

# connect to target
session = ConnectHelper.session_with_chosen_probe()
with session:
    target = session.target
    target.resume()          # let CPU run
    print('Reading counts, press Ctrl-C to stop')
    try:
        while True:
            v1 = target.read32(addr_enc1)
            v2 = target.read32(addr_enc2)
            print(f'enc1={v1:8d}  enc2={v2:8d}', end='\r')
            time.sleep(0.1)
    except KeyboardInterrupt:
        print('\nDone.')
