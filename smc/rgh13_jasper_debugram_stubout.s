
    .org 0x244F
ipc_debugram_write_patch_start:
    nop    ; change mov @r0,a to a nop so writes do nothing
ipc_debugram_write_patch_end:

    .org 0x246F
ipc_debugram_read_patch_start:
    clr a  ; change mov a,@r0 to clr a so reads always return 0
ipc_debugram_read_patch_end: