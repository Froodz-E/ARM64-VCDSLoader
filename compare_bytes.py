#!/usr/bin/env python3
"""Compare bytes and decode ARM64 instructions at the patch site across multiple binaries."""
import struct
import sys
import os

PATCH_OFFSET = 0x763F0  # FUN_140076ff0 file offset


def decode_inst(val: int) -> str:
    if val == 0xD2800000: return "MOV X0,#0"
    if val == 0xD65F03C0: return "RET"
    if val == 0xD503201F: return "NOP"
    if val == 0xA9BE53F3: return "STP X19,X30,[SP,#-0x50]!"
    if val == 0xA9015BF5: return "STP X21,X22,[SP,#0x10]"
    return f"0x{val:08X}"


def compare_bytes(filepaths: list, offset: int = PATCH_OFFSET):
    for filepath in filepaths:
        label = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            f.seek(offset)
            data = f.read(16)

        insts = [struct.unpack('<I', data[i:i+4])[0] for i in range(0, 16, 4)]
        inst_str = "  ".join(decode_inst(x) for x in insts)
        print(f"{label:<40s} @ 0x{offset:X}: {data.hex(' ')}")
        print(f"{'':>40s}   asm: {inst_str}")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {os.path.basename(__file__)} <binary1> [binary2] [...]")
        print("  Reads 16 bytes at the patch site (0x763F0) from each file and decodes instructions.")
        sys.exit(1)
    compare_bytes(sys.argv[1:])
