;
; Xenon/Elpis GPIO defs
; Mostly the same as ZFJ
;

    .include "ghidra_consts.inc"

gpio_gpu_rst_n                          equ P0.1
gpio_argon_clk                          equ P0.2
gpio_argon_data                         equ P0.3
gpio_cpu_rst_n                          equ P0.6
gpio_gpu_reset_done                     equ P0.7
gpio_tiltsw_n                           equ P1.1
gpio_5vpo_enable                        equ P1.5

gpio_psu_12v_enable                     equ P2.1
gpio_powersw_n                          equ P2.7

gpio_dbg_led0                           equ FIFLG.0
gpio_dbg_led1                           equ FIFLG.1
gpio_dbg_led2                           equ FIFLG.2
gpio_dbg_led3                           equ FIFLG.3
gpio_ddc_clk                            equ FIFLG.4
gpio_av_mode0                           equ FIFLG.5
gpio_av_mode1                           equ FIFLG.6
gpio_av_mode2                           equ FIFLG.7

gpioddr_port3 equ DAT_SFR_a5
