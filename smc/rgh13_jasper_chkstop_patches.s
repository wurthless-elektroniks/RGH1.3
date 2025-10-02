    ; patch checkstop check so it is always 0
    .org 0x0093
chkstop_patch_start:
    clr cy
    ret
chkstop_patch_end:

