; ------------------------------------------------------------------------------------
;
; Quality of life improvement: force power down if power button held 5 seconds
; (saves people the effort of unplugging their system if it freezes)
;
; ------------------------------------------------------------------------------------

holdpowerbutton_sm_exec:
    jnb gpio_psu_12v_enable,_holdpowerbutton_idle ; power must be on (active high)
    jnb gpio_powersw_n,_holdpowerbutton_held      ; and powerbutton must be held (active low)
_holdpowerbutton_idle:
    ; 250 * 20 = 5000 ms
    mov r0,#g_holdpowerbutton_counter
    mov @r0,#250
_holdpowerbutton_done:
    ret

_holdpowerbutton_held:
    ; decrement counter
    mov r0,#g_holdpowerbutton_counter
    dec @r0
    cjne @r0,#0,_holdpowerbutton_done

    ; when it hits 0, force hard reset to standby mode
    ljmp 0x0000
