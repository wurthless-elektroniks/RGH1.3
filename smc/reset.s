;
; Common reset handling code
;


;
; hook arrives from normal reset watchdog code and indicates that
; a RRoD error case happened, so raise it immediately instead of
; doing five tries then giving up
;
on_reset_watchdog_error_case:
    acall on_reset_watchdog_timeout
    ljmp msftsmc_sysreset_watchdog_raise_rrod_and_give_up

;
; all custom code goes through here to reset if we're resetting via the watchdog
;
reset_via_watchdog:
    acall on_reset_watchdog_timeout
    ljmp msftsmc_sysreset_watchdog_request_reset

;
; common code path between the two that turns off our custom statemachines
;
on_reset_watchdog_timeout:
    ; assert /CPU_RST_N now so POST bits drop to 0
    ; if we don't do this then our POST bit check will fail and we'll get a RRoD
    clr gpio_cpu_rst_n

    ; turn off statemachines that might be running
    acall _led_lightshow_sm_go_idle
    sjmp  _turboreset_sm_disarm
