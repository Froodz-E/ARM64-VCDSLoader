#!/usr/bin/env python3
"""Verify the patcher output against known-good references."""
import struct
import sys
import os

PATCH_OFFSET = 0x763F0  # FUN_140076ff0 file offset


def decode_arm64(inst: int) -> str:
    if inst == 0xD2800000: return "MOV X0,#0"
    if inst == 0xD65F03C0: return "RET"
    if inst == 0xA9BE53F3: return "STP X19,X30,[SP,#-0x50]!"
    if inst == 0xA9015BF5: return "STP X21,X22,[SP,#0x10]"
    return f"0x{inst:08X}"


def verify(original_path: str, patched_path: str, offset: int = PATCH_OFFSET):
    print("=" * 65)
    print("  VERIFICATION: Byte-level comparison at patch site")
    print("=" * 65)

    for label, path in [
        ("Original (unpatched)", original_path),
        ("Patched", patched_path),
    ]:
        with open(path, "rb") as f:
            f.seek(offset)
            data = f.read(8)
        i1 = struct.unpack("<I", data[0:4])[0]
        i2 = struct.unpack("<I", data[4:8])[0]
        print(f"  {label:>30s}: {decode_arm64(i1):<30s} {decode_arm64(i2):<30s}")

    # Full binary compare
    print()
    with open(original_path, "rb") as f:
        orig = f.read()
    with open(patched_path, "rb") as f:
        patched = f.read()

    if len(orig) != len(patched):
        print(f"  Size mismatch: {len(orig):,} vs {len(patched):,}")
    else:
        diff_count = sum(1 for a, b in zip(orig, patched) if a != b)
        print(f"  Total differing bytes: {diff_count}")
        print(f"  Size: {len(orig):,} bytes")

    # Check if patch is MOV X0,#0 + RET at the right offset
    print()
    with open(patched_path, "rb") as f:
        f.seek(offset)
        patched_bytes = f.read(8)
    expected = struct.pack("<I", 0xD2800000) + struct.pack("<I", 0xD65F03C0)
    if patched_bytes == expected:
        print("  ✓ Patch verified: MOV X0,#0 + RET in place at 0x{:X}".format(offset))
    else:
        print(f"  ✗ Patch NOT in place at 0x{offset:X}")
        print(f"    Expected: {expected.hex(' ')}")
        print(f"    Got:      {patched_bytes.hex(' ')}")

    print()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python {os.path.basename(__file__)} <original.exe> <patched.exe>")
        print("  Verifies that the ARM64 VCDS patch (MOV X0,#0 + RET) was applied correctly.")
        sys.exit(1)
    verify(sys.argv[1], sys.argv[2])
