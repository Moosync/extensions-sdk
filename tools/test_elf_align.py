import ctypes
import unittest

from tools.elf_align import (
    ELF_MAGIC,
    ELFCLASS64,
    PAGE_SIZE_16K,
    PF_R,
    PF_X,
    PT_GNU_RELRO,
    PT_LOAD,
    PT_NULL,
    Elf64Ehdr,
    Elf64Phdr,
    align_elf_16k,
)


def _build_synthetic_elf(
    loads: list[tuple[int, int, int, int, int, int]],
    relro: tuple[int, int, int, int] | None = None,
    payload_size: int = 0x5000,
) -> bytes:
    ehdr_size = ctypes.sizeof(Elf64Ehdr)
    phdr_size = ctypes.sizeof(Elf64Phdr)
    phnum = len(loads) + (1 if relro else 0)
    buf = bytearray(max(payload_size, ehdr_size + phnum * phdr_size))

    ehdr = Elf64Ehdr.from_buffer(buf)
    ehdr.e_ident[:4] = list(ELF_MAGIC)
    ehdr.e_ident[4] = ELFCLASS64
    ehdr.e_phoff = ehdr_size
    ehdr.e_ehsize = ehdr_size
    ehdr.e_phentsize = phdr_size
    ehdr.e_phnum = phnum
    ehdr.e_shoff = 0x1234
    ehdr.e_shnum = 5
    ehdr.e_shstrndx = 4

    for idx, (flags, offset, vaddr, filesz, memsz, align) in enumerate(loads):
        phdr = Elf64Phdr.from_buffer(buf, ehdr_size + idx * phdr_size)
        phdr.p_type = PT_LOAD
        phdr.p_flags = flags
        phdr.p_offset = offset
        phdr.p_vaddr = vaddr
        phdr.p_paddr = vaddr
        phdr.p_filesz = filesz
        phdr.p_memsz = memsz
        phdr.p_align = align

    if relro is not None:
        r_off, r_vaddr, r_filesz, r_memsz = relro
        phdr = Elf64Phdr.from_buffer(buf, ehdr_size + len(loads) * phdr_size)
        phdr.p_type = PT_GNU_RELRO
        phdr.p_flags = PF_R
        phdr.p_offset = r_off
        phdr.p_vaddr = r_vaddr
        phdr.p_paddr = r_vaddr
        phdr.p_filesz = r_filesz
        phdr.p_memsz = r_memsz
        phdr.p_align = 1

    return bytes(buf)


class TestElfAlign16k(unittest.TestCase):
    def test_non_elf_passthrough(self):
        raw = b"not an elf binary"
        self.assertEqual(align_elf_16k(raw), raw)

    def test_aligns_unaligned_pt_load_and_clears_shdr(self):
        raw = _build_synthetic_elf(
            loads=[
                (PF_R | PF_X, 0x0100, 0x1000, 0x0200, 0x0200, 0x1000),
                (PF_R, 0x0300, 0x2200, 0x0100, 0x0100, 0x1000),
            ],
            payload_size=0x1000,
        )

        aligned = bytearray(align_elf_16k(raw))
        ehdr = Elf64Ehdr.from_buffer(aligned)
        self.assertEqual(ehdr.e_shoff, 0)
        self.assertEqual(ehdr.e_shnum, 0)
        self.assertEqual(ehdr.e_shstrndx, 0)

        for idx in range(2):
            phdr = Elf64Phdr.from_buffer(aligned, ehdr.e_phoff + idx * ehdr.e_phentsize)
            self.assertEqual(phdr.p_vaddr % PAGE_SIZE_16K, phdr.p_offset % PAGE_SIZE_16K)
            self.assertGreaterEqual(phdr.p_align, PAGE_SIZE_16K)

    def test_preserves_pf_x_on_shared_16k_page_and_trims_relro(self):
        raw = _build_synthetic_elf(
            loads=[
                (PF_R | PF_X, 0x1000, 0x1000, 0x0400, 0x0400, 0x1000),
                (PF_R, 0x2000, 0x2000, 0x0200, 0x0200, 0x1000),
            ],
            relro=(0x2000, 0x2000, 0x0100, 0x0100),
            payload_size=0x3000,
        )

        aligned = bytearray(align_elf_16k(raw))
        ehdr = Elf64Ehdr.from_buffer(aligned)
        ro_phdr = Elf64Phdr.from_buffer(aligned, ehdr.e_phoff + 1 * ehdr.e_phentsize)
        relro_phdr = Elf64Phdr.from_buffer(aligned, ehdr.e_phoff + 2 * ehdr.e_phentsize)

        self.assertEqual(ro_phdr.p_flags, PF_R | PF_X)
        self.assertEqual(relro_phdr.p_type, PT_NULL)


if __name__ == "__main__":
    unittest.main()
