import sys
import struct
import hashlib
from argparse import ArgumentParser,RawTextHelpFormatter
from enum import Enum
import ecc

# somehow, the Jasper images use the exact same SMC, I don't know why
SHA1_FALCON_RGH3_27MHZ = "9b89a53dbdb4735782e92b70bb5e956f6b35da5f"
SHA1_FALCON_RGH3_10MHZ = "a4ae6a6f1ff374739d1c91f8a2881f4eecc210d3"


SHA1_CBB_5772_XEBUILD = ""
SHA1_CBB_6752_XEBUILD = ""

def _init_argparser():
    argparser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                               prog='convert_rgh13',
                               description='Converts RGH3 NAND to RGH1.3')
    
    argparser.add_argument("--badjasper",
                           default=False,
                           action='store_true',
                           help="Use badjasper SMC if specified")
    
    argparser.add_argument("updflash",
                           nargs='?',
                           help="Path to updflash.bin (WARNING: FILE WILL BE OVERWRITTEN)")
  
    return argparser

def main():
    argparser = _init_argparser()
    args = argparser.parse_args()
    if args.updflash is None:
        print("invalid usage - must specify path to updflash.bin")
        print("run with --help for more options")
        return

    nand = None
    with open(args.updflash, "rb") as f:
        nand = f.read()

    nand_type = ecc.ecc_detect_type(nand)
    if nand_type is None:
        print("NAND type cannot be detected, exiting.")
        return
    
    # FIXME: there is a bug somewhere that breaks big block NANDs, have to find it...
    if nand_type == ecc.NandType.NAND_64M:
        print("sorry, big block NANDs are not supported yet")
        return

    if nand_type == ecc.NandType.NAND_16M_JASPER:
        print("found Jasper-style 16m NAND")

    if nand_type == ecc.NandType.NAND_16M:
        print("found standard 16m NAND")

    # only inspect/modify the first chunk (1 block on big blocks)
    nand_stripped = ecc.ecc_strip(nand[0:0x021000])

    # get shasum of encrypted SMC - that will be enough to determine what it is
    smc_hash = hashlib.sha1(nand_stripped[0x1000:0x4000])
    if smc_hash.hexdigest() == SHA1_FALCON_RGH3_27MHZ:
        print("found RGH3 v1 27 MHz SMC")
    elif smc_hash.hexdigest() == SHA1_FALCON_RGH3_10MHZ:
        print("found RGH3 v1 10 MHz SMC")
    else:
        print(f"WARNING: unrecognized SMC: {smc_hash.hexdigest()}")

    # now identify if this really is a RGH3 image.
    # find first CB @ 0x8000
    # then look at next CB in chain
    # if it's not CB_X (ver 15432), then it's not an RGH3 image
    first_cb_size = struct.unpack(">I", nand_stripped[0x800C:0x8010])[0]
    next_cb_addr = 0x8000+first_cb_size
    if nand_stripped[next_cb_addr:next_cb_addr+4] != bytes([0x43, 0x42, 0x3C, 0x48]):
        print("error: not a RGH3 image - CB_X did not follow CB_A")
        return

    print("image looks like RGH3 or glitch3, checking CB_B")

    # advance to next CB stage
    cbx_size = struct.unpack(">I", nand_stripped[next_cb_addr+0x0C:next_cb_addr+0x10])[0]
    next_cb_addr += cbx_size
    if nand_stripped[next_cb_addr:next_cb_addr+2] != bytes([0x43, 0x42]):
        print("error: CB magicword not found at next CB slot")
        return
    
    cbb_version = struct.unpack(">H",nand_stripped[next_cb_addr+2:next_cb_addr+4])[0]
    cbb_size = struct.unpack(">I", nand_stripped[next_cb_addr+0x0C:next_cb_addr+0x10])[0]

    # calc SHA hash of CB_B to determine what it really is
    # (hash runs from 0x140 through to end of CB_B)
    cbb_hash = hashlib.sha1(nand_stripped[next_cb_addr + 0x140:next_cb_addr + cbb_size])

    if cbb_version == 5772 and cbb_hash == SHA1_CBB_5772_XEBUILD:
        print("found xeBuild-patched Falcon CB_B")
    elif cbb_version == 6752 and cbb_hash == SHA1_CBB_6752_XEBUILD:
        print("found xeBuild-patched Jasper CB_B")
    else:
        print("error: unrecognized/unsupported CB_B version")
        return

    # inject appropriate SMC image

    # inject appropriate hacked CB_B

    # write updated NAND

if __name__ == '__main__':
    main()
