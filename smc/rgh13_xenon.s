;
; RGH1.3 code for Xenon/Elpis boards
; Actually only really useful for EXT+3
;

    .include "xenondefs.inc"

RGH13_POST_6 equ gpio_dbg_led1
RGH13_POST_7 equ gpio_dbg_led2

; TODO: find safe value for this - for now we're leaving it be
RESET_WATCHDOG_TIMEOUT_TICKS equ 0xAF

CBB_HWINIT_POST6_TOGGLE_TIMEOUT equ 254

; define EXT_PLUS_3 so we get faster CB_A timeouts
; (PLL is basically useless on Waternoose)
EXT_PLUS_3 equ 1

; ------------------------------------------------------------------------------------

; the Xenon SMC program is really weird in that it leaves large chunks of memory uninitialized
;
; - 0x07E5: clear 0x2F~0x35
; - 0x0808: clear 0x35~0x67
; - 0x07DE: clear 0xBD~0xC2
; - 0x0801: clear 0xC2~0xE1
;
; 0xBC and upward seem unused so we use that.
; first up, variables that are supposed to get zeroed out on reset
; (0xBD clear loop will be patched to zero them)

VARBASE equ 0B0h
g_holdpowerbutton_counter               equ VARBASE+0
g_turboreset_sm_state                   equ VARBASE+1
g_turboreset_sm_counter                 equ VARBASE+2
g_ledlightshow_watchdog_state           equ VARBASE+3
g_ledlightshow_watchdog_death_counter   equ VARBASE+4

; above that are variables that will persist between resets
g_hardreset_sm_init                     equ VARBASE-3
g_hardreset_sm_state                    equ VARBASE-2
g_power_up_cause_backup                 equ VARBASE-1

; ------------------------------------------------------------------------------------
;
; Patchlist
;
; ------------------------------------------------------------------------------------
    .org 0x0000

    mov dptr,#gpu_reset_deassert_start
    mov dptr,#gpu_reset_deassert_end

    mov dptr,#mainloop_reorg_start
    mov dptr,#mainloop_reorg_end

    mov dptr,#memclear_reposition_start
    mov dptr,#memclear_reposition_end

    mov dptr,#ipc_setled_reroute_start
    mov dptr,#ipc_setled_reroute_end

    mov dptr,#resetwatchdog_release_cpu_reset_start
    mov dptr,#resetwatchdog_release_cpu_reset_end
    mov dptr,#resetwatchdog_reload_counter_2_start
    mov dptr,#resetwatchdog_reload_counter_2_end
    mov dptr,#resetwatchdog_on_success_start
    mov dptr,#resetwatchdog_on_success_end
    mov dptr,#resetwatchdog_on_timeout_start
    mov dptr,#resetwatchdog_on_timeout_end

    mov dptr,#powerup_reroute_start
    mov dptr,#powerup_reroute_end

    mov dptr,#avpack_reroute_1_start
    mov dptr,#avpack_reroute_1_end
    mov dptr,#avpack_reroute_2_start
    mov dptr,#avpack_reroute_2_end

    mov dptr,#dbgled_readfcn_stubout_start
    mov dptr,#dbgled_readfcn_stubout_end

    mov dptr,#port3_ddr_set_all_inputs_1_start
    mov dptr,#port3_ddr_set_all_inputs_1_end
    mov dptr,#port3_ddr_set_all_inputs_2_start
    mov dptr,#port3_ddr_set_all_inputs_2_end

    mov dptr,#rgh13_common_code_start
    mov dptr,#rgh13_common_code_end

    .byte 0 ; end of list

; ------------------------------------------------------------------------------------
;
; Patches
;
; ------------------------------------------------------------------------------------

    ; 0x0078: function strobes FIFLG.3 several times before bringing GPU out of reset
    ; so remove that unnecessary behavior
    .org 0x0078
gpu_reset_deassert_start:
    setb gpio_gpu_rst_n
    ret
gpu_reset_deassert_end:


    .org 0x7B6
mainloop_reorg_start:
    ; we drop this reorg in where the debug led statemachine was
    ; (it's NOP'd out on hacked SMCs)
    lcall 0x1CDE                        ; power event monitor (checks for button presses and acts on them)
    lcall 0x1064                        ; ???
    lcall 0x0F55                        ; powerup statemachine
    lcall 0x11C4                        ; reset watchdog (reboots if GetPowerUpCause isn't received in time)
    lcall 0x0FF6                        ; reset statemachine (performs actual hardware reset sequence)
    lcall 0x0D94                        ; powerdown statemachine
    lcall rgh13_statemachines_exec      ; our custom code below
mainloop_reorg_end:

    ; 0x07DE - zero out memory starting from 0xB8 instead
    ; so our work vars get init'd to zero
    .org 0x07DE
memclear_reposition_start:
    mov r0,#VARBASE
    mov r2,#(0xC2-VARBASE)
memclear_reposition_end:

    .org 0xB93
ipc_setled_reroute_start:
    ljmp ipc_led_anim_has_arrived
ipc_setled_reroute_end:


    .org 0x1148
resetwatchdog_release_cpu_reset_start:
    lcall cpu_reset_handler
    mov 0x3D,#RESET_WATCHDOG_TIMEOUT_TICKS
resetwatchdog_release_cpu_reset_end:

    .org 0x115C
resetwatchdog_reload_counter_2_start:
    mov 0x3D,#RESET_WATCHDOG_TIMEOUT_TICKS
resetwatchdog_reload_counter_2_end:

    .org 0x117C
resetwatchdog_on_success_start:
    ljmp on_reset_watchdog_done
resetwatchdog_on_success_end:

    .org msftsmc_sysreset_watchdog_exec_state_10
resetwatchdog_on_timeout_start:
    lcall on_reset_watchdog_timeout
    ljmp  0x1197
resetwatchdog_on_timeout_end:


    .org 0x1212
avpack_reroute_1_start:
    lcall avpack_detect_reroute
avpack_reroute_1_end:

    .org 0x1235
avpack_reroute_2_start:
    lcall avpack_detect_reroute
avpack_reroute_2_end:

    .org 0x1D72
powerup_reroute_start:
    lcall powerup_event_callback
    nop
powerup_reroute_end:


    ; 0x224E: reads dbg leds
    ; can likely skip this, and use the rest of the function as free space
    .org 0x224E
dbgled_readfcn_stubout_start:
    ret

; quality of life improvement: if no avpack present, pretend a composite cable
; is plugged in, so the system can boot headless without flashing the four red lights
;
; from https://gamesx.com/wiki/doku.php?id=av:xbox360av
; the avpack mode lines are pulled up by resistors on the motherboard
; and the cables themselves pull the pins low.
; if all avpack bits are 1, nothing's present.
avpack_detect_reroute:
    lcall 0x2506 ; query avpack id and other stuff (bits 4~2 will be avpack id)
    push acc
    anl a,#0b11100
    cjne a,#0b11100,_avpack_is_present
    pop acc
    anl a,#0b11100011
    ret
_avpack_is_present:
    pop acc
    ret

dbgled_readfcn_stubout_end:


    ; 0x22B8: set pin directions among other things.
    ; we'll set all pins on port 3 to inputs.
    ; 0x22C1 - change to ORL DAT_SFR_a5,#0xFF
    ; 0x22EE - change to MOV DAT_SFR_a5,#0xFF
    .org 0x22C1
port3_ddr_set_all_inputs_1_start:
    orl gpioddr_port3,#0xFF
port3_ddr_set_all_inputs_1_end:
    .org 0x22EE
port3_ddr_set_all_inputs_2_start:
    mov gpioddr_port3,#0xFF
port3_ddr_set_all_inputs_2_end:



    .org 0x2DAA
rgh13_common_code_start:


cpu_reset_handler:
    lcall on_reset_watchdog_deassert_cpu_reset
    ljmp msftsmc_deassert_cpu_reset

    .include "rgh13.s"

rgh13_common_code_end:

    .end