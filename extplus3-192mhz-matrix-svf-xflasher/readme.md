# EXT+3 192 MHz Matrix/Coolrunner SVFs for XFlasher users

These are named in the form `ext3_192mhz_pw2_d8002.svf`, where

- `pw` is the glitched reset pulse width (2 or 3), and
- `d` is the delay before the glitch pulse (between 117998 and 118010 cycles)

So `ext3_192mhz_pw2_d8002.svf` means "at POST 0xDA, delay for 118002 cycles and then do a glitch pulse that is 2 cycles wide".

With CPU_EXT_CLK_EN, the CPU can handle pulse widths of 2 or 3, so both pulse widths are provided here.
