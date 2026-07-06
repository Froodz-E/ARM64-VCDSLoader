#!/usr/bin/env python3
"""Compare bytes across back, current, and patched VCDS.exeL files."""
import struct

BASE = r"D:\VCDS Test\ARM64\Installation\VCDS"
OFFSET = 0x763F0

for label, fname in [("bak", "VCDS.exeL.bak"), ("cur", "VCDS.exeL"), ("patched", "VCDS.exeL.patched")]:
    with open(f"{BASE}\\{fname}", "rb") as f:
        f.seek(OFFSET)
        data = f.read(16)
    
    insts = [struct.unpack('<I', data[i:i+4])[0] for i in range(0, 16, 4)]
    inst_str = " ".join(f"0x{x:08X}" for x in insts)
    print(f'{fname:>20s} @ 0x{OFFSET:X}: {data.hex(" ")}')
    print(f'{"":>20s}   asm: {inst_str}')

# Also decode instructions
print()
print("Instruction decode:")
print("  0xD2800000 = MOV X0, #0")
print("  0xD65F03C0 = RET")
print("  0xD503201F = NOP")
