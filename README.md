# ARM64 VCDSLoader

Native ARM64 VCDS loader/patcher for **Snapdragon X Windows on ARM**.

Patches the ARM64 VCDS 26.3 binary to bypass license validation, enabling native execution without x86 emulation.

## Quick Start

```bash
python vcds_loader.py          # Patch the ARM64 VCDS binary
python vcds_loader.py -n       # Dry run (see what changes)
```

## Documentation

| Document | Description |
|----------|-------------|
| **[docs/README.md](docs/README.md)** | Full project overview — background, approach, structure |
| **[docs/USAGE.md](docs/USAGE.md)** | User guide — prerequisites, step-by-step, troubleshooting |
| **[docs/TECHNICAL.md](docs/TECHNICAL.md)** | Technical deep dive — x86 loader internals, ARM64 code-patching, Ghidra methodology |

## How It Works

The ARM64 VCDS binary calls a validation function (`FUN_140076ff0`) that checks for an approved interface. This patcher replaces the function's prologue with `MOV X0, #0; RET` — making it always return success. All license checks are bypassed at the source.

See [docs/TECHNICAL.md](docs/TECHNICAL.md) for the full reverse-engineering breakdown.

## Status

- ✅ VCDS 26.3 ARM64 binary analyzed (Ghidra 11.2.1 + JDK 21)
- ✅ Validation function identified: `FUN_140076ff0` at file offset `0x763F0`
- ✅ Patch verified: `MOV X0,#0; RET` replaces function prologue
- ✅ Patcher script stable and idempotent (vcds_loader.py)
- 📁 Full documentation in `docs/`

## License & Disclaimer

For educational and research purposes only. VCDS is a registered trademark of Ross-Tech, LLC. Users must own a valid license.

## Drivers

**FTDI ARM64 VCP driver** (for legacy HEX-USB, Micro-CAN, KII-USB, KEY-USB, and FTDI-based clones):

- 📦 `drivers/CDM-v2.12.36.20-for-ARM64-WHQL-Certified.zip`
- See **[drivers/README.md](drivers/README.md)** for installation and cable compatibility

**HEX-V2 and HEX-NET** users: no drivers needed! HEX-V2 uses HID (plug & play on ARM64), HEX-NET uses WiFi.

## Status: VERIFIED WORKING on Snapdragon X (2026-07-06)

ARM64 VCDS 26.3 launches successfully after patch. License bypass at FUN_140076ff0 confirmed.
