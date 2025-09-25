# RGH1.3 installation, TILTSW for POST 7, Falcon/Jasper

The tiltswitch RGH1.3 method was the first to be created. It requires you disable or remove the tiltswitch
to reuse the tiltswitch line as an input for POST bit 7.

The tiltswitch was chosen because:
- It's a line that's pulled up to 3v3 internally
- It makes for slightly cleaner wire routing
- It isn't externally accessible
- If the tiltswitch is disabled by a trace cut, it can be reconnected later without much fuss

The downside is that you lose the tiltswitch's functionality, which, let's be honest, is just to orient
the Ring of Light patterns differently if your console is standing up or lying down. It's not a major loss
but I'd understand why some people would want to keep it.

## Installing

Now first up is how you wire up your glitch chip. It's the exact same pinout as RGH1.2.
In case you need a reminder, here's the list:

Matrix:
- A = /CPU_RST_1V1P_N
- B = FT6U1 (POST bit 0)
- C = STBY_CLK
- F = CPU_PLL_BYPASS

You will also need two diodes (1N400x slow power diodes will work, speed's not critical here):
- GPU_RESET_DONE/SMC_POST --> diode --> FT6U2 (POST bit 6)
- TILTSW --> diode --> FT6U8 (POST bit 7)

**WE MUST REPEAT: The tilt switch MUST be disabled (with a trace cut) or removed.** Not like anyone will miss it, anyway.

Here's a professionally made diagram showing where you should solder things. Route wires at your own discretion.
It's better to keep your wires short and to avoid the high speed busses and power rail inductors whenever possible.

![](rgh13_points_top.png)

![](rgh13_points_bottom.png)

Connect your Matrix or whatever to your programmer, **MAKING SURE YOU AREN'T CONNECTING IT IN REVERSE
POLARITY BECAUSE YOU WILL FRY THE GLITCH CHIP IF YOU DO.** Most Matrix chips don't come with a pin
header; if you're looking for one, it's just standard 2.54mm pitch male pins. You can get long strips of them
and cut them to fit.

In J-Runner, click "Program Timing Files". Then, select Program -> Choose timing file, and choose the
timing file you want to program. You should see the thing program your Matrix. Awesome job, your chip's
programmed. You might need to program it multiple times before you're satisfied, so keep your programmer
around.

The timing file you should start with is `rgh13_pw2_d21.xsvf`. Play around with them until you find
one that your console likes. Additional pulse widths are provided in case your console likes wider
pulse widths.

**For people wanting to use the bodge capacitor:** RGH1.3 glitches so rapidly that you'll get misleading
results with the glitch chip's blinking LED. The SMC code can catch major CPU issues (see error handling
info below) but it won't be able to diagnose how much noise is on the PLL line.

Tips for capacitor users:
- 68 nF (0.068 uF) and 100 nf (0.1 uF) are the common capacitor values
- Matrix users MUST ensure the glitch chip AND the capacitor are properly grounded or there will be too much noise
- You can see how the glitch chip LED behaves under RGH1.2 to better diagnose PLL noise
