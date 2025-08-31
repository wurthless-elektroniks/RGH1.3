# RGH1.3: Fast Boots For Fat 360s

RGH1.3 combines a glitch chip, the RGH3 loader chain, a completely unorthodox patched CB_B and a hacked SMC image to rapidly glitch the CPU.

As it ports many RGH3 features to glitch chips, it can facetiously be described as "RGH3, but with a glitch chip". However, it is much more
aggressive when monitoring the boot process in an attempt to make it as bulletproof as possible.

## WARNING 1: THIS IS EXPERIMENTAL

RGH1.3 is experimental. Who knows if this is stable in real world scenarios or not.
You can use it if you want but I can't guarantee it'll work for you. Use it at your own risk!

## WARNING 2: ACTUAL BOOT TIME IMPROVEMENTS NOT GUARANTEED

**If your console already instaboots with RGH1.2 (or RGH3), and has been instabooting for a long time, RGH1.3 will not
do much to improve your boot times.** When RGH1.3 instaboots, it boots in around the same time as RGH1.2 so
if your console already works near-perfectly with RGH1.2, the only improvement it can provide is to speed
up the occasional failed boot.

RGH1.3 is intended for the following cases:
1. When your console occasionally doesn't boot first try and you don't want to wait for SMC timeouts
2. When your console still boots reliably, but takes a few tries before it works, and you can't really
   do much else to speed up the process
3. When you're glitching the system using a microcontroller or some other device that
   can't be as precise as a CPLD/FPGA glitch chip, but is more precise than the SMC
4. When you just want to get the job done with and move on to something more important

## Explanation

Read [this](storytime.md) if you want the full explanation.

In short, RGH1.3 does the following:
- We use the intermediate CB_X stage from RGH3 to speed up the initial glitch phase
- The glitch chip gets modified RGH1.2 v2 firmware that only waits 10 ms instead of 400 ms before applying PLL slowdown
- The SMC program is hacked to read POST bits 6 and 7 and reboots early if it doesn't like what it sees
- CB_B is hacked so HWINIT toggles POST bits as it's running, allowing the SMC to monitor boot progress there
- We add a second watchdog to the SMC to reset the system if the ring of light boot animation doesn't
  play in time, which catches failed boots late in the boot process
- For the most uncooperative Jaspers, we power cycle the system if things fail very early
- As a bonus, the Ring of Light blinks throughout the boot process so you can tell where things go right or wrong

Benefits over RGH1.2:
- Instant reboots if things go wrong
- More aggressive approaches for stubborn systems (hi Jasper owners)

Benefits over RGH3:
- More precise glitching since we're using a glitch chip
- No possibility of SMC hangs causing the system to power off during the boot

Disadvantages:
- Requires a trace cut (or removal of the tilt switch) and two diodes
- RGH3 loader is known to break support for older kernels
- See "Known improvements" below for more information

## Wiring everything up

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

**IMPORTANT: The tilt switch MUST be disabled (with a trace cut) or removed.** Not like anyone will miss it, anyway.

Here's a professionally made diagram showing where you should solder things. Route wires at your own discretion.
It's better to keep your wires short and to avoid the high speed busses and power rail inductors whenever possible.

![](solderpoints_top.png)

![](solderpoints_bottom.png)

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

**If you absolutely must use the bodge capacitor:** RGH1.3 glitches so rapidly that you'll get misleading
results with the glitch chip's blinking LED. See how it behaves with RGH1.2 first to ensure that the capacitor
isn't causing problems.

## Flashing XeLL

⚠️ **ALWAYS back up your NAND first! You will lose your keyvault if you're not careful!** ⚠️

Pick the ECC you want from the `ecc/` directory, and load it into J-Runner with the "Load Glitch2 XeLL" option. Then, click "Write XeLL".

Once XeLL is written, power on the console and it'll drop to XeLL within a minute. Obviously, sooner is better.

🤬 **For super uncooperative consoles:** 🤬

If you find your console isn't reliably glitching, here's an explanation: for whatever reason those systems are grumpy and
often get up on the wrong side of the bed. When that happens, they will refuse to glitch past CB_A no matter how many times
you try, and the only way around this is to power cycle the system. Nobody knows why this happens, it's board-dependent,
and we don't know how to solve it. I've seen it happen on Jaspers, but it's known to happen on Falcons too.

If you encounter such a console, that's what the `badjasper` and `badfalcon` ECCs are for. It will hard reset your console
if the boot fails early. This method isn't bulletproof by any stretch of the imagination, and it can take 30 seconds or more
before the system boots, but it will typically succeed within 10-15 seconds.

The easiest way to tell if your system needs this workaround is to see how it cooperates either with RGH1.2 or RGH1.3.
If, for a given power cycle, it does not boot within 20 attempts on RGH1.2 or one minute on RGH1.3, but it works eventually
if you power cycle the system enough times, it will need this workaround.

**When using badjasper/badfalcon and your system bootloops for way too long and you want to power the system off, hold the Power
button and it should instantly power down.**

## Ring of Light blink codes

The blinking LED on the glitch chip rarely says a whole lot useful. As such, the SMC code is hacked
to display useful information on the Ring of Light so you can tell what's going on, or, more
importantly, where the glitch attempt failed.

Here's what the colorful twinkling lights mean:

| Color code                    | What happened              | What's supposed to happen next    |
|-------------------------------|----------------------------|-----------------------------------|
| Red                           | CB_A started               | Glitch pulse happens, CB_X runs   |
| Red/Red                       | CB_X started               | CB_B loads and runs               |
| Red/Orange                    | CB_B started               | Fusecheck/HWINIT runs             |
| Red/Orange/Red                | HWINIT running             | HWINIT doesn't crash              |
| Red/Orange/Orange             | HWINIT complete            | CD loads and executes             |
| Red/Orange/Green              | GetPowerUpCause arrived    | Kernel or XeLL loads and runs     |
| Normal Ring of Light bootanim | Kernel/XeLL finishing boot | Things work                       |

Remember that the CPU is in its most unstable state in the 100 ms following the glitch pulse.
Most boot attempts will fail with a Red or Red/Orange blink, although most of the time a Red blink
is all you'll see on a failed attempt.

These blink codes will help with tuning the glitch chip timings too. If the CPU isn't getting past
CB_A, the timing is way off or the pulse width is too large. You want it so that CB_B consistently
starts and runs HWINIT.

Also there's error handling in which case you'll get an Orange Ring of Death. (It's orange to distinguish it from a
normal RRoD.) Press SYNC and EJECT as usual to display the error code.

Error codes are:
- 2222: CPU did not make it to CB_A in time. CPU might be dying or you wired something wrong.
- 3333: POST bits 6 and 7 were not low coming out of CPU reset. Diodes are missing or wired incorrectly.
  Also check that you've disabled the tilt switch.

## Creating your updflash.bin

I doubt J-Runner will ever support this crap so here's a workaround.

In J-Runner, make sure "RGH3" is selected before building your NAND. It doesn't matter if you select 27 MHz or 10 MHz,
the buildscript will use the same SMC regardless.

Once your image is built and converted to RGH3, **don't flash it immediately**. You need to write some crap on the commandline.

**If you used the recommended timeouts above:**

`python3 convert_rgh13.py path/to/updflash.bin`

**If you used badjasper:**

- `python3 convert_rgh13.py path/to/updflash.bin --badjasper`

If you get the message

``converted to RGH1.3 successfully, happy flashing``

then your updflash.bin is ready for flashing. Flash that sucker, test your console, tweak glitch chip timings as necessary, and enjoy.

## Awesome! When's slim support?

`¯\_(ツ)_/¯`

## No, seriously, when's slim support?

RGH3 already reliably instaboots slims so there's not much need to convert this code to slims.

## Can we at least get the blinky LEDs on RGH3?

For slims, see above, there's not much point since they reliably instaboot. For phats, though, yeah, absolutely possible
and very much recommended due to the issues phats have with RGH3. In fact the tiltswitch approach was picked because
it could be easily ported to RGH3.

## What about dual NAND support?

Not supported with these xsvfs but could be added easily. Why do you need two NANDs anyway. Don't be silly. 360s are cheap these days.

## How about a port to EXT_CLK for us EXT_CLKsuckers?

EXT_CLK will benefit enormously from this technique since the instaboot rate is lower than it is on RGH1.2.
I've tried it with Raspberry Pi Pico where it was called EXT+3. It will require a couple of pullup resistors on the DBG_LED
lines on Xenon/Elpis. Zephyr can practically use the same install method as Falcon/Jasper since Zephyr is basically a Falcon with
a Waternoose. Also, EXT_CLK glitch attempts run faster than with PLL slowdown, so EXT+3 may as well be ported to the other phats too.

## Wow, this shit sucks. Why even bother doing this? RGH1.2 works for me!

In professional software development, we focus on valid use cases and reliability, not the #WorksForMe mentality and sneering elitism that
makes the 360 scene suck so much. If you are a professional modder, then please get a real job, and by that, I mean a job where
you actually have to work with team members and have a boss, and where you have to collaborate with all of them in order to keep
your position and pay the bills. Then we'll see how far that attitude gets you in real life.

## Help! I am stuck in a washing machine!

I am all in favor of healthy sexual relationships between consenting and informed adults. However, if you are actually stuck in
the washing machine or are otherwise having problems, you can open an issue or, if you've found a fix, open a pull request.
Please note though that once I finish a project I usually move on to the next one, so someone else will likely end up maintaining
this project in the future.

For bug reports, please provide the following:
- Motherboard revision (Falcon, Jasper, Tonkaset, etc.)
- GPU type if possible (shouldn't be necessary on Jasper/Tonkaset)
- SDRAM manufacturer
- Southbridge revision/date code
- etc. etc. You get the picture. More information = better.

## Known issues and improvements

- It's possible to get rid of the POST diode(s), but the only way to do that is to manually initialize the SMC FIFOs at the
  start of CB_B, when the CPU is still coming out of the glitch and can be in an unstable state, so it wouldn't be that
  reliable anyway. Plus which, most failed glitch attempts will die within the first 100 ms, which means we have to monitor
  the POST lines anyway.

- The RGH3 bootloader chain is known to break compatibility with older dashboards (Blades for sure) and those issues likely
  apply here too. The cause isn't clear, it might have to do with the use of the manufacturing CB_A (retail 9188 and 5772
  are practically the same code byte for byte). The good news is that RGH1.3 no longer needs precise timings on the SMC
  side like RGH3 does so we might be able to kill that one easily.

- It's possible to speed up resets on failed attempts simply by resetting the CPU. However, the CPU can go into
  a coma on failed attempts, which will cause it to lock up and ignore any attempts to reset it.

- 15432 is working on RGH3 improvements that will need to be ported to this method once they're released and confirmed
  working across multiple consoles.

## Credits

Some idiot threw this together in an afternoon. Here are people whose work it was based on.

- GliGli, Tiros, cOz and everyone else who got this reset glitching madness started in the first place
- 15432 for RGH1.2, RGH3, and a lot of code that I modified and used in development
- Octal450 for RGH1.2v2, which the Matrix VHDL source is a modification of
- Mate Kukri for being super knowledgable about low level 360 stuff, for doing HWINIT reverse engineering,
  for tearing the pants off of all BadUpdate doubters, and generally being a chill guy
- Mena for also being a chill guy
- jnftech for the wonderful PCB images
- Nadaman for the fancy ConsoleMods.org-themed XeLL

## License

Public domain
