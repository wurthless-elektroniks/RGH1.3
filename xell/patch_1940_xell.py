'''
For Xenons CB 1940 is the last release (that I can find right now) that has POST codes.

Another project idea is to find patches for all CBs so we can use any one we want,
not just the ones xeBuild forced on us. So this is a nice start for that...
'''

from patcher import *

def xell1940_do_patches(cbb_image: bytes) -> bytes:
    cbb_image = bytearray(cbb_image)

    # 0x04CC: skip fusecheck function entirely
    cbb_image, _ = assemble_nop(cbb_image, 0x4CC)

    # 0x454C: skip decrypt of CD as it's already in plaintext
    cbb_image, _ = assemble_nop(cbb_image, 0x454C)
    
    # 0x4598: skip hash check
    cbb_image, _ = assemble_branch(cbb_image, 0x4598, 0x45AC)

    return cbb_image
