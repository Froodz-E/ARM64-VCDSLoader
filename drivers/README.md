# FTDI ARM64 VCP Driver — Patched for Ross-Tech HEX-USB

**Version:** 2.12.36.20 (Feb 2025) · **Architecture:** ARM64 native · **WHQL signed**

This driver package has been patched to add Ross-Tech's custom PID (`VID_0403&PID_FA24`)
so it works with Ross-Tech HEX-USB, Micro-CAN, KII-USB, and KEY-USB interfaces on
**Windows ARM64 (Snapdragon X)**.

> **HEX-V2 or HEX-NET?** You don't need this. HEX-V2 uses HID (built into Windows),
> HEX-NET uses WiFi. This driver is only for USB cables with FTDI chips.

---

## Installation — "Have Disk" Method

The standard FTDI driver doesn't list Ross-Tech's custom PID. You'll install it
manually using Device Manager's "Have Disk" — **twice** (once for the bus driver, 
once for the serial port driver).

### Step 1: Install the Bus Driver (FTDIBUS)

1. Open **Device Manager** (`Win+R` → `devmgmt.msc`)
2. Find **"Ross-Tech HEX-USB"** under "Other devices" (yellow warning icon)
3. Right-click → **Update driver**
4. Click **"Browse my computer for drivers"**
5. Click **"Let me pick from a list of available drivers"**
6. Click **"Have Disk..."**
7. Click **Browse** → navigate to this folder: `ARM64\Release\`
8. Select **`FTDIBUS.inf`** → Open → OK
9. Select **"USB Serial Converter"** from the list
10. Click **Next** → Click **Yes** on the compatibility warning
11. Click **Install** (ignore any signature warning)

The device should now show as **"USB Serial Converter"** under "Universal Serial Bus controllers".

### Step 2: Install the Serial Port Driver (FTDIPORT)

A second device will appear — **"USB Serial Port"** with a yellow warning.
Repeat the exact same process, but this time select **`FTDIPORT.inf`**:

1. Find **"USB Serial Port"** under "Other devices" (or expand "USB Serial Converter")
2. Right-click → **Update driver** → **Browse my computer** → **Let me pick**
3. Click **"Have Disk..."** → Browse → select **`FTDIPORT.inf`**
4. Select **"USB Serial Port"** → Next → Yes → Install

The device should now appear as **"USB Serial Port (COM3)"** under "Ports (COM & LPT)".

### Verify

Open PowerShell and run:

```powershell
Get-PnpDevice | Where-Object { $_.InstanceId -like "*0403*FA24*" }
```

Should show:
```
Status  Class   FriendlyName
------  -----   ------------
OK      USB     USB Serial Converter
OK      Ports   USB Serial Port (COM3)
```

---

## Architecture Verification

Both kernel drivers are ARM64 native (not emulated):

```powershell
# Should output 0xAA64 for both:
python -c "
import struct
for f in ['ftdibus.sys','ftser2k.sys']:
    with open(f,'rb') as fh:
        d=fh.read(4096); pe=struct.unpack_from('<I',d,0x3C)[0]
        print(f'{f}: 0x{struct.unpack_from(\"<H\",d,pe+4)[0]:04X}')
"
# Expected: ftdibus.sys: 0xAA64, ftser2k.sys: 0xAA64
```

## What Was Patched

| File | Change |
|------|--------|
| `FTDIBUS.inf` | Added `USB\VID_0403&PID_FA24` to ARM64 hardware IDs |
| `FTDIPORT.inf` | Added `FTDIBUS\COMPORT&VID_0403&PID_FA24` to ARM64 hardware IDs |

The `.sys` kernel binaries are unmodified — they're the original WHQL-signed ARM64 drivers from FTDI.
Only the INF files were updated to recognize Ross-Tech's custom PID.
