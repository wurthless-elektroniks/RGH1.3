'''
RGH1.3 CB_B patches

Identical between 5772 and 6752
'''

from patcher import *

HWINIT_POSTCOUNT_BLOCK_BASE_ADDRESS = 0x280


def assemble_hwinit_postcount_block(cbb_image: bytes, address: int):
    # assemble hwinit_postcount_unified.s, then take the hexdump and shove it in here.
    # total size of this stub cannot exceed 256 bytes!
    hwinit_postcount_block = bytes([

    ])

    hwinit_postcount_block_size = len(hwinit_postcount_block)
    if hwinit_postcount_block_size > 256:
        raise RuntimeError("hwinit postcount block too big - must be 256 bytes or less")

    cbb_image[address:address+hwinit_postcount_block_size] = hwinit_postcount_block
    return cbb_image


def rgh13cbb_do_patches(cbb_image: bytes):
    cbb_image = assemble_hwinit_postcount_block(cbb_image, HWINIT_POSTCOUNT_BLOCK_BASE_ADDRESS)

    # 0x0944: call our postcounter init function instead of going to 0x0D5C directly
    cbb_image, _ = assemble_branch_with_link(cbb_image, 0x0944, HWINIT_POSTCOUNT_BLOCK_BASE_ADDRESS + 0)

    # 0x0998: reroute start of hwinit interpreter loop through toggle stub
    cbb_image, _ = assemble_branch(cbb_image, 0x0998, HWINIT_POSTCOUNT_BLOCK_BASE_ADDRESS + 4)

    # 0x09E8: reroute hwinit interpreter delay function through delayop stub
    cbb_image, _ = assemble_branch(cbb_image, 0x09E8, HWINIT_POSTCOUNT_BLOCK_BASE_ADDRESS + 8)

    # 0x0DC4: reroute success case through done stub
    cbb_image, _ = assemble_branch(cbb_image, 0x0DC4, HWINIT_POSTCOUNT_BLOCK_BASE_ADDRESS + 12)

    return cbb_image
