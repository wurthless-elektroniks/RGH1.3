    .org 0x1279
resetwatchdog_reload_counter_1_start:
    mov 0x3D,#RESET_WATCHDOG_TIMEOUT_TICKS
resetwatchdog_reload_counter_1_end:

    .org 0x1290
resetwatchdog_reload_counter_2_start:
    mov 0x3D,#RESET_WATCHDOG_TIMEOUT_TICKS
resetwatchdog_reload_counter_2_end:

    .org 0x129E
resetwatchdog_reboot_on_timeout_start:
    ; treat normal SMC timeout as a reboot case instead of an error case
    ljmp reset_via_watchdog
resetwatchdog_reboot_on_timeout_end:

    ; reset watchdog patch: GetPowerUpCause arrived
    ; so jump to custom code to start the LED lightshow watchdog
    ; (I had problems monitoring g_has_getpowerupcause_arrived)
    .org 0x12AD
resetwatchdog_on_success_start:
    ljmp on_reset_watchdog_done
resetwatchdog_on_success_end:

    .org 0x12BA
resetwatchdog_on_error_start:
    ljmp on_reset_watchdog_error_case
resetwatchdog_on_error_end:

