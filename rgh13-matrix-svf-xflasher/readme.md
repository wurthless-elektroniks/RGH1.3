# RGH1.3 Matrix/Coolrunner SVFs for XFlasher users

These are named in the form `rgh13_pwX_dY.svf`, where

- `pw` is the glitched reset pulse width (2, 3 or 4), and
- `d` is the delay before the glitch pulse (between 349816 and 349826 cycles)

So `rgh13_pw2_d21.svf` means "at POST 0xDA, delay for 349821 cycles and then do a glitch pulse that is 2 cycles wide".

The most cooperative systems shouldn't need a pulse width more than 2 cycles wide. Pulse widths of 3 and 4 are provided in case
your console prefers a wider pulse width.

Please note: I don't have an XFlasher (I am a JR Programmer grandpa) so feedback and bugreports from XFlasher users is very welcome.
