'''
Glitch3 XeLL ECC builder

Modified from 15432's RGH3 builder
'''

import struct, secrets, sys, hmac, hashlib
from enum import Enum
import Crypto.Cipher.ARC4 as RC4
import os
from ecc import NandType, ecc_encode
from smc import encrypt_smc

from xell.patch_5772_xell import xell5772_do_patches
from xell.patch_6752_xell import xell6752_do_patches
from cbbpatch import rgh13cbb_do_patches

key_1BL = b"\xDD\x88\xAD\x0C\x9E\xD6\x69\xE7\xB5\x67\x94\xFB\x68\x56\x3E\xFA"

class ImageType(Enum):
    GLITCH2 = 0
    '''
    Standard RGH2/RGH1.2/EXT_CLK
    '''

    GLITCH3 = 1
    '''
    RGH3 / RGH1.3 / EXT+3
    '''

    CABOOM = 2
    '''
    CAboom-type image
    '''


def encrypt_cba(cba):
    # should not be random or the build changes everytime
    rnd = b"CB_ACB_ACB_ACB_A"
    
    key = hmac.new(key_1BL, rnd, hashlib.sha1).digest()[0:0x10]
    return (key, cba[0:0x10] + rnd + RC4.new(key).encrypt(cba[0x20:]))

def encrypt_cbb(cbb, cba_key, cpu_key=b"\x00"*16):
    # should not be random or the build changes everytime
    rnd = b"CB_BCB_BCB_BCB_B"
    
    key = hmac.new(cba_key, rnd + cpu_key, hashlib.sha1).digest()[0:0x10]
    return cbb[0:0x10] + rnd + RC4.new(key).encrypt(cbb[0x20:])

def insert(image, data, offset=None):
    if offset is None:
        offset = len(image)
    if offset > len(image):
        image += b"\x00" * (offset - len(image))
    return image[:offset] + data + image[offset + len(data):]

def make_image_binary(smc_plaintext: bytes,
                      cba_plaintext: bytes,
                      cbx_plaintext: bytes,
                      cbb_plaintext: bytes,
                      cd_plaintext:  bytes,
                      xell:          bytes,
                      image_type:    ImageType = ImageType.GLITCH3) -> bytes:
    # SMC
    smc_ptr = 0x4000 - len(smc_plaintext)

    # BLs
    cba_ptr = 0x8000

    # make header
    image = struct.pack(">HHLLL64s16xLLLLLLLL", 0xFF4F, 1888, 0, cba_ptr, 0x70000, b"wurthless elektroniks presents glitch3",  0x4000, 0x70000, 0x20712, 0x4000, 0x10000, 0, len(smc_plaintext), smc_ptr)

    # add SMC
    image = insert(image, encrypt_smc(smc_plaintext), smc_ptr)

    # add BLs
    if image_type == ImageType.CABOOM:
        (key, cba_enc) = encrypt_cba(cbx_plaintext)
        image = insert(image, cba_enc, cba_ptr)
        image = insert(image, cbb_plaintext) # CB_X loads CB_B in plaintext
    else:
        (key, cba_enc) = encrypt_cba(cba_plaintext)
        image = insert(image, cba_enc, cba_ptr)
        if image_type == ImageType.GLITCH2:
            image = insert(image, encrypt_cbb(cbb_plaintext, key))
        else:
            image = insert(image, encrypt_cbb(cbx_plaintext, key))
            image = insert(image, cbb_plaintext) # CB_X loads CB_B in plaintext
        
    image = insert(image, cd_plaintext)  # CB_B is hacked to load CD in plaintext

    #add XeLL
    image = insert(image, xell, 0xC0000)
    image = insert(image, xell, 0x100000)

    return image

def load_or_die(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

XELL_TARGETS = {
    # falcon, jasper, badjasper are "production" ECCs
    "falcon" : {
        "nandtype":  NandType.NAND_16M,
        "smc":       os.path.join("smc","build","rgh13_falcon.bin"),
        "output":    os.path.join("ecc","rgh13_falcon.ecc"),
        "imagetype": ImageType.GLITCH3,
        "cbb":       '5772',
    },
    "jasper" : {
        "nandtype": NandType.NAND_16M_JASPER,
        "smc":      os.path.join("smc","build","rgh13_jasper.bin"),
        "output":   os.path.join("ecc","rgh13_jasper.ecc"),
        "imagetype": ImageType.GLITCH3,
        "cbb":      '6752',
    },
    "jasper_badjasper": {
        "nandtype":  NandType.NAND_16M_JASPER,
        "smc":       os.path.join("smc","build","rgh13_badjasper.bin"),
        "output":    os.path.join("ecc","rgh13_badjasper.ecc"),
        "imagetype": ImageType.GLITCH3,
        "cbb":       '6752'
    },

    # test ECC for testing CB_B patches
    "test_falcon_resetme": {
        "nandtype":  NandType.NAND_16M,
        "smc":       os.path.join("smc","build","smc+resetme_falcon.bin"),
        "output":    os.path.join("ecc","testonly_smc+resetme_falcon.ecc"),
        "imagetype": ImageType.GLITCH3,
        "cbb":       '5772'
    }
}

def main():
    print("loading prerequisite binaries...")

    # cba  = cba/cba_9188_mfg.bin
    # cbx  = cbx/cbx_xell.bin
    # cbb  = cbb/cbb_9188_clean.bin
    # cd   = cd/cd_xell.bin
    # xell = xell/xell.bin
    cba  = load_or_die("cba/cba_9188_mfg.bin")
    cbx  = load_or_die("cbx/cbx_xell.bin")
    cd   = load_or_die("cd/cd_xell.bin")
    xell = load_or_die("xell/xell.bin")

    cbb_5772 = load_or_die(os.path.join("cbb","cbb_5772_clean.bin"))
    cbb_5772 = xell5772_do_patches(cbb_5772)
    cbb_6752 = load_or_die(os.path.join("cbb","cbb_6752_clean.bin"))
    cbb_6752 = xell6752_do_patches(cbb_6752)

    # RGH1.3 postcounter patches are the same between 5772/6752
    cbb_5772 = rgh13cbb_do_patches(cbb_5772)
    cbb_6752 = rgh13cbb_do_patches(cbb_6752)

    cbbs = {
        '5772': cbb_5772,
        '6752': cbb_6752
    }

    try:
        for target, target_params in XELL_TARGETS.items():
            print(f"building target: {target}")
            nandtype   = target_params["nandtype"]
            smc        = target_params["smc"]
            output     = target_params["output"]
            imagetype  = target_params["imagetype"]
            cbb        = cbbs[target_params["cbb"]]

            smc_data = load_or_die(smc)

            img_bin = make_image_binary(smc_data,
                                        cba,
                                        cbx,
                                        cbb,
                                        cd,
                                        xell,
                                        imagetype)

            print("\tbuilt bin image, encoding to ECC now")
            img_ecc = ecc_encode(img_bin, nandtype, 0)
            with open(output, "wb") as f:
                f.write(img_ecc)
            print(f"\twrote ECC to {output}")

    finally:
        pass

if __name__ == '__main__':
    main()

