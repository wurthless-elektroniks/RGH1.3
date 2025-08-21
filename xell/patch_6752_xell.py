from patcher import *

def xell6752_do_patches(cbb_image: bytes) -> bytes:
    cbb_image = bytearray(cbb_image)

    # 0x68A8: skip over a good chunk of the fusecheck function
    cbb_image, _ = assemble_branch(cbb_image, 0x68A8, 0x6A10)

    # 0x6AA0: prevent bne into hostile territory
    cbb_image, _ = assemble_nop(cbb_image, 0x6AA0)

    # 0x71B0: skip decrypting CD
    cbb_image, _ = assemble_nop(cbb_image, 0x71B0)

    # 0x7200: don't POST 0xAD and die
    cbb_image, _ = assemble_branch(cbb_image, 0x7200, 0x7214)

    return cbb_image
