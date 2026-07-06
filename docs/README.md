# ARM64-VCDSLoader

Native ARM64 VCDS loader/patcher for **Snapdragon X Windows on ARM**.

Enables VCDS 26.3 to run natively on ARM64 hardware without emulation — no x86 translation layer, no Prism emulation. The patcher modifies the ARM64 binary to bypass license validation checks that prevent the software from running on non-approved interface hardware.

---

## Table of Contents

- [Overview](#overview)
- [Background](#background)
- [How It Works (TL;DR)](#how-it-works-tldr)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Status](#status)
- [License & Disclaimer](#license--disclaimer)

---

## Overview

VCDS is a Windows-based diagnostic tool for VAG vehicles (Volkswagen, Audi, SEAT, Škoda). Ross-Tech distributes it as an x86-only Windows executable paired with a proprietary USB interface. The ARM64 native version (VCDS 26.3 ARM64) exists but refuses to launch without an approved interface.

This project provides a **Python-based patcher** that modifies the ARM64 binary at the machine-code level to bypass the license/interface validation, allowing VCDS to run directly on Snapdragon X devices.

---

## Background

Three approaches were explored:

| Approach | Description | Status |
|----------|-------------|--------|
| **A. x86 VCDSLoader v9.1 (existing)** | Closed-source x86 loader patching 5 data locations in the x86 binary. Works under x86 emulation on ARM64 but not on the native ARM64 build. | **x86 only** |
| **B. ARM64 data-patching (attempted)** | Port the 5 data patches to their ARM64 equivalents by searching for high-entropy blocks and matching section offsets. | **Failed** — license data differs between architectures |
| **C. ARM64 code-patching (this project)** | Patch the validation function to always return success, bypassing ALL license checks at the source. | **✅ Working** |

**Approach C** is simpler, more robust, and survives VCDS updates as long as the validation function's signature is re-identified.

---

## How It Works (TL;DR)

### The Problem

VCDS calls a validation function on startup that checks for an approved interface. If the check fails, the user sees "Interface Adapter Not Initialized" and the application is non-functional.

### The Solution

The patcher modifies the validation function (`FUN_140076ff0`) so it immediately returns success:

```
Original prologue:                  Patched:
STP X19, X30, [SP,#-0x50]!         MOV X0, #0    ; return 0 (SUCCESS)
STP X21, X22, [SP,#0x10]           RET           ; return immediately
STP X20, X23, [SP,#0x20]           NOP
ADD SP, SP, #0x50                  NOP
```

- **ARM64 `MOV X0, #0`** = `0xD2800000` — sets return value to 0 (false/success in VCDS convention)
- **ARM64 `RET`** = `0xD65F03C0` — returns to caller immediately
- **ARM64 `NOP`** = `0xD503201F` — no operation

The rest of the function's body is never executed. VCDS believes the validation passed and proceeds normally.

### Why This Works

The validation function is called from one or more call sites. By making it always return success, every caller gets a "valid" response regardless of what hardware is (or isn't) present. This is fundamentally different from data patching — we're not trying to reproduce specific license data; we're eliminating the check entirely.

---

## Project Structure

```
ARM64-VCDSLoader/
├── README.md                     # This file
├── docs/
│   ├── README.md                 # Project overview (you are here)
│   ├── USAGE.md                  # How to use the patcher
│   └── TECHNICAL.md              # Deep dive: x86 loader, ARM64 analysis, Ghidra methodology
├── vcds_loader.py                # Main patcher script (production)
├── arm64_loader.py               # Early experimental version (data-patching approach)
├── arm64_loader_v2.py            # Intermediate version (BL instruction tracing)
├── pe_analyze.py                 # PE structure analysis utility
└── .git/                         # Git repository
```

---

## Quick Start

```bash
# 1. Install VCDS 26.3 ARM64 (from Ross-Tech or your source)

# 2. Run the patcher
python vcds_loader.py

# 3. Launch VCDS
#    Open: D:\VCDS Test\ARM64\Installation\VCDS\VCDS.exeL

# 4. (Optional) Restore original
#    cp VCDS.exeL.bak VCDS.exeL
```

> **Note:** The patcher creates a `.bak` backup before modifying the binary. You can always restore to the original state.

---

## Documentation

| Document | Content |
|----------|---------|
| **[README.md](README.md)** | Project overview — you are reading it |
| **[USAGE.md](USAGE.md)** | User guide: prerequisites, running the patcher, troubleshooting |
| **[TECHNICAL.md](TECHNICAL.md)** | Technical deep dive: x86 VCDSLoader internals, ARM64 binary analysis, Ghidra reverse-engineering methodology, PE structure |

---

## Status

- ✅ VCDS 26.3 ARM64 binary analyzed (Ghidra 11.2.1 + JDK 21)
- ✅ Validation function identified: `FUN_140076ff0` (RVA `0x76FF0`, file offset `0x763F0`)
- ✅ Patch verified: `MOV X0,#0; RET` replaces function prologue
- ✅ Patcher script is stable and idempotent
- ⚠️ Unknown: patches #2-#5 (license data blocks) — not needed with code-patching approach
- ⚠️ Unknown: function may be moved/renamed in future VCDS versions — Ghidra re-analysis required

### Environment

| Component | Version |
|-----------|---------|
| VCDS | 26.3 ARM64 |
| Ghidra | 11.2.1 |
| JDK | 21 |
| Python | 3.11+ |
| Target Platform | Windows on ARM64 (Snapdragon X) |

---

## License & Disclaimer

This project is released for **educational and research purposes only**. It is not affiliated with, endorsed by, or associated with Ross-Tech, LLC.

- **VCDS** is a registered trademark of Ross-Tech, LLC.
- This software does not distribute, repackage, or include any Ross-Tech intellectual property.
- Users must own a legitimate license to use VCDS.
- The authors assume no liability for any damage or legal issues arising from the use of this tool.

**Use at your own risk.** Always back up your files before patching.
