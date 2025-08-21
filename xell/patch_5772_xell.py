from patcher import *

def xell5772_do_patches(cbb_image: bytes) -> bytes:
    cbb_image = bytearray(cbb_image)

    # 0x04F0: skip fusecheck function entirely
    cbb_image, _ = assemble_nop(cbb_image, 0x4F0)

    # 0x7168: skip decrypt of CD as it's already in plaintext
    cbb_image, _ = assemble_nop(cbb_image, 0x7168)
    
    # 0x71B0: skip hash check
    cbb_image, _ = assemble_branch(cbb_image, 0x71B0, 0x71CC)

    return cbb_image
