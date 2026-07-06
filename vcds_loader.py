#!/usr/bin/env python3
"""
VCDSLoader — ARM64 VCDS.exeL License Bypass Patcher
=====================================================

Target: ARM64 VCDS v26.3 (VCDS.exeL)
ImageBase: 0x140000000

Patches Applied:
  Patch #1 (Version String) — file offset 0x1FA31B
    The leading byte of a version/license string is already 0x00.
    No binary change needed; documented here for audit trail.

  Patch #2 (License Validation Bypass) — RVA 0x140076FF0 → file offset 0x763F0
    Function FUN_140076ff0 checks a global interface pointer (DAT_140553f40).
    When NULL, it shows MessageBoxA("Interface Adapter Not Initialized") and
    returns an error code. We patch the function prologue to always return 0:
      MOV X0, #0   (0xD2800000)   — set return value to 0 (success)
      RET          (0xD65F03C0)   — return immediately
    Original first 8 bytes are backed up to <output>.orig.bin.

Usage:
  python vcds_loader.py --input VCDS.exeL --output VCDS_patched.exeL
  python vcds_loader.py --input VCDS.exeL --dry-run
"""

import argparse
import os
import struct
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# PE32+ (64-bit) constants
IMAGE_FILE_MACHINE_ARM64 = 0xAA64
PE32_PLUS_MAGIC = 0x020B

# Patch definitions
# Patch #1: Version string byte — no change needed but documented
PATCH1_FILE_OFFSET = 0x1FA31B
PATCH1_DESCRIPTION = (
    "Version/license string leading byte at file offset 0x1FA31B — "
    "already 0x00 (null-terminator / empty flag). No binary change required."
)

# Patch #2: License validation bypass at FUN_140076ff0
TARGET_RVA = 0x76FF0  # 0x140076FF0 - ImageBase 0x140000000
PATCH2_DESCRIPTION = (
    "FUN_140076ff0 license validation bypass.  "
    "Replace function prologue with MOV X0,#0 + RET."
)
# ARM64 instruction encoding (little-endian in the file):
#   MOV X0, #0  → 0xD2800000
#   RET         → 0xD65F03C0
PATCH2_ASM = [
    ("MOV X0, #0", struct.pack("<I", 0xD2800000)),
    ("RET",        struct.pack("<I", 0xD65F03C0)),
]
PATCH2_SIZE = sum(len(b) for _, b in PATCH2_ASM)  # 8 bytes


# ---------------------------------------------------------------------------
# PE data structures
# ---------------------------------------------------------------------------

@dataclass
class PESection:
    """Represents one PE section header."""
    name: str
    virtual_address: int   # RVA of section start
    virtual_size: int      # size in memory
    raw_offset: int        # file offset of section data
    raw_size: int          # size on disk
    characteristics: int   # section flags

    def contains_rva(self, rva: int) -> bool:
        """Check if an RVA falls within this section."""
        return self.virtual_address <= rva < self.virtual_address + self.virtual_size

    def rva_to_file_offset(self, rva: int) -> int:
        """Convert an RVA within this section to a file offset."""
        if not self.contains_rva(rva):
            raise ValueError(
                f"RVA 0x{rva:X} not in section {self.name} "
                f"(range 0x{self.virtual_address:X}–0x{self.virtual_address + self.virtual_size:X})"
            )
        return self.raw_offset + (rva - self.virtual_address)


@dataclass
class PEInfo:
    """Parsed PE header information."""
    image_base: int
    sections: List[PESection] = field(default_factory=list)
    machine: int = 0
    is_arm64: bool = False

    def rva_to_file_offset(self, rva: int) -> int:
        """Convert an RVA to a raw file offset using the section table."""
        for sec in self.sections:
            if sec.contains_rva(rva):
                return sec.rva_to_file_offset(rva)
        raise ValueError(f"RVA 0x{rva:X} does not fall within any section.")


# ---------------------------------------------------------------------------
# PE parsing
# ---------------------------------------------------------------------------

def parse_pe(filepath: str) -> PEInfo:
    """
    Parse PE headers from a Windows executable and return PEInfo.

    Raises ValueError if the file is not a valid ARM64 PE32+ executable.
    """
    with open(filepath, "rb") as f:
        # --- DOS header ---
        dos = f.read(64)
        if len(dos) < 64 or dos[0:2] != b"MZ":
            raise ValueError("Not a valid DOS/PE executable (missing MZ signature).")

        e_lfanew = struct.unpack_from("<I", dos, 0x3C)[0]

        # --- PE signature ---
        f.seek(e_lfanew)
        pe_sig = f.read(4)
        if pe_sig != b"PE\x00\x00":
            raise ValueError("Missing PE signature at e_lfanew.")

        # --- COFF header ---
        coff = f.read(20)
        machine = struct.unpack_from("<H", coff, 0)[0]
        num_sections = struct.unpack_from("<H", coff, 2)[0]
        size_of_optional_header = struct.unpack_from("<H", coff, 16)[0]

        if machine != IMAGE_FILE_MACHINE_ARM64:
            raise ValueError(
                f"Expected ARM64 machine (0x{IMAGE_FILE_MACHINE_ARM64:04X}), "
                f"got 0x{machine:04X}."
            )

        # --- Optional header (PE32+) ---
        opt = f.read(size_of_optional_header)
        magic = struct.unpack_from("<H", opt, 0)[0]
        if magic != PE32_PLUS_MAGIC:
            raise ValueError(f"Expected PE32+ (0x{PE32_PLUS_MAGIC:04X}), got 0x{magic:04X}.")

        image_base = struct.unpack_from("<Q", opt, 24)[0]

        # --- Section headers ---
        f.seek(e_lfanew + 4 + 20 + size_of_optional_header)
        sections = []
        for _ in range(num_sections):
            raw = f.read(40)
            name = raw[0:8].rstrip(b"\x00").decode("ascii", errors="replace")
            virt_size   = struct.unpack_from("<I", raw, 8)[0]
            virt_addr   = struct.unpack_from("<I", raw, 12)[0]
            raw_size    = struct.unpack_from("<I", raw, 16)[0]
            raw_offset  = struct.unpack_from("<I", raw, 20)[0]
            chars       = struct.unpack_from("<I", raw, 36)[0]
            sections.append(PESection(
                name=name,
                virtual_address=virt_addr,
                virtual_size=virt_size,
                raw_offset=raw_offset,
                raw_size=raw_size,
                characteristics=chars,
            ))

    return PEInfo(
        image_base=image_base,
        sections=sections,
        machine=machine,
        is_arm64=True,
    )


# ---------------------------------------------------------------------------
# Core patching logic
# ---------------------------------------------------------------------------

def read_bytes_at(filepath: str, offset: int, size: int) -> bytes:
    """Read `size` bytes from `filepath` at `offset`."""
    with open(filepath, "rb") as f:
        f.seek(offset)
        return f.read(size)


def apply_patch(data: bytearray, offset: int, patch_bytes: bytes) -> None:
    """Overwrite bytes in `data` at `offset` with `patch_bytes`."""
    end = offset + len(patch_bytes)
    if end > len(data):
        raise ValueError(
            f"Patch at 0x{offset:X} runs past end of file "
            f"(patch end=0x{end:X}, file size=0x{len(data):X})."
        )
    data[offset:end] = patch_bytes


def backup_patch_bytes(
    data: bytearray, offset: int, size: int, backup_path: str
) -> None:
    """Save the original bytes being overwritten to a backup file."""
    original = bytes(data[offset : offset + size])
    with open(backup_path, "wb") as f:
        f.write(original)


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------

def print_banner():
    """Print a header banner."""
    print("=" * 65)
    print("  VCDSLoader — ARM64 VCDS.exeL License Bypass Patcher")
    print("=" * 65)


def run_patch(
    input_path: str,
    output_path: str,
    dry_run: bool = False,
) -> bool:
    """
    Open the ARM64 VCDS.exeL, apply patches, and save the result.

    Returns True on success, False on failure.
    """
    # ------------------------------------------------------------------
    # Step 1: Validate input
    # ------------------------------------------------------------------
    if not os.path.isfile(input_path):
        print(f"[ERROR] Input file not found: {input_path}")
        return False

    file_size = os.path.getsize(input_path)
    print(f"\n[INFO] Input file : {input_path}")
    print(f"[INFO] File size   : {file_size:,} bytes (0x{file_size:X})")

    # ------------------------------------------------------------------
    # Step 2: Parse PE headers
    # ------------------------------------------------------------------
    print("\n[STEP 1] Parsing PE headers ...")
    try:
        pe = parse_pe(input_path)
    except ValueError as e:
        print(f"[ERROR] PE parsing failed: {e}")
        return False

    print(f"  ImageBase      : 0x{pe.image_base:016X}")
    print(f"  Machine        : ARM64 (0x{pe.machine:04X})")
    print(f"  Sections       : {len(pe.sections)}")
    for sec in pe.sections:
        print(
            f"    {sec.name:<10s}  "
            f"VirtAddr=0x{sec.virtual_address:08X}  "
            f"VirtSize=0x{sec.virtual_size:08X}  "
            f"RawOff=0x{sec.raw_offset:08X}  "
            f"RawSize=0x{sec.raw_size:08X}"
        )

    # ------------------------------------------------------------------
    # Step 3: Resolve patch offsets
    # ------------------------------------------------------------------
    print("\n[STEP 2] Resolving patch offsets ...")

    # Patch #2: RVA → file offset
    try:
        patch2_file_offset = pe.rva_to_file_offset(TARGET_RVA)
    except ValueError as e:
        print(f"[ERROR] Cannot resolve patch #2 RVA: {e}")
        return False

    print(f"  Patch #2 RVA 0x{TARGET_RVA:X} → file offset 0x{patch2_file_offset:X}")

    # Read original bytes at patch site
    original_patch2_bytes = read_bytes_at(input_path, patch2_file_offset, PATCH2_SIZE)

    # Patch #1: fixed file offset
    print(f"  Patch #1 file offset 0x{PATCH1_FILE_OFFSET:X} (fixed)")
    original_patch1_byte = read_bytes_at(input_path, PATCH1_FILE_OFFSET, 1)

    # ------------------------------------------------------------------
    # Step 4: Build patch plan
    # ------------------------------------------------------------------
    patch2_bytes = b"".join(b for _, b in PATCH2_ASM)

    print("\n[STEP 3] Patch plan")
    print(f"  Patch #1 (Version String @ 0x{PATCH1_FILE_OFFSET:X}):")
    print(f"    Current byte : 0x{original_patch1_byte.hex():>02s}")
    print(f"    Target byte  : 0x00 (no change)")
    print(f"    {PATCH1_DESCRIPTION}")

    print(f"\n  Patch #2 (License Bypass @ 0x{patch2_file_offset:X}):")
    for i, (mnemonic, encoded) in enumerate(PATCH2_ASM):
        addr = patch2_file_offset + i * 4
        orig = original_patch2_bytes[i * 4 : (i + 1) * 4]
        print(
            f"    0x{addr:08X}:  {orig.hex(' '):<11s} → "
            f"{encoded.hex(' '):<11s}  ({mnemonic})"
        )

    # Check if already patched
    already_patched = original_patch2_bytes[:PATCH2_SIZE] == patch2_bytes
    if already_patched:
        print("\n  [!] Patch #2 appears ALREADY APPLIED (bytes match MOV X0,#0 + RET).")
    else:
        print("\n  [→] Patch #2 will be applied.")

    # ------------------------------------------------------------------
    # Step 5: Dry-run / apply
    # ------------------------------------------------------------------
    if dry_run:
        print("\n" + "=" * 65)
        print("  DRY-RUN MODE — No files were modified.")
        print("=" * 65)
        return True

    # ------------------------------------------------------------------
    # Step 6: Read full binary and apply patches
    # ------------------------------------------------------------------
    print(f"\n[STEP 4] Reading input file ({file_size:,} bytes) ...")
    with open(input_path, "rb") as f:
        data = bytearray(f.read())

    # Only apply patch #2 (patch #1 is a no-op)
    if not already_patched:
        print(f"[STEP 5] Applying Patch #2 at offset 0x{patch2_file_offset:X} ...")

        # Back up original bytes
        orig_backup_path = output_path + ".orig.bin"
        backup_patch_bytes(data, patch2_file_offset, PATCH2_SIZE, orig_backup_path)
        print(f"  Original bytes saved to: {orig_backup_path}")

        # Apply patch
        apply_patch(data, patch2_file_offset, patch2_bytes)
        print("  Patch applied successfully.")
    else:
        print("[STEP 5] Patch #2 already in place; skipping.")
        # Still save a copy of current bytes as backup for reference
        orig_backup_path = output_path + ".orig.bin"
        backup_patch_bytes(data, patch2_file_offset, PATCH2_SIZE, orig_backup_path)
        print(f"  Current bytes saved to: {orig_backup_path} (for reference)")

    # ------------------------------------------------------------------
    # Step 7: Write patched binary
    # ------------------------------------------------------------------
    print(f"\n[STEP 6] Writing patched binary to: {output_path}")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(data)

    output_size = os.path.getsize(output_path)
    print(f"  Written {output_size:,} bytes.")

    # ------------------------------------------------------------------
    # Step 8: Verify
    # ------------------------------------------------------------------
    print("\n[STEP 7] Verifying patched binary ...")
    verify_bytes = read_bytes_at(output_path, patch2_file_offset, PATCH2_SIZE)
    expected = patch2_bytes

    if verify_bytes[:PATCH2_SIZE] == expected:
        print("  ✓ Patch #2 verified — MOV X0,#0 + RET in place.")
    else:
        print(f"  ✗ VERIFICATION FAILED!")
        print(f"    Expected: {expected.hex(' ')}")
        print(f"    Got:      {verify_bytes.hex(' ')}")
        return False

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    print("\n" + "=" * 65)
    print("  PATCH COMPLETE")
    print("=" * 65)
    print(f"  Input  : {input_path}")
    print(f"  Output : {output_path}")
    print(f"  Backup : {orig_backup_path}")
    print()
    print("  Patch #1 (Version String): Documented — no binary change needed.")
    print("  Patch #2 (License Bypass): FUN_140076ff0 → MOV X0,#0 ; RET")
    return True


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="VCDSLoader — ARM64 VCDS.exeL License Bypass Patcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python vcds_loader.py --input VCDS.exeL --dry-run
  python vcds_loader.py --input VCDS.exeL --output VCDS_patched.exeL
  python vcds_loader.py -i VCDS.exeL.bak -o VCDS_patched.exeL
        """,
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to the ARM64 VCDS.exeL binary to patch.",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Path for the patched output binary (default: <input>.patched).",
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Print what would be patched without modifying any files.",
    )
    args = parser.parse_args()

    # Resolve output path
    if args.output is None:
        args.output = args.input + ".patched"

    print_banner()

    success = run_patch(
        input_path=args.input,
        output_path=args.output,
        dry_run=args.dry_run,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
