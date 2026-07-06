"""Check which bytes differ between VCDS.exeL.bak and VCDS.exeL."""
BASE = r"D:\VCDS Test\ARM64\Installation\VCDS"
with open(f"{BASE}\\VCDS.exeL.bak", "rb") as f:
    bak = f.read()
with open(f"{BASE}\\VCDS.exeL", "rb") as f:
    cur = f.read()

diffs = []
for i in range(min(len(bak), len(cur))):
    if bak[i] != cur[i]:
        diffs.append((i, bak[i], cur[i]))

print(f"Total differing bytes: {len(diffs)}")
for offset, b1, b2 in diffs[:20]:
    note = ""
    if 0x763F0 <= offset < 0x763F8:
        note = " <-- PATCH SITE (FUN_140076ff0)"
    print(f"  0x{offset:06X}: 0x{b1:02X} → 0x{b2:02X}{note}")
if len(diffs) > 20:
    print(f"  ... and {len(diffs) - 20} more")
