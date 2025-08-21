;
; RGH1.3 common turbo SMC code
; Also includes badjasper stuff
;


; ------------------------------------------------------------------------------------
;
; Common definitions/consts
;
; ------------------------------------------------------------------------------------

; amount of time the bootrom has to load and run CB_A.
; if it doesn't in time, we raise RRoD 0022 because this is a major hardware fault.
; default is 25 * 20 = 500 ms
BOOTROM_TIMEOUT   equ 25

; amount of time CB_A has to finish execution and de-assert POST bit 7.
; default value is 16 * 20 = 320 ms
CBA_POST7_TIMEOUT equ 16

; amount of time CB_X has to load and run CB_B.
; you may need to adjust this for certain CB_Bs.
; default value is 4 * 20 = 80 ms
CBX_POST6_TIMEOUT equ 4

; amount of time CB_B has to make it to HWINIT.
; remember: CB_B is hacked to assert POST bit 7 while HWINIT is running.
; default value is  9 * 20 = 180 ms
CBB_PRE_HWINIT_POST7_TIMEOUT equ 9

; period between which POST bit 6 must toggle during HWINIT.
; this can loop over and over, the main reset watchdog will reboot if HWINIT takes too long.
; default value is 14 * 20 = 280 ms
CBB_HWINIT_POST6_TOGGLE_TIMEOUT equ 14

; once GetPowerUpCause arrives the CPU has this amount of time to make it to the LED bootanim
; or else we will reboot. this is a workaround for some systems that crash late in the boot,
; primarily jaspers, but falcons are known to do this too.
; default value is 125 * 20 * 2 = 5000 ms, adjust as necessary
LED_LIGHTSHOW_SM_TIMEOUT_TICKS equ 125

;                                  ggggrrrr
;                                  32103210
LEDPATTERN_RED               equ 0b00000001

;                                  ggggrrrr
;                                  32103210
LEDPATTERN_RED_RED           equ 0b00000011

;                                  ggggrrrr
;                                  32103210
LEDPATTERN_RED_ORANGE        equ 0b00100011

;                                  ggggrrrr
;                                  32103210
LEDPATTERN_RED_ORANGE_RED    equ 0b00100111

;                                  ggggrrrr
;                                  32103210
LEDPATTERN_RED_ORANGE_ORANGE equ 0b01100111

;                                  ggggrrrr
;                                  32103210
LEDPATTERN_RED_ORANGE_GREEN  equ 0b01100011

; RRoD Classic, but orange so we don't confuse it with a normal system error
LED_ERROR_PATTERN equ 0b11011101

; ------------------------------------------------------------------------------------

rgh13_statemachines_exec:
    acall turboreset_sm_exec       ; manages POST watchdogs
    acall hardreset_sm_exec        ; manages hard reset stuff, if necessary
    acall led_lightshow_sm_exec    ; manages ring of light bootanim watchdog
    ret

; ------------------------------------------------------------------------------------
;
; Turbo reset
; Monitor POST bits 6/7 during the boot and reboot if we don't like what we see
;
; ------------------------------------------------------------------------------------

; hook from SMC code lands here
;
; code for reset watchdog state 7 (load counter and go to state 8) varies between falcon/jasper.
; falcon just de-asserts reset immediately and loads the counter.
; jasper does a bit of extra stuff before the counter gets loaded.
on_reset_watchdog_deassert_cpu_reset:
    ; these POST bits MUST be zero or there's a wiring issue.
    ; in which case, refuse to let the system run
    jb gpio_gpu_reset_done,_post_bits_not_zero_at_reset
    jb gpio_tiltsw_n,_post_bits_not_zero_at_reset

    mov r0,#g_turboreset_sm_state   ; enable statemachine
    mov @r0,#1
    mov r0,#g_turboreset_sm_counter ; with bootrom timeout
    mov @r0,#BOOTROM_TIMEOUT

    ; and clear LEDs state in case it was stuck on from previous attempt
    mov a,#0
    ljmp rol_set_leds

_post_bits_not_zero_at_reset:
    mov g_rrod_errorcode_1,#0xFF ; RRoD error code 3333
    mov g_rrod_errorcode_2,#0xFF
    sjmp _setup_rrod

_turboreset_sm_disarm:
    mov r0,#g_turboreset_sm_state
    mov @r0,#0
    ret

; main turboreset statemachine code here
turboreset_sm_exec:
    ; short-circuit if reset watchdog statemachine suddenly turned off
    ; or if the main watchdog requested a reset
    jnb g_sysreset_watchdog_should_run,_turboreset_sm_disarm
    jb  g_requesting_reset,_turboreset_sm_disarm

    ; also cut the state machine off if RRoD raised
    jb g_force_rrod_3,_turboreset_sm_disarm
    jb g_force_rrod_4,_turboreset_sm_disarm
    jb g_force_rrod_ipc,_turboreset_sm_disarm

    ; read the state, it's time to start execution
    mov r0,#g_turboreset_sm_state
    mov a,@r0

;
; state 1 - wait for POST bit 6 to rise, and throw RRoD if it doesn't in time
;
    cjne a,#1,_turboreset_sm_exec_state_2
    jb gpio_gpu_reset_done,_turboreset_go_state_2

    ; tick timer down
    mov r0,#g_turboreset_sm_counter
    dec @r0
    cjne @r0,#0,_turboreset_do_nothing

    ; on timeout, raise RRoD 2222 and give up
    mov g_rrod_errorcode_1,#0xAA
    mov g_rrod_errorcode_2,#0xAA
_setup_rrod:
    mov g_rrod_set_zero,#0
    mov g_rrod_base_error_pattern,#LED_ERROR_PATTERN
    mov r0,#g_rol_af_cell
    mov @r0,g_rrod_base_error_pattern

    setb g_force_rrod_ipc
    setb g_rol_update_pending

    mov r0,#g_turboreset_sm_counter
    mov @r0,#0
_turboreset_do_nothing:
    ret

_turboreset_go_state_2:
    mov r0,#g_turboreset_sm_state
    mov @r0,#2
    mov r0,#g_turboreset_sm_counter
    mov @r0,#CBA_POST7_TIMEOUT

    ; flash red on ring of light
    mov a,#LEDPATTERN_RED
    sjmp _turboreset_set_leds_and_return

;
; state 2 - POST bit 7 (connected to TILTSW) must fall in time
; (the glitch chip sends the malformed reset pulse during this phase)
;
_turboreset_sm_exec_state_2:
    cjne a,#2,_turboreset_sm_exec_state_3
    jnb gpio_tiltsw_n,_turboreset_sm_go_state_3 ; has to fall in time

    ; tick timer down
    mov r0,#g_turboreset_sm_counter
    dec @r0
    cjne @r0,#0,_turboreset_do_nothing
    
    ; we've timed out - call common disarm code below instead of repeating it
    acall _turboreset_sm_disarm

    ; clear LEDs state
    mov a,#0
    acall _turboreset_set_leds_and_return

     ; for badjaspers, hard reset always
ifdef BADJASPER
    sjmp hard_reset
else
    ; reboot via sysreset watchdog
    ljmp msftsmc_sysreset_watchdog_exec_state_10
endif

_turboreset_sm_go_state_3:
    mov r0,#g_turboreset_sm_state
    mov @r0,#3
    mov r0,#g_turboreset_sm_counter
    mov @r0,#CBX_POST6_TIMEOUT

    mov a,#LEDPATTERN_RED_RED
    sjmp _turboreset_set_leds_and_return

;
; state 3 - wait for POST bit 6 to fall
; if it doesn't fall in time, CB_X crashed and we need to reboot
;
_turboreset_sm_exec_state_3:
    cjne a,#3,_turboreset_sm_exec_state_4
    jnb gpio_gpu_reset_done,_turboreset_sm_go_state_4

_turboreset_sm_common_timeout_code:
    mov r0,#g_turboreset_sm_counter
    dec @r0
    cjne @r0,#0,_turboreset_do_nothing
    
    ; we've timed out - call common disarm code below instead of repeating it
    lcall _turboreset_sm_disarm

    ; clear LEDs state
    mov a,#0
    acall _turboreset_set_leds_and_return

    ; reboot via sysreset watchdog
    ljmp msftsmc_sysreset_watchdog_exec_state_10

_turboreset_sm_go_state_4:

    mov r0,#g_turboreset_sm_state
    mov @r0,#4
    mov r0,#g_turboreset_sm_counter
    mov @r0,#CBB_PRE_HWINIT_POST7_TIMEOUT

    mov a,#LEDPATTERN_RED_ORANGE
    sjmp _turboreset_set_leds_and_return


;
; state 4 - wait for POST bit 7 to rise again
; and if it doesn't, the CPU crashed before HWINIT
;
_turboreset_sm_exec_state_4:
    cjne a,#4,_turboreset_sm_exec_state_5
    jb gpio_tiltsw_n,_turboreset_sm_go_state_5
    sjmp _turboreset_sm_common_timeout_code

_turboreset_sm_go_state_5:
    mov r0,#g_turboreset_sm_state
    mov @r0,#5

    mov r0,#g_turboreset_sm_counter
    mov @r0,#CBB_HWINIT_POST6_TOGGLE_TIMEOUT

    mov a,#LEDPATTERN_RED_ORANGE
_turboreset_set_leds_and_return:
    ljmp rol_set_leds

;
; state 5 and 6 - monitor POST bit 6 toggles.
; this will loop over and over with state 6 until POST bit 7 falls
; and if HWINIT goes into an infinite loop the normal SMC watchdog will reboot
;
_turboreset_sm_exec_state_5:
    cjne a,#5,_turboreset_sm_exec_state_6
    jnb gpio_tiltsw_n,_turboreset_sm_go_state_7      ; run as long as POST bit 7 is high
    jb gpio_gpu_reset_done,_turboreset_sm_go_state_6 ; state 5 waits for rise
    sjmp _turboreset_sm_common_timeout_code

_turboreset_sm_go_state_6:
    mov r0,#g_turboreset_sm_state
    mov @r0,#6
    
    mov r0,#g_turboreset_sm_counter
    mov @r0,#CBB_HWINIT_POST6_TOGGLE_TIMEOUT

    mov a,#LEDPATTERN_RED_ORANGE_RED
    sjmp _turboreset_set_leds_and_return

_turboreset_sm_exec_state_6:
    cjne a,#6,_turboreset_do_nothing
    jnb gpio_tiltsw_n,_turboreset_sm_go_state_7       ; run as long as POST bit 7 is high
    jnb gpio_gpu_reset_done,_turboreset_sm_go_state_5 ; state 6 waits for fall
    sjmp _turboreset_sm_common_timeout_code

_turboreset_sm_go_state_7:
    mov r0,#g_turboreset_sm_state
    mov @r0,#7

    ; set LEDs red/orange/orange
    mov a,#LEDPATTERN_RED_ORANGE_ORANGE
    sjmp _turboreset_set_leds_and_return

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
    lcall rol_set_leds

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

    ; also cut the state machine off if RRoD raised
    jb g_force_rrod_3,_led_lightshow_sm_go_idle
    jb g_force_rrod_4,_led_lightshow_sm_go_idle
    jb g_force_rrod_ipc,_led_lightshow_sm_go_idle

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

    mov a,#0
    acall rol_set_leds

_led_lightshow_sm_go_idle:
    mov r0,#g_ledlightshow_watchdog_state
    mov @r0,#0
    ret

    ; other IPC hook lands here
ipc_displayerror_has_arrived:
    ; these instructions were trashed by our lcall
    ; addresses are different between falcon/jasper, but the code is still the same
    mov g_rrod_errorcode_1,r2
    mov g_rrod_errorcode_2,r3

    ; shut statemachine off
    sjmp _led_lightshow_sm_go_idle

;
; Common function to set Ring of Light LEDs
; a - LED states (upper 4 bits green, lower 4 bits red)
;
rol_set_leds:
    mov r0,#g_rol_ledstate
    mov @r0,a

    jz _clear_led_priority_bit

    ; bits 5/7 must be set for argon sm to display things
    ; bit 5 is apparently some "high priority" bit and when it is set
    ; nothing else will display on the ring
    mov a,g_rol_flags
    orl a,#0b10100000
_rol_set_leds_finish:
    mov g_rol_flags,a
    
    ; and this bit has to be set too
    setb g_rol_update_pending
    ret

    ; clear priority flag when turning LEDs off
_clear_led_priority_bit:
    mov a,g_rol_flags
    anl a,#0b11011111 
    sjmp _rol_set_leds_finish
