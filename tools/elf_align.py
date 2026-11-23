"""Aligns ELF64 PT_LOAD segments to 16 KiB boundaries for Android 15+ devices."""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import dataclass

PAGE_SIZE_16K = 0x4000

ELF_MAGIC = b"\x7fELF"
ELFCLASS64 = 2

PT_NULL = 0
PT_LOAD = 1
PT_GNU_RELRO = 0x6474E552

PF_X = 1
PF_R = 4


class Elf64Ehdr(ctypes.LittleEndianStructure):
    """ELF64 file header."""

    _pack_ = 1
    _fields_ = [
        ("e_ident", ctypes.c_uint8 * 16),
        ("e_type", ctypes.c_uint16),
        ("e_machine", ctypes.c_uint16),
        ("e_version", ctypes.c_uint32),
        ("e_entry", ctypes.c_uint64),
        ("e_phoff", ctypes.c_uint64),
        ("e_shoff", ctypes.c_uint64),
        ("e_flags", ctypes.c_uint32),
        ("e_ehsize", ctypes.c_uint16),
        ("e_phentsize", ctypes.c_uint16),
        ("e_phnum", ctypes.c_uint16),
        ("e_shentsize", ctypes.c_uint16),
        ("e_shnum", ctypes.c_uint16),
        ("e_shstrndx", ctypes.c_uint16),
    ]


class Elf64Phdr(ctypes.LittleEndianStructure):
    """ELF64 program header."""

    _pack_ = 1
    _fields_ = [
        ("p_type", ctypes.c_uint32),
        ("p_flags", ctypes.c_uint32),
        ("p_offset", ctypes.c_uint64),
        ("p_vaddr", ctypes.c_uint64),
        ("p_paddr", ctypes.c_uint64),
        ("p_filesz", ctypes.c_uint64),
        ("p_memsz", ctypes.c_uint64),
        ("p_align", ctypes.c_uint64),
    ]


@dataclass
class _LoadSegment:
    phdr_index: int
    p_flags: int
    p_offset: int
    p_vaddr: int
    p_filesz: int
    p_memsz: int
    p_align: int


def _page_range(vaddr: int, memsz: int) -> range:
    start_pg = vaddr // PAGE_SIZE_16K
    end_pg = (vaddr + max(memsz, 1) - 1) // PAGE_SIZE_16K
    return range(start_pg, end_pg + 1)


def _phdr_at(data: bytearray, e_phoff: int, e_phentsize: int, index: int) -> Elf64Phdr:
    return Elf64Phdr.from_buffer(data, e_phoff + index * e_phentsize)


def align_elf_16k(raw: bytes, force_repack: bool = False) -> bytes:
    """Aligns ELF64 PT_LOAD file offsets to 16 KiB boundaries and fixes RELRO/PF_X."""
    if len(raw) < ctypes.sizeof(Elf64Ehdr) or raw[:4] != ELF_MAGIC or raw[4] != ELFCLASS64:
        return raw

    data = bytearray(raw)
    ehdr = Elf64Ehdr.from_buffer(data)
    e_phoff = ehdr.e_phoff
    e_phentsize = ehdr.e_phentsize
    e_phnum = ehdr.e_phnum

    if e_phentsize < ctypes.sizeof(Elf64Phdr) or e_phoff + e_phnum * e_phentsize > len(data):
        return raw

    loads: list[_LoadSegment] = []
    needs_repack = force_repack
    for idx in range(e_phnum):
        phdr = _phdr_at(data, e_phoff, e_phentsize, idx)
        if phdr.p_type != PT_LOAD:
            continue
        if (phdr.p_vaddr % PAGE_SIZE_16K) != (phdr.p_offset % PAGE_SIZE_16K) or phdr.p_align < PAGE_SIZE_16K:
            needs_repack = True
        loads.append(
            _LoadSegment(
                phdr_index=idx,
                p_flags=phdr.p_flags,
                p_offset=phdr.p_offset,
                p_vaddr=phdr.p_vaddr,
                p_filesz=phdr.p_filesz,
                p_memsz=phdr.p_memsz,
                p_align=phdr.p_align,
            )
        )

    if not loads:
        return raw

    exec_pages: set[int] = set()
    for seg in loads:
        if seg.p_flags & PF_X:
            exec_pages.update(_page_range(seg.p_vaddr, seg.p_memsz))

    # Preserve PF_X on any read-only PT_LOAD sharing a 16 KiB page with an executable PT_LOAD.
    for seg in loads:
        if seg.p_flags == PF_R and any(pg in exec_pages for pg in _page_range(seg.p_vaddr, seg.p_memsz)):
            _phdr_at(data, e_phoff, e_phentsize, seg.phdr_index).p_flags = PF_R | PF_X

    # Ensure PT_GNU_RELRO never mprotect(PROT_READ)s a 16 KiB page containing PF_X code.
    for idx in range(e_phnum):
        phdr = _phdr_at(data, e_phoff, e_phentsize, idx)
        if phdr.p_type != PT_GNU_RELRO or phdr.p_memsz == 0:
            continue
        start_pg = phdr.p_vaddr // PAGE_SIZE_16K
        if start_pg not in exec_pages:
            continue
        next_pg_addr = (start_pg + 1) * PAGE_SIZE_16K
        if phdr.p_vaddr + phdr.p_memsz <= next_pg_addr:
            phdr.p_type = PT_NULL
        else:
            delta = next_pg_addr - phdr.p_vaddr
            phdr.p_offset += delta
            phdr.p_vaddr = next_pg_addr
            phdr.p_paddr += delta
            phdr.p_filesz = phdr.p_filesz - delta if phdr.p_filesz > delta else 0
            phdr.p_memsz -= delta

    if not needs_repack:
        return bytes(data)

    out = bytearray(data[: loads[0].p_offset])
    orig_to_new: list[tuple[int, int, int]] = []
    phdr_updates: list[tuple[int, int, int | None]] = []
    for idx, seg in enumerate(loads):
        if idx > 0:
            prev = loads[idx - 1]
            prev_end = prev.p_offset + prev.p_filesz
            if seg.p_offset > prev_end:
                out.extend(data[prev_end : seg.p_offset])
        pad = ((seg.p_vaddr % PAGE_SIZE_16K) - (len(out) % PAGE_SIZE_16K)) % PAGE_SIZE_16K
        out.extend(b"\x00" * pad)
        new_off = len(out)
        orig_to_new.append((seg.p_offset, seg.p_offset + seg.p_filesz, new_off - seg.p_offset))
        out.extend(data[seg.p_offset : seg.p_offset + seg.p_filesz])
        phdr_updates.append(
            (seg.phdr_index, new_off, PAGE_SIZE_16K if seg.p_align < PAGE_SIZE_16K else None)
        )

    for phdr_index, new_off, new_align in phdr_updates:
        out_phdr = _phdr_at(out, e_phoff, e_phentsize, phdr_index)
        out_phdr.p_offset = new_off
        if new_align is not None:
            out_phdr.p_align = new_align

    for idx in range(e_phnum):
        out_phdr = _phdr_at(out, e_phoff, e_phentsize, idx)
        if out_phdr.p_type != PT_LOAD and out_phdr.p_offset != 0:
            for s_start, s_end, delta in orig_to_new:
                if s_start <= out_phdr.p_offset < s_end:
                    out_phdr.p_offset += delta
                    break

    out_ehdr = Elf64Ehdr.from_buffer(out)
    out_ehdr.e_shoff = 0
    out_ehdr.e_shnum = 0
    out_ehdr.e_shstrndx = 0
    return bytes(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input ELF64 file path")
    parser.add_argument("--output", required=True, help="Output aligned ELF64 file path")
    args = parser.parse_args()

    with open(args.input, "rb") as f:
        raw = f.read()
    aligned = align_elf_16k(raw)
    with open(args.output, "wb") as f:
        f.write(aligned)


if __name__ == "__main__":
    main()
