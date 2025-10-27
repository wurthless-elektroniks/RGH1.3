import struct

def xebuild_apply_cb_patch(cbb_original: bytes, patch: bytes) -> bytes:
    pos = 0

    cbb = bytearray(cbb_original)

    while pos < len(patch):
        offset = struct.unpack(">I", patch[pos:pos+4])[0]
        if offset == 0xFFFFFFFF:
            break

        length_in_32_bit_words = struct.unpack(">I", patch[pos+4:pos+8])[0]
        patch_length = length_in_32_bit_words * 4
        pos += 8
        cbb[offset:offset+patch_length] = patch[pos:pos+patch_length]
        pos += patch_length

    return cbb

def xebuild_apply_cb_patch_from_file(cbb_original: bytes, patchfile: str) -> bytes:
    patch = None
    print(f"applying patch from file: {patchfile}")
    with open(patchfile, "rb") as f:
        patch = f.read()
    return xebuild_apply_cb_patch(cbb_original, patch)
