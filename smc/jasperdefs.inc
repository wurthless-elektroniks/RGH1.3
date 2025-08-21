;
; Jasper-specific SMC defs
; Do NOT put custom defs here - this is all stock Microsoft stuff
;

    .include "gpios_zfj.inc"

g_powerswitch_pushed                    equ 021h.0
g_powerup_sm_should_run                 equ 021h.5
g_sysreset_watchdog_should_run          equ 021h.6
g_requesting_reset                      equ 021h.7

g_powerdown_sm_should_run               equ 022h.0

g_has_getpowerupcause_arrived           equ 022h.3

; these flags all trigger RRoD
g_force_rrod_3                          equ 023h.3
g_force_rrod_4                          equ 023h.4 ; raised if there's a power problem
g_force_rrod_ipc                        equ 023h.6 ; from IPC, also set by reset watchdog

g_rrod_errorcode_1        equ 05Ah
g_rrod_set_zero           equ 05Bh
g_rrod_errorcode_2        equ 05Ch
g_rrod_base_error_pattern equ 05Dh

g_power_up_cause                        equ 063h

g_shared_timer_cell                     equ 03Dh

g_rol_ledstate                          equ 0AFh
g_rol_af_cell                           equ 0B0h
g_rol_flags                             equ 062h
g_rol_update_pending                    equ 029h.0
g_rol_run_bootanim                      equ 028h.7

; important functions
msftsmc_sysreset_watchdog_exec_state_10 equ 0x12B7
