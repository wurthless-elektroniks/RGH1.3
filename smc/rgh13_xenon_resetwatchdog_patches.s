

    .org 0x1148
resetwatchdog_release_cpu_reset_start:
    lcall cpu_reset_handler
    mov 0x3D,#RESET_WATCHDOG_TIMEOUT_TICKS
resetwatchdog_release_cpu_reset_end:

    .org 0x115C
resetwatchdog_reload_counter_2_start:
    mov 0x3D,#RESET_WATCHDOG_TIMEOUT_TICKS
resetwatchdog_reload_counter_2_end:

    .org 0x116D
resetwatchdog_reboot_on_timeout_start:
    ; treat normal SMC timeout as a reboot case instead of an error case
    ljmp reset_via_watchdog
resetwatchdog_reboot_on_timeout_end:

    .org 0x117C
resetwatchdog_on_success_start:
    ljmp on_reset_watchdog_done
resetwatchdog_on_success_end:

    .org msftsmc_sysreset_watchdog_exec_state_10
resetwatchdog_on_timeout_start:
    ljmp on_reset_watchdog_error_case
resetwatchdog_on_timeout_end:
