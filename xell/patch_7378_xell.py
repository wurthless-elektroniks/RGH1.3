'''
(Zeropaired) patch for Elpis CB_B 7378

CB_B 9188 fails on Elpis systems with Samsung RAMs, the CPU will crash and reboot during hwinit
even if the glitch attack succeeds. The reason: CB_B simply doesn't support it.

The Elpis CB_B 7378 loader also can't be used in a glitch attack as is because it
expects a different CD than the one normally used for glitching. Also, the Glitch2
9188 loads the CD as plaintext, while 7378 has to decrypt it first. There are other
code differences here and there, but one of the more important ones is that POST codes
don't get output (typical retail CB_B behavior), which throws off glitch attempts and
provides no useful information.

This file patches 7378 so that it can load the normal unsigned CD,
and also adds POST codes back.
'''

from patcher import *

# ------------------------------------------------------------------------------------------------

def patch_entry_point(cbb_image: bytes, free_space_area: FreeSpaceArea) -> bytes:
    # 0x4E8: call to fusechecks and security engine init
    # we remove the call to fusechecks and instead use this area to POST 0x22 and 0x2F.
    # also, we move the call to init_seceng (at 0x6EE8) up a bit.
    pos = 0x4E8
    cbb_image, pos = assemble_post_call(cbb_image, pos, free_space_area.func("post"), 0x22)
    cbb_image, pos = assemble_branch_with_link(cbb_image, pos, 0x6ee8)
    cbb_image, pos = assemble_post_call(cbb_image, pos, free_space_area.func("post"), 0x2F)

    # fill NOPs until 0x500, where execution picks up again (code is about to relocate itself)
    fill_nops_between(cbb_image, pos, 0x500)

    return cbb_image

def patch_after_relocation_steps(cbb_image: bytes, free_space_area: FreeSpaceArea) -> bytes:
    '''
    Patch post-relocation steps at 0x06C0.
    '''
    post_addr = free_space_area.func("post")
    panic_fcn_address = free_space_area.func("panic")

    # create new function that POSTs 0x23, 0x2E before running hwinit_proxy (at 0x7110)
    post_23_2e_trampoline = free_space_area.head()
    pos = post_23_2e_trampoline
    # `mfspr r28,LR` - need to preserve LR or bad things happen.
    # r28 is normally used by CB_A to pass us decryption keys, now unused,
    # so we should be safe using it
    cbb_image[pos:pos+4] = bytes([0x7f, 0x88, 0x02, 0xa6])
    pos += 4
    cbb_image, pos = assemble_post_call(cbb_image, pos, post_addr, 0x23)
    cbb_image, pos = assemble_post_call(cbb_image, pos, post_addr, 0x2E)
    # `mtspr r28,LR` - restore return address to LR
    cbb_image[pos:pos+4] = bytes([0x7f, 0x88, 0x03, 0xa6])
    pos += 4
    # `or r3,r31,r31`` must be put here because calls to the POST function overwrote r3.
    cbb_image[pos:pos+4] = bytes([0x7f, 0xe3, 0xfb, 0x78])
    pos += 4
    cbb_image, pos = assemble_branch(cbb_image, pos, 0x7110)
    free_space_area.create_func_and_set_head("hwinitproxy_trampoline", pos)

    # change call at 0x6D0 to point to this rerouted function
    # instead of calling hwinit_proxy directly
    assemble_branch_with_link(cbb_image, 0x06D0, post_23_2e_trampoline)

    # 0x768 is a panic case - it's where execution ends up if RAM size is bad
    assemble_panic(cbb_image, 0x768, 0xAF, panic_fcn_address)

    return cbb_image

def patch_cd_load_and_jump(cbb_image: bytes, free_space_area: FreeSpaceArea) -> bytes:
    '''
    Patch CD load/verify/jump routine at 0x6FA8
    '''
    post_fcn_address  = free_space_area.func("post")
    panic_fcn_address = free_space_area.func("panic")

    # put POST 0x30 (VERIFY_OFFSET_4BL) at 0x7388
    # this isn't always validated, so it may be normal if you don't see 0x30 before 0x31
    cbb_image = make_post_codecave(cbb_image, free_space_area, 0x7388, 0x30)

    # 0x73a4: panic because of invalid offset (POST 0xAA)
    # build function stub in free space then put a branch at 0x73A4
    pos = free_space_area.head()
    panic_aa_stub = pos
    cbb_image, pos = assemble_panic(cbb_image, pos, 0xAA, panic_fcn_address)
    cbb_image, _ = assemble_branch(cbb_image, 0x73A4, panic_aa_stub)
    free_space_area.create_func_and_set_head("panic_aa_stub", pos)

    # create codecave so we can POST 0x31
    cbb_image = make_post_codecave(cbb_image, free_space_area, 0x73A8, 0x31)

    # put POST 0x32 at 0x73c0
    assemble_post_call(cbb_image, 0x73c0, post_fcn_address, 0x32)

    # 0x73EC: the typical "CD" exploit code has its entrypoint at 0x270,
    # which is invalid on 7378 (expects at least 0x310).
    # so let's restore 0x270 as the minimum value.
    cbb_image[0x73EE:0x73F0] = bytes([0x02, 0x70])

    # 0x7430: panic because CD header is invalid
    pos = free_space_area.head()
    panic_ab_stub = pos
    cbb_image, pos = assemble_panic(cbb_image, pos, 0xAB, panic_fcn_address)
    cbb_image, _ = assemble_branch(cbb_image, 0x7430, panic_ab_stub)
    free_space_area.create_func_and_set_head("panic_ab_stub", pos)

    # create codecave so we can POST 0x33
    cbb_image = make_post_codecave(cbb_image, free_space_area, 0x7434, 0x33)

    # at 0x745c, CD has been copied to RAM.
    # all we need to do is count POSTs 34-37,39 and then go directly to PCI init
    # because HMAC/SHA verification is no longer necessary
    pos = 0x745C
    cbb_image, pos = assemble_post_call(cbb_image, pos, post_fcn_address, 0x34)
    cbb_image, pos = assemble_post_call(cbb_image, pos, post_fcn_address, 0x35)
    cbb_image, pos = assemble_post_call(cbb_image, pos, post_fcn_address, 0x36)
    cbb_image, pos = assemble_post_call(cbb_image, pos, post_fcn_address, 0x37)
    cbb_image, pos = assemble_post_call(cbb_image, pos, post_fcn_address, 0x39)
    cbb_image, pos = assemble_post_call(cbb_image, pos, post_fcn_address, 0x3B)
    cbb_image, pos = assemble_branch_with_link(cbb_image, pos, 0x71a0) # call pci_init
    cbb_image, pos = assemble_branch(cbb_image, pos, 0x75cc) # return to code below

    # 0x75cc - 0x762c follows pci_init and is useless for our purposes.
    # it's useful if you're calling a normal CD, but we're calling the exploit
    # payload instead, so it's gotta go.
    # so let's skip directly to 0x762C, where we'll put POST 0x3A.
    # (we won't be using r5/r6 when patching cd_jump.)
    cbb_image, _ = assemble_branch(cbb_image, 0x75CC, 0x762C)
    cbb_image, _ = assemble_post_call(cbb_image, 0x762C, post_fcn_address, 0x3A)

    return cbb_image

def patch_cd_jump(cbb_image: bytes):
    # 0xE20 is cd_jump
    # inputs are:
    # r3 - entry point, gets futzed about and ends up in CMPE
    # r4 - gets moved to r31
    # r5 - does something, useless
    # r6 - jump target, goes into LR
    #
    # on 9188:
    # r3 - entry point
    # r4 - gets moved to r31
    #
    # so this is basically obfuscated/fucked around with.

    # assemble 9188 preamble
    cdjump_9188_preamble = [
        0x54, 0x63, 0x04, 0x3e, # rlwinm 3,r3,0x0,0x10,0x1f
        0x3c, 0x63, 0x04, 0x00, # addis r3,r3,0x400
        0x7c, 0x68, 0x03, 0xa6, # mtspr LR,r3
        0x7c, 0x9f, 0x23, 0x78, # or r31,r4,r4
    ]

    # cd_jump identical past 0xE54, so we'll land there
    cdjump_preamble_inject_end_point = 0xE54
    cdjump_preamble_inject_point = cdjump_preamble_inject_end_point - len(cdjump_9188_preamble)
    cbb_image[cdjump_preamble_inject_point:cdjump_preamble_inject_end_point] = cdjump_9188_preamble

    # add immediate branch at 0xE20 to skip past now-useless opcodes
    assemble_branch(cbb_image, 0xE20, cdjump_preamble_inject_point)

def patch_exception_handler(cbb_image: bytes):
    # basically duplicates the "unexpected IRQ" handler, but with POST code 0x81 ("machine check").
    #
    # do NOT use this exception handler with xeBuild!
    # the kernel expects it to have been left alone.
    # if you try, it'll halt at startup and not boot at all!
    new_exception_handler = [
        0x38, 0x60, 0x00, 0x81, # li r3, 0x81 - this is our POST code
        0x78, 0x63, 0xc1, 0xc6, # rldicr r3,r3,0x38,0x7
        0x38, 0x80, 0x02, 0x00, # li r4,0x200
        0x64, 0x84, 0x80, 0x00, # oris r4,r4,0x8000
        0x78, 0x84, 0x07, 0xc6, # rldicr r4,r4,0x20,0x1f
        0x64, 0x84, 0x00, 0x06, # oris r4,r4,r6
        0xf8, 0x64, 0x10, 0x10, # std r3,(r4)
        0x38, 0x00, 0x00, 0x00, # li r0,0x00
        0x7c, 0x18, 0x23, 0xa6, # mtspr CMPE,r0
        0x4b, 0xff, 0xff, 0xf8, # b -8
    ]

    cbb_image[0x780:0x780+len(new_exception_handler)] = new_exception_handler

def xell7378_do_patches(cbb_image: bytes) -> bytes:

    cbb_image = bytearray(cbb_image)

    # first thing:
    # 0x4f8 calls a big function that's patched out on CB_B 9188, and it's responsible for
    # doing fusechecks and other undesirable stuff. so NOP that out
    assemble_nop(cbb_image, 0x4f8)

    # 0x4f8 called 0x6b58, which is no longer used.
    # create our free space area and put two important functions (post and panic) there.
    # we'll continue creating stubs in this free space area for other patches later on.
    free_space_area = FreeSpaceArea(0x6B58, 0x6EE4)
    head = free_space_area.head()
    post_fcn_address = head
    cbb_image, head = assemble_post_function(cbb_image, head)
    free_space_area.create_func_and_set_head("post", head)
    cbb_image, head = assemble_panic_function(cbb_image, head, post_fcn_address)
    free_space_area.create_func_and_set_head("panic", head)

    # now let's patch some functions
    patch_entry_point(cbb_image, free_space_area)
    patch_after_relocation_steps(cbb_image, free_space_area)
    patch_exception_handler(cbb_image)
    patch_cd_load_and_jump(cbb_image, free_space_area)
    patch_cd_jump(cbb_image)

    # vanity string at end of free space
    vanity_string = b"wurthless elektroniks presents elpiss v2\x00"
    head = free_space_area.head()
    cbb_image[head:head+len(vanity_string)] = vanity_string

    return cbb_image
