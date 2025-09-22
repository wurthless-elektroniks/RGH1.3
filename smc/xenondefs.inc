;
; Xenon-specific defs
;

    .include "gpios_xenon.inc"


g_powerswitch_pushed                    equ 021h.0
g_powerup_sm_should_run                 equ 021h.5
g_sysreset_watchdog_should_run          equ 021h.6
g_requesting_reset                      equ 021h.7

g_powerdown_sm_should_run               equ 022h.0

g_rrod_errorcode_1        equ 059h
g_rrod_errorcode_2        equ 05Bh
g_rrod_set_zero           equ 05Ah
g_rrod_base_error_pattern equ 05Ch

g_power_up_cause equ 061h

; these flags all trigger RRoD
g_force_rrod_3                          equ 023h.1
g_force_rrod_4                          equ 023h.2
g_force_rrod_ipc                        equ 023h.4

g_rol_ledstate                          equ 0D6h
g_rol_af_cell                           equ 0D7h
g_rol_flags                             equ 060h
g_rol_error_pending                     equ 028h.2
g_rol_run_bootanim                      equ 028h.3
g_rol_update_pending                    equ 028h.4

msftsmc_sysreset_watchdog_exec_state_10 equ 0x1180
msftsmc_deassert_cpu_reset equ 0x00A0
