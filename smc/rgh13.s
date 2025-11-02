;
; RGH1.3 common turbo SMC code
; Also includes badjasper stuff
;

ifndef JASPER
    JASPER equ 0
endif

; ------------------------------------------------------------------------------------
;
; Common definitions/consts
;
; ------------------------------------------------------------------------------------

; amount of time the bootrom has to load and run CB_A.
; if it doesn't in time, we raise RRoD 0022 because this is a major hardware fault.
; default is 50 * 20 = 1000 ms
BOOTROM_TIMEOUT   equ 50

; amount of time CB_A has to finish execution and de-assert POST bit 7.
; default value is 16 * 20 = 320 ms
; for EXT+3 it's 8
ifdef EXT_PLUS_3
CBA_POST7_TIMEOUT equ 8
else
CBA_POST7_TIMEOUT equ 16
endif

; amount of time CB_X has to load and run CB_B.
; you may need to adjust this for certain CB_Bs.
; default value is 4 * 20 = 80 ms
ifndef CBX_POST6_TIMEOUT
CBX_POST6_TIMEOUT equ 4
endif

; amount of time CB_B has to make it to HWINIT.
; remember: CB_B is hacked to assert POST bit 7 while HWINIT is running.
; default value is  12 * 20 = 240 ms
ifndef CBB_PRE_HWINIT_POST7_TIMEOUT
CBB_PRE_HWINIT_POST7_TIMEOUT equ 12
endif

; CBB_HWINIT_POST6_TOGGLE_TIMEOUT in rgh13_falcon.s and rgh13_jasper.s
; specifies the period between which POST bit 6 must toggle during HWINIT.
; this can loop over and over, the main reset watchdog will reboot if HWINIT takes too long.
; note the behavior is console-dependent.

; RRoD Classic, but orange so we don't confuse it with a normal system error
LED_ERROR_PATTERN equ 0b11011101

; ------------------------------------------------------------------------------------

rgh13_statemachines_exec:
    acall turboreset_sm_exec       ; manages POST watchdogs
    acall hardreset_sm_exec        ; manages hard reset stuff, if necessary
    acall led_lightshow_sm_exec    ; manages ring of light bootanim watchdog
    ljmp holdpowerbutton_sm_exec   ; hold powerbutton for 5 seconds to power off

; ------------------------------------------------------------------------------------
;
; Turbo reset
; Monitor POST bits 6/7 during the boot and reboot if we don't like what we see
;
; ------------------------------------------------------------------------------------

on_reset_watchdog_timeout:
    ; assert /CPU_RST_N now so POST bits drop to 0
    ; if we don't do this then our POST bit check will fail and we'll get a RRoD
    clr gpio_cpu_rst_n

    ; turn off statemachines that might be running
    acall _led_lightshow_sm_go_idle
    sjmp  _turboreset_sm_disarm

; hook from SMC code lands here
;
; code for reset watchdog state 7 (load counter and go to state 8) varies between falcon/jasper.
; falcon just de-asserts reset immediately and loads the counter.
; jasper does a bit of extra stuff before the counter gets loaded.
on_reset_watchdog_deassert_cpu_reset:
    ; these POST bits MUST be zero or there's a wiring issue.
    ; in which case, refuse to let the system run.
    jb RGH13_POST_6,_post_bits_not_zero_at_reset
    jb RGH13_POST_7,_post_bits_not_zero_at_reset

    mov r0,#g_turboreset_sm_state   ; enable statemachine
    mov @r0,#1
    mov r0,#g_turboreset_sm_counter ; with bootrom timeout
    mov @r0,#BOOTROM_TIMEOUT

    ; clear LEDs, they'll have been left on from previous (failed) attempts
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
    jb g_force_rrod_4,_turboreset_sm_disarm
    jb g_force_rrod_ipc,_turboreset_sm_disarm

    ; read the state, it's time to start execution
    mov r0,#g_turboreset_sm_state
    mov a,@r0

;
; state 1 - wait for POST bits 6 and 7 to rise
;
    cjne a,#1,_turboreset_sm_exec_state_2
    jnb RGH13_POST_6,_turboreset_sm_state_1_timeout
    jnb RGH13_POST_7,_turboreset_sm_state_1_timeout

_turboreset_go_state_2:
    mov r0,#g_turboreset_sm_state
    mov @r0,#2
    mov r0,#g_turboreset_sm_counter
    mov @r0,#CBA_POST7_TIMEOUT

    ; flash red on ring of light
    mov a,#LEDPATTERN_RED
    sjmp _turboreset_set_leds_and_return

_turboreset_sm_state_1_timeout:
    ; tick timer down
    mov r0,#g_turboreset_sm_counter
    dec @r0
    cjne @r0,#0,_turboreset_do_nothing

    ; old behavior here was to RRoD 0000/4444
    ; however POST bus noise and other things caused false positives.
    ; if the CPU is stuck in a coma, just reboot the whole thing...
    ljmp hard_reset

_setup_rrod:
    mov g_rrod_set_zero,#0
    mov g_rrod_base_error_pattern,#LED_ERROR_PATTERN
    mov r0,#g_rol_af_cell
    mov @r0,g_rrod_base_error_pattern

    setb g_force_rrod_4
    setb g_force_rrod_ipc
    setb g_rol_update_pending
    clr  g_sysreset_watchdog_should_run

    mov r0,#g_turboreset_sm_state
    mov @r0,#0
_turboreset_do_nothing:
    ret

;
; state 2 - POST bit 7 (connected to TILTSW) must fall in time
; (the glitch chip sends the malformed reset pulse during this phase)
;
_turboreset_sm_exec_state_2:
    cjne a,#2,_turboreset_sm_exec_state_3
    jnb RGH13_POST_7,_turboreset_sm_go_state_3 ; has to fall in time

    ; tick timer down
    mov r0,#g_turboreset_sm_counter
    dec @r0
    cjne @r0,#0,_turboreset_do_nothing
    
    ; we've timed out - call common disarm code below instead of repeating it
    acall _turboreset_sm_disarm

    ; for badjaspers, hard reset always
ifdef HARD_RESET_ON_CBA_FAIL
    sjmp hard_reset
else
    sjmp _turboreset_reboot_via_sysreset_watchdog
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
    jnb RGH13_POST_6,_turboreset_sm_go_state_4

_turboreset_sm_common_timeout_code:
    mov r0,#g_turboreset_sm_counter
    dec @r0
    cjne @r0,#0,_turboreset_do_nothing
    
    ; we've timed out - call common disarm code below instead of repeating it
    acall _turboreset_sm_disarm

_turboreset_reboot_via_sysreset_watchdog:
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
    jb RGH13_POST_7,_turboreset_sm_go_state_5
    sjmp _turboreset_sm_common_timeout_code

_turboreset_sm_go_state_5:
    mov r0,#g_turboreset_sm_state
    mov @r0,#5

    mov r0,#g_turboreset_sm_counter
    mov @r0,#CBB_HWINIT_POST6_TOGGLE_TIMEOUT

    ; A2/E2 toggles only once on Jasper so display red/orange/red there
if JASPER == 1
    mov a,#LEDPATTERN_RED_ORANGE_RED
else
    mov a,#LEDPATTERN_RED_ORANGE
endif

_turboreset_set_leds_and_return:
    ljmp rol_set_leds

;
; state 5 and 6 - monitor POST bit 6 toggles.
; this will loop over and over with state 6 until POST bit 7 falls
; and if HWINIT goes into an infinite loop the normal SMC watchdog will reboot
;
_turboreset_sm_exec_state_5:
    cjne a,#5,_turboreset_sm_exec_state_6
    jnb RGH13_POST_7,_turboreset_sm_go_state_7      ; run as long as POST bit 7 is high
    jb  RGH13_POST_6,_turboreset_sm_go_state_6      ; state 5 waits for rise
    sjmp _turboreset_sm_common_timeout_code

_turboreset_sm_go_state_6:
    mov r0,#g_turboreset_sm_state
    mov @r0,#6
    
    mov r0,#g_turboreset_sm_counter
    mov @r0,#CBB_HWINIT_POST6_TOGGLE_TIMEOUT

    mov a,#LEDPATTERN_RED_ORANGE_RED
    sjmp _turboreset_set_leds_and_return

_turboreset_sm_exec_state_6:
    cjne a,#6,_turboreset_sm_exec_state_7
    jnb RGH13_POST_7,_turboreset_sm_go_state_7     ; run as long as POST bit 7 is high
    jnb RGH13_POST_6,_turboreset_sm_go_state_5     ; state 6 waits for fall
    sjmp _turboreset_sm_common_timeout_code

_turboreset_sm_go_state_7:
    mov r0,#g_turboreset_sm_state
    mov @r0,#7

    ; set LEDs red/orange/orange
    mov a,#LEDPATTERN_RED_ORANGE_ORANGE
    sjmp _turboreset_set_leds_and_return

;
; state 7 - monitor POST bit 7 and go back to state 5/6 if it rises again
; this is mostly intended to catch POST bit 7 sometimes registering as 0 but could
; also catch errors and force a reboot
;
_turboreset_sm_exec_state_7:
    cjne a,#7,_turboreset_do_nothing
    jnb RGH13_POST_7,_turboreset_do_nothing
    jb RGH13_POST_6,_turboreset_sm_go_state_6
    sjmp _turboreset_sm_go_state_5


;
; Common modules
;
    .include "hardreset.s"
    .include "rolwatchdog.s"
    .include "ledctrl.s"
    .include "powerbutton.s"
