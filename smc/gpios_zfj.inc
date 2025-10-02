;
; Common I/O ports shared between Zephyr, Falcon and Jasper boards
; (Zephyr is really just a Falcon with a Waternoose)
;

    .include "ghidra_consts.inc"

; hardware I/Os
gpio_cpu_rst_n                          equ P0.6
gpio_gpu_reset_done                     equ P0.7
gpio_tiltsw_n                           equ P1.1
gpio_5vpo_enable                        equ P1.5

gpio_psu_12v_enable                     equ P2.1
gpio_powersw_n                          equ P2.7

gpio_dbg_led0                           equ FIFLG.0
gpio_vreg_v5p0_vmem_pwrgd               equ FIFLG.1
gpio_ana_vrst_ok                        equ FIFLG.2
gpio_gpu_tclk_r                         equ FIFLG.3
gpio_hdmi_ddc_clk                       equ FIFLG.4
gpio_av_mode0                           equ FIFLG.5
gpio_av_mode1                           equ FIFLG.6
gpio_av_mode2                           equ FIFLG.7

gpio_smc_cpu_chkstop_detect             equ TR2
gpio_ext_pwr_on_n                       equ RCLK