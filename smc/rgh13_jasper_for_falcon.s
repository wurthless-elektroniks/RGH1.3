;
; Use Jasper SMC on Falcon
; 
; This is a nasty hack to get around SMC issues on Falcon that result in the board playing blind.
; RGH3 v1 uses a similar solution in that it uses the same SMC code between boards.
;

    JASPER_FOR_FALCON equ 1

    .include "rgh13_jasper.s"
    .end
