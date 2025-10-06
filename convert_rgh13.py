import sys
import struct
import hashlib
from argparse import ArgumentParser,RawTextHelpFormatter
from enum import Enum
from smc import encrypt_smc
from cbbpatch import rgh13cbb_do_patches
import ecc
import os

# RGH3 v1 uses the same SMC for Falcon and Jasper, likely because they're compatible
# We expect these for all phat builds
SHA1_FALCON_RGH3_27MHZ = "9b89a53dbdb4735782e92b70bb5e956f6b35da5f"
SHA1_FALCON_RGH3_10MHZ = "a4ae6a6f1ff374739d1c91f8a2881f4eecc210d3"


SHA1_CBB_5772_XEBUILD = "3a8fb9580ce01cf1c0e2d885e0fd96a05571643f"
SHA1_CBB_6752_XEBUILD = "899cd01e00ef7b27ceb010dde42e4d6e9c871330"

# TODO: calc hash of patched elpiss 7378 now that jrunner is supporting it
SHA1_CBB_7378_ELPISS  = ""

def _init_argparser():
    argparser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                               prog='convert_rgh13',
                               description='Converts RGH3 NAND to RGH1.3/EXT+3')
    
    argparser.add_argument("--board",
                           help="Specifies target board (xenon, zephyr, falcon, jasper). Required for some CB_B versions.")

    argparser.add_argument("--badjasper",
                           default=False,
                           action='store_true',
                           help="Use badjasper SMC if specified")
    
    argparser.add_argument("--tiltsw",
                           default=False,
                           action='store_true',
                           help="Use tiltswitch method SMC for Zephyr/Falcon/Jasper")

    argparser.add_argument("--extpwr",
                           default=False,
                           action='store_true',
                           help="Use EXT_PWR_ON_N method SMC for Zephyr/Falcon/Jasper")

    argparser.add_argument("--chkstop",
                           default=False,
                           action='store_true',
                           help="Use chkstop method SMC for Zephyr/Falcon/Jasper")

    argparser.add_argument("updflash",
                           nargs='?',
                           help="Path to updflash.bin (WARNING: FILE WILL BE OVERWRITTEN)")
  
    return argparser

# FIXME: there is a bug in the Falcon SMC code that results in the board playing blind
# For now, use Jasper-on-Falcon SMCs for Falcon targets
# See https://github.com/wurthless-elektroniks/RGH1.3/issues/1
SMC_FILEPATH_MAP = {
    'xenon': os.path.join("smc", "build", "rgh13_xenon.bin"),

    'falcon_tiltsw': os.path.join("smc", "build", "rgh13_jasper_for_falcon.bin"),
    'badfalcon_tiltsw': os.path.join("smc", "build", "rgh13_badjasper_for_falcon.bin"),
    'jasper_tiltsw': os.path.join("smc", "build", "rgh13_jasper.bin"),
    'badjasper_tiltsw': os.path.join("smc", "build", "rgh13_badjasper.bin"),

    'falcon_extpwr': os.path.join("smc", "build", "rgh13_jasper_for_falcon_extpwr.bin"),
    'badfalcon_extpwr': os.path.join("smc", "build", "rgh13_badjasper_for_falcon_extpwr.bin"),
    'jasper_extpwr': os.path.join("smc", "build", "rgh13_jasper_extpwr.bin"),
    'badjasper_extpwr': os.path.join("smc", "build", "rgh13_badjasper_extpwr.bin"),

    'falcon_chkstop': os.path.join("smc", "build", "rgh13_jasper_for_falcon_chkstop.bin"),
    'badfalcon_chkstop': os.path.join("smc", "build", "rgh13_badjasper_for_falcon_chkstop.bin"),
    'jasper_chkstop': os.path.join("smc", "build", "rgh13_jasper_chkstop.bin"),
    'badjasper_chkstop': os.path.join("smc", "build", "rgh13_badjasper_chkstop.bin"),
}

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
        print("found Jasper big boy NAND")

    if nand_type == ecc.NandType.NAND_16M_JASPER:
        print("found Jasper-style 16m NAND")

    if nand_type == ecc.NandType.NAND_16M:
        print("found standard 16m NAND")

    # only inspect/modify the first chunk (1 block on big blocks)
    nand_stripped = ecc.ecc_strip(nand[0:0x021000])

    # the SMC data MUST be from 0x1000~0x4000, there's no microsoft SMC that isn't like that
    if nand_stripped[0x78:0x80] != bytes([0x00, 0x00, 0x30, 0x00, 0x00, 0x00, 0x10, 0x00]):
        print("error: SMC isn't located at 0x1000~0x4000 like it should be. something's wrong with your NAND.")
        return

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

    cbb = nand_stripped[next_cb_addr:next_cb_addr+cbb_size]

    # calc SHA hash of CB_B to determine what it really is
    # (hash runs from 0x140 through to end of CB_B)
    cbb_hash = hashlib.sha1(cbb[0x140:]).hexdigest()

    #with open("cbb_debug.bin", "wb") as f:
    #    f.write(cbb)

    smctype = ""

    # TODO: jrunner's annoying falcon-for-xenon behavior will break things here
    # especially because when it builds RGH3 images it'll build a falcon image.
    # if falcon found we probably need to force the user to specify --board xenon
    # or --board falcon
    if cbb_version == 5772 and cbb_hash == SHA1_CBB_5772_XEBUILD:
        print("found xeBuild-patched Falcon CB_B")

        # J-Runner's annoying Falcon-for-Xenon behavior forces us to do this
        if args.board is None:
            print("error: ambiguous target board. please specify --board xenon or --board falcon")
            return
        
        if args.board not in [ "xenon", "falcon" ]:
            print("error: 5772 should only be present on falcon and falcon-for-xenon builds")
            return

        smctype = args.board

    elif cbb_version == 6752 and cbb_hash == SHA1_CBB_6752_XEBUILD:
        print("found xeBuild-patched Jasper CB_B")

        if args.board is not None and args.board != "jasper":
            print("error: jasper loader used on non-jasper board. don't be silly!")
            return

        smctype = "jasper"
    else:
        print(f"error: unrecognized/unsupported CB_B version (hash was: {cbb_hash})")
        return

    if smctype in [ "zephyr", "falcon", "jasper" ]:
        build_type = [ args.tiltsw, args.extpwr, args.chkstop ]

        if True not in build_type:
            print("error: must specify one of --tiltsw OR --extpwr OR --chkstop for zephyr/falcon/jasper boards depending on your install")
            return
        
        if args.tiltsw is True:
            print("using tiltswitch smc")
            smctype += "_tiltsw"
        elif args.extpwr is True:
            print("using extpwr smc")
            smctype += "_extpwr"
        elif args.chkstop is True:
            print("using chkstop smc")
            smctype += "_chkstop"

    if args.badjasper is True:
        smctype = "bad"+smctype
        if smctype not in SMC_FILEPATH_MAP:
            print("error: no badjasper SMC build exists for that board")
            return
        
        print("badjasper mode enabled!")

    smcpath = SMC_FILEPATH_MAP[smctype]
    print(f"attempting to read SMC from: {smcpath}")

    smcdata = None
    with open(smcpath,"rb") as f:
        smcdata = f.read()

    # TODO: corona/chesty SMCs are 0x3800 bytes. this works fine for xsb/psb smcs though.
    if len(smcdata) != 0x3000:
        print("error: SMC somehow was not 0x3000 bytes. stopping.")
        return

    # inject appropriate SMC image
    smcdata_encrypted = encrypt_smc(smcdata)
    nand_stripped[0x1000:0x4000] = smcdata_encrypted
    print("injected new SMC program")

    # inject appropriate hacked CB_B
    cbb_patched = rgh13cbb_do_patches(cbb)
    nand_stripped[next_cb_addr:next_cb_addr+cbb_size] = cbb_patched
    print("patched CB_B")
    
    print("recalculating ECC data...")
    nand_stripped_ecc = ecc.ecc_encode(nand_stripped, nand_type, 0)
    nand = bytearray(nand)
    nand[0:0x021000] = nand_stripped_ecc

    print("writing final NAND...")
    with open(args.updflash, "wb") as f:
        f.write(nand)

    print("converted to RGH1.3 successfully, happy flashing")

if __name__ == '__main__':
    main()
