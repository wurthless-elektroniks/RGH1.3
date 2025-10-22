import sys
import struct
import hashlib
import hmac
from argparse import ArgumentParser,RawTextHelpFormatter
from enum import Enum
from smc import encrypt_smc
from cbbpatch import rgh13cbb_do_patches
from patcher import assemble_branch
import ecc
import os

from rc4 import RC4

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

    argparser.add_argument("--fast5050",
                           default=False,
                           action='store_true',
                           help="Enable fast SDRAM training patch for supported CB_Bs (boots Falcons faster)")
    
    argparser.add_argument("--veryfast5050",
                           default=False,
                           action='store_true',
                           help="Enable very fast SDRAM training patch for supported CB_Bs (might be unstable)")
    
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

    argparser.add_argument("--onewire",
                           default=False,
                           action='store_true',
                           help="Use one-wire POST method")


    argparser.add_argument("--zerowire",
                           default=False,
                           action='store_true',
                           help="Use zero-wire POST method")
    
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

    'falcon_1wire': os.path.join("smc", "build", "rgh13_jasper_for_falcon_1wire.bin"),
    'jasper_1wire': os.path.join("smc", "build", "rgh13_jasper_1wire.bin"),

    'falcon_0wire': os.path.join("smc", "build", "rgh13_jasper_for_falcon_0wire.bin"),
    'jasper_0wire': os.path.join("smc", "build", "rgh13_jasper_0wire.bin"),

    'badfalcon_0wire': os.path.join("smc", "build", "rgh13_badjasper_for_falcon_0wire.bin"),
    'badjasper_0wire': os.path.join("smc", "build", "rgh13_badjasper_0wire.bin"),
}

def encrypt_cba(cba, rnd = "CB_ACB_ACB_ACB_A"):
    key_1BL = b"\xDD\x88\xAD\x0C\x9E\xD6\x69\xE7\xB5\x67\x94\xFB\x68\x56\x3E\xFA"
    key = hmac.new(key_1BL, rnd, hashlib.sha1).digest()[0:0x10]
    return (key, cba[0:0x10] + rnd + RC4(key).crypt(cba[0x20:]))

def encrypt_cbb(cbb, cba_key, rnd=b"CB_BCB_BCB_BCB_B", cpu_key=b"\x00"*16):
    key = hmac.new(cba_key, rnd + cpu_key, hashlib.sha1).digest()[0:0x10]
    return cbb[0:0x10] + rnd + RC4(key).crypt(cbb[0x20:])


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
    cba_addr = 0x8000
    cba_size = struct.unpack(">I", nand_stripped[0x800C:0x8010])[0]
    next_cb_addr = cba_addr+cba_size
    if nand_stripped[next_cb_addr:next_cb_addr+4] != bytes([0x43, 0x42, 0x3C, 0x48]):
        print("error: not a RGH3 image - CB_X did not follow CB_A")
        return

    print("image looks like RGH3 or glitch3, checking CB_B")

    # advance to next CB stage
    cbx_size = struct.unpack(">I", nand_stripped[next_cb_addr+0x0C:next_cb_addr+0x10])[0]
    cbx_seed = nand_stripped[next_cb_addr+0x10:next_cb_addr+0x20]
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

    if args.onewire:
        smctype += "_1wire"
    elif args.zerowire:
        smctype += "_0wire"
    elif smctype in [ "zephyr", "falcon", "jasper" ]:
        build_type = [ args.tiltsw, args.extpwr, args.chkstop, ]

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

    # replace whatever CB_A is there with the 9188 MFG image
    new_cba = None
    with open(os.path.join("cba", "cba_9188_mfg.bin"), "rb") as f:
        new_cba = f.read()
    if len(new_cba) > cba_size:
        print("error: replacement CB_A somehow larger than the original")
        return

    padding_bytes_required = cba_size - len(new_cba)
    print(f"CB_B will be padded by {padding_bytes_required} byte(s)")

    hmac_seed = nand_stripped[cba_addr+0x10:cba_addr+0x20]
    cba_key, cba_encrypted = encrypt_cba(new_cba, rnd=hmac_seed)

    cb_inject_pos = 0x8000
    nand_stripped[cb_inject_pos:cb_inject_pos+len(cba_encrypted)] = cba_encrypted
    cb_inject_pos += len(cba_encrypted)

    print("injected CB_A 9188 MFG")

    # drop CB_Y into place
    new_cbx = None
    cbx_file = "cby.bin" if args.zerowire or args.onewire else "cbx_xell.bin"
    with open(os.path.join("cbx", cbx_file), "rb") as f:
        new_cbx = f.read()
    
    if len(new_cbx) != 0x400:
        print("error: CB_X/CB_Y was not 0x400 bytes")

    if cbx_file == "cbx_xell.bin":
        new_cbx[0x3C0:0x3C4] = bytes([0x7F, 0xE4, 0xFB, 0x78]) # mov r4,r31 (avoid r31 being trashed by cbb_jump)
        new_cbx, _ = assemble_branch(new_cbx, 0x3C4, 0x478) # jump to CB_A cbb_jump function

    cby_encrypted = encrypt_cbb(new_cbx, cba_key, rnd=cbx_seed)

    nand_stripped[cb_inject_pos:cb_inject_pos+len(cby_encrypted)] = cby_encrypted
    cb_inject_pos += len(cby_encrypted)
    print("injected CB_X/CB_Y")

    # inject appropriate hacked CB_B
    cbb_patched = rgh13cbb_do_patches(cbb, use_smc_ipc=args.onewire)

    # FIXME: this is a hack to get around a panic in CB_B.
    # the best way to do this is to recalculate whatever value here so that the check passes.
    # for now, though, this works, so we can live with this hack.
    if cbb[0x6B2C:0x6B30] == bytes([0x40, 0x9A, 0x00, 0x14]):
        print("CB_B 5772: skipping SMC HMAC panic")
        cbb, _ = assemble_branch(cbb, 0x6B2C, 0x6B40)
    elif cbb[0x6B74:0x6B78] == bytes([0x40, 0x9A, 0x00, 0x14]):
        print("CB_B 6752: skipping SMC HMAC panic")
        cbb, _ = assemble_branch(cbb, 0x6B74, 0x6B88)
    else:
        print("WARNING: can't apply SMC checksum disable patch...")

    if args.fast5050 or args.veryfast5050:
        training_step_default = bytes([0x01, 0x01, 0x01, 0x01])
        training_step_fast    = bytes([0x10, 0x10, 0x10, 0x10]) if args.veryfast5050 else bytes([0x04, 0x04, 0x04, 0x04])
        if cbb_patched[0x46B0:0x46B4] == training_step_default and \
            cbb_patched[0x4A2C:0x4A30] == training_step_default:
            
            cbb_patched[0x46B0:0x46B4] = training_step_fast
            cbb_patched[0x4A2C:0x4A30] = training_step_fast
            print("fast5050: applied 5772 patches")
        elif cbb_patched[0x4e54:0x4e58] == training_step_default and \
            cbb_patched[0x51d0:0x51d4] == training_step_default:
            
            cbb_patched[0x4e54:0x4e58] = training_step_fast
            cbb_patched[0x51d0:0x51d4] = training_step_fast
            print("fast5050: applied 6752 patches")
        else:
            print("fast5050: CB_B unrecognized, no patches applied.")
        
    cbb_patched += bytes([0x00 * padding_bytes_required])
    cbb_patched[0x000C:0x0010] = struct.pack(">I", cbb_size + padding_bytes_required)

    nand_stripped[cb_inject_pos:cb_inject_pos+len(cbb_patched)] = cbb_patched
    print("patched and padded CB_B")
    
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
