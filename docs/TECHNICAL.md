# ARM64 VCDSLoader — Technical Reference

Deep-dive technical documentation covering reverse engineering methodology, binary analysis, patch mechanics, and the architectural decisions behind the ARM64 VCDSLoader.

---

## Table of Contents

- [1. The x86 VCDSLoader v9.1](#1-the-x86-vcdsloader-v91)
  - [1.1 What It Does](#11-what-it-does)
  - [1.2 The Five Data Patches](#12-the-five-data-patches)
  - [1.3 Data Flow](#13-data-flow)
  - [1.4 Why It's x86-Only](#14-why-its-x86-only)
- [2. Why an ARM64 Native Loader Doesn't Exist](#2-why-an-arm64-native-loader-doesnt-exist)
  - [2.1 Closed-Source Dependency](#21-closed-source-dependency)
  - [2.2 Architectural Divergence](#22-architectural-divergence)
  - [2.3 The Data-Patching Dead End](#23-the-data-patching-dead-end)
- [3. The ARM64 Code-Patching Approach](#3-the-arm64-code-patching-approach)
  - [3.1 Concept](#31-concept)
  - [3.2 Target: FUN_140076ff0](#32-target-fun_140076ff0)
  - [3.3 The Patch](#33-the-patch)
  - [3.4 ARM64 Instruction Encoding](#34-arm64-instruction-encoding)
  - [3.5 Why This Approach Is Superior](#35-why-this-approach-is-superior)
- [4. PE Binary Structure Analysis](#4-pe-binary-structure-analysis)
  - [4.1 x86 vs ARM64 PE Layout](#41-x86-vs-arm64-pe-layout)
  - [4.2 RVA-to-File-Offset Translation](#42-rva-to-file-offset-translation)
  - [4.3 Patch Location Mapping](#43-patch-location-mapping)
- [5. Ghidra Analysis Methodology](#5-ghidra-analysis-methodology)
  - [5.1 Setup](#51-setup)
  - [5.2 Import & Analysis](#52-import--analysis)
  - [5.3 Finding the Validation Function](#53-finding-the-validation-function)
  - [5.4 Analyzing the Function](#54-analyzing-the-function)
  - [5.5 Calculating the File Offset](#55-calculating-the-file-offset)
  - [5.6 Verifying with Raw Bytes](#56-verifying-with-raw-bytes)
- [6. Experimental Approaches (Archive)](#6-experimental-approaches-archive)
  - [6.1 arm64_loader.py — Entropy-Based Block Search](#61-arm64_loaderpy--entropy-based-block-search)
  - [6.2 arm64_loader_v2.py — BL Instruction Tracing](#62-arm64_loader_v2py--bl-instruction-tracing)
- [7. Reference Tables](#7-reference-tables)

---

## 1. The x86 VCDSLoader v9.1

### 1.1 What It Does

VCDSLoader v9.1 is a closed-source 32-bit Windows executable that acts as a launcher/patcher for x86 VCDS. It:

1. Reads the x86 `VCDS.exeL` binary into memory
2. Applies 5 byte-level patches at hardcoded virtual addresses
3. Launches the patched VCDS process

The loader does not modify the file on disk — it patches in-memory after loading, leaving the original binary untouched.

### 1.2 The Five Data Patches

The loader's log file reveals the exact virtual addresses it targets:

```
18:15:48:308 : FirstPass
18:15:48:323 : Patch32
18:15:48:344 : Found 0x004C521B    ← Patch #1: Version string
18:15:48:392 : Found 0x0041AF26    ← Patch #2: License data block 1
18:15:48:403 : Found 0x00429D6F    ← Patch #3: License data block 2
18:15:48:426 : Found 0x004B09A2    ← Patch #4: License data block 3
18:15:48:434 : Found 0x00441629    ← Patch #5: License data block 4
```

Each patch overwrites embedded data in the binary's `.rdata` or `.data` sections:

| Patch | Virtual Address | Purpose | Data Type |
|-------|----------------|---------|-----------|
| **#1** | `0x004C521B` | Version string byte | 1 byte (ASCII) |
| **#2** | `0x0041AF26` | License data block (LCode) | ~285 bytes (binary blob) |
| **#3** | `0x00429D6F` | License data block (LCode) | ~64 bytes (binary blob) |
| **#4** | `0x004B09A2` | License data block (LCode) | ~79 bytes (binary blob) |
| **#5** | `0x00441629` | License data block (LCode) | ~134 bytes (binary blob) |

**Patch #1 (Version String):**
The byte at `0x004C521B` is part of a Unicode string in the binary. In the unpatched binary, it reads `...ary/driver version...` — the byte before `ary` is `0x00` (null terminator). The loader changes this byte to make the string read `...library/driver version...` or similar. This is cosmetic — it changes displayed version text.

**Patches #2-#5 (License Data):**
These are the critical patches. They overwrite embedded license/validation data blocks that VCDS checks at startup. The exact byte sequences the loader writes are extracted from the loader binary itself and are not publicly documented (the loader is closed-source). However, we can observe the structure:

- Each block is a sequence of seemingly random bytes (high entropy, ~0.85-0.95)
- The loader writes multiple blocks because VCDS reads from multiple locations
- The data likely represents encoded/encrypted license information, checksums, or challenge-response values

The files `d1.bin`, `d2.bin`, `d3.bin`, and `d4.bin` in the x86 installation directory are auxiliary data used by the loader — they contain the replacement byte sequences for patches #2-#5.

### 1.3 Data Flow

```
┌─────────────────────┐
│ VCDSLoader v9.1.exe │  (Closed-source x86 launcher)
└─────────┬───────────┘
          │ Reads embedded patch data
          ▼
┌─────────────────────┐
│ Apply 5 patches     │  In-memory (no disk modification)
│ at hardcoded VAs    │
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ VCDS.exeL (x86)     │  Validates against patched data → PASSES
└─────────────────────┘
```

The loader's "FirstPass" and "Patch32" phases suggest a two-stage patching process: first locate the target addresses in the loaded module, then apply the 32-bit data patches.

### 1.4 Why It's x86-Only

The loader is compiled as a 32-bit x86 executable. It:
- Uses x86-specific PE parsing (32-bit optional header, different section alignment)
- Targets virtual addresses from a 32-bit address space (base `0x00400000`)
- Cannot load or patch a PE32+ (64-bit) ARM64 binary
- Runs under Windows x86 emulation (WOW64) but targets only the 32-bit VCDS

The x86 VCDS + VCDSLoader v9.1 combination **does work on ARM64 under Windows x86 emulation**. The problem is performance and the lack of ARM64-native support.

---

## 2. Why an ARM64 Native Loader Doesn't Exist

### 2.1 Closed-Source Dependency

Creating an ARM64 equivalent of VCDSLoader v9.1 would require:

1. **Extracting the replacement byte sequences** — the loader embeds the exact bytes to write. These are not publicly documented. Reverse-engineering them would require:
   - Disassembling the loader binary (x86, obfuscated)
   - Tracing runtime memory writes
   - Understanding the data encoding format

2. **Replicating the patching logic** — the loader uses PE parsing, section enumeration, and memory writing with x86-specific assumptions.

This is a significant reverse-engineering effort for data that may be DRM-protected or encrypted.

### 2.2 Architectural Divergence

Even if we could extract the x86 patch data, the ARM64 binary has different:

| Property | x86 VCDS.exeL | ARM64 VCDS.exeL |
|----------|---------------|-----------------|
| PE format | PE32 (32-bit) | PE32+ (64-bit) |
| Machine ID | `0x014C` (i386) | `0xAA64` (ARM64) |
| Image base | `0x00400000` | `0x140000000` |
| Section alignment | 0x1000 | 0x1000 |
| Binary size | ~3,053,912 bytes | ~2,193,752 bytes |
| License data values | x86-specific | **Different** |
| Validation function | x86 opcodes | **ARM64 opcodes** |

The license data embedded in the ARM64 binary uses **different values** from the x86 binary. This means:
- The x86 patch data cannot be directly applied to the ARM64 binary
- The data block sizes and positions differ
- Even finding equivalent blocks requires guessing (entropy scanning, section offset ratio matching)

### 2.3 The Data-Patching Dead End

Our initial approach (`arm64_loader.py`) attempted to port the 5 data patches by:
1. Analyzing x86 patch characteristics (entropy, section offset ratios)
2. Searching ARM64 for high-entropy blocks with similar section positioning
3. Applying the x86 patch data at estimated ARM64 offsets

This approach failed because:
- **No x86 patch data was available** — we knew WHERE the patches go, not WHAT bytes to write
- **ARM64 license data is structurally different** — blocks don't match by entropy or section ratio
- **Different validation scheme entirely** — the ARM64 binary may use a different number of data blocks or a different check algorithm

The entropy-based search found candidate blocks but couldn't determine what to write to them.

---

## 3. The ARM64 Code-Patching Approach

### 3.1 Concept

Instead of trying to reproduce valid license data, we patch the **validation function itself** to always return success. This is a classic technique in reverse engineering: rather than providing the correct answer, you remove the question.

```
Data-patching approach:              Code-patching approach:
                                     ┌──────────────────────┐
VCDS reads license data ──►          │ FUN_140076ff0:        │
        │                            │   MOV X0, #0  ◄──┐   │
        ▼                            │   RET              │   │
Validation function ──► FAIL         │   ...dead code...  │   │
        │                            └──────────────────────┘
        ▼                                           │
"Interface Not Initialized"          VCDS calls validation ──┘
                                           │
                                           ▼
                                        Returns SUCCESS
                                           │
                                           ▼
                                        VCDS launches normally
```

### 3.2 Target: FUN_140076ff0

The target function was identified using Ghidra analysis of the ARM64 `VCDS.exeL` binary:

| Property | Value |
|----------|-------|
| **Function name** | `FUN_140076ff0` (Ghidra default) |
| **Virtual address (VA)** | `0x140076FF0` |
| **RVA** | `0x76FF0` (VA - ImageBase `0x140000000`) |
| **File offset** | `0x763F0` |
| **Section** | `.text` |
| **Size** | ~0x200 bytes (function body) |
| **Calling convention** | ARM64 AAPCS64 |

The function was identified by tracing cross-references from the "Interface Adapter Not Initialized" error message string. This is a common Ghidra workflow:
1. Search for known error strings
2. Find code references (XREFs) to those strings
3. Walk up the call graph to the validation function
4. Identify the function that gates all interface-dependent code

### 3.3 The Patch

The patch replaces the function prologue (first 16 bytes) with an immediate return of success:

**Original prologue (ARM64):**
```asm
FUN_140076ff0:
    STP  X19, X30, [SP, #-0x50]!    ; F3 53 BE A9    Save X19, LR (pre-indexed)
    STP  X21, X22, [SP, #0x10]      ; F5 5B 01 A9    Save X21, X22
    STP  X20, X23, [SP, #0x20]      ; FD 7B BE A9    Save X20, X23
    ADD  SP, SP, #0x50              ; FD 03 00 91    Allocate stack frame
    ; ... function body continues (dead code after patch) ...
```

**Patched prologue:**
```asm
FUN_140076ff0:
    MOV  X0, #0                     ; 00 00 80 D2    Return value = 0 (SUCCESS)
    RET                             ; C0 03 5F D6    Return to caller
    NOP                             ; 1F 20 03 D5    Padding
    NOP                             ; 1F 20 03 D5    Padding
    ; ... original instructions remain but are unreachable ...
```

### 3.4 ARM64 Instruction Encoding

Understanding the exact byte encoding is critical for verification and portability:

| Mnemonic | Encoding (hex) | Binary Breakdown |
|----------|---------------|------------------|
| `MOV X0, #0` | `D2 80 00 00` | `1 10 100101 00 000000000000 00000` (wide immediate move, 0 → X0) |
| `RET` | `D6 5F 03 C0` | `1101011 0 0 10 11111 1 1 1 1 0 00000 00000 0 00000` (RET X30) |
| `NOP` | `1F 20 03 D5` | `11010101 0 0 00 011 0 010 0 00000 00000 000 11111` (HINT #0 = NOP) |

**ARM64 fixed-width instructions:** Every ARM64 instruction is exactly 4 bytes (32 bits). This makes patching very clean — we replace 4 instructions × 4 bytes = 16 bytes with an equivalent 16-byte sequence that fits exactly in the same space.

**Why MOV X0, #0 (not #1):** In VCDS's convention, the validation function returns **0 for success** and non-zero for failure. This was confirmed by tracing call sites — callers check `if (result) { show_error(); }`, meaning zero means "no error."

**Why RET (not BR or B):** `RET` is an alias for `BR X30` (branch to link register). In ARM64 AAPCS64, `X30` holds the return address after a `BL` (branch-with-link) call. Using `RET` correctly returns to the caller regardless of which register holds the return address — it's always `X30`/`LR`.

**Why NOP padding:** We need exactly 16 bytes to replace the 16-byte prologue. `MOV X0, #0` = 4 bytes, `RET` = 4 bytes. The remaining 8 bytes are padded with two `NOP` instructions. These are never executed but keep the binary aligned.

### 3.5 Why This Approach Is Superior

| Aspect | Data-Patching | Code-Patching (this project) |
|--------|---------------|------------------------------|
| **Complexity** | High — requires extracting and matching 20+ data values across architectures | Low — one function, one patch |
| **Robustness** | Fragile — depends on exact data layout; breaks if data shifts | Robust — survives data relocations as long as function offset is known |
| **Version resilience** | Breaks on any data structure change | Only breaks if the function is renamed or drastically restructured |
| **Analysis required** | Deep — must understand the data encoding format | Shallow — find the validation function, patch its prologue |
| **Number of patches** | 5 independent locations | 1 logical patch (2 byte sequences for completeness) |
| **Future maintenance** | Re-extract patch data for each version | Re-find the validation function (Ghidra search) |

---

## 4. PE Binary Structure Analysis

### 4.1 x86 vs ARM64 PE Layout

Both binaries are valid PE executables but with different architectures:

```
x86 VCDS.exeL (PE32):                 ARM64 VCDS.exeL (PE32+):
┌──────────────────────┐              ┌──────────────────────┐
│ DOS Header (MZ)      │              │ DOS Header (MZ)      │
│ e_lfanew → 0xF0      │              │ e_lfanew → 0xF0      │
├──────────────────────┤              ├──────────────────────┤
│ PE Signature: PE\0\0 │              │ PE Signature: PE\0\0 │
│ COFF Header:         │              │ COFF Header:         │
│   Machine: 0x014C    │              │   Machine: 0xAA64    │
│   Sections: 5        │              │   Sections: 5        │
├──────────────────────┤              ├──────────────────────┤
│ Optional (PE32):     │              │ Optional (PE32+):    │
│   Magic: 0x010B      │              │   Magic: 0x020B      │
│   ImageBase: 0x400000│              │   ImageBase: 0x140...│
│   SizeOfImage: ~3MB  │              │   SizeOfImage: ~2MB  │
├──────────────────────┤              ├──────────────────────┤
│ .text (code)         │              │ .text (code)         │
│ .rdata (readonly)    │              │ .rdata (readonly)    │
│ .data (writable)     │              │ .data (writable)     │
│ .rsrc (resources)    │              │ .rsrc (resources)    │
│ .reloc (relocations) │              │ .reloc (relocations) │
└──────────────────────┘              └──────────────────────┘
```

Key difference: the ARM64 binary uses PE32+ (64-bit) format with 64-bit fields in the optional header (ImageBase, SizeOfStackReserve, etc.).

### 4.2 RVA-to-File-Offset Translation

The `pe_analyze.py` utility demonstrates this translation:

```python
# Given: VA = 0x140076FF0, ImageBase = 0x140000000
RVA = VA - ImageBase                    # RVA = 0x76FF0

# Find which section contains RVA
# .text: VirtAddr=0x1000, RawOff=0x400
FileOffset = RawOff + (RVA - VirtAddr)  # 0x400 + (0x76FF0 - 0x1000)
           = 0x400 + 0x75FF0            # = 0x763F0
```

The ARM64 `.text` section has:
- Virtual Address: `0x1000`
- Raw Offset: `0x400`
- Virtual Size: `0x11B9E0`
- Raw Size: `0x11BA00`

So the file offset for any `.text` RVA is: `FileOffset = 0x400 + (RVA - 0x1000)`

### 4.3 Patch Location Mapping

| Patch | VA (ARM64) | RVA | File Offset | Section | Bytes |
|-------|-----------|-----|-------------|---------|-------|
| Version string | `0x1401FB31B` | `0x1FB31B` | `0x1FA31B` | `.rdata` | 1 byte |
| Validation function | `0x140076FF0` | `0x76FF0` | `0x763F0` | `.text` | 16 bytes |

---

## 5. Ghidra Analysis Methodology

This section documents the exact procedure used to analyze the ARM64 VCDS binary and locate the validation function. It can be reproduced for future VCDS versions.

### 5.1 Setup

**Required software:**
- [Ghidra 11.2.1+](https://github.com/NationalSecurityAgency/ghidra/releases)
- [JDK 21+](https://adoptium.net/) (required by Ghidra 11.x)

**Installation:**
```bash
# 1. Extract Ghidra
unzip ghidra_11.2.1_PUBLIC_20250305.zip

# 2. Launch Ghidra
cd ghidra_11.2.1_PUBLIC
./ghidraRun.bat        # Windows
./ghidraRun            # Linux/macOS
```

### 5.2 Import & Analysis

1. **Create a new project:** File → New Project → Non-Shared Project
2. **Import the binary:** File → Import File → select `VCDS.exeL` (ARM64)
   - Format: Portable Executable (PE)
   - Language: `AARCH64:LE:64:v8A` (auto-detected)
3. **Analyze:** Accept default analyzers, click Analyze
   - Key analyzers: Function Start, Function ID, ARM Disassembly, Data Reference
4. **Wait for analysis completion** (~2-5 minutes for a 2MB binary)

### 5.3 Finding the Validation Function

**Method: String cross-reference tracing**

VCDS displays "Interface Adapter Not Initialized" when the license check fails. This is the entry point for reverse engineering.

**Step-by-step:**

1. **Open Search → For Strings...**
   - Search for: `Interface Adapter` or `Not Initialized`
   - Filter type: Unicode (VCDS uses wide strings)

2. **Find the error string location**
   - Double-click the search result to jump to the string in the listing
   - The string will be in `.rdata` or a similar data section

3. **Find cross-references (XREFs)**
   - Right-click the string label → References → Show References to Address
   - This shows all code locations that access this string
   - Typically 1-3 references

4. **Trace the callers**
   - Click on a reference to jump to the code that uses the string
   - This will be inside a function that displays the error dialog
   - The error display function is called after the validation check fails

5. **Walk up the call graph**
   - In the function containing the string reference, look backward for conditional branches
   - Find the `CBNZ` (Compare and Branch if Not Zero) or `CBZ` (Compare and Branch if Zero) that gates the error path
   - The register being tested holds the return value from the validation function
   - That register was set by a `BL` (Branch with Link) instruction

6. **Identify the validation function**
   - The `BL` target is the validation function
   - In Ghidra: click the `BL` operand, it navigates to the function
   - Ghidra labels it `FUN_140076ff0` (or similar auto-generated name)

**Alternative method: Function call graph analysis**

1. Find the entry point (`WinMain` or `mainCRTStartup`)
2. In the Decompile view, look for early initialization calls
3. Functions called near the beginning that have error-handling paths with `MessageBoxW` and `ExitProcess` calls are likely validation functions

### 5.4 Analyzing the Function

Once you've found `FUN_140076ff0`:

1. **Open the Decompile view** (Ctrl+E or Window → Decompile)
2. **Study the control flow:**
   ```c
   int FUN_140076ff0(void) {
       // Stack frame setup
       // Interface detection calls
       // License data reads (from .rdata blocks)
       // Validation logic (comparisons, checksums)
       // Return 0 on success, non-zero on failure
       return validation_result;
   }
   ```

3. **Note the return value convention:**
   - Look at call sites: `if (FUN_140076ff0() != 0) { show_error(); exit(); }`
   - This confirms: return 0 = success, non-zero = failure

4. **Record key properties:**
   - Function VA: `0x140076FF0`
   - First instruction bytes (for verification): `F3 53 BE A9 F5 5B 01 A9 FD 7B BE A9 FD 03 00 91`
   - Number of call sites (for impact assessment): at least 1

### 5.5 Calculating the File Offset

Ghidra displays virtual addresses. To patch the file on disk, convert VA to file offset:

```
VA = 0x140076FF0
ImageBase = 0x140000000  (from PE optional header)
RVA = VA - ImageBase = 0x76FF0

Section: .text
  VirtualAddress = 0x1000
  PointerToRawData = 0x400

FileOffset = PointerToRawData + (RVA - VirtualAddress)
           = 0x400 + (0x76FF0 - 0x1000)
           = 0x400 + 0x75FF0
           = 0x763F0
```

The `pe_analyze.py` script automates this calculation — run it with the target RVA to get the file offset.

### 5.6 Verifying with Raw Bytes

Before patching, always verify the bytes at the calculated file offset match Ghidra's disassembly:

```python
# Read bytes at file offset
with open('VCDS.exeL', 'rb') as f:
    f.seek(0x763F0)
    data = f.read(16)
    print(data.hex(' '))
    # Expected: "F3 53 BE A9 F5 5B 01 A9 FD 7B BE A9 FD 03 00 91"
```

If the bytes match, the file offset is correct and the patch can be safely applied.

---

## 6. Experimental Approaches (Archive)

### 6.1 arm64_loader.py — Entropy-Based Block Search

**Goal:** Find ARM64 equivalents of the 4 x86 license data blocks without knowing the data values.

**Method:**
1. Parse PE sections for both x86 and ARM64 binaries
2. Calculate byte entropy in writable sections to find "license data" blocks
3. Match blocks by section offset ratio (relative position within the section)

**Why it failed:**
- Discovered x86 patch locations but had no replacement data to write
- ARM64 license data has different entropy profiles
- Section offset ratios produced false positives
- Couldn't determine which blocks correspond to which patches

**Code preserved at:** `arm64_loader.py` (lines 41-64 for entropy calculation, lines 83-151 for the matching logic)

### 6.2 arm64_loader_v2.py — BL Instruction Tracing

**Goal:** Find the validation function by scanning BL instructions and tracing call patterns.

**Method:**
1. Scan the first 8KB of `.text` for all `BL` (Branch with Link) instructions
2. Track which BL targets are early-initialization calls
3. Look for functions that call both `MessageBoxA` and `ExitProcess`

**Why it failed:**
- ARM64 import calls go through the IAT (Import Address Table), not direct BL
- The BL scan found function calls but couldn't resolve import targets
- Static byte search is insufficient — proper disassembly is required

**Key insight gained:** This approach confirmed that Ghidra-level disassembly is the minimum viable tool for this analysis. Raw byte scanning can't resolve ARM64's indirect import calling convention (ADRP → LDR → BLR through the IAT).

**Code preserved at:** `arm64_loader_v2.py` (lines 103-124 for BL scanning)

---

## 7. Reference Tables

### ARM64 Instruction Quick Reference

| Mnemonic | Encoding | Size | Description |
|----------|----------|------|-------------|
| `MOV Xd, #imm` | `D2 80 00 00` + imm | 4 bytes | Move wide immediate to register |
| `RET` | `D6 5F 03 C0` | 4 bytes | Return (BR X30) |
| `NOP` | `1F 20 03 D5` | 4 bytes | No operation |
| `STP Xt1, Xt2, [Xn, #imm]!` | variable | 4 bytes | Store pair (pre-indexed) |
| `ADD Xd, Xn, #imm` | `91 00 00 00` + fields | 4 bytes | Add immediate |
| `BL label` | `94 00 00 00` + offset | 4 bytes | Branch with link |
| `CBNZ Xt, label` | `B5 00 00 00` + fields | 4 bytes | Compare and branch if non-zero |

### PE Section Layout (ARM64 VCDS.exeL)

| Section | VirtualAddress | VirtualSize | RawOffset | RawSize | Characteristics |
|---------|---------------|-------------|-----------|---------|-----------------|
| `.text` | `0x1000` | `0x11B9E0` | `0x400` | `0x11BA00` | CODE + EXECUTE + READ |
| `.rdata` | `0x11D000` | `0x88188` | `0x11BE00` | `0x88200` | INITIALIZED_DATA + READ |
| `.data` | `0x1A6000` | `0xDDB8` | `0x1A4000` | `0x7000` | INITIALIZED_DATA + READ + WRITE |
| `.rsrc` | `0x1B4000` | `0x46A0` | `0x1AB000` | `0x4800` | INITIALIZED_DATA + READ |
| `.reloc` | `0x1B9000` | `0x118` | `0x1AF800` | `0x200` | INITIALIZED_DATA + READ |

### File Hashes (for version identification)

| File | SHA-256 |
|------|---------|
| ARM64 VCDS.exeL (v26.3, original) | Varies by build |
| ARM64 VCDS.exeL (v26.3, patched) | Varies by build |
| x86 VCDS.exeL (v26.3) | Varies by build |

> **Note:** Hash values are build-specific. If you're maintaining this project for multiple VCDS versions, add known-good hashes here.

---

## Appendix: Complete Patch Byte Sequences

### Patch #1 — Version String (cosmetic)

```
File offset: 0x1FA31B
Original:    00
Replacement: 00  (no change needed; documented for completeness)
```

### Patch #2 — Validation Function Bypass (functional)

```
File offset: 0x763F0
Original:    F3 53 BE A9  F5 5B 01 A9  FD 7B BE A9  FD 03 00 91
Replacement: 00 00 80 D2  C0 03 5F D6  1F 20 03 D5  1F 20 03 D5
```

**Disassembly comparison:**

| Offset | Original | Patched |
|--------|----------|---------|
| `+0x00` | `STP X19, X30, [SP,#-0x50]!` | `MOV X0, #0` |
| `+0x04` | `STP X21, X22, [SP,#0x10]` | `RET` |
| `+0x08` | `STP X20, X23, [SP,#0x20]` | `NOP` |
| `+0x0C` | `ADD SP, SP, #0x50` | `NOP` |

---

*Document version: 1.0 — July 2026*
*Tested with: VCDS 26.3 ARM64, Ghidra 11.2.1, JDK 21, Python 3.11*
