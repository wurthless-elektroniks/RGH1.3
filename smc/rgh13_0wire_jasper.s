
ifndef ZEPHYR
    ; zephyr has a jumper where checkstop normally is.
    ; if this is 1, then patch out checkstop checks always.
    ZEPHYR equ 0
endif

    ; horrible hack 
ifdef JASPER_FOR_FALCON
    JASPER equ 0

    ; from rgh13_falcon.s, but also seems to work fine without this
    RESET_WATCHDOG_TIMEOUT_TICKS equ 137
else
    JASPER equ 1
    
    ; timeout for normal reset watchdog
    ; default for jasper is 100 * 20 * 2 = 4000 ms
    RESET_WATCHDOG_TIMEOUT_TICKS equ 100
endif

    .include "jasperdefs.inc"


RGH13_1WIRE_POST equ gpio_gpu_reset_done

; ------------------------------------------------------------------------------------

; these variables will be automatically zeroed out on reset
g_holdpowerbutton_counter               equ 093h
g_turboreset_sm_state                   equ 094h
g_turboreset_sm_counter                 equ 095h
g_ledlightshow_watchdog_state           equ 096h
g_ledlightshow_watchdog_death_counter   equ 097h

; these variables will persist past a reboot
; see init_memclear_patch_start
g_hardreset_sm_init                     equ 098h
g_hardreset_sm_state                    equ 099h
g_power_up_cause_backup                 equ 09Ah


; 6752 on my test Jasper toggles A2/E2 only once, but the delay is somewhere around 660 ms.
; 
; default value is 35 * 20 = 700 ms
CBB_HWINIT_POST6_TOGGLE_TIMEOUT equ 35

; ------------------------------------------------------------------------------------
;
; Patchlist
;
; ------------------------------------------------------------------------------------
    .org 0x0000

if ZEPHYR=1
    .include "rgh13_jasper_chkstop_decls.inc"
endif

    mov dptr,#mainloop_reorg_start
    mov dptr,#mainloop_reorg_end

    mov dptr,#init_memclear_patch_start
    mov dptr,#init_memclear_patch_end

    mov dptr,#ipc_command_bit7_received_start
    mov dptr,#ipc_command_bit7_received_end

    mov dptr,#ipc_command_12_reroute_start
    mov dptr,#ipc_command_12_reroute_end
        
    mov dptr,#ipc_setled_reroute_start
    mov dptr,#ipc_setled_reroute_end

    mov dptr,#on_reset_done_reroute_start
    mov dptr,#on_reset_done_reroute_end

    mov dptr,#resetwatchdog_reload_counter_1_start
    mov dptr,#resetwatchdog_reload_counter_1_end
    mov dptr,#resetwatchdog_reload_counter_2_start
    mov dptr,#resetwatchdog_reload_counter_2_end
    mov dptr,#resetwatchdog_on_success_start
    mov dptr,#resetwatchdog_on_success_end
    mov dptr,#resetwatchdog_on_timeout_start
    mov dptr,#resetwatchdog_on_timeout_end

    mov dptr,#powerup_reroute_start
    mov dptr,#powerup_reroute_end
    
    .include "rgh13_jasper_softreset_callback_decls.inc"

    ; there are SMC commands that can use otherwise unused SMC space
    ; for storing a bunch of variables. i don't think the system ever
    ; uses these, so we disable all writes and return 0 for all reads
    mov dptr,#ipc_debugram_write_patch_start
    mov dptr,#ipc_debugram_write_patch_end
    mov dptr,#ipc_debugram_read_patch_start
    mov dptr,#ipc_debugram_read_patch_end

    mov dptr,#rgh13_common_code_start
    mov dptr,#rgh13_common_code_end

    .byte 0 ; end of list

; ------------------------------------------------------------------------------------
;
; Patches
;
; ------------------------------------------------------------------------------------

    ; mainloop re-org
    .org 0x07C2
mainloop_reorg_start:
    ; we drop this reorg in where the debug led statemachine was
    ; (it's NOP'd out on hacked SMCs)
    lcall 0x1DE9                        ; power event monitor (checks for button presses and acts on them)
    lcall 0x119B                        ; no idea what this does
    lcall 0x1072                        ; powerup statemachine
    lcall 0x12D5                        ; reset watchdog (reboots if GetPowerUpCause isn't received in time)
    lcall 0x1127                        ; reset statemachine (performs actual hardware reset sequence)
    lcall 0x0EA9                        ; powerdown statemachine
    lcall rgh13_statemachines_exec      ; our custom code below

    ; should end at 0x07D7 - if it doesn't, we've broken the build
mainloop_reorg_end:

    ; make room for our hard reset state machine variables
    ; so they are in a safe space and don't get killed on reboot
    .org 0x7EC
init_memclear_patch_start:
    mov r2,#0x1A ; stop memory clear at 0x97, so 0x98, 0x99, 0x9A don't get overwritten on reboot
init_memclear_patch_end:

    .org 0x843
ipc_command_bit7_received_start:
    ljmp ipc_command_bit7_received_reroute
ipc_command_bit7_received_end:

    .org 0xA9C
ipc_command_12_reroute_start:
    ljmp ipc_command_12_received_reroute
ipc_command_12_reroute_end:

    ; reroute any power LED changes (via IPC) to custom code below
    .org 0xC77
ipc_setled_reroute_start:
    ljmp ipc_led_anim_has_arrived
ipc_setled_reroute_end:

    ; if CPU sends an error code to the SMC, then we need
    ; to cancel the LED lightshow watchdog to prevent reboots
    .org 0xCF5
ipc_displayerror_reroute_start:
    lcall ipc_displayerror_has_arrived
    nop
ipc_displayerror_reroute_end:

    .org 0x11DB
on_reset_done_reroute_start:
    lcall cpu_reset_handler
on_reset_done_reroute_end:

    .org 0x1279
resetwatchdog_reload_counter_1_start:
    mov 0x3D,#RESET_WATCHDOG_TIMEOUT_TICKS
resetwatchdog_reload_counter_1_end:

    .org 0x1290
resetwatchdog_reload_counter_2_start:
    mov 0x3D,#RESET_WATCHDOG_TIMEOUT_TICKS
resetwatchdog_reload_counter_2_end:

    ; reset watchdog patch: GetPowerUpCause arrived
    ; so jump to custom code to start the LED lightshow watchdog
    ; (I had problems monitoring g_has_getpowerupcause_arrived)
    .org 0x12AD
resetwatchdog_on_success_start:
    ljmp on_reset_watchdog_done
resetwatchdog_on_success_end:

    .org 0x12BA
resetwatchdog_on_timeout_start:
    lcall on_reset_watchdog_timeout
    ljmp  0x12D1
resetwatchdog_on_timeout_end:

    .org 0x1E7D
powerup_reroute_start:
    lcall powerup_event_callback
    nop ; because we overwrote two CLR opcodes
powerup_reroute_end:

if ZEPHYR=1
    .include "rgh13_jasper_chkstop_patches.s"
endif

    .include "rgh13_jasper_debugram_stubout.s"
    .include "rgh13_jasper_softreset_callback_patches.s"

    .org 0x2D73
rgh13_common_code_start:

cpu_reset_handler:
    lcall on_reset_watchdog_deassert_cpu_reset
    ljmp msftsmc_deassert_cpu_reset

    .include "rgh13_0wire.s"

rgh13_common_code_end:

    .end
