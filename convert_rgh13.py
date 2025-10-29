import sys
import struct
import hashlib
import hmac
import re
from argparse import ArgumentParser,RawTextHelpFormatter
from enum import Enum
from smc import encrypt_smc
from cbbpatch import rgh13cbb_do_patches
from patcher import assemble_branch
from xebuildpatch import xebuild_apply_cb_patch, xebuild_apply_cb_patch_from_file
import ecc
import os

from rc4 import RC4

# RGH3 v1 uses the same SMC for Falcon and Jasper, likely because they're compatible
# We expect these for all phat builds
SHA1_FALCON_RGH3_27MHZ = "9b89a53dbdb4735782e92b70bb5e956f6b35da5f"
SHA1_FALCON_RGH3_10MHZ = "a4ae6a6f1ff374739d1c91f8a2881f4eecc210d3"

SHA1_CBB_4577_XEBUILD = "a67690a35bcc6284c53933fed721b56abbde312b"
SHA1_CBB_5772_XEBUILD = "3a8fb9580ce01cf1c0e2d885e0fd96a05571643f"
SHA1_CBB_6752_XEBUILD = "899cd01e00ef7b27ceb010dde42e4d6e9c871330"
SHA1_CBB_7378_ELPISS  = "9110a599e8f566e16635affeef4aeadf3c80efd5"

def _parse_cpukey(cpu_key):
    CPUKEY_EXP = re.compile(r"^[0-9a-fA-F]{32}$")
    if CPUKEY_EXP.match(cpu_key) is None:
        raise RuntimeError("error: invalid CPU key format")
    return bytes.fromhex(cpu_key)

def _init_argparser():
    argparser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                               prog='convert_rgh13',
                               description='Converts RGH1.2 or RGH3 NAND to RGH1.3/EXT+3')
    
    argparser.add_argument("--board",
                           help="Specifies target board (xenon, elpis, zephyr, falcon, jasper). Required for some CB_B versions.")

    argparser.add_argument("--cpukey",
                           type=_parse_cpukey,
                           help="Specify CPU key (required for Glitch2 images or to run older kernels)")
    
    argparser.add_argument("--keep-cb",
                           default=False,
                           action='store_true',
                           help="Do not replace CB_B in image (e.g. for Xenon and Elpis)")

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
    'zephyr_tiltsw': os.path.join("smc", "build", "rgh13_jasper_for_falcon.bin"),
    'badzephyr_tiltsw': os.path.join("smc", "build", "rgh13_badjasper_for_falcon.bin"),
    'jasper_tiltsw': os.path.join("smc", "build", "rgh13_jasper.bin"),
    'badjasper_tiltsw': os.path.join("smc", "build", "rgh13_badjasper.bin"),

    'falcon_extpwr': os.path.join("smc", "build", "rgh13_jasper_for_falcon_extpwr.bin"),
    'badfalcon_extpwr': os.path.join("smc", "build", "rgh13_badjasper_for_falcon_extpwr.bin"),
    'zephyr_extpwr': os.path.join("smc", "build", "rgh13_jasper_for_falcon_extpwr.bin"),
    'badzephyr_extpwr': os.path.join("smc", "build", "rgh13_badjasper_for_falcon_extpwr.bin"),
    'jasper_extpwr': os.path.join("smc", "build", "rgh13_jasper_extpwr.bin"),
    'badjasper_extpwr': os.path.join("smc", "build", "rgh13_badjasper_extpwr.bin"),

    'falcon_chkstop': os.path.join("smc", "build", "rgh13_jasper_for_falcon_chkstop.bin"),
    'badfalcon_chkstop': os.path.join("smc", "build", "rgh13_badjasper_for_falcon_chkstop.bin"),
    'zephyr_chkstop': os.path.join("smc", "build", "rgh13_jasper_for_falcon_chkstop.bin"),
    'badzephyr_chkstop': os.path.join("smc", "build", "rgh13_badjasper_for_falcon_chkstop.bin"),
    'jasper_chkstop': os.path.join("smc", "build", "rgh13_jasper_chkstop.bin"),
    'badjasper_chkstop': os.path.join("smc", "build", "rgh13_badjasper_chkstop.bin"),

    'xenon_1wire':  os.path.join("smc", "build", "rgh13_xenon_1wire.bin"),
    'falcon_1wire': os.path.join("smc", "build", "rgh13_jasper_for_falcon_1wire.bin"),
    'zephyr_1wire': os.path.join("smc", "build", "rgh13_jasper_for_falcon_1wire.bin"),
    'jasper_1wire': os.path.join("smc", "build", "rgh13_jasper_1wire.bin"),
    'badfalcon_1wire': os.path.join("smc", "build", "rgh13_badjasper_for_falcon_1wire.bin"),
    'badzephyr_1wire': os.path.join("smc", "build", "rgh13_badjasper_for_falcon_1wire.bin"),
    'badjasper_1wire': os.path.join("smc", "build", "rgh13_badjasper_1wire.bin"),

    'xenon_0wire':  os.path.join("smc", "build", "rgh13_xenon_0wire.bin"),
    'falcon_0wire': os.path.join("smc", "build", "rgh13_jasper_for_falcon_0wire.bin"),
    'zephyr_0wire': os.path.join("smc", "build", "rgh13_jasper_for_falcon_0wire.bin"),
    'jasper_0wire': os.path.join("smc", "build", "rgh13_jasper_0wire.bin"),
    'badfalcon_0wire': os.path.join("smc", "build", "rgh13_badjasper_for_falcon_0wire.bin"),
    'badzephyr_0wire': os.path.join("smc", "build", "rgh13_badjasper_for_falcon_0wire.bin"),
    'badjasper_0wire': os.path.join("smc", "build", "rgh13_badjasper_0wire.bin"),
}

def encrypt_cba(cba, rnd = "CB_ACB_ACB_ACB_A"):
    key_1BL = b"\xDD\x88\xAD\x0C\x9E\xD6\x69\xE7\xB5\x67\x94\xFB\x68\x56\x3E\xFA"
    key = hmac.new(key_1BL, rnd, hashlib.sha1).digest()[0:0x10]
    return (key, cba[0:0x10] + rnd + RC4(key).crypt(cba[0x20:]))

decrypt_cba = encrypt_cba

def encrypt_cbb(cbb, cba_key, rnd=b"CB_BCB_BCB_BCB_B", cpu_key=b"\x00"*16):
    key = hmac.new(cba_key, rnd + cpu_key, hashlib.sha1).digest()[0:0x10]
    return (key, cbb[0:0x10] + rnd + RC4(key).crypt(cbb[0x20:]))

decrypt_cbb = encrypt_cbb

def _load_and_patch_cb(cb_prefix: str) -> bytes:
    cb = None
    with open(os.path.join("cbb", f"{cb}_clean.bin"),"rb") as f:
        cb = f.read()
    patch = None
    with open(os.path.join("xebuild", f"{cb}_xebuild.bin"), "rb") as f:
        patch = f.read()

    return xebuild_apply_cb_patch(cb, patch)

def _extract_loaders(nand_stripped: bytes) -> dict:
    pos = 0x8000
    result = {}

    while True:
        loader_type_raw = nand_stripped[pos+0x01]
        loader_size = struct.unpack(">I", nand_stripped[pos+0x0C:pos+0x010])[0]

        # pad CE to nearest 16th byte boundary
        if (loader_size & 0x0F) != 0:
            if loader_type_raw != 0x45:
                raise RuntimeError("non-CE loader not 16-byte aligned")
            loader_size = (loader_size + 0x10) & 0xFFFFFFF0

        loader      = nand_stripped[pos:pos+loader_size]

        if loader_type_raw == 0x42:
            if loader_size == 0x400 and 'cbx' not in result:
                result['cbx'] = loader
            elif 'cba' not in result:
                result['cba'] = loader
            elif 'cbb' not in result:
                result['cbb'] = loader
            else:
                raise RuntimeError("unrecognized CB found in bootloader chain")
        elif loader_type_raw == 0x44:
            if 'cd' in result:
                raise RuntimeError("found more than one CD")
            result['cd'] = loader
        elif loader_type_raw == 0x45:
            result['ce'] = loader

            # xeBuild leaves empty space between CE and XeLL
            return result
        else:
            print(f"unrecognized loader type encountered: 0x{loader_type_raw:02x}")
        pos += loader_size

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
    
    if nand_type == ecc.NandType.NAND_64M:
        print("found Jasper big boy NAND")

    if nand_type == ecc.NandType.NAND_16M_JASPER:
        print("found Jasper-style 16m NAND")

    if nand_type == ecc.NandType.NAND_16M:
        print("found standard 16m NAND")

    nand_stripped = ecc.ecc_strip(nand[0:0x021000 * 4])

    # the SMC data MUST be from 0x1000~0x4000 (slims are not supported right now)
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

    # detect XeLL position
    xell_pos = None
    xell_signature = bytes([0x48, 0x00, 0x00, 0x20, 0x48, 0x00, 0x00, 0xEC,
                            0x48, 0x00, 0x00, 0x00, 0x48, 0x00, 0x00, 0x00,
                            0x48, 0x00, 0x00, 0x00, 0x48, 0x00, 0x00, 0x00,
                            0x48, 0x00, 0x00, 0x00, 0x48, 0x00, 0x00, 0x00])

    if nand_stripped[0x070000:0x070000+len(xell_signature)] == xell_signature:
        xell_pos = 0x070000
    elif nand_stripped[0x73800:0x73800+len(xell_signature)] == xell_signature:
        xell_pos = 0x73800

    if xell_pos is None:
        print("error: cannot find XeLL - might not be a valid glitch2/glitch3 image")
        return
    
    max_loaderspace_size = xell_pos-0x8000
    print(f"XeLL found at 0x{xell_pos:03x}. estimated bootloader space is {max_loaderspace_size} byte(s)")
    
    loaders = _extract_loaders(nand_stripped)

    imagetype = None
    if 'cbx' in loaders:
        print("found glitch3/RGH3 image")
        imagetype = 3
    elif 'cbb' in loaders:
        if args.cpukey is None:
            print("error: glitch2 image detected - you must specify CPU key")
            return
        print("found glitch2/RGH1.2 image")
        imagetype = 2
    else:
        print("error: unrecognized image type. stopping.")
        return

    cba_seed = loaders['cba'][0x10:0x20]
    cba_key, _ = decrypt_cba(loaders['cba'], rnd=cba_seed)
    if imagetype == 2:
        cbb_key, cbb = decrypt_cbb(loaders['cbb'], cba_key, loaders['cbb'][0x10:0x20], cpu_key=args.cpukey)

        # put proper decryption key in place or else CD will not decrypt correctly
        cbb[0x10:0x20] = cbb_key
    else:
        cbb = loaders['cbb']     # Glitch3 already has that in plaintext

    cbb_version = struct.unpack(">H",cbb[2:4])[0]
    cbb_size = struct.unpack(">I", cbb[0x0C:0x10])[0]

    # calc SHA hash of CB_B to determine what it really is
    # (hash runs from 0x140 through to end of CB_B)
    cbb_hash = hashlib.sha1(cbb[0x140:]).hexdigest()

    smctype = ""

    if cbb_version == 4577 and cbb_hash == SHA1_CBB_4577_XEBUILD:
        print("found xeBuild-patched Zephyr CB_B")
        smctype = "zephyr"  
    elif cbb_version == 5772 and cbb_hash == SHA1_CBB_5772_XEBUILD:
        print("found xeBuild-patched Falcon CB_B")

        # J-Runner's annoying Falcon-for-Xenon behavior forces us to do this
        if args.board is None:
            print("error: ambiguous target board. please specify --board xenon, --board elpis, --board falcon, --board zephyr")
            return
        
        if args.board not in [ "xenon", "falcon", "elpis", "zephyr" ]:
            print("error: 5772 should only be present on falcon and falcon-for-xenon builds")
            return

        # xenon/elpis are the same SMC type
        smctype = args.board if args.board != "elpis" else "xenon"

    elif cbb_version == 6752 and cbb_hash == SHA1_CBB_6752_XEBUILD:
        print("found xeBuild-patched Jasper CB_B")

        if args.board is not None and args.board != "jasper":
            print("error: jasper loader used on non-jasper board. don't be silly!")
            return

        smctype = "jasper"

    elif cbb_version == 7378 and cbb_hash == SHA1_CBB_7378_ELPISS:
        print("found elpiss hacked 7378 CB_B")
        smctype = "xenon"
    else:
        print(f"error: unrecognized/unsupported CB_B version (hash was: {cbb_hash})")
        print("possible issues: image already patched, CB_B unsupported, invalid CPU key")
        return

    if args.onewire:
        smctype += "_1wire"
    elif args.zerowire:
        smctype += "_0wire"
    elif smctype in [ "zephyr", "falcon", "jasper" ]:
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

    new_loader_buffer = bytearray([])


    # replace whatever CB_A is there with the 9188 MFG image
    new_cba = None
    cba_file = "cba_9188_mfg.bin" if args.cpukey is None else "cba_5772.bin"
    with open(os.path.join("cba", cba_file), "rb") as f:
        new_cba = f.read()
    print(f"loaded CB_A from file: {cba_file}")
    
    cba_key, cba_encrypted = encrypt_cba(new_cba, rnd=b"15432 py builder")
    new_loader_buffer += cba_encrypted

    # drop CB_Y into place
    new_cbx = None
    cbx_file = "cby.bin" if args.zerowire or args.onewire else "cbx_xell.bin"
    with open(os.path.join("cbx", cbx_file), "rb") as f:
        new_cbx = f.read()
    
    if len(new_cbx) != 0x400:
        print("error: CB_X/CB_Y was not 0x400 bytes")

    cbx_seed = bytes([0]*16)

    if cbx_file == "cbx_xell.bin":
        new_cbx = bytearray(new_cbx)
        new_cbx[0x3C0:0x3C4] = bytes([0x7F, 0xE4, 0xFB, 0x78]) # mov r4,r31 (avoid r31 being trashed by cbb_jump)
        new_cbx, _ = assemble_branch(new_cbx, 0x3C4, 0x478) # jump to CB_A cbb_jump function

    print(f"loaded CB_X/CB_Y from file: {cbx_file}")

    if args.cpukey is None:
        _, cby_encrypted = encrypt_cbb(new_cbx, cba_key, rnd=cbx_seed)
    else:
        _, cby_encrypted = encrypt_cbb(new_cbx, cba_key, rnd=cbx_seed, cpu_key=args.cpukey)

    new_loader_buffer += cby_encrypted

    # backup params now in case they get replaced
    cbb_params = cbb[0x10:0x40]

    if args.keep_cb is False:
        '''
        if cbb_version == 5772 and args.board == "xenon":
            print("replacing xeBuild 5772 CB_B with 1940")
            cbb = _load_and_patch_cb("cb_1940")
        '''

        if cbb_version == 5772 and args.board == "elpis":
            print("replacing xeBuild 5772 CB_B with 7378")
            cbb = _load_and_patch_cb("cbb_7378")
            cbb_version = 7378
        elif cbb_version == 5772 and args.board == "zephyr":
            print("replacing xeBuild 5772 CB_B with 4577")
            cbb = _load_and_patch_cb("cbb_4577")
            cbb_version = 4577
    
    # inject appropriate hacked CB_B
    cbb_patched = rgh13cbb_do_patches(cbb, use_smc_ipc=args.onewire or args.zerowire)

    # restore parameters if the CB_B was replaced
    cbb_patched[0x10:0x40] = cbb_params

    # FIXME: this is a hack to get around a panic in CB_B.
    # the best way to do this is to recalculate whatever value here so that the check passes.
    # for now, though, this works, so we can live with this hack.
    cbb_patched = xebuild_apply_cb_patch_from_file(cbb_patched,
                                                   os.path.join("patches",  f"cbb_{cbb_version}_nosmcsum.bin"))
    
    if args.fast5050 or args.veryfast5050:
        patchfile = os.path.join("patches",  f"cbb_{cbb_version}_{'very' if args.veryfast5050 else ''}fast5050.bin")
        if os.path.exists(patchfile):
            cbb_patched = xebuild_apply_cb_patch_from_file(cbb_patched, patchfile)
        
    new_loader_buffer += cbb_patched
    new_loader_buffer += loaders['cd']
    new_loader_buffer += loaders['ce']

    if len(new_loader_buffer) > max_loaderspace_size:
        print(f"error: maximum bootloader size exceeded. maximum was {max_loaderspace_size}, got {len(new_loader_buffer)}")
        return
    zeropad_size = max_loaderspace_size-len(new_loader_buffer)
    print(f"built new loader space successfully. total was {len(new_loader_buffer)}, with {zeropad_size} byte(s) to spare")
    new_loader_buffer += bytes([0] * zeropad_size)

    nand_stripped[0x8000:0x8000+len(new_loader_buffer)] = new_loader_buffer
    print("injected patched loader chain successfully!")

    print("recalculating ECC data...")
    nand_stripped_ecc = ecc.ecc_encode(nand_stripped, nand_type, 0)
    nand = bytearray(nand)
    nand[0:len(nand_stripped_ecc)] = nand_stripped_ecc

    print("writing final NAND...")
    with open(args.updflash, "wb") as f:
        f.write(nand)

    print("converted to RGH1.3 successfully, happy flashing")

if __name__ == '__main__':
    main()
