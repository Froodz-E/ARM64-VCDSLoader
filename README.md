# ARM64 VCDSLoader

**Native ARM64 VCDS 26.3 patcher — compatible with all Windows ARM64 devices, including Snapdragon X.**

[![Status](https://img.shields.io/badge/status-verified_working-success?style=flat-square)](release/VCDS%20ARM64%20Patched.exe)
[![Platform](https://img.shields.io/badge/platform-Windows%20ARM64-blue?style=flat-square)](#)
[![VCDS](https://img.shields.io/badge/VCDS-26.3%20ARM64-orange?style=flat-square)](#)
[![License](https://img.shields.io/badge/license-educational--only-lightgrey?style=flat-square)](#disclaimer)

---

## ⚡ Downloads

| File | Description |
|------|-------------|
| **[VCDS ARM64 Patched.exe](release/VCDS%20ARM64%20Patched.exe)** | VCDS 26.3 pre-patched for ARM64 — drop into your VCDS folder and run. No loader, no emulation. |
| **[CDM-v2.12.36.20-for-ARM64-WHQL-Certified.zip](drivers/CDM-v2.12.36.20-for-ARM64-WHQL-Certified.zip)** | FTDI ARM64 VCP driver with Ross-Tech PID support — required for USB cables. |

---

## 🚀 Quick Start

1. **Drop** `VCDS ARM64 Patched.exe` into your VCDS 26.3 ARM64 installation folder.
2. **Install** the FTDI ARM64 driver via Device Manager → "Have Disk" if using a USB cable.
3. **Launch** — connect cable, select COM port, done.

---

## 🧠 How It Works

VCDS calls a validation function (`FUN_140076ff0`) at startup that checks for an approved interface. This patcher replaces the function's prologue with `MOV X0, #0; RET` — always returns success. License checks bypassed at the machine-code level.

> **Deep dive:** [docs/TECHNICAL.md](docs/TECHNICAL.md) — full Ghidra reverse-engineering breakdown, PE analysis, and ARM64 instruction encoding.

---

## 📂 Documentation

| Document | What's Inside |
|----------|---------------|
| **[docs/README.md](docs/README.md)** | Project overview, background, project structure |
| **[docs/USAGE.md](docs/USAGE.md)** | Step-by-step guide: prerequisites, patching, troubleshooting, FAQ |
| **[docs/TECHNICAL.md](docs/TECHNICAL.md)** | x86 VCDSLoader internals, ARM64 binary analysis, Ghidra methodology, PE structure |
| **[drivers/README.md](drivers/README.md)** | FTDI ARM64 driver installation ("Have Disk" method, architecture verification) |

---

## 🔌 Cable Compatibility

| Cable / Interface | Connection | Driver Required | Status |
|:---|:---|:---|:---:|
| **HEX-USB** | USB (FTDI chip) | FTDI ARM64 VCP driver | ✅ Supported |
| **Micro-CAN** | USB (FTDI chip) | FTDI ARM64 VCP driver | ✅ Supported |
| **KII-USB** | USB (FTDI chip) | FTDI ARM64 VCP driver | ✅ Supported |
| **KEY-USB** | USB (FTDI chip) | FTDI ARM64 VCP driver | ✅ Supported |
| **Clone cables** (FTDI-based) | USB (FTDI chip) | FTDI ARM64 VCP driver | ✅ Likely works |
| **HEX-V2** | USB (HID) | None — built into Windows | ✅ Plug & play |
| **HEX-NET** | WiFi / USB | None | ✅ Supported |
| **HEX-CAN** | USB (proprietary) | ❌ No ARM64 driver | ❌ Unsupported |
| **Generic ELM327** | Bluetooth / USB | N/A | ❌ Not VCDS-compatible |

> **HEX-USB / Micro-CAN / KII-USB / KEY-USB users:** You MUST install the FTDI ARM64 VCP driver. Windows Update will not install the correct ARM64 driver for Ross-Tech's custom PID (`VID_0403&PID_FA24`). See [drivers/README.md](drivers/README.md) for detailed install instructions.

> **HEX-V2 / HEX-NET users:** Download the latest official VCDS release directly from Ross-Tech:  
> 🔗 **[ross-tech.com/vcds/download/current.php](https://www.ross-tech.com/vcds/download/current.php)** — the installer auto-detects ARM64 (since Release 22.3) and installs the native build. HEX-V2 and HEX-NET work out of the box without any driver or patch.

---

## 📊 Status

| Check | Result |
|:------|:------:|
| ARM64 VCDS 26.3 analyzed (Ghidra 11.2.1) | ✅ |
| Validation function identified (`FUN_140076ff0`) | ✅ |
| Patch applied (`MOV X0,#0; RET` at file offset `0x763F0`) | ✅ |
| Tested on ARM64 (Snapdragon X) | ✅ |
| FTDI ARM64 driver (v2.12.36.20 WHQL) | ✅ |
| HEX-V2 / HEX-NET support | ✅ Plug & play |
| Pre-patched binary available | ✅ [Download](release/VCDS%20ARM64%20Patched.exe) |

---

## ⚠️ Disclaimer

For **educational and research purposes only**. VCDS is a registered trademark of Ross-Tech, LLC. This project does not distribute, repackage, or include any Ross-Tech intellectual property. Users must own a valid license. Use at your own risk — always back up your files before patching.
