# What could laughably be called the RGH1.3 project retro/post-mortem

So a brief refresher. When it comes to modding phats, RGH1.2 and RGH3 have advantages but they also have disadvantages.

RGH3 doesn't need a glitch chip and runs its glitch attempts at a rate of one per second because it's able to
monitor the boot process and reset immediately if it doesn't like what it sees. Its disadvantage is that it
has issues on phats because it's running on the slow-ass SMC, which can't time its glitch pulses precisely enough.
And it has issues on Jaspers, including the one where the console powers off almost immediately after you power it on. But
RGH3 does work and I've successfully modded Falcons with it before, but I don't anymore because my success rate
with it has fallen drastically. Might be because the QSB I designed sucks balls.

RGH1.2 runs on a glitch chip and can glitch the CPU super precisely. However, the CPU is forced to load and hash
the entire CB_B, which is slow (at least half a second slower than RGH3), and there is no error checking mechanism
as there is on RGH3. The result is that if you have a failed boot on RGH1.2, you might be waiting around for 3.5
seconds on Jaspers or 5.5 seconds on Falcons (with SMC+) before the SMC finally resets the system, and on some
systems it can take a lot more attempts, and consequently time, to get the system up and running. Also, there are
some Jaspers that are super uncooperative and will not successfully glitch until the system is power cycled.
RGH1.2 and RGH1.2 v2 never fixed this issue or even had a workaround for it. Finally, when you're installing RGH1.2,
you're expected to spend all fucking afternoon doing contortionist acts with some combination of wire routing and
capacitor bodging until the thing cooperates, simply because the professional el33t modders hate you and would rather
have you spend $150 on their send-in service just to mod a console that costs $30 at Value Village.

So it appears that neither approach is friendly. RGH3 works until it doesn't, RGH1.2 causes more headaches than
it should because the most respected people in the 360 scene are lamers and profiteers with the #WorksForMe mindset,
and neither have solved the issue of super uncooperative Jaspers. Let's look for an alternative.
Because alternatives are good! Well, maybe not R-JTOP. But still.

I had been experimenting with various ways of glitching the CPU with a Raspberry Pi Pico and quickly
found that some of my attacks were failing before HWINIT. My guess was that there was some hardware
crap on the CPU that was being initialized early on in CB_B (this was before I actually read the damn
code) and the glitch pulses were causing these supposed hardware units to crap out and freeze the CPU.
With that in mind I chose to alter the boot process by taking an RGH3 image, shoving a normal glitch SMC
into it, and calling this type of image "Glitch3". After all, RGH3's CB_X alters code execution somewhat, so maybe
by delaying entry into CB_B, that would give things time to stabilize. But I had no success. The CPU still
crashed.

When you're tinkering on a project, the best thing that can happen is when you have one idiot idea that, while it
doesn't work, turns up something even better. And that's what happened. Behold, the power of using CB_X with a glitch
chip:

1. CB_X takes next to no time to load, so the glitch can run a lot sooner. This happens slightly faster
   than RGH3, since we're only using PLL slowdown and not PLL+I2C slowdown.

2. As a side effect, CB_X can alter the failure case on an unsuccessful glitch attempt. CB_X will output POST
   0x54 when the payload has been moved to safe SRAM and it's delaying execution before loading CB_B.
   If the CPU crashes during a failed glitch attempt, it often does at POST 0x54. We can easily track this by
   monitoring POST bit 6: if, after the glitch runs, it isn't 0 within a certain amount of time,
   then we can assume the boot has failed and restart immediately. 15432 actually knew about this behavior,
   so the RGH3 code catches a similar case (POST bit 1 must rise within 255 ms after CB_X starts). I didn't
   know about this at the time, though, as I didn't really read the RGH3 code that thoroughly.

This is enough to catch a good chunk of failed boots. I say a good chunk, because the CPU can still crash
at the fusecheck or HWINIT phase. But it's a good start.

Now we run into a problem: where do we put our watchdog? Unfortunately, the Matrix glitcher which everyone uses
has no room for a watchdog. This is primarily because I have absolutely no VHDL experience. Also, the D and E
lines on the Matrix are strictly 3v3 only, making them incompatible with the 1v1 POST pins. An external microcontroller
isn't ideal for a lot of other reasons that I'll get into later. So the only viable choice we have is to put the watchdog
code on the SMC, and to stick a diode between GPU_RESET_DONE and POST bit 6, similar to how RGH3 does it. When we see
the line rise, CB_A and CB_X have about 400 ms to make it to CB_B, or we reset and try again. Simple as.

This catches most failed glitch attempts, but it doesn't catch two more of them: the case where the CPU
crashes during the fusecheck or HWINIT phase, and the second is where the CPU somehow gets far into the
boot process, even sending GetPowerUpCause, but crashes before the boot animation. We can kill the second
one easy: set a watchdog once GetPowerUpCause arrives and if we don't see the LED boot animation in time
we assume the boot has failed. Or more likely someone's being a nincompoop and hasn't plugged his HDMI cable in,
in which case we punish him with a reboot for no real reason.

HWINIT is critical to proper system operation and cannot be skipped. Unfortunately, it's implemented as an
interpreter, and takes a while to execute. HWINIT runtime also varies per board; on Falcon it's about 2.7-3
seconds and on Jasper it's around 1.5-1.7 seconds. There's also the problem where the CPU can crash just before HWINIT
in the fusecheck phase, so we want to avoid that edge case too. 

We have a couple options of how to speed up the boot here. The first is to move GetPowerUpCause to CB_B,
and I really did consider doing this. After all, the SMC will keep returning the same result to the CPU,
as it doesn't care how many times it's called as long as the CPU calls it only once. We could even put
the CDxell code in CB_B if we wanted to be completely insane. But this still doesn't solve one problem
with HWINIT: the CPU can crash while it's running. So let's get even more aggressive.

Remember that bit about uncooperative Jaspers? I found that with some Jasper boards, there's a chance that
for one power cycle, glitch attempts always fail at 0xDB, and the only way to get around it is to power cycle
the system until it cooperates. The SMC can't catch this just by monitoring POST bit 6 as 0xDB and 0x54 both
have bit 6 set. However, bit 7 changes between the two. (Bit 1 also does but we're not monitoring it here.)
So with those boards, the solution is to monitor POST bit 7, and power cycle the system if it's stuck on after
a glitch cycle. This is very easy to implement with a microcontroller, but it breaks XeLL support because
when the system is hard reset, the SMC forgets that you've pressed the eject button. Also, with a microcontroller,
you have a lot more I/O lines that can be set as pullups, but that isn't the case with the SMC, where we're
basically out of I/Os. Even DBG_LED0 isn't ideal as there's a pulldown resistor on that line and we'd have
to hack the board up or add strong pullup resistors to use it for reading POST bit 7. So, looks like we're out of luck here.

Or are we?

Let's focus on the most useless I/O line in the system, one that even 15432 overlooked or ignored when he wrote
RGH3. I speak, of course, of the tilt switch. Yeah, I bet you didn't know the 360 had a tilt switch. All
the tilt switch does is change the Ring of Light's orientation depending on whether the system is lying flat or
standing up. If we remove or disable the tilt switch, we gain an I/O line that is conveniently pulled up to 3.3v
and has an easily accessible test point under the PCB for installing a second diode to POST pin 7. On top of that,
even if we do a trace cut to disable the tilt switch, it's super easy to reenable it afterwards, as we just need
to run a wire from the pullup resistor back to the tilt switch itself. So we shall bid farewell to our friend
the tilt switch in the name of progress. [Here's a dramatic reenactment of his funeral.](https://youtu.be/0Y2BxyOyH3Q?t=18)

(A bonus for using the tilt switch for POST bit 7 is that it's easy to port this two-wire POST technique to RGH3
 so RGH3 users get all the same benefits. But that's a task for later.)

Now that we're monitoring two POST bits, we gain about a 60 ms advantage on the CB_A to CB_X transition, but more
importantly, we can now hack HWINIT to toggle POST bits as it's running. Bit 7 goes high when HWINIT is running,
and bit 6 toggles every so often. If we don't see bit 6 toggle in time, we reboot. Once HWINIT finishes, bit 7 falls
and the SMC concludes that all is well. This, naturally, comes with a slight performance penalty,
as every opcode in the HWINIT interpreter now takes several extra cycles to execute. 

Oh, almost forgot. We don't have the CPU key, so we can't patch CB_B without it. Except for the fact that
we used CB_X and that puts CB_B in plaintext. We don't need a stinking CPU key!

So all the heavy lifting with this technique is done by the CPU and the SMC. And that leaves the last thing we
need to do: actually write the glitch chip code. And it's just a one line change in the RGH1.2 v2 source so that
only we wait 10 ms before applying PLL slowdown instead of RGH1.2's timing of 400 ms.

