
    ; patch tilt switch routine so it always returns 0
    .org 0x25FC
tiltsw_nullify_start:
    clr cy
    ret
tiltsw_nullify_end: