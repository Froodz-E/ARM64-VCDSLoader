# ARM64 VCDSLoader

Native ARM64 VCDS loader/patcher for **Snapdragon X Windows on ARM**.

✅ Patched ARM64 VCDS 26.3 — launches natively, no emulation, no loader needed.

## Download & Use

### 1. Get the Patched VCDS
Download **[VCDS ARM64 Patched.exe](release/VCDS%20ARM64%20Patched.exe)** from the `release/` folder. This is VCDS 26.3 natively compiled for ARM64 with the license validation bypassed. Drop it into your VCDS installation folder and run it.

### 2. Install the FTDI ARM64 VCP Driver (for USB cables)
If your cable connects via USB (HEX-USB, Micro-CAN, KII-USB, clones), download:
- 📦 **[CDM-v2.12.36.20-for-ARM64-WHQL-Certified.zip](drivers/CDM-v2.12.36.20-for-ARM64-WHQL-Certified.zip)**

Extract and install via Device Manager → "Have Disk" → select `FTDIBUS.inf` then `FTDIPORT.inf`.

> **HEX-V2 or HEX-NET?** No driver needed — HEX-V2 is HID (plug & play), HEX-NET uses WiFi.

### 3. Run
Launch `VCDS ARM64 Patched.exe`. Connect cable, select COM port, done.

## How It Works

The ARM64 VCDS calls a validation function (`FUN_140076ff0`) that checks for an approved interface. We replaced its prologue with `MOV X0, #0; RET` — always returns success. License checks skipped at the source.

See **[docs/TECHNICAL.md](docs/TECHNICAL.md)** for the full Ghidra reverse-engineering breakdown.

## Status

| Item | Status |
|------|:---:|
| ARM64 VCDS 26.3 analysis | ✅ Ghidra 11.2.1 |
| Validation function found | ✅ `FUN_140076ff0` |
| Patch applied | ✅ `MOV X0,#0; RET` at file 0x763F0 |
| Tested on Snapdragon X | ✅ Working |
| FTDI ARM64 driver | ✅ v2.12.36.20 WHQL |
| HEX-V2 / HEX-NET support | ✅ Plug & play |

## Disclaimer

For educational and research purposes only. VCDS is a registered trademark of Ross-Tech, LLC. Users must own a valid license.
