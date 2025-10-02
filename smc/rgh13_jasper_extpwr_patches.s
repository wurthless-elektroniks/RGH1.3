    ; for ext_pwr_on: change jb checking poweron line to ljmp
    ; falcon = 0x151, jasper is also 0x151
    .org 0x0151
extpwron_skip_jb_check_start:
    ljmp 0x0156
extpwron_skip_jb_check_end:


    ; extpwr builds: patch ext_pwr_on_n read routine so it always returns 0
    ; jasper = 0x2626, falcon = 0x25D4
    .org 0x2626
extpwron_nullify_start:
    clr cy
    ret
extpwron_nullify_end:
