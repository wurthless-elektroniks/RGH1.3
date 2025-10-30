# EXT+3 installation, SMC_CPU_CHKSTOP_DETECT for POST 7, Falcon/Jasper

The Zephyr board can be idealized as a "Falcon with a Waternoose" and any Falcon or Jasper SMC can
program can be used with it. There is, however, one important difference, and it's that the I/O
used for checkstop detection on Falcon and Jasper is instead a debug jumper on Zephyr.

On Zephyr the line is actually called SB_DETECT, and it functions as a jumper. While the Zephyr
board was in development, Microsoft were bringing up the R0 XSB southbridge, and they added this
jumper so the program could tell if the southbridge was a G0 or R0 southbridge. In production however
Zephyrs universally used the R0 southbridge.

To err on the side of caution, **you CANNOT use this method if R2N27 is populated**. It should always
be empty on production boards, but check for it anyway.

## And now, the actual wiring

The glitch chip wiring is the same as EXT_CLK, but here it is again in case you're doing a new install.

- A = /CPU_RST_1V1P_N
- B = FT6U1 (POST bit 0)
- C = STBY_CLK
- F = CPU_EXT_CLK_EN

You will also need two diodes (1N400x slow power diodes will work, speed's not critical here):
- GPU_RESET_DONE/SMC_POST --> diode --> FT6U2 (POST bit 6)
- FT2N5 --> diode --> FT6U8 (POST bit 7)

Diagrams TODO.

Connect your Matrix or whatever to your programmer, **MAKING SURE YOU AREN'T CONNECTING IT IN REVERSE
POLARITY BECAUSE YOU WILL FRY THE GLITCH CHIP IF YOU DO.** Most Matrix chips don't come with a pin
header; if you're looking for one, it's just standard 2.54mm pitch male pins. You can get long strips of them
and cut them to fit.

In J-Runner, click "Program Timing Files". Then, select Program -> Choose timing file, and choose the
timing file you want to program. You should see the thing program your Matrix. Awesome job, your chip's
programmed. You might need to program it multiple times before you're satisfied, so keep your programmer
around.

The timing file you should start with is `ext3_192mhz_d8008_pw2.xsvf`. Play around with them until you find
one that your console likes. Additional pulse widths are provided in case your console likes wider
pulse widths.
