; ------------------------------------------------------------------------------------
;
; Ring of light bootanim watchdog
; Reboots system if the bootanim isn't received in time
;
; ------------------------------------------------------------------------------------

    ; we land in here once the main reset watchdog finishes execution
on_reset_watchdog_done:
    ; we overwrote this instruction (to turn the watchdog off)
    ; so do so here
    clr g_sysreset_watchdog_should_run

    ; set RoL pattern red, orange, green
    mov a,#LEDPATTERN_RED_ORANGE_GREEN
    acall _turboreset_set_leds_and_return

    ; start LED lightshow watchdog
    mov r0,#g_ledlightshow_watchdog_state
    mov @r0,#1

led_lightshow_sm_reload_counter_and_exit:
    mov r0,#g_ledlightshow_watchdog_death_counter
    mov @r0,#LED_LIGHTSHOW_SM_TIMEOUT_TICKS
led_lightshow_sm_do_nothing:
    ret

led_lightshow_sm_exec:
    ; short-circuit if powerdown statemachine starts
    ; so that we don't power up again by mistake
    jb g_powerdown_sm_should_run,_led_lightshow_sm_go_idle

    mov r0,#g_ledlightshow_watchdog_state
    mov a,@r0
    cjne a,#0,_led_lightshow_sm_do_state_1
    sjmp _led_lightshow_sm_go_idle

_led_lightshow_sm_do_state_1:
    ; for all "active" states:
    ; cut the state machine off if RRoD raised
    jb g_force_rrod_3,_led_lightshow_sm_clear_leds_and_go_idle
    jb g_force_rrod_4,_led_lightshow_sm_clear_leds_and_go_idle
    jb g_force_rrod_ipc,_led_lightshow_sm_clear_leds_and_go_idle

    mov r0,#g_ledlightshow_watchdog_state
    mov a,@r0
    cjne a,#1,_led_lightshow_sm_do_state_2

    ; tick death counter down
    ; djnz can't be used here because our vars are in high memory
    mov r0,#g_ledlightshow_watchdog_death_counter
    dec @r0
    cjne @r0,#0,led_lightshow_sm_do_nothing

    ; timed out - reload counter and go to state 2
    mov r0,#g_ledlightshow_watchdog_state
    mov @r0,#2
    sjmp led_lightshow_sm_reload_counter_and_exit

_led_lightshow_sm_do_state_2:
    cjne a,#2,led_lightshow_sm_do_nothing

    ; tick death counter down
    ; djnz can't be used here because our vars are in high memory
    mov r0,#g_ledlightshow_watchdog_death_counter
    dec @r0
    cjne @r0,#0,led_lightshow_sm_do_nothing

    ; reset on timeout
    ljmp hard_reset

    ; IPC hook lands here
ipc_led_anim_has_arrived:
    ; this setb was overwritten by our ljmp earlier so restore it
    setb g_rol_run_bootanim

    ; REALLY make sure the CPU requested that we play the animation
    ; (carry should still be set coming into this function)
    jnc led_lightshow_sm_do_nothing

    ; it has, so clear our LED state and let the ring of light run normally
    sjmp _led_lightshow_sm_clear_leds_and_go_idle

    ; other IPC hook lands here
ipc_displayerror_has_arrived:
    ; these instructions were trashed by our lcall
    ; addresses are different between falcon/jasper, but the code is still the same
    mov g_rrod_errorcode_1,r2
    mov g_rrod_errorcode_2,r3

_led_lightshow_sm_clear_leds_and_go_idle:
    ; if any RRoD raised, clear LED state
    mov a,#0
    acall rol_set_leds

_led_lightshow_sm_go_idle:
    mov r0,#g_ledlightshow_watchdog_state
    mov @r0,#0
    ret
