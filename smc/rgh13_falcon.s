;
; RGH1.3 code for Falcons
;

    .include "falcondefs.inc"

; timeout for normal reset watchdog
; default is 137 * 20 * 2 = 5480 ms
RESET_WATCHDOG_TIMEOUT_TICKS equ 137


; ------------------------------------------------------------------------------------

; these variables will be automatically zeroed out on reset
g_turboreset_sm_state                   equ 093h
g_turboreset_sm_counter                 equ 094h
g_ledlightshow_watchdog_state           equ 095h
g_ledlightshow_watchdog_death_counter   equ 096h

; these variables will persist past a reboot
; see init_memclear_patch_start
g_hardreset_sm_init                     equ 097h
g_hardreset_sm_state                    equ 098h
g_power_up_cause_backup                 equ 099h

; ------------------------------------------------------------------------------------
;
; Patchlist
;
; ------------------------------------------------------------------------------------
    .org 0x0000

    mov dptr,#mainloop_reorg_start
    mov dptr,#mainloop_reorg_end

    mov dptr,#init_memclear_patch_start
    mov dptr,#init_memclear_patch_end
    
    mov dptr,#skip_reading_gpu_reset_done_1_start
    mov dptr,#skip_reading_gpu_reset_done_1_end
    mov dptr,#skip_reading_gpu_reset_done_2_start
    mov dptr,#skip_reading_gpu_reset_done_2_end

    mov dptr,#resetwatchdog_reload_counter_1_start
    mov dptr,#resetwatchdog_reload_counter_1_end
    mov dptr,#resetwatchdog_reload_counter_2_start
    mov dptr,#resetwatchdog_reload_counter_2_end
    mov dptr,#resetwatchdog_on_success_start
    mov dptr,#resetwatchdog_on_success_end
    mov dptr,#resetwatchdog_boot_tries_increment_nopout_start
    mov dptr,#resetwatchdog_boot_tries_increment_nopout_end

    mov dptr,#powerup_reroute_start
    mov dptr,#powerup_reroute_end

    mov dptr,#tiltsw_nullify_start
    mov dptr,#tiltsw_nullify_end

    mov dptr,#rgh13_common_code_start
    mov dptr,#rgh13_common_code_end

    .byte 0 ; end of list

; ------------------------------------------------------------------------------------
;
; Patches
;
; ------------------------------------------------------------------------------------

    ; reorg mainloop to move calls up over the useless statemachine that reads DBG_LED0,
    ; so we can add a call to our custom RGH1.3 statemachine at the end
    .org 0x07C2
mainloop_reorg_start:
    lcall 0x1DCE                   ; power event monitor (checks for button presses and acts on them)
    lcall 0x1196                   ; no idea what this does
    lcall 0x106D                   ; powerup statemachine
    lcall 0x12C6                   ; reset watchdog (reboots if GetPowerUpCause isn't received in time)
    lcall 0x1112                   ; hardware reset statemachine (actually resets hardware)
    lcall 0x0EA4                   ; powerdown statemachine
    lcall rgh13_statemachines_exec ; our custom code below
mainloop_reorg_end:
    ; should have ended at 0x7D7 or we've overwritten bits of the mainloop

    ; make room for our hard reset state machine variables
    ; so they are in a safe space and don't get killed on reboot
    .org 0x7EC
init_memclear_patch_start:
    mov r2,#0x1A ; stop memory clear at 0x97, so 0x98, 0x99, 0x9A don't get overwritten on reboot
init_memclear_patch_end:

    ; reroute any power LED changes (via IPC) to custom code below
    .org 0xC91
ipc_setled_reroute_start:
    ljmp ipc_led_anim_has_arrived
ipc_setled_reroute_end:

    ; if CPU sends an error code to the SMC, then we need
    ; to cancel the LED lightshow watchdog to prevent reboots
    .org 0xCF0
ipc_displayerror_reroute_start:
    lcall ipc_displayerror_has_arrived
    nop
ipc_displayerror_reroute_end:

    ; GPU_RESET_DONE reads in reset watchdog must be patched out to avoid RRoD
    ; RGH3 does this too
    .org 0x11D4
skip_reading_gpu_reset_done_1_start:
    sjmp 0x11E8
skip_reading_gpu_reset_done_1_end:

    .org 0x11FF
skip_reading_gpu_reset_done_2_start:
    sjmp 0x1216
skip_reading_gpu_reset_done_2_end:


    .org 0x1274
resetwatchdog_reload_counter_1_start:
    mov 0x3D,#RESET_WATCHDOG_TIMEOUT_TICKS
resetwatchdog_reload_counter_1_end:

    .org 0x1282
resetwatchdog_reload_counter_2_start:
    mov 0x3D,#RESET_WATCHDOG_TIMEOUT_TICKS
resetwatchdog_reload_counter_2_end:

    ; reset watchdog patch: GetPowerUpCause arrived
    ; so jump to custom code to start the LED lightshow watchdog
    ; (I had problems monitoring g_has_getpowerupcause_arrived)
    .org 0x129F
resetwatchdog_on_success_start:
    ljmp on_reset_watchdog_done
resetwatchdog_on_success_end:

    .org 0x12A3
resetwatchdog_boot_tries_increment_nopout_start:
    nop ; 2 NOPs to kill the inc instruction
    nop
resetwatchdog_boot_tries_increment_nopout_end:

    .org 0x1E62
powerup_reroute_start:
    lcall powerup_event_callback
    nop ; because we overwrote two CLR opcodes
powerup_reroute_end:


    ; patch tilt switch read routine so it always returns 0
    .org 0x25AA
tiltsw_nullify_start:
    clr cy
    ret
tiltsw_nullify_end:


    .org 0x2D10

rgh13_common_code_start:
    ; include common rgh1.3 code
    .include "rgh13.s"
rgh13_common_code_end:

    .end
