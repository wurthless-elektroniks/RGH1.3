
ifndef JASPER
    JASPER equ 0
endif

LED_ERROR_PATTERN equ 0b11011101

; ------------------------------------------------------------------------------------
;
; Common definitions/consts
;
; ------------------------------------------------------------------------------------

RED_BLINK_DELAY equ 20  ; not actual CB_A start timing
IPC_A0_TIMEOUT  equ 20  ; 
IPC_A1_TIMEOUT  equ 4   ; 4 x 20 = 80 ms to get to cbb_jump
IPC_12_TIMEOUT  equ 22  ; 22 x 20 = 
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
    mov r0,#g_turboreset_sm_state   ; enable statemachine
    mov @r0,#1
    mov r0,#g_turboreset_sm_counter
    mov @r0,#RED_BLINK_DELAY

    ; clear LEDs, they'll have been left on from previous (failed) attempts
    mov a,#0
    sjmp _turboreset_set_leds_and_return

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

    ; also cut the state machine off if *ANY* RRoD raised
    jb g_force_rrod_power,_turboreset_sm_disarm
    jb g_force_rrod_overheat,_turboreset_sm_disarm
    jb g_force_rrod_ipc,_turboreset_sm_disarm

    ; read the state, it's time to start execution
    mov r0,#g_turboreset_sm_state
    mov a,@r0

;
; state 1 - wait a bit, then turn on the red LED
;
    cjne a,#1,_turboreset_sm_exec_state_2

    mov r0,#g_turboreset_sm_counter
    dec @r0
    cjne @r0,#0,_turboreset_do_nothing

    ; go to state 2 on timeout
    mov r0,#g_turboreset_sm_state
    mov @r0,#2

    mov r0,#g_turboreset_sm_counter
    mov @r0,#IPC_A0_TIMEOUT

    mov a,#LEDPATTERN_RED
    sjmp _turboreset_set_leds_and_return

;
; state 2 - wait for IPC command 0xA0
;
_turboreset_sm_exec_state_2:
    cjne a,#2,_turboreset_sm_exec_state_3

    ; no way to exit this state except through SMC callback

    mov r0,#g_turboreset_sm_counter
    dec @r0
    cjne @r0,#0,_turboreset_do_nothing
    acall _turboreset_sm_disarm

    ; for badjaspers, hard reset always
    ; (not receiving 0xA0 means a crash happened before CB_X)
ifdef HARD_RESET_ON_CBA_FAIL
    sjmp hard_reset
else
    sjmp _turboreset_reboot_via_sysreset_watchdog
endif

;
; state 3 - wait for IPC command 0xA1
;
_turboreset_sm_exec_state_3:
    cjne a,#3,_turboreset_sm_exec_state_4
    ; no way to exit this state except through SMC callback
    sjmp _turboreset_common_timeout    

;
; state 4 - wait for IPC command 0x12
;
_turboreset_sm_exec_state_4:
    cjne a,#4,_turboreset_sm_exec_state_5
    ; no way to exit this state except through SMC callback

    ; tick timer down
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
; state 5 - wait for some SMC commands (0xA2, 0xE2, 0xA4)
;
_turboreset_sm_exec_state_5:
    cjne a,#6,_turboreset_do_nothing

    ; no way to exit this state except through SMC callback
    sjmp _turboreset_common_timeout

; ------------------------------------------------------------------------------------
;
; IPC hooks specific to 0-wire RGH1.3
;
; ------------------------------------------------------------------------------------

; hwinit bytecode sends command 0x12 early on in execution
ipc_command_12_received_reroute:
    ; we overwrote a lcall to somewhere, so restore it.
    lcall msftsmc_ipc_write_outbox_fifo
    
    ; only act on this if turboreset in state 4
    mov r0,#g_turboreset_sm_state
    cjne @r0,#4,_turboreset_do_nothing
_turboreset_sm_go_state_5:
    mov @r0,#5
    
    mov r0,#g_turboreset_sm_counter
    mov @r0,#IPC_A2_E2_TOGGLE_TIMEOUT

    mov a,#LEDPATTERN_RED_ORANGE
_turboreset_set_leds_and_return:
    ljmp rol_set_leds



ipc_command_bit7_received_reroute:
    mov r0,#g_turboreset_sm_state
    cjne @r0,#5,_bit7_maybe_in_state_2 ; A2/E2/A4 only in state 5
_handle_bit7_command:
    cjne a,#0xA2,_check_e2

    mov a,#LEDPATTERN_RED_ORANGE
_state_4_kick_watchdog_and_exit:
    acall rol_set_leds
    mov r0,#g_turboreset_sm_counter
    mov @r0,#IPC_A2_E2_TOGGLE_TIMEOUT
    ret

_check_e2:
    cjne a,#0xE2,_check_a4
    mov a,#LEDPATTERN_RED_ORANGE_RED
    sjmp _state_4_kick_watchdog_and_exit

_check_a4:
    cjne a,#0xA4,_continue_handling_bit7_command

    mov r0,#g_turboreset_sm_state
    mov @r0,#6
    mov a,#LEDPATTERN_RED_ORANGE_ORANGE
    sjmp _turboreset_set_leds_and_return

_bit7_maybe_in_state_2:
    cjne @r0,#2,_bit7_maybe_in_state_3
    cjne a,#0xA0,_continue_handling_bit7_command ; A0 only in state 2

    ; command 0xA0 received
    mov r0,#g_turboreset_sm_state
    mov @r0,#3

    mov r0,#g_turboreset_sm_counter
    mov @r0,#IPC_A1_TIMEOUT

    mov a,#LEDPATTERN_RED_RED
    sjmp _turboreset_set_leds_and_return

_bit7_maybe_in_state_3:
    cjne @r0,#3,_continue_handling_bit7_command
    cjne a,#0xA1,_continue_handling_bit7_command ; A1 only in state 3

    mov r0,#g_turboreset_sm_state
    mov @r0,#4

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
