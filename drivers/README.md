# FTDI ARM64 VCP Drivers for VCDS
# ================================
# Required for: Ross-Tech HEX-USB+CAN, Micro-CAN, KII-USB, KEY-USB, and clones
# NOT required for: Ross-Tech HEX-V2 (HID), HEX-NET (WiFi)

## Driver Package

- **File:** CDM-v2.12.36.20-for-ARM64-WHQL-Certified.zip
- **Version:** 2.12.36.20 (Feb 2025)
- **Source:** https://ftdichip.com/drivers/vcp-drivers/
- **Architecture:** ARM64 native (WHQL certified)
- **Kernel drivers:** ftdibus.sys (bus), ftser2k.sys (serial port) - both ARM64

## Cable Compatibility

| Ross-Tech Cable         | VID:PID     | Driver Needed        | ARM64 Status |
|-------------------------|-------------|----------------------|:---:|
| HEX-V2                  | HID device  | None (Windows inbox) | ✅ Plug & play |
| HEX-NET / HEX-NET2      | WiFi / HID  | None                 | ✅ WiFi native |
| HEX-USB+CAN (legacy)    | 0403:FA24   | FTDI VCP ARM64       | ✅ This driver |
| Micro-CAN (legacy)      | 0403:FA23   | FTDI VCP ARM64       | ✅ This driver |
| KII-USB / KEY-USB       | 0403:FA20   | FTDI VCP ARM64       | ✅ This driver |
| Clone cables (FTDI)     | 0403:6001   | FTDI VCP ARM64       | ✅ This driver |
| Clone cables (CH340)    | 1A86:xxxx   | WCH driver           | ❌ No ARM64 driver |

## Installation (HEX-USB / FTDI-based)

### Method 1: pnputil (CLI)
```powershell
# Extract the ZIP, then:
pnputil /add-driver "ARM64\Release\FTDIBUS.inf" /install
pnputil /add-driver "ARM64\Release\FTDIPORT.inf" /install
pnputil /scan-devices
```

### Method 2: Device Manager (GUI)
1. Open Device Manager → find "Ross-Tech HEX-USB" (yellow bang)
2. Right-click → Update driver → Browse my computer
3. Navigate to extracted `ARM64\Release\` folder
4. Select `FTDIBUS.inf`
5. Repeat for child "USB Serial Port" → select `FTDIPORT.inf`

### Verify
```powershell
Get-PnpDevice | Where-Object { $_.InstanceId -like "*0403*" }
# Should show: USB Serial Converter (OK) + USB Serial Port (COMx) (OK)
```

## HEX-V2 Users
No driver needed! HEX-V2 enumerates as a standard HID device. Windows on ARM64 has native HID drivers built in. Just plug it in and it works.

## Architecture Note
x64 VCP drivers (like Ross-Tech's RT-USB64.sys) will NOT load on ARM64 Windows. The kernel driver must be compiled for ARM64 - this FTDI package provides ARM64-native kernel drivers verified with `ftdibus.sys` (0xAA64) and `ftser2k.sys` (0xAA64).
