'''
Bulk SMC makescript
'''

import struct
import platform
import os
import subprocess

def find_c51asm() -> str | None:
    if platform.system() == "Darwin": # =macos
        return os.path.join("bin", "c51asm_darwin")

    if platform.system() == "Windows":
        return os.path.join("bin", "c51asm.exe")

    raise RuntimeError("your platform isn't supported yet (sorry, linux havers)")

def apply_overlay(clean_smc: bytes, smc_overlay: bytes) -> bytes | None:
    # check for 0x90 as first byte in overlay
    if smc_overlay[0] != 0x90:
        print("first byte of overlay not 0x90")
        return None

    # read overlays. they are two instructions back to back.
    # and keep reading until 0x00 is encountered.
    overlay_parse_pos = 0

    patched_smc = bytearray(clean_smc)

    while True:
        if smc_overlay[overlay_parse_pos+0] == 0:
            break

        if smc_overlay[overlay_parse_pos+0] != 0x90 or smc_overlay[overlay_parse_pos+3] != 0x90:
            print(f"overlay header is invalid at offset {overlay_parse_pos:04x}")

        # there's not much error handling here, so be careful with how you assemble things
        patch_start_address = struct.unpack(">H", smc_overlay[overlay_parse_pos+1:overlay_parse_pos+3])[0]
        patch_end_address   = struct.unpack(">H", smc_overlay[overlay_parse_pos+4:overlay_parse_pos+6])[0]

        # 0x2FC0 onward means patch is too big
        if patch_end_address >= 0x2FC0:
            raise RuntimeError("patch is too big. size optimize your shit please")

        patched_smc[patch_start_address:patch_end_address] = smc_overlay[patch_start_address:patch_end_address]

        print(f"\t- patched {patch_start_address:04x}~{patch_end_address:04x}")

        overlay_parse_pos += 6

    return patched_smc

def load_or_die(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def make_patched_smc(c51asm_path:    str,
                     clean_smc_path: str,
                     asm_path:       str,
                     overlay_path:   str,
                     output_path:    str,
                     additional_args: list | None):
    

    args=[
            '',
            asm_path,
            '-fB'            
    ]

    if additional_args is not None:
        args += additional_args

    args.append('-o')
    args.append(overlay_path)

    # run c51asm to assemble the overlay
    result = subprocess.call(
        executable=c51asm_path,
        args=args
    )
    if result != 0:
        raise RuntimeError("c51asm FAILED.")

    clean_smc   = load_or_die(clean_smc_path)
    smc_overlay = load_or_die(overlay_path)
    patched_smc = apply_overlay(clean_smc, smc_overlay)

    with open(output_path, "wb") as f:
        f.write(patched_smc)


def _permutate_jasper_targets(gpio_name: str, base_args: list):
    target_templates = {
        'rgh13_jasper': {
            "additional_args": []
        },
        'rgh13_badjasper': {
            "additional_args": [
                '-D','HARD_RESET_ON_CBA_FAIL=1'
            ]
        },
        'rgh13_jasper_for_falcon': {
            "additional_args": [
                '-D','JASPER_FOR_FALCON=1'
            ]
        },
        'rgh13_badjasper_for_falcon': {
            "additional_args": [
                '-D','JASPER_FOR_FALCON=1',
                '-D','HARD_RESET_ON_CBA_FAIL=1'
            ]
        },
        'rgh13_jasper_for_zephyr': {
            "additional_args": [
                '-D','JASPER_FOR_FALCON=1',
                '-D','ZEPHYR=1'
            ]
        },
        'rgh13_badjasper_for_zephyr': {
            "additional_args": [
                '-D','JASPER_FOR_FALCON=1',
                '-D','HARD_RESET_ON_CBA_FAIL=1',
                '-D','ZEPHYR=1'
            ]
        }
    }

    asm_name = "rgh13_jasper.s" if gpio_name not in [ '0wire', '1wire' ] else f"rgh13_{gpio_name}_jasper.s"
    targets = {}
    for target_name,target_params in target_templates.items():
        overlay_name = f"{target_name}_{gpio_name}_overlay.bin" if gpio_name != "tiltsw" else f"{target_name}_overlay.bin"
        output_name = f"{target_name}_{gpio_name}.bin" if gpio_name != "tiltsw" else f"{target_name}.bin"
        
        targets[f"{target_name}_{gpio_name}"] = {
            "clean_smc_name": "jasper_clean.bin",          
            "asm_name": asm_name,
            "overlay_name": overlay_name,
            "output": output_name,
            "additional_args": target_params["additional_args"] + base_args
        }

    return targets


SMC_TARGETS = {
    "xenon": {
        "clean_smc_name": "xenon_clean.bin",
        "asm_name": "rgh13_xenon.s",
        "overlay_name": "rgh13_xenon_overlay.bin",
        "output": "rgh13_xenon.bin"
    },

    "xenon_1wire": {
        "clean_smc_name": "xenon_clean.bin",
        "asm_name": "rgh13_1wire_xenon.s",
        "overlay_name": "rgh13_xenon_1wire_overlay.bin",
        "output": "rgh13_xenon_1wire.bin"
    },

    "xenon_0wire": {
        "clean_smc_name": "xenon_clean.bin",
        "asm_name": "rgh13_0wire_xenon.s",
        "overlay_name": "rgh13_xenon_0wire_overlay.bin",
        "output": "rgh13_xenon_0wire.bin"
    },

}

SMC_TARGETS.update(_permutate_jasper_targets("tiltsw",['-D','POST7_TILTSW=1']))
SMC_TARGETS.update(_permutate_jasper_targets("extpwr",['-D','POST7_EXTPWR=1']))
SMC_TARGETS.update(_permutate_jasper_targets("chkstop",['-D','POST7_CHKSTOP=1']))
SMC_TARGETS.update(_permutate_jasper_targets("1wire",[]))
SMC_TARGETS.update(_permutate_jasper_targets("0wire",[]))


def main():
    # find c51asm - MUST be an absolute path
    print("checking for c51asm...")
    c51asm_path = os.path.join(os.getcwd(),find_c51asm())
    print(f"found c51asm at: {c51asm_path}")
    
    try:
        # cd into the smc directory if we're not there already
        # (this throws exception on failure)
        os.chdir('smc')
        
        for target, target_params in SMC_TARGETS.items():
            print(f"building target: {target}")

            clean_smc_path = target_params["clean_smc_name"]
            asm_path       = target_params["asm_name"]
            overlay_path   = os.path.join("build", target_params["overlay_name"])
            output_path    = os.path.join("build", target_params["output"])

            print(f"\tclean_smc_path = {clean_smc_path}")
            print(f"\tasm_path = {asm_path}")
            print(f"\toverlay_path = {overlay_path}")
            print(f"\toutput_path = {output_path}")
            
            additional_args = target_params["additional_args"] if "additional_args" in target_params else None

            make_patched_smc(c51asm_path, clean_smc_path, asm_path, overlay_path, output_path, additional_args)

    finally:
        pass

if __name__ == '__main__':
    main()

