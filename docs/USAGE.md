# ARM64 VCDSLoader — Usage Guide

How to patch and run VCDS 26.3 natively on Windows on ARM (Snapdragon X).

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Step-by-Step Guide](#step-by-step-guide)
  - [1. Install VCDS 26.3 ARM64](#1-install-vcds-263-arm64)
  - [2. Locate the Binary](#2-locate-the-binary)
  - [3. Configure the Patcher](#3-configure-the-patcher)
  - [4. Dry Run (Recommended)](#4-dry-run-recommended)
  - [5. Apply the Patch](#5-apply-the-patch)
  - [6. Launch VCDS](#6-launch-vcds)
- [Command-Line Options](#command-line-options)
- [Restoring the Original Binary](#restoring-the-original-binary)
- [Troubleshooting](#troubleshooting)
- [Frequently Asked Questions](#frequently-asked-questions)

---

## Prerequisites

| Requirement | Minimum | Notes |
|-------------|---------|-------|
| **Windows on ARM** | Windows 11 24H2+ | Snapdragon X Elite / Plus |
| **Python** | 3.8+ | Any modern Python 3 works |
| **VCDS 26.3 ARM64** | Build from Mar 2026 or later | Must be the native ARM64 build, not x86 |
| **Disk space** | ~5 MB | For backup copy of binary |

> **Important:** The x86 build of VCDS (`VCDS.exe` / 32-bit `VCDS.exeL`) will NOT be patched by this tool. You need the ARM64-native `VCDS.exeL` (PE32+ with Machine ID `0xAA64`). Running `pe_analyze.py` can verify your binary type.

---

## Quick Start

```bash
# 1. Navigate to the patcher directory
cd arm64-loader

# 2. Dry run first (no files modified)
python vcds_loader.py --input "C:\Ross-Tech\VCDS\VCDS.exeL" --dry-run

# 3. Apply the patch
python vcds_loader.py --input "C:\Ross-Tech\VCDS\VCDS.exeL" --output "VCDS_patched.exeL"

# 4. Launch the patched VCDS
```

---

## Step-by-Step Guide

### 1. Install VCDS 26.3 ARM64

Download and install the ARM64 build of VCDS 26.3. The installer typically places the files in:

```
C:\Ross-Tech\VCDS\          (default)
```

The key binary is `VCDS.exeL` — this is the main VCDS executable. On ARM64, it's a PE32+ binary compiled for `AArch64`.

> **Verification:** Running `pe_analyze.py` on the binary should report `Machine: 0xAA64 (ARM64)`. If it reports `0x8664` (x64) or `0x14C` (x86), you have the wrong build.

### 2. Locate the Binary

Note the full path to your ARM64 `VCDS.exeL`:

```powershell
# Example: find VCDS.exeL anywhere on C:\
Get-ChildItem -Path "C:\Ross-Tech" -Recurse -Filter "VCDS.exeL" 2>$null
```

Common installation paths:
- `C:\Ross-Tech\VCDS\VCDS.exeL` (default)
- `C:\Program Files\Ross-Tech\VCDS\VCDS.exeL`

### 3. Configure the Patcher

No configuration needed — the patcher takes the binary path as a command-line argument:

```bash
python vcds_loader.py --input <path_to_VCDS.exeL> --output <output_path>
```

### 4. Dry Run (Recommended)

Always do a dry run first to verify the binary is correct and patches will apply cleanly:

```bash
python vcds_loader.py --dry-run
```

Expected output:

```
============================================================
  VCDSLoader — ARM64 VCDS.exeL License Bypass Patcher
============================================================

[STEP 1] Parsing PE headers ...
  ImageBase      : 0x0000000140000000
  Machine        : ARM64 (0xAA64)
  Sections       : 5
    ...

[STEP 2] Resolving patch offsets ...
  Patch #2 RVA 0x76FF0 → file offset 0x763F0
  Patch #1 file offset 0x1FA31B (fixed)

[STEP 3] Patch plan
  ...

============================================================
  DRY-RUN MODE — No files were modified.
============================================================
```

### 5. Apply the Patch

When the dry run looks correct, apply the patch:

```bash
python vcds_loader.py --input "C:\Ross-Tech\VCDS\VCDS.exeL" --output "VCDS_patched.exeL"
```

The script will:
1. Verify the binary is a valid ARM64 PE
2. Parse the PE headers and resolve patch offsets
3. Back up the original bytes to `<output>.orig.bin`
4. Apply the MOV X0,#0 + RET patch at the validation function
5. Verify the patch was applied correctly

Expected output:

```
============================================================
  VCDSLoader — ARM64 VCDS.exeL License Bypass Patcher
============================================================

[STEP 6] Writing patched binary to: VCDS_patched.exeL
  Written 2,193,752 bytes.

[STEP 7] Verifying patched binary ...
  ✓ Patch #2 verified — MOV X0,#0 + RET in place.

============================================================
  PATCH COMPLETE
============================================================
  Input  : C:\Ross-Tech\VCDS\VCDS.exeL
  Output : VCDS_patched.exeL
  Backup : VCDS_patched.exeL.orig.bin

  Patch #1 (Version String): Documented — no binary change needed.
  Patch #2 (License Bypass): FUN_140076ff0 → MOV X0,#0 ; RET
```

### 6. Launch VCDS

Copy the patched binary into your VCDS installation directory and run it:

```bash
# Copy patched binary into VCDS installation
copy VCDS_patched.exeL "C:\Ross-Tech\VCDS\VCDS.exeL"

# From terminal:
cd "C:\Ross-Tech\VCDS"
start VCDS.exeL
```

Or double-click `VCDS.exeL` in File Explorer.

VCDS should launch without the "Interface Adapter Not Initialized" error. The application will start normally and display the main diagnostic screen.

---

## Command-Line Options

| Flag | Alias | Description |
|------|-------|-------------|
| `--input` | `-i` | **(Required)** Path to the ARM64 `VCDS.exeL` binary to patch. |
| `--output` | `-o` | Path for the patched output binary (default: `<input>.patched`). |
| `--dry-run` | `-n` | Simulate patches without writing. Shows what WOULD change. |

### Examples

```bash
# Dry run: see what changes would be made
python vcds_loader.py --input VCDS.exeL --dry-run

# Apply patch (output defaults to VCDS.exeL.patched)
python vcds_loader.py --input VCDS.exeL

# Specifying a custom output path
python vcds_loader.py -i VCDS.exeL -o patched\VCDS.exeL
```

---

## Restoring the Original Binary

The patcher saves the original bytes to `<output>.orig.bin`. To restore:

```bash
# Re-patch from the original binary (if you still have it)
python vcds_loader.py --input VCDS.exeL.orig --output VCDS_restored.exeL

# Or re-install VCDS from the original source
```

> **Note:** The patcher saves the overwritten bytes (8 bytes) in `<output>.orig.bin`. This is for verification — to fully restore, keep a copy of the original binary.

---

## Troubleshooting

### "Not a valid PE file (missing MZ signature)"

The binary is corrupt or not a PE executable. Re-install VCDS from the original source.

### "Not an ARM64 binary (machine=0x8664)"

You're pointing at the wrong build. VCDS ships an x64 build for Intel/AMD and an ARM64 build for Snapdragon. Ensure you have the ARM64 installer. Check with `pe_analyze.py`.

### "Target not found"

The `--input` path doesn't point to a valid file. Verify the path to your VCDS binary:

```bash
# Example
dir "C:\Ross-Tech\VCDS\VCDS.exeL"
```

### "Bytes at offset don't match expected!"

The binary's bytes at the patch location differ from what was expected. This can happen if:
- You're using a different VCDS version (not 26.3 ARM64)
- The binary was already patched by another tool
- The binary was modified post-installation

**Solution:** Restore from backup (or reinstall) and try again. If the problem persists, the validation function may have been moved — re-analyze with Ghidra (see [TECHNICAL.md](TECHNICAL.md)).

### VCDS crashes after patching

1. Restore from backup
2. Verify you're patching the ARM64 build, not x86/x64
3. Verify VCDS version is 26.3 — the patch is version-specific
4. Check Windows on ARM compatibility — ensure all Visual C++ runtimes are installed

---

## Frequently Asked Questions

### Do I need a Ross-Tech interface?

The patcher bypasses the interface validation check. You can launch VCDS without any connected interface. However, to actually communicate with a vehicle, you'll need a compatible cable or interface. The patcher does not provide diagnostic functionality — it only removes the software lock.

### Is this the same as VCDSLoader v9.1?

No. VCDSLoader v9.1 is a closed-source x86 binary that patches 5 specific data locations in the x86 build of VCDS. It works by replacing license data blocks with "valid" values. Our ARM64 approach is fundamentally different: we patch the validation function code to always return success, which works regardless of the data values.

### Will this work with future VCDS updates?

Maybe. If Ross-Tech recompiles VCDS without changing the validation function's structure, the patch should continue to work as long as the function's offset remains the same. If the binary layout changes significantly, you'll need to:
1. Re-analyze the new binary in Ghidra
2. Find the validation function (look for "Interface Adapter Not Initialized" string references)
3. Calculate the new file offset
4. Update the file offset in `vcds_loader.py`'s `TARGET_RVA` constant

### Can I use this on x86/x64 Windows?

No. The patch targets the ARM64 (`AArch64`) instruction set. x86/x64 CPUs use different opcodes. For x86 VCDS, use the original VCDSLoader v9.1.

### Does this modify the Windows registry or system files?

No. The patcher only writes a new patched binary file. It does not modify the original binary, the Windows registry, or any system files. One small backup file (`<output>.orig.bin`) is created containing the original 8 bytes that were overwritten.

### Is this tool legal?

This tool is distributed for educational and research purposes. VCDS is commercial software by Ross-Tech. You must own a valid license. Consult the [license and disclaimer](README.md#license--disclaimer) in the main README.
