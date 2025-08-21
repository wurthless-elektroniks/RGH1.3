#
# Unified HWINIT postcounting code
#

    .text

    .org 0x0280
hwinit_postcount_code_start:
    # stubs - code in cbbpatch.py uses these instead of going to the routines directly
    b hwinit_init           # +0x00
    b hwinit_toggle_post    # +0x04
    b hwinit_delay_case     # +0x08
    b hwinit_done           # +0x0C

hwinit_init:
    mftb   %r6              # read timebase counter
    andis. %r6,%r6,0x0800   # 1 << 27 - MUST be the same between this and hwinit_toggle_post
    stw    %r6,-0xA4(%r1)   # store in safe space on stack

    # setup POST register base (0x8000020000060000)
    mfspr %r7,%lr           # need to stash LR because we're in the middle of another function call
    bl setup_postaddr_r5
    mtspr %lr,%r7

    li  %r7,0xAE         # keep POST bit 7 set so SMC can pick up on it
    cmpwi %r6,0          # if the bit we checked earlier was 0, leave as-is
    beq _hwinit_init_send_post
    ori %r7,%r7,0x40     # otherwise toggle POST bit 6
_hwinit_init_send_post:
    rldicr %r7,%r7,56,7              # r7 <<= 56
    std %r7,0x1010(%r5)              # write to POST register
    b hwinit_register_setup_function # continue to register setup function at 0x0D5C

# ------------------------------------------------------------------------------------------------

hwinit_toggle_post:
    # our hook overwrites these instructions
    cmpld %r16,%r4
    bge hwinit_done # patcher also needs to hook 0xDC4 to land there, too
    
    # scratch registers: r5, r6, r7, r8
    lwz    %r6,-0xA4(%r1)               # read last poll
    mftb   %r5                          # read timebase counter
    andis. %r7,%r5,0x0800               # check bit (1 << 27)
    cmpw   %r6,%r7                      # has the bit flipped?
    beq    hwinit_continue_interpreting # if it hasn't, continue interpreting
    
    stw   %r7,-0xA4(%r1)                # update last poll state

    # setup POST register base (0x8000020000060000)
    bl setup_postaddr_r5

    li  %r7,0xAE         # keep POST bit 7 set so SMC can pick up on it
    cmpwi %r6,0          # if the bit we checked earlier was 0, leave as-is
    beq _hwinit_toggle_post_send_post
    ori %r7,%r7,0x40     # otherwise toggle POST bit 6
_hwinit_toggle_post_send_post:
    rldicr %r7,%r7,56,7            # r7 <<= 56
    std %r7,0x1010(%r5)            # write to POST register
    b hwinit_continue_interpreting # continue interpreting

# ------------------------------------------------------------------------------------------------

hwinit_delay_case:
    # normal hwinit code
    mulli %r6,%r6,50
    mftb  %r8
    add   %r8,%r8,%r6

    # now this is where things differ
    # we exit to hwinit_toggle_post because that leads back to the main
    # interpreter loop
_hwinit_delay_loop:
    mftb %r7
    cmpld %r7,%r8
    bgt hwinit_toggle_post            # original instruction is a ble

    # now comes the custom code - DO NOT TOUCH R8
    lwz    %r6,-0xA4(%r1)             # read last poll
    andis. %r7,%r7,0x0800             # check bit (1 << 27)
    cmpw   %r6,%r7                    # has the bit flipped?
    beq _hwinit_delay_loop            # if it hasn't, keep looping
    
    stw   %r7,-0xA4(%r1)              # update last poll state

    # setup POST register base (0x8000020000060000)
    bl setup_postaddr_r5

    li  %r7,0xAE         # keep POST bit 7 set so SMC can pick up on it
    cmpwi %r6,0          # if the bit we checked earlier was 0, leave as-is
    beq _hwinit_delay_send_post
    ori %r7,%r7,0x40     # otherwise toggle POST bit 6
_hwinit_delay_send_post:
    rldicr %r7,%r7,56,7  # r7 <<= 56
    std %r7,0x1010(%r5)  # write to POST register
    b _hwinit_delay_loop # and keep running the delay

# ------------------------------------------------------------------------------------------------

hwinit_done:
    bl setup_postaddr_r5
    
    # clear POST bits 6/7
    li  %r7,0x2E
    rldicr %r7,%r7,56,7  # r7 <<= 56
    std %r7,0x1010(%r5)  # write to POST register

    # return success and go to epilogue as normal
    li %r5,1
    b hwinit_exit

setup_postaddr_r5:
    # setup POST register base (0x8000020000060000)
    lis %r5,0x8000
    ori %r5,%r5,0x0200
    rldicr %r5,%r5,32,31
    oris %r5,%r5,0x0006
    blr

hwinit_postcount_code_end:

    .org 0x09A0
hwinit_continue_interpreting:

    .org 0xD5C
hwinit_register_setup_function:

    .org 0xDD0
hwinit_exit:
