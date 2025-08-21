# RGH1.3 Matrix/Coolrunner XSVFs

These are named in the form `rgh13_pwX_dY.xsvf`, where

- `pw` is the glitched reset pulse width (2, 3 or 4), and
- `d` is the delay before the glitch pulse (between 349816 and 349826 cycles)

So `rgh13_pw4_d21.xsvf` means "at POST 0xDA, delay for 349821 cycles and then do a glitch pulse that is 4 cycles wide".
