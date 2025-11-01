'''
RGH1.3 in Micropython, single wire POST edition
'''
from time import sleep, ticks_us
from machine import Pin,mem32,freq
import rp2
from rp2 import PIO

# ------------------------------------------------------------------------
#
# Important Configuration Stuff
#
# ------------------------------------------------------------------------

RESET_DELAY            = 349821  # <-- start at 349821

# scroll down to PIO program to change pulse width

# ------------------------------------------------------------------------

TEST_JIG = False

RP2040_ZERO = False
if RP2040_ZERO is True:
    # RP2040 Zero, pin configuration is temporary
    # RP2040 Zero clones can run the stock RPi Pico Micropython build.
    # note that it might be unstable - testing continues
    PIN_POST_1 = 7
    PIN_CPU_RESET_IN = 5
    SET_PIN_BASE = 10
elif TEST_JIG is True:
    # rpi pico with pinout matching 8-wire POST version (debug/development only)
    PIN_POST_1 = 16
    PIN_CPU_RESET_IN = 10
    SET_PIN_BASE = 13  # 13 = PLL, 14 = reset output
else:
    # rpi pico
    PIN_POST_1 = 13
    PIN_CPU_RESET_IN = 12
    SET_PIN_BASE = 14  # 14 = PLL, 15 = reset output


CPU_RESET_OUT     = Pin(SET_PIN_BASE+1, Pin.IN) # will switch to output later
CPU_PLL_BYPASS    = Pin(SET_PIN_BASE+0, Pin.OUT)

DBG_CPU_POST_OUT6  = Pin(PIN_POST_1, Pin.IN, Pin.PULL_UP)
CPU_RESET_IN       = Pin(PIN_CPU_RESET_IN, Pin.IN, Pin.PULL_UP) # to FT2P11 under southbridge

@rp2.asm_pio(set_init=[PIO.OUT_LOW, PIO.IN_LOW])
def rgh12():
    pull(noblock)                         # 0
    mov(x, osr)                           # 1
    pull(noblock)                         # 2
    mov(y, osr)                           # 3
    wait(1, pin, 0)                       # 4
    wait(0, pin, 0)                       # 5
    wait(1, pin, 0)                       # 6
    wait(0, pin, 0)                       # 7
    wait(1, pin, 0)                       # 8
    wait(0, pin, 0)                       # 9
    wait(1, pin, 0)                       # 10
    wait(0, pin, 0)                       # 11
    wait(1, pin, 0)                       # 12
    wait(0, pin, 0)                       # 13
    wait(1, pin, 0)                       # 14
    wait(0, pin, 0)                       # 15
    label("16")
    jmp(x_dec, "16")                      # 16
    set(pins, 1)                          # 17
    wait(1, pin, 0)                       # 18
    label("19")
    jmp(y_dec, "19")                      # 19
    set(pindirs, 3)                  [3]  # <-- PULSE WIDTH: USE [1], [2] OR [3]
    set(pins, 3)                          # 21
    set(pindirs, 1)                       # 22
    set(y, 31)                       [31] # 23
    label("24")
    set(x, 31)                       [31] # 24
    label("25")
    nop()                            [13] # 25
    jmp(x_dec, "25")                 [31] # 26
    jmp(y_dec, "24")                 [31] # 27
    set(x, 24)                       [14] # 28
    label("29")
    jmp(x_dec, "29")                 [31] # 29
    set(pins, 0)                          # 30
    wrap_target()
    nop()                                 # 31
    wrap()

pio_sm = None

def init_sm(reset_assert_delay):
    global pio_sm
    pio_sm = rp2.StateMachine(0, rgh12, freq = 48000000, in_base=DBG_CPU_POST_OUT6, set_base=CPU_PLL_BYPASS)

    pio_sm.active(0)
    pio_sm.restart()
    pio_sm.active(0)
    print("restarted sm")

    # change reset drive params
    mem32[0x4001c004 + ((SET_PIN_BASE+1)*4)]   = 0b01110011
    if mem32[0x4001c004 + ((SET_PIN_BASE+1)*4)] != 0b01110011:
        raise RuntimeError("cannot set I/O drive...")
    
    # the "pll delay" is the amount of time we wait between POST 0xD8
    # and when CPU_PLL_BYPASS is asserted.
    # 0xD8-0xD9 length is about 6.8 ms, 0xD9 PLL delay is about 10ms
    pll_delay = int(0.016  * 48_000_000)

    # the "pulse delay" is how long to wait before asserting /RESET after POST 0xDA,
    # give or take a few cycles for the PIO to do stuff.
    #
    # to find the right timing for this, check the POST code when the reset happens.
    #
    # when using a large reset pulse (i.e., you're intentionally doing a full CPU reset),
    # if 0x00 is returned, the CPU rebooted too early.
    # if 0xF2 is returned, the hash check failed and the value is too high.
    #
    # the delay should be 7200-7300 microseconds, with RGH1.2 V2 timing file 21's
    # preferred value being 7287.9375 microseconds (349821 cycles).
    # if you find the 0xDA -> 0xF2 transition is nowhere near this value,
    # something is wrong.
    reset_delay = reset_assert_delay

    print("using these settings")
    print(f"- pll delay {pll_delay}")
    print(f"- reset delay {reset_delay}")

    # populate FIFO - when PIO starts, it'll grab both these values immediately
    pio_sm.put(pll_delay)
    pio_sm.put(reset_delay)
    print("buffered FIFO")

def do_reset_glitch():
    pio_sm.active(1)
    
    # do not return until CPU has been reset by the SMC
    while CPU_RESET_IN.value() == 1:
        pass
    
def do_reset_glitch_loop():
    # this is the key to the whole thing - you have to set frequency
    # to a multiple of 12 MHz, or this shit won't work
    freq(192000000)

    # in a 4-wire configuration:
    # 21 seems to work okay for falcon
    # 24 seems to work okay for jasper
    # this timing value will depend on your wiring, obvs
    reset_trial = RESET_DELAY
    while True:
        print(f"start trial of: {reset_trial}")
        init_sm(reset_trial)

        # wait for the CPU to go into reset so we don't count POSTs incorrectly
        while CPU_RESET_IN.value() == 1:
            pass

        while CPU_RESET_IN.value() == 0:
            pass

        print("CPU active")
        do_reset_glitch()
        print("glitch attempted, going idle...")
