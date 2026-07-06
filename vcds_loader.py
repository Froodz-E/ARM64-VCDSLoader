#!/usr/bin/env python3
"""
ARM64 VCDSLoader - Native ARM64 VCDS 26.3 Patcher
=================================================
Patches the ARM64 VCDS.exeL binary so it runs without license verification.

Strategy: Patch FUN_140076ff0 (the interface/license validation function)
to immediately return 0 (success), bypassing the "Interface Adapter
Not Initialized" error and all license checks.

Combined approach:
  - Patch #1 (cosmetic): Version string at file offset 0x1FA31B
  - Patch #2 (functional): Validation function at file offset 0x763F0
    Replace STP/STP/STP/ADD function prologue with MOV X0,#0; RET

Original research by Ghidra 11.2.1 disassembly of VCDS 26.3 ARM64.
Target: Snapdragon X / Windows on ARM64
"""

import struct
import os
import shutil
import sys

# Target binary
VCDS_PATH = r"D:\VCDS Test\ARM64\Installation\VCDS\VCDS.exeL"

# Patch definitions
PATCHES = [
    {
        "name": "Version string (cosmetic)",
        "file_offset": 0x1FA31B,
        "original": b'\x00',  # 1 byte
        "replacement": b'\x00',  # No change needed (documented for completeness)
        "description": "Unicode string 'ary/driver version' - cosmetic patch"
    },
    {
        "name": "License validation function bypass",
        "file_offset": 0x763F0,
        "original": bytes.fromhex("F3 53 BE A9 F5 5B 01 A9 FD 7B BE A9 FD 03 00 91"),
        "replacement": bytes.fromhex("00 00 80 D2 C0 03 5F D6 1F 20 03 D5 1F 20 03 D5"),
        # MOV X0, #0; RET; NOP; NOP
        "description": "FUN_140076ff0: Replace function prologue with MOV X0,#0; RET; NOP; NOP"
    },
]


def backup(path):
    """Create backup if it doesn't exist"""
    backup_path = path + ".bak"
    if not os.path.exists(backup_path):
        shutil.copy2(path, backup_path)
        print(f"[+] Backup created: {backup_path}")
        return True
    print(f"[i] Backup already exists: {backup_path}")
    return False


def read_binary(path):
    """Read binary as mutable bytearray"""
    with open(path, 'rb') as f:
        return bytearray(f.read())


def verify_pe(data):
    """Basic PE sanity check"""
    if data[:2] != b'MZ':
        raise ValueError("Not a valid PE file (missing MZ signature)")
    pe_off = struct.unpack_from('<I', data, 0x3C)[0]
    if data[pe_off:pe_off+4] != b'PE\x00\x00':
        raise ValueError("Invalid PE signature")
    machine = struct.unpack_from('<H', data, pe_off + 4)[0]
    if machine != 0xAA64:
        raise ValueError(f"Not an ARM64 binary (machine=0x{machine:04X})")
    print(f"[+] Valid ARM64 PE binary ({len(data):,} bytes)")


def apply_patches(data, dry_run=False):
    """Apply all patches to the binary"""
    for patch in PATCHES:
        offset = patch["file_offset"]
        original = patch["original"]
        replacement = patch["replacement"]
        name = patch["name"]
        desc = patch["description"]
        
        # Read current bytes
        current = bytes(data[offset:offset + len(replacement)])
        expected = original.ljust(len(replacement), b'\x00')[:len(replacement)]
        
        print(f"\n--- {name} ---")
        print(f"  Description: {desc}")
        print(f"  File offset: 0x{offset:08X}")
        print(f"  Size: {len(replacement)} bytes")
        print(f"  Original:  {' '.join(f'{b:02X}' for b in current[:16])}")
        
        if dry_run:
            print(f"  [DRY RUN] Would replace with: {' '.join(f'{b:02X}' for b in replacement[:16])}")
        else:
            # Verify current bytes match expected (at least the length of `original`)
            if current[:len(original)] != original[:len(original)]:
                print(f"  WARNING: Bytes at offset don't match expected!")
                print(f"  Expected:  {' '.join(f'{b:02X}' for b in expected[:16])}")
                print(f"  Got:       {' '.join(f'{b:02X}' for b in current[:16])}")
                response = input("  Continue anyway? [y/N]: ")
                if response.lower() != 'y':
                    print("  Skipped.")
                    continue
            
            # Apply the patch
            data[offset:offset + len(replacement)] = replacement
            print(f"  PATCHED: {' '.join(f'{b:02X}' for b in replacement[:16])}")
            print(f"  Result:  {' '.join(f'{b:02X}' for b in data[offset:offset+16])}")
    
    return data


def main():
    """Main entry point"""
    print("=" * 60)
    print("  ARM64 VCDSLoader v0.1")
    print("  Target: VCDS 26.3 ARM64 (Snapdragon X)")
    print("=" * 60)
    
    if not os.path.exists(VCDS_PATH):
        print(f"\n[!] Target not found: {VCDS_PATH}")
        sys.exit(1)
    
    # Parse arguments
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    force = "--force" in sys.argv or "-f" in sys.argv
    
    if dry_run:
        print("\n[DRY RUN MODE] No changes will be written.\n")
    
    # Read binary
    data = read_binary(VCDS_PATH)
    
    # Verify PE
    try:
        verify_pe(data)
    except ValueError as e:
        print(f"[!] {e}")
        sys.exit(1)
    
    # Create backup
    is_new_backup = backup(VCDS_PATH)
    
    if not dry_run and not is_new_backup and not force:
        print("\n[!] Binary already has a backup. Use --force to re-patch.")
        print("    Restore from backup first: cp VCDS.exeL.bak VCDS.exeL")
        sys.exit(1)
    
    # Apply patches
    data = apply_patches(data, dry_run=dry_run)
    
    if dry_run:
        print("\n[DRY RUN] No changes written. Remove -n/--dry-run to apply.")
        return
    
    # Write patched binary
    with open(VCDS_PATH, 'wb') as f:
        f.write(data)
    
    print(f"\n{'='*60}")
    print(f"[SUCCESS] Patched binary written: {VCDS_PATH}")
    print(f"  Backup: {VCDS_PATH}.bak")
    print(f"")
    print(f"  To test: Launch VCDS.exeL from the ARM64 test folder.")
    print(f"  To restore: cp {VCDS_PATH}.bak {VCDS_PATH}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
