#
# Unified HWINIT postcounting code
#

    .text

    .equ BASE_POST, 0xA2

    .equ BASE_AND, 0x0100

    .org 0x0280
hwinit_postcount_code_start:
    # stubs - code in cbbpatch.py uses these instead of going to the routines directly
    b hwinit_init           # +0x00
    b hwinit_toggle_post    # +0x04
    b hwinit_delay_case     # +0x08
    b hwinit_done           # +0x0C

hwinit_init:
    mftb   %r6              # read timebase counter
    andis. %r6,%r6,BASE_AND
    std    %r6,-0xA8(%r1)   # store in safe space on stack

    # base POST must be setup always
    lis %r5,0x8000
    ori %r5,%r5,0x0200
    rldicr %r5,%r5,32,31
    oris %r5,%r5,0x0006
    li  %r7,BASE_POST
    rldicr %r7,%r7,56,7
    std %r7,0x1010(%r5)
   
    bl hwinit_register_setup_function # call normal register setup function at 0x0D5C
    
    # hook to hwinit_toggle_post might not be installed
    b hwinit_interpreter_top

# ------------------------------------------------------------------------------------------------

hwinit_toggle_post:
    # our hook overwrites these instructions
    cmpld %r16,%r4
    bge hwinit_success # go to 0xDC4 in case it isn't hooked
    
    # TODO: remove this or find alternative in case it isn't compatible with 6752.
    # if this hook is enabled, the mainloop either slows down significantly or destabilizes and crashes.
    # doing the post toggles in the delay block is enough to do post toggling on 5772.
    bl toggle_post

    b hwinit_continue_interpreting

# ------------------------------------------------------------------------------------------------

hwinit_delay_case:
    # normal hwinit code
    mulli %r6,%r6,50
    mftb  %r8
    add   %r8,%r8,%r6

_hwinit_delay_loop:
    mftb %r7
    cmpld %r7,%r8
    bgt hwinit_toggle_post            # original instruction is a ble

    bl toggle_post

    b _hwinit_delay_loop # and keep running the delay

# ------------------------------------------------------------------------------------------------

hwinit_done:
    # setup POST register base (0x8000020000060000)
    lis %r5,0x8000
    ori %r5,%r5,0x0200
    rldicr %r5,%r5,32,31
    oris %r5,%r5,0x0006
    
    # clear POST bits 6/7
    li  %r7,0x2E
    rldicr %r7,%r7,56,7  # r7 <<= 56
    std %r7,0x1010(%r5)  # write to POST register

    # return success and go to epilogue as normal
    li %r5,1
    b hwinit_exit

toggle_post:
    std %r5,-0xB0(%r1)
    std %r6,-0xB8(%r1)
    std %r7,-0xC0(%r1)
    std %r8,-0xC8(%r1)

    ld     %r6,-0xA8(%r1)               # read last poll
    mftb   %r5                          # read timebase counter
    andis. %r7,%r5,BASE_AND               # check bit (1 << 27)
    cmpld  %r6,%r7                      # has the bit flipped?
    beq    _toggle_post_exit            # if it hasn't, exit
    
    std   %r7,-0xA8(%r1)                # update last poll state

    # setup POST register base (0x8000020000060000)
    lis %r5,0x8000
    ori %r5,%r5,0x0200
    rldicr %r5,%r5,32,31
    oris %r5,%r5,0x0006

    li  %r7,BASE_POST    # keep POST bit 7 set so SMC can pick up on it
    cmpwi %r6,0          # if the bit we checked earlier was 0, leave as-is
    beq _toggle_post_send_post
    ori %r7,%r7,0x40     # otherwise toggle POST bit 6
_toggle_post_send_post:
    rldicr %r7,%r7,56,7            # r7 <<= 56
    std %r7,0x1010(%r5)            # write to POST register
_toggle_post_exit:
    ld %r5,-0xB0(%r1)
    ld %r6,-0xB8(%r1)
    ld %r7,-0xC0(%r1)
    ld %r8,-0xC8(%r1)
    blr


hwinit_postcount_code_end:

    .org 0x0998
hwinit_interpreter_top:

    .org 0x09A0
hwinit_continue_interpreting:

    .org 0xD5C
hwinit_register_setup_function:

    .org 0xDC4
hwinit_success:

    .org 0xDD0
hwinit_exit:
