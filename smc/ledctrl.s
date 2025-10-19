
; LED blink patterns
;
; assuming the system is lying flat:
; bit 0/4 - top left
; bit 1/5 - top right
; bit 2/6 - bottom left
; bit 3/7 - bottom right

;                                  ggggrrrr
;                                  32103210
LEDPATTERN_RED               equ 0b00000001

;                                  ggggrrrr
;                                  32103210
LEDPATTERN_RED_RED           equ 0b00000011

;                                  ggggrrrr
;                                  32103210
LEDPATTERN_RED_ORANGE        equ 0b00100011

;                                  ggggrrrr
;                                  32103210
LEDPATTERN_RED_ORANGE_RED    equ 0b00100111

;                                  ggggrrrr
;                                  32103210
LEDPATTERN_RED_ORANGE_ORANGE equ 0b01100111

;                                  ggggrrrr
;                                  32103210
LEDPATTERN_RED_ORANGE_GREEN  equ 0b01100011

;
; Common function to set Ring of Light LEDs
; a - LED states (upper 4 bits green, lower 4 bits red)
;
rol_set_leds:
    mov r0,#g_rol_ledstate
    mov @r0,a

    jz _clear_led_priority_bit

    ; bits 5/7 must be set for argon sm to display things
    ; bit 5 is apparently some "high priority" bit and when it is set
    ; nothing else will display on the ring
    mov a,g_rol_flags
    orl a,#0b10100000
_rol_set_leds_finish:
    mov g_rol_flags,a
    
    ; and this bit has to be set too
    setb g_rol_update_pending
    ret

    ; clear priority flag when turning LEDs off
_clear_led_priority_bit:
    mov a,g_rol_flags
    anl a,#0b11011111 
    sjmp _rol_set_leds_finish