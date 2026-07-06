#!/usr/bin/env python3
"""Check which bytes differ between two VCDS binary files."""
import sys
import os

def diff_check(file_a: str, file_b: str, patch_offset: int = 0x763F0, patch_size: int = 8):
    with open(file_a, "rb") as f:
        data_a = f.read()
    with open(file_b, "rb") as f:
        data_b = f.read()

    diffs = []
    for i in range(min(len(data_a), len(data_b))):
        if data_a[i] != data_b[i]:
            diffs.append((i, data_a[i], data_b[i]))

    print(f"Total differing bytes: {len(diffs)}")
    for offset, b1, b2 in diffs[:30]:
        note = ""
        if patch_offset <= offset < patch_offset + patch_size:
            note = " <-- PATCH SITE (FUN_140076ff0)"
        print(f"  0x{offset:06X}: 0x{b1:02X} → 0x{b2:02X}{note}")
    if len(diffs) > 30:
        print(f"  ... and {len(diffs) - 30} more")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python {os.path.basename(__file__)} <original.exe> <patched.exe>")
        print("  Compares two VCDS binaries byte-by-byte and highlights the patch site.")
        sys.exit(1)
    diff_check(sys.argv[1], sys.argv[2])
