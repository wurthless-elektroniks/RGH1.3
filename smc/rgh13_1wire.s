
ifndef JASPER
    JASPER equ 0
endif

LED_ERROR_PATTERN equ 0b11011101

; ------------------------------------------------------------------------------------
;
; Common definitions/consts
;
; ------------------------------------------------------------------------------------

; amount of time the bootrom has to load and run CB_A.
; if it doesn't in time, we raise RRoD 0022 because this is a major hardware fault.
; default is 50 * 20 = 1000 ms
BOOTROM_TIMEOUT          equ 50

ifdef EXT_PLUS_3
CBA_POST_TIMEOUT         equ 8
else
CBA_POST_TIMEOUT         equ 16
endif

IPC_A1_TIMEOUT           equ 8
IPC_12_TIMEOUT           equ 26
IPC_A2_E2_TOGGLE_TIMEOUT equ 35

; ------------------------------------------------------------------------------------

rgh13_statemachines_exec:
    acall turboreset_sm_exec       ; manages POST watchdogs
    acall hardreset_sm_exec        ; manages hard reset stuff, if necessary
    acall led_lightshow_sm_exec    ; manages ring of light bootanim watchdog
    ljmp holdpowerbutton_sm_exec   ; hold powerbutton for 5 seconds to power off

; ------------------------------------------------------------------------------------

on_reset_watchdog_timeout:
    ; assert /CPU_RST_N now so POST bits drop to 0
    ; if we don't do this then our POST bit check will fail and we'll get a RRoD
    clr gpio_cpu_rst_n

    ; turn off statemachines that might be running
    acall _led_lightshow_sm_go_idle
    sjmp  _turboreset_sm_disarm

on_reset_watchdog_deassert_cpu_reset:
    jb RGH13_1WIRE_POST,_post_bit_not_zero_at_reset

    mov r0,#g_turboreset_sm_state   ; enable statemachine
    mov @r0,#1
    mov r0,#g_turboreset_sm_counter ; with bootrom timeout
    mov @r0,#BOOTROM_TIMEOUT

    ; clear LEDs, they'll have been left on from previous (failed) attempts
    mov a,#0
    sjmp _turboreset_set_leds_and_return

_post_bit_not_zero_at_reset:
    mov g_rrod_errorcode_1,#0xFF ; RRoD error code 3333
    mov g_rrod_errorcode_2,#0xFF
    mov g_rrod_set_zero,#0
    mov g_rrod_base_error_pattern,#LED_ERROR_PATTERN
    mov r0,#g_rol_af_cell
    mov @r0,g_rrod_base_error_pattern

    setb g_force_rrod_3        ; forces immediate power down
    setb g_force_rrod_4
    setb g_force_rrod_ipc
    setb g_rol_update_pending
    clr  g_sysreset_watchdog_should_run

_turboreset_sm_disarm:
    mov r0,#g_turboreset_sm_state
    mov @r0,#0
_turboreset_do_nothing:
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
; state 1 - wait for POST bit to rise
;
    cjne a,#1,_turboreset_sm_exec_state_2
    jnb RGH13_1WIRE_POST,_turboreset_sm_state_1_timeout
_turboreset_go_state_2:
    mov r0,#g_turboreset_sm_state
    mov @r0,#2
    mov r0,#g_turboreset_sm_counter
    mov @r0,#CBA_POST_TIMEOUT

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
;
; state 2 - the POST bit needs to fall in time or we reboot
;
_turboreset_sm_exec_state_2:
    cjne a,#2,_turboreset_sm_exec_state_4
    jnb RGH13_1WIRE_POST,_turboreset_sm_go_state_4 ; has to fall in time

    ; tick timer down
    mov r0,#g_turboreset_sm_counter
    dec @r0
    cjne @r0,#0,_turboreset_do_nothing
    
    acall _turboreset_sm_disarm

    ; for badjaspers, hard reset always
ifdef HARD_RESET_ON_CBA_FAIL
    ljmp hard_reset
else
    sjmp _turboreset_reboot_via_sysreset_watchdog
endif

_turboreset_sm_go_state_4:
    mov r0,#g_turboreset_sm_state
    mov @r0,#4

    mov r0,#g_turboreset_sm_counter
    mov @r0,#IPC_A1_TIMEOUT

    mov a,#LEDPATTERN_RED_RED
_turboreset_set_leds_and_return:
    ljmp rol_set_leds

; There used to be a state 3 here. It's gone now.

;
; state 4 - wait for IPC message 0xA1 (CB_Y done)
;
_turboreset_sm_exec_state_4:
    cjne a,#4,_turboreset_sm_exec_state_5

    ; no way to exit this state except through SMC callback

_turboreset_common_timeout:
    mov r0,#g_turboreset_sm_counter
    dec @r0
    cjne @r0,#0,_turboreset_do_nothing
    
    ; we've timed out - call common disarm code below instead of repeating it
    acall _turboreset_sm_disarm

    ; and go reboot
_turboreset_reboot_via_sysreset_watchdog:
    ljmp msftsmc_sysreset_watchdog_exec_state_10
;
; state 5 - wait for SMC command 0x12 (hwinit started)
;
_turboreset_sm_exec_state_5:
    cjne a,#5,_turboreset_sm_exec_state_6

    ; no way to exit this state except through SMC callback
    sjmp _turboreset_common_timeout

;
; state 6 - wait for some SMC commands (0xA2, 0xE2, 0xA4)
;
_turboreset_sm_exec_state_6:
    cjne a,#6,_turboreset_do_nothing

    ; no way to exit this state except through SMC callback
    sjmp _turboreset_common_timeout

; ------------------------------------------------------------------------------------
;
; IPC hooks
;
; ------------------------------------------------------------------------------------

; hwinit bytecode sends command 0x12 early on in execution
ipc_command_12_received_reroute:
    ; we overwrote a lcall to somewhere, so restore it.
    lcall msftsmc_ipc_write_outbox_fifo
    
    ; only act on this if turboreset in state 5
    mov r0,#g_turboreset_sm_state
    cjne @r0,#5,_turboreset_do_nothing
    
    mov @r0,#6
    
    mov r0,#g_turboreset_sm_counter
    mov @r0,#IPC_A2_E2_TOGGLE_TIMEOUT

    mov a,#LEDPATTERN_RED_ORANGE
    sjmp _turboreset_set_leds_and_return

ipc_command_bit7_received_reroute:
    mov r0,#g_turboreset_sm_state
    cjne @r0,#6,_bit7_maybe_in_state_4 ; A2/E2/A4 only in state 6
_handle_bit7_command:
    cjne a,#0xA2,_check_e2

    mov a,#LEDPATTERN_RED_ORANGE
_state_6_kick_watchdog_and_exit:
    acall rol_set_leds
    mov r0,#g_turboreset_sm_counter
    mov @r0,#IPC_A2_E2_TOGGLE_TIMEOUT
    ret

_check_e2:
    cjne a,#0xE2,_check_a4
    mov a,#LEDPATTERN_RED_ORANGE_RED
    sjmp _state_6_kick_watchdog_and_exit

_check_a4:
    cjne a,#0xA4,_continue_handling_bit7_command

    mov r0,#g_turboreset_sm_state
    mov @r0,#7
    mov a,#LEDPATTERN_RED_ORANGE_ORANGE
    sjmp _turboreset_set_leds_and_return

_bit7_maybe_in_state_4:
    cjne @r0,#4,_continue_handling_bit7_command

    cjne a,#0xA1,_continue_handling_bit7_command ; A1 only in state 4

    mov r0,#g_turboreset_sm_state
    mov @r0,#5

    mov r0,#g_turboreset_sm_counter
    mov @r0,#IPC_12_TIMEOUT

    mov a,#LEDPATTERN_RED_ORANGE
    sjmp _turboreset_set_leds_and_return

_continue_handling_bit7_command:
    ljmp msftsmc_ipc_handle_bit7_message

;
; Common modules
;
    .include "hardreset.s"
    .include "rolwatchdog.s"
    .include "ledctrl.s"
    .include "powerbutton.s"
