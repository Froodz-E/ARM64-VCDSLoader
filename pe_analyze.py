#!/usr/bin/env python3
"""Analyze PE structure of a VCDS ARM64 binary to find file offsets for RVAs."""
import struct
import sys
import os


def pe_analyze(filepath: str, target_rva: int = 0x76FF0):
    """Parse PE headers and show section layout, resolving a target RVA to file offset."""
    with open(filepath, 'rb') as f:
        # DOS header
        dos_header = f.read(64)
        e_lfanew = struct.unpack_from('<I', dos_header, 0x3C)[0]
        print(f'PE signature offset (e_lfanew): 0x{e_lfanew:X}')

        # PE signature
        f.seek(e_lfanew)
        pe_sig = f.read(4)
        print(f'PE signature: {pe_sig.hex()}')

        # COFF header
        coff = f.read(20)
        machine = struct.unpack_from('<H', coff, 0)[0]
        num_sections = struct.unpack_from('<H', coff, 2)[0]
        size_of_optional_header = struct.unpack_from('<H', coff, 16)[0]
        print(f'Machine: 0x{machine:04X} (ARM64=0xAA64)')
        print(f'Number of sections: {num_sections}')
        print(f'Size of optional header: 0x{size_of_optional_header:X}')

        # Optional header
        opt_header = f.read(size_of_optional_header)
        magic = struct.unpack_from('<H', opt_header, 0)[0]
        image_base = struct.unpack_from('<Q', opt_header, 24)[0]
        section_alignment = struct.unpack_from('<I', opt_header, 32)[0]
        file_alignment = struct.unpack_from('<I', opt_header, 36)[0]

        print(f'Optional header magic: 0x{magic:04X} (PE32+=0x020B)')
        print(f'ImageBase: 0x{image_base:016X}')
        print(f'SectionAlignment: 0x{section_alignment:X}')
        print(f'FileAlignment: 0x{file_alignment:X}')

        # Section headers
        f.seek(e_lfanew + 4 + 20 + size_of_optional_header)
        print()
        print(f'{"Name":<10} {"VirtSize":>10} {"VirtAddr":>10} {"RawSize":>10} {"RawOff":>10}')
        print('-' * 60)

        target_section = None

        for i in range(num_sections):
            sec = f.read(40)
            name = sec[0:8].rstrip(b'\x00').decode('ascii', errors='replace')
            virt_size = struct.unpack_from('<I', sec, 8)[0]
            virt_addr = struct.unpack_from('<I', sec, 12)[0]
            raw_size = struct.unpack_from('<I', sec, 16)[0]
            raw_offset = struct.unpack_from('<I', sec, 20)[0]

            marker = ''
            if virt_addr <= target_rva < virt_addr + virt_size:
                file_offset = raw_offset + (target_rva - virt_addr)
                target_section = (name, file_offset)
                marker = f'  <-- TARGET! file_offset=0x{file_offset:X}'

            print(f'{name:<10} 0x{virt_size:08X} 0x{virt_addr:08X} 0x{raw_size:08X} 0x{raw_offset:08X}{marker}')

        print()
        if target_section:
            name, offset = target_section
            print(f'RVA 0x{target_rva:X} -> section "{name}", file offset 0x{offset:X}')
            f.seek(offset)
            original_bytes = f.read(16)
            print(f'Original bytes at offset 0x{offset:X}: {original_bytes.hex(" ")}')
        else:
            print(f'RVA 0x{target_rva:X} NOT found in any section!')
            sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {os.path.basename(__file__)} <VCDS.exeL> [target_rva]")
        print("  Parses PE headers and resolves an RVA to a file offset.")
        print("  Default target RVA: 0x76FF0 (FUN_140076ff0)")
        sys.exit(1)

    rva = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x76FF0
    pe_analyze(sys.argv[1], rva)
