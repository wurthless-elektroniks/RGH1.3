'''
g3fix - Script to attempt to fix compatibility issues with the RGH3 v1 loader
Intended for RGH1.3, might work with RGH3 also.

Current status: No improvement over RGH2to3 patches.
- Blades (6717): Boots, but kernel displays Christmas lights and halts.
- NXE (9199): Works, but RGH2to3 supports this already.
- Kinect (13604): Boots to Christmas lights.
- Metro (17559): Works, but RGH2to3 supports this already.
'''

import sys
import os
import re
import struct
import hmac
import hashlib
from argparse import ArgumentParser,RawTextHelpFormatter
import Crypto.Cipher.ARC4 as RC4
import ecc

key_1BL = b"\xDD\x88\xAD\x0C\x9E\xD6\x69\xE7\xB5\x67\x94\xFB\x68\x56\x3E\xFA"

# hi dr schottky!!!
CPUKEY_EXP = re.compile(r"^[0-9a-fA-F]{32}$")

def _init_argparser():
    argparser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                               prog='g3fix')
    
    argparser.add_argument("cpukey",
                           nargs='?',
                           help="Specifies CPU key")
    
    argparser.add_argument("updflash",
                           nargs='?',
                           help="Path to updflash.bin (WARNING: FILE WILL BE OVERWRITTEN)")
  
    return argparser

def encrypt_cba(cba, cba_seed):
    # should not be random or the build changes everytime
    rnd = cba_seed

    key = hmac.new(key_1BL, rnd, hashlib.sha1).digest()[0:0x10]
    return (key, cba[0:0x10] + rnd + RC4.new(key).encrypt(cba[0x20:]))

def encrypt_cbb(cbb, cba_key, cbb_seed, cpu_key=b"\x00"*16):
    rnd = cbb_seed
    
    key = hmac.new(cba_key, rnd + cpu_key, hashlib.sha1).digest()[0:0x10]
    return cbb[0:0x10] + rnd + RC4.new(key).encrypt(cbb[0x20:])

def main():
    argparser = _init_argparser()
    args = argparser.parse_args()
    if args.updflash is None or args.cpukey is None:
        print("invalid usage - must specify path to updflash.bin AND cpukey")
        print("run with --help for more options")
        return
    
    cpu_key = args.cpukey
    if CPUKEY_EXP.match(cpu_key) is None:
        print("error: invalid CPU key format")
        return
    cpu_key = bytes.fromhex(cpu_key)

    nand = None
    with open(args.updflash, "rb") as f:
        nand = f.read()

    nand_type = ecc.ecc_detect_type(nand)
    if nand_type is None:
        print("NAND type cannot be detected, exiting.")
        return
    
    if nand_type == ecc.NandType.NAND_64M:
        print("found Jasper big boy NAND")

    if nand_type == ecc.NandType.NAND_16M_JASPER:
        print("found Jasper-style 16m NAND")

    if nand_type == ecc.NandType.NAND_16M:
        print("found standard 16m NAND")

    # only inspect/modify the first chunk (1 block on big blocks)
    nand_stripped = ecc.ecc_strip(nand[0:0x021000])

    # grab CB_A stuff first (might be useful if we want to use retail CB_A)
    cba_address   = 0x8000
    cba_size      = struct.unpack(">I", nand_stripped[0x800C:0x8010])[0]
    cba_hmac_seed = bytearray([0xF4, 0x27, 0x3D, 0xEC, 0x9D, 0xDC, 0xCC, 0x6E, 0xDE, 0x48, 0x1A, 0x7B, 0xD8, 0xE8, 0xB7, 0x12])
    
    next_cb_addr = cba_address+cba_size

    if nand_stripped[next_cb_addr:next_cb_addr+4] != bytes([0x43, 0x42, 0x3C, 0x48]):
        print("error: not a RGH3 image - CB_X did not follow CB_A")
        return

    cbx_address = next_cb_addr
    cbx_size = struct.unpack(">I", nand_stripped[cbx_address+0x0C:cbx_address+0x10])[0]
    cbx_hmac_seed = nand_stripped[cbx_address+0x10:cbx_address+0x20]
    next_cb_addr = cbx_address+cbx_size

    # for whatever reason RGH3 v1 uses a weird loader (10918) that is slightly
    # bigger than the retail CB_As, so we need to juggle some crap around.
    # extract the plaintext CB_B first.
    cbb_address = next_cb_addr
    cbb_size = struct.unpack(">I", nand_stripped[cbb_address+0x0C:cbb_address+0x10])[0]
    cbb_hmac_seed = nand_stripped[cbb_address+0x10:cbb_address+0x20]
    cbb = nand_stripped[cbb_address:cbb_address+cbb_size]

    # 5772 / 6752 / 9188 retail are practically the same code byte for byte.
    # only a few things change between them (probably CB_B expected hash).
    # so let's just use falcon for everything for the time being
    new_cba = None
    with open(os.path.join("cba", "cba_5772.bin"), "rb") as f:
        new_cba = f.read()
    
    if len(new_cba) > cba_size:
        print("error: replacement CB_A somehow larger than the original")
        return

    padding_bytes_required = cba_size - len(new_cba)

    new_cbx = None
    with open(os.path.join("cbx","cbx_xell.bin"), "rb") as f:
        new_cbx = f.read()
    
    if len(new_cbx) != cbx_size:
        print("error: CB_X size mismatch")
        return

    new_cbx = bytearray(new_cbx)
    new_cbx[0x10:0x20] = cbb_hmac_seed

    insert_pos = 0x8000

    (cba_key, encrypted_cba) = encrypt_cba(new_cba, cba_hmac_seed)
    nand_stripped[insert_pos:insert_pos+len(encrypted_cba)] = encrypted_cba
    print("CB_A replaced")
    insert_pos += len(encrypted_cba)

    encrypted_cbx = encrypt_cbb(new_cbx, cba_key, cbb_hmac_seed, cpu_key)
    nand_stripped[insert_pos:insert_pos+len(encrypted_cbx)] = encrypted_cbx
    print("CB_X replaced")
    insert_pos += len(encrypted_cbx)

    cbb = bytearray(cbb)
    cbb += bytes([0] * padding_bytes_required)
    cbb[0x0C:0x10] = struct.pack(">I", len(cbb))
    nand_stripped[insert_pos:insert_pos+len(cbb)] = cbb
    print("CB_B padded")
    insert_pos += len(cbb)

    # sanity check: next loader in line should be CD
    if nand_stripped[insert_pos] != 0x43 or nand_stripped[insert_pos+1] != 0x44:
        print(f"sanity check failed: didn't end up at CD after inserts (final pos was 0x{insert_pos:08x})")
        return

    print("recalculating ECC data...")
    nand_stripped_ecc = ecc.ecc_encode(nand_stripped, nand_type, 0)
    nand = bytearray(nand)
    nand[0:0x021000] = nand_stripped_ecc

    print("writing final NAND...")
    with open(args.updflash, "wb") as f:
        f.write(nand)

    print("dunzo")

if __name__ == '__main__':
    main()
