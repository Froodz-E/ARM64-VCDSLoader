#!/usr/bin/env python3
"""Verify the patcher output against known-good references."""
import struct
import os

BASE = r"D:\VCDS Test\ARM64\Installation\VCDS"
OFFSET = 0x763F0

def decode_arm64(inst: int) -> str:
    if inst == 0xD2800000: return "MOV X0,#0"
    if inst == 0xD65F03C0: return "RET"
    if inst == 0xA9BE53F3: return "STP X19,X20,[SP,#-0x30]!"
    if inst == 0xA9015BF5: return "STP X21,X22,[SP,#0x10]"
    return f"0x{inst:08X}"

print("=" * 65)
print("  VERIFICATION: Byte-level comparison")
print("=" * 65)

for label, fname in [
    ("bak (original)",           "VCDS.exeL.bak"),
    ("current (already patched)", "VCDS.exeL"),
    ("our test output",           "VCDS_test_patched.exeL"),
]:
    path = os.path.join(BASE, fname)
    with open(path, "rb") as f:
        f.seek(OFFSET)
        data = f.read(8)
    i1 = struct.unpack("<I", data[0:4])[0]
    i2 = struct.unpack("<I", data[4:8])[0]
    print(f"  {label:>30s}: {decode_arm64(i1):<30s} {decode_arm64(i2):<30s}")

# Verify backup file
print()
backup_path = os.path.join(BASE, "VCDS_test_patched.exeL.orig.bin")
with open(backup_path, "rb") as f:
    orig = f.read(8)
print(f"  Backup (.orig.bin):  {orig.hex(' ')}")
print(f"  Expected (original): f3 53 be a9 f5 5b 01 a9")
print(f"  Match: {orig.hex(' ') == 'f353bea9f55b01a9'}")

# Full binary compare: our output vs already-patched VCDS.exeL
print()
with open(os.path.join(BASE, "VCDS.exeL"), "rb") as f:
    existing = f.read()
with open(os.path.join(BASE, "VCDS_test_patched.exeL"), "rb") as f:
    ours = f.read()
print(f"  Our output matches already-patched VCDS.exeL: {existing == ours}")
print(f"  Size check: {len(existing):,} vs {len(ours):,}")

# Clean up test files
print("\n  Cleaning up test files...")
for f in ["VCDS_test_copy.exeL", "VCDS_test_patched.exeL", "VCDS_test_patched.exeL.orig.bin"]:
    path = os.path.join(BASE, f)
    if os.path.exists(path):
        os.remove(path)
        print(f"    Removed: {f}")
print("\n  Done.")
