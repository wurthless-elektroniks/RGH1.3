# RGH1.3 and EXT+3: Fast Boots For Fat 360s

RGH1.3 combines a glitch chip, the RGH3 loader chain, a completely unorthodox patched CB_B and a hacked SMC image to rapidly glitch the CPU.

As it ports many RGH3 features to glitch chips, it can facetiously be described as "RGH3, but with a glitch chip". However, it is much more
aggressive when monitoring the boot process in an attempt to make it as bulletproof as possible.

Also included in this project is EXT+3. It is the EXT_CLK equivalent of RGH1.3, allowing for much faster boot attempts on Xenon and Zephyr
consoles.

## WARNING 1: THIS IS IN BETA

RGH1.3 is no longer experimental and can be called a beta, but it still has bugs that need to be killed.
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
- The SMC program is hacked to read POST bits 6 and 7 (or receives that data from the CPU via IPC) and reboots early if it doesn't like what it sees
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
- ~~Requires two diodes and occasional bodges/trace cuts~~ Not required anymore, but still recommended for more stubborn consoles
- See "Known improvements" below for more information

## Wiring everything up

This depends on your board and method:

### Two-wire POST methods

The two-wire POST methods are the oldest and probably the fastest. The code relies entirely on monitoring boot progress
via the POST pins, and as such they require two POST diodes and occasionally some bodges.

- [EXT+3 for Xenon/Elpis, 2-wire method](install_ext3_xenon.md)
- [RGH1.3 for Falcon/Jasper, chkstop method](install_rgh13_zfj_chkstop.md) (optimal balance between jank and functional)
- [RGH1.3 for Falcon/Jasper, extpwr method](install_rgh13_zfj_extpwr.md) (cleaner, but more annoying)
- [RGH1.3 for Falcon/Jasper, tiltswitch method](install_rgh13_zfj_tiltsw.md) (jankier, but easier)

### Zero-wire POST method

The zero-wire POST method was created for people who are converting their consoles from RGH1.2 or EXT_CLK but don't want
to bust out the soldering iron to add more wires (although you probably should anyway in case of a bad flash). It relies
entirely on CPU to SMC communication to track boot progress, so it is a bit slower than the two-wire or one-wire POST methods. 

Wiring is exactly the same as RGH1.2 and EXT_CLK so it will not be repeated here.

**Do NOT use the zero-wire POST method for fresh installs on Jaspers.** Jaspers are subject to issues when reset glitched (see badjasper information
below), and installing the bodge capacitor improperly will cause major CPU problems that the zero-wire method cannot detect. So be safe
and use two-wire or one-wire methods if you're doing a fresh install.

### One-wire POST method

In progress, to be documented when it's done.

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

There are two ways to tell if your system needs this workaround. On one given power cycle, if you get this behavior,
but on another power cycle the system boots, then you'll need to use `badjasper`.
- The system never successfully glitches for one given power cycle (20+ attempts for both RGH1.2 and RGH3)
- On RGH1.3, a single red light blinks on the Ring of Light (see blink codes below)

**When using badjasper/badfalcon and your system bootloops for way too long and you want to power the system off, hold the Power
button and it should instantly power down.** As a quality of life improvement, you can also hold the power button down for five seconds
on both `badjasper` and normal ECCs and the system will immediately power off.

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
Most boot attempts will fail with a Red or Red/Red blink.

These blink codes will help with tuning the glitch chip timings too. If the CPU isn't getting past
CB_A, the timing is way off or the pulse width is too large. You want it so that CB_B consistently
starts and runs HWINIT.

Also there's error handling. If something goes wrong at boot, the system will raise a Red Ring of Death
and shut down. Press Eject and Sync as usual to get the error codes. The RGH1.3 error codes are:

- 3333: POST bits 6 and 7 were not low coming out of CPU reset. Diodes are missing or wired incorrectly.
  Also check that you've disabled the tilt switch. **If you are using the capacitor and you get this error
  code, there is too much noise on the PLL wire.**

## Creating your updflash.bin

I doubt J-Runner will ever support this crap so here's a workaround.

In J-Runner, make sure "RGH3" is selected before building your NAND. It doesn't matter if you select 27 MHz or 10 MHz,
the buildscript will use the same SMC regardless.

Once your image is built and converted to RGH3, **don't flash it immediately**. You need to write some crap on the commandline.

For Xenon it's simple: `python3 convert_rgh3.py --board xenon path/to/updflash.bin`

For Falcon and Jasper, you will need to add more arguments depending on which method you used and whether you needed a badjasper SMC.
Examples are:
- `python3 convert_rgh3.py --board falcon --chkstop path/to/updflash.bin`
- `python3 convert_rgh3.py --board jasper --chkstop --badjasper path/to/updflash.bin`

If you get the message

``converted to RGH1.3 successfully, happy flashing``

then your updflash.bin is ready for flashing. Flash that sucker, test your console, tweak glitch chip timings as necessary, and enjoy.

## Speeding up boot times

Microsoft's stock CB_B code is very slow when running SDRAM training, especially on Falcon loaders, but it is possible
to patch it to run much faster at the risk of unstable system behavior.

To use these patches, pass one of the following to `convert_rgh13.py`:

- `--fast5050` seems to be a good compromise between speed and stability. I'm able to play a game for about an hour
  with this patch.
- `--veryfast5050` is a bit more risky, but you can still run games and the dash with no complaints, and it is super
  fast.

## Running older kernels

The 9188 MFG CB_A and a bug in CB_X break support for older kernels (Blades and Kinect being the most obvious).
If you want to run an older kernel, you'll need to specify your CPU key when running `convert_rgh13.py`. This will
replace the manufacturing CB_A with a retail CB_A and allow any kernel to run.

Example usage:
```
python3 convert_rgh13.py --board falcon --zerowire --veryfast5050 --cpukey ...your cpu key... updflash.bin
```

See [this issue](https://github.com/wurthless-elektroniks/RGH1.3/issues/2) for technical documentation of the bug.

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

## Wow, this shit sucks. Why even bother doing this? RGH1.2 works for me!

In professional software development, we focus on valid use cases and reliability, not the #WorksForMe mentality and sneering elitism that
makes the 360 scene suck so much. If you are a professional modder, then please get a real job, and by that, I mean a job where
you actually have to work with team members and have a boss, and where you have to collaborate with all of them in order to keep
your position and pay the bills. Then we'll see how far that attitude gets you in real life.

## Hah! There's a softmod coming and I've been using ABadDildo for months now. Why the fuck would anyone use this?

Oh my god, you people too???

Okay, let's be rational. RGH didn't obsolete JTAG and softmods haven't obsoleted either of those. The only thing that will
obsolete RGH for good (as well as JTAG and any softmods) is the release of the RSA-2048 private keys used to sign the
bootloaders, or a signed bootloader stub that breaks the chain of trust.

If you're softmodding your system to play the hottest zero-day warez of the 2010s, all the power to you. But softmods still
have a ways to go before they'll be on par with RGH and JTAG (*hint to kernel hackers: instead of payloads like XeUnshackle,
you should try to reboot the system into a hacked state like how JTAG does it*).

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

See [here](https://github.com/wurthless-elektroniks/RGH1.3/issues) for known bugs.

## Known issues and improvements

- It's possible to get rid of the POST diode(s), but the only way to do that is to manually initialize the SMC FIFOs at the
  start of CB_B, when the CPU is still coming out of the glitch and can be in an unstable state, so it wouldn't be that
  reliable anyway. Plus which, most failed glitch attempts will die within the first 100 ms, which means we have to monitor
  the POST lines anyway.

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
