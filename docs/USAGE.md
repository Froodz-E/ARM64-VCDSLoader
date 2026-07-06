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
cd "D:\VCDS Test\arm64-loader"

# 2. Edit vcds_loader.py: set VCDS_PATH to your ARM64 binary location
#    Default: D:\VCDS Test\ARM64\Installation\VCDS\VCDS.exeL

# 3. Dry run first
python vcds_loader.py --dry-run

# 4. Apply the patch
python vcds_loader.py

# 5. Launch VCDS from the ARM64 installation folder
```

---

## Step-by-Step Guide

### 1. Install VCDS 26.3 ARM64

Download and install the ARM64 build of VCDS 26.3. The installer typically places the files in:

```
C:\Ross-Tech\VCDS\          (default)
D:\VCDS Test\ARM64\         (custom)
```

The key binary is `VCDS.exeL` — this is the main VCDS executable. On ARM64, it's a PE32+ binary compiled for `AArch64`.

> **Verification:** Running `pe_analyze.py` on the binary should report `Machine: 0xAA64 (ARM64)`. If it reports `0x8664` (x64) or `0x14C` (x86), you have the wrong build.

### 2. Locate the Binary

Note the full path to your ARM64 `VCDS.exeL`:

```powershell
# Example
Get-ChildItem -Path "C:\Ross-Tech" -Recurse -Filter "VCDS.exeL"
```

If you installed VCDS in a different location, update the `VCDS_PATH` variable in `vcds_loader.py`:

```python
VCDS_PATH = r"C:\Ross-Tech\VCDS\VCDS.exeL"
```

### 3. Configure the Patcher

Open `vcds_loader.py` and verify:

```python
VCDS_PATH = r"D:\VCDS Test\ARM64\Installation\VCDS\VCDS.exeL"
```

Change the path if your VCDS installation differs.

### 4. Dry Run (Recommended)

Always do a dry run first to verify the binary is correct and patches will apply cleanly:

```bash
python vcds_loader.py --dry-run
```

Expected output:

```
============================================================
  ARM64 VCDSLoader v0.1
  Target: VCDS 26.3 ARM64 (Snapdragon X)
============================================================

[DRY RUN MODE] No changes will be written.

[+] Valid ARM64 PE binary (2,193,752 bytes)

--- Version string (cosmetic) ---
  Description: Unicode string 'ary/driver version' - cosmetic patch
  File offset: 0x001FA31B
  Size: 1 bytes
  Original:  00
  [DRY RUN] Would replace with: 00

--- License validation function bypass ---
  Description: FUN_140076ff0: Replace function prologue with MOV X0,#0; RET; NOP; NOP
  File offset: 0x000763F0
  Size: 16 bytes
  Original:  F3 53 BE A9 F5 5B 01 A9 FD 7B BE A9 FD 03 00 91
  [DRY RUN] Would replace with: 00 00 80 D2 C0 03 5F D6 1F 20 03 D5 1F 20 03 D5

[DRY RUN] No changes written. Remove -n/--dry-run to apply.
```

### 5. Apply the Patch

When the dry run looks correct, apply the patch:

```bash
python vcds_loader.py
```

The script will:
1. Verify the binary is a valid ARM64 PE
2. Create a backup at `VCDS.exeL.bak` (only on first run)
3. Apply both patches in-place
4. Confirm success

Expected output:

```
============================================================
  ARM64 VCDSLoader v0.1
  Target: VCDS 26.3 ARM64 (Snapdragon X)
============================================================

[+] Valid ARM64 PE binary (2,193,752 bytes)
[+] Backup created: D:\VCDS Test\ARM64\Installation\VCDS\VCDS.exeL.bak

--- Version string (cosmetic) ---
  ...
  PATCHED: 00

--- License validation function bypass ---
  ...
  PATCHED: 00 00 80 D2 C0 03 5F D6 1F 20 03 D5 1F 20 03 D5

============================================================
[SUCCESS] Patched binary written: D:\VCDS Test\ARM64\Installation\VCDS\VCDS.exeL
  Backup: D:\VCDS Test\ARM64\Installation\VCDS\VCDS.exeL.bak

  To test: Launch VCDS.exeL from the ARM64 test folder.
  To restore: cp VCDS.exeL.bak VCDS.exeL
============================================================
```

### 6. Launch VCDS

Navigate to the VCDS installation directory and run `VCDS.exeL`:

```bash
# From terminal:
cd "D:\VCDS Test\ARM64\Installation\VCDS"
start VCDS.exeL
```

Or double-click `VCDS.exeL` in File Explorer.

VCDS should launch without the "Interface Adapter Not Initialized" error. The application will start normally and display the main diagnostic screen.

---

## Command-Line Options

| Flag | Alias | Description |
|------|-------|-------------|
| `--dry-run` | `-n` | Simulate patches without writing. Shows what WOULD change. |
| `--force` | `-f` | Re-apply patches even if a `.bak` already exists. |

### Examples

```bash
# Dry run: see what changes would be made
python vcds_loader.py --dry-run
python vcds_loader.py -n

# Force re-patch (if already patched once)
python vcds_loader.py -f

# Combine (dry run with force flag — useful for verification)
python vcds_loader.py -n -f
```

---

## Restoring the Original Binary

The patcher creates `VCDS.exeL.bak` on the first run. To restore:

```bash
# Option 1: Copy backup over patched binary
cp "D:\VCDS Test\ARM64\Installation\VCDS\VCDS.exeL.bak" \
   "D:\VCDS Test\ARM64\Installation\VCDS\VCDS.exeL"

# Option 2: Re-install VCDS
```

> **Note:** If you run the patcher again without `--force`, it will refuse to patch (detects existing `.bak` backup). This is intentional — a safety mechanism to prevent accidental double-patching.

---

## Troubleshooting

### "Not a valid PE file (missing MZ signature)"

The binary is corrupt or not a PE executable. Re-install VCDS from the original source.

### "Not an ARM64 binary (machine=0x8664)"

You're pointing at the wrong build. VCDS ships an x64 build for Intel/AMD and an ARM64 build for Snapdragon. Ensure you have the ARM64 installer. Check with `pe_analyze.py`.

### "Target not found"

The `VCDS_PATH` in `vcds_loader.py` doesn't point to a valid file. Update it to your actual installation path.

### "Bytes at offset don't match expected!"

The binary's bytes at the patch location differ from what was expected. This can happen if:
- You're using a different VCDS version (not 26.3 ARM64)
- The binary was already patched by another tool
- The binary was modified post-installation

**Solution:** Restore from backup (or reinstall) and try again. If the problem persists, the validation function may have been moved — re-analyze with Ghidra (see [TECHNICAL.md](TECHNICAL.md)).

### "Binary already has a backup"

You've already run the patcher once. Either:
- Restore from backup and re-patch: `cp VCDS.exeL.bak VCDS.exeL` then retry
- Force re-patch: `python vcds_loader.py --force`

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
4. Update the `PATCHES` list in `vcds_loader.py`

### Can I use this on x86/x64 Windows?

No. The patch targets the ARM64 (`AArch64`) instruction set. x86/x64 CPUs use different opcodes. For x86 VCDS, use the original VCDSLoader v9.1.

### Does this modify the Windows registry or system files?

No. The patcher only modifies the `VCDS.exeL` file in the VCDS installation directory. It creates one backup file (`.bak`) in the same folder. No registry changes, no system file modifications.

### Is this tool legal?

This tool is distributed for educational and research purposes. VCDS is commercial software by Ross-Tech. You must own a valid license. Consult the [license and disclaimer](README.md#license--disclaimer) in the main README.
