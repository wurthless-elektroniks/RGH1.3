
    ; 0x22B8: set pin directions among other things.
    ; port3 pin 3 is left as an output as it strobes GPU JTAG TCLK
    ; on GPU reset (unnecessary behavior, but we can leave it alone)
    ;
    ; 0x22C1 - change to ORL DAT_SFR_a5,#0xF7
    ; 0x22EE - change to MOV DAT_SFR_a5,#0xF7
    .org 0x22C1
port3_ddr_set_all_inputs_1_start:
    orl gpioddr_port3,#0xF7
port3_ddr_set_all_inputs_1_end:

    ; 0x22D0: enable pullups on port 3 pins 0,1,2
    ; (do NOT set on pin 3 as that's tied to GPU JTAG)
    .org 0x22D0
port3_pinmode_set_pullups_start:
    mov 0A1h,#0x07
port3_pinmode_set_pullups_end:

    .org 0x22EE
port3_ddr_set_all_inputs_2_start:
    mov gpioddr_port3,#0xF7
port3_ddr_set_all_inputs_2_end:

