; ------------------------------------------------------------------------------------
;
; Hard reset code, needed for some very uncooperative Jaspers
;
; ------------------------------------------------------------------------------------

hard_reset:
    ; if power button is held, power off immediately so the user can actually power the console down.
    ; if we don't do this, the console will bootloop until power is disconnected.
    jnb gpio_powersw_n,_hard_reset_power_off

    ; stash powerup cause because it will get trashed on reboot
    mov r0,#g_power_up_cause
    mov a,@r0
    mov r0,#g_power_up_cause_backup
    mov @r0,a

    ; activate statemachine below
    mov r0,#g_hardreset_sm_state   ; init first state
    mov @r0,#0x43

    ; and force a hard reset
    ; (this should NOT clear our work var space!!)
_hard_reset_power_off:
    jmp 0x0000

hardreset_init_vars:
    mov r0,#g_power_up_cause_backup     ; power button by default
    mov @r0,0x11
    mov r0,#g_hardreset_sm_state        ; statemachine off by default
    mov @r0,#0
    mov r0,#g_hardreset_sm_init         ; SM now initialized
    mov @r0,#69
_hardreset_do_nothing:
    ret

hardreset_sm_exec:
    ; init work vars if not initialized already
    mov r0,#g_hardreset_sm_init
    mov a,@r0
    cjne a,#69,hardreset_init_vars

    ; actual state machine execution here
    mov r0,#g_hardreset_sm_state
    mov a,@r0

    cjne a,#0x43,_hardreset_sm_check_case_54

    ; first state is just to load the next state
    ; this delays the power-on by 20 or so ms, giving things time to cool down a bit
    mov r0,#g_hardreset_sm_state
    mov @r0,#0x54
    ret

_hardreset_sm_check_case_54:
    cjne a,#0x54,_hardreset_do_nothing

    ; push power button and go to next state
    ; (callback below will pick up on this)
    setb g_powerswitch_pushed
    mov r0,#g_hardreset_sm_state
    mov @r0,#0x63
    ret

powerup_event_callback:
    ; lcall overwrote these
    ; these are consistent between falcon/jasper so excuse the hardcoding
    ; (they are also the same on xenon)
    clr 020h.3 ; this is normally set in the IPC poweron/reset command
    clr 021h.1 ; "eject button pressed" flag

    ; if hard reset didn't cause us to get here, stop
    mov r0,#g_hardreset_sm_state
    cjne @r0,#0x63,_hardreset_do_nothing

    ; otherwise restore powerup cause and continue
    mov @r0,#0                      ; turn off hard reset statemachine
    mov r0,#g_power_up_cause_backup ; read stashed powerup cause
    mov a,@r0
    mov r0,#g_power_up_cause        ; write it back to restore it
    mov @r0,a
    ret

