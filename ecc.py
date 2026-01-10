'''
ECC helper stuff, ported to Python so I don't have to keep using Nandpro on Windows.
'''

import struct
from enum import Enum

class NandType(Enum):
    NAND_16M = 0
    '''
    Old 16mb mode (Xenon/Zephyr/Falcon)
    '''

    NAND_16M_JASPER = 0x01
    '''
    New 16 MB mode (Jasper/Trinity/Corona)
    '''

    NAND_64M        = 0x10
    '''
    Big Block mode (Jasper)
    '''

def ecc_calc(sector: bytes, special_data: int = 0) -> bytes:
    if len(sector) != (512+12):
        raise RuntimeError("sector size not 524 bytes (512 data, 12 bytes ECC header data)")

    # insert zero bytes to round the message out to 528
    sector_padded = bytearray(sector)
    sector_padded += bytes([0] * 4)

    # this is modernized from the classic imgbuild by gligli et al
    val = 0
    for i in range(0x1066):
        if not i & 31:
            word = int(i / 8)
            v = ~struct.unpack("<L", sector_padded[word:word+4])[0]
        val ^= v & 1
        v >>= 1
        if val & 1:
            val ^= 0x6954559
        val >>= 1

    # ECC data is actually 26 bits; lowest 6 bits are reserved for some
    # metadata like indicating if the block contains system settings etc.
    val = (~val << 6) & 0xFFFFFFC0
    val = val | (special_data & 0x3F)

    return struct.pack("<L", val)

def ecc_encode(bin_image: bytes,
               nand_type: NandType,
               starting_block: int = 0) -> bytes:

    if (len(bin_image) % 512) != 0:
        raise RuntimeError("bin_image size not a multiple of 512 bytes")

    block_id                   = starting_block
    sectors_written_this_block = 0
    num_sectors_per_block      = 256 if nand_type == NandType.NAND_64M else 32

    result = bytearray()

    pos = 0
    while pos < len(bin_image):
        sector = bin_image[pos:pos+512]

        sector_ecc = bytearray()

        sector_ecc += sector

        if nand_type == NandType.NAND_64M:
            # big boy NANDs have a weird format, but thankfully we don't
            # really have to obey it when encoding stuff in the first few
            # blocks - it's only when we hit system flash stuff that we
            # have to care about other flags.
            sector_ecc += struct.pack("<BHB", 0xFF, block_id, 0x00)
            sector_ecc += bytes([0x00, 0x00, 0x00, 0x00])
            sector_ecc += bytes([0x00, 0x00, 0x00, 0x00])
        elif nand_type == NandType.NAND_16M_JASPER:
            sector_ecc += struct.pack("<BHB", 0x00, block_id, 0x00)
            sector_ecc += bytes([0x00, 0xFF, 0x00, 0x00])
            sector_ecc += bytes([0x00, 0x00, 0x00, 0x00])
        elif nand_type == NandType.NAND_16M:
            sector_ecc += struct.pack("<I", block_id)
            sector_ecc += bytes([0x00, 0xFF, 0x00, 0x00])
            sector_ecc += bytes([0x00, 0x00, 0x00, 0x00])

        sector_ecc += ecc_calc(sector_ecc)

        result += sector_ecc

        pos += 512
        sectors_written_this_block += 1
        if sectors_written_this_block >= num_sectors_per_block:
            block_id += 1
            sectors_written_this_block = 0

    return result

def ecc_strip(ecc_image: bytes) -> bytes:
    out = bytearray()

    pos = 0
    while pos < len(ecc_image):
        out += ecc_image[pos:pos+0x200]
        pos += 0x210

    return out

def ecc_detect_type(ecc_image: bytes) -> NandType | None:
    block_0_sector_0_header = ecc_image[0x200:0x20C]
    block_0_sector_1_header = ecc_image[0x410:0x41C]
    block_0_sector_2_header = ecc_image[0x620:0x62C]
    block_0_sector_3_header = ecc_image[0x830:0x83C]

    # first 8 bytes should match between all sectors
    if (block_0_sector_0_header == block_0_sector_1_header and \
        block_0_sector_1_header == block_0_sector_2_header and \
        block_0_sector_2_header == block_0_sector_3_header) is False:
        print("error: first four ECC headers do not match")
        return None

    # validate ECC for each of those sectors
    # this should be enough to catch crap inputs
    if ecc_calc(ecc_image[0x000:0x20C]) != ecc_image[0x20C:0x210] or \
       ecc_calc(ecc_image[0x210:0x41C]) != ecc_image[0x41C:0x420] or \
       ecc_calc(ecc_image[0x420:0x62C]) != ecc_image[0x62C:0x630] or \
       ecc_calc(ecc_image[0x630:0x83C]) != ecc_image[0x83C:0x840]:
        print("error: ECC mismatch, image is probably corrupt or invalid")
        return None
    
    nandtype_preliminary = None

    # okay, it looks fine - what kind of image we got here?
    if block_0_sector_0_header[0:8] == bytes([0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]):
        # if big block, there's nothing more to do here
        return NandType.NAND_64M

    # for 16mb images check block 1 header for jasper-type NANDs
    block_1_sector_0_header = ecc_image[0x4400:0x440C]
    if block_1_sector_0_header[0:8] == bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00]):
        return NandType.NAND_16M
    if block_1_sector_0_header[0:8] == bytes([0x00, 0x01, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00]):
        return NandType.NAND_16M_JASPER
    
    if nandtype_preliminary is None:
        print("error: ECC type not recognized")
        return None
