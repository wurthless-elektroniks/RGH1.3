;
; Common I/O ports shared between Zephyr, Falcon and Jasper boards
; (Zephyr is really just a Falcon with a Waternoose)
;


; hardware I/Os
gpio_cpu_rst_n                          equ P0.6
gpio_gpu_reset_done                     equ P0.7
gpio_tiltsw_n                           equ P1.1
gpio_5vpo_enable                        equ P1.5
gpio_powersw_n                          equ P2.7
