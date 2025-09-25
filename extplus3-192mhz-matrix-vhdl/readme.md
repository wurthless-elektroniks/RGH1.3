# EXT+3 192 MHz VHDL, Matrix/Coolrunner

Basically Octal450's timing files but with a shorter CPU_EXT_CLK_EN assert delay.

Original source [here](https://github.com/Octal450/EXT_CLK/).

## Compiling

Instructions by RoanPlayz [here](https://www.reddit.com/r/360hacks/comments/1inkdfk/compiling_svfxsvf_timing_files_guide_triplequad/).

Note that Xilinx ISE Design Suite will crash randomly on newer Windows versions. The typical workaround for this is to replace
`libPortability.dll` with `libPortabilityNOSH.dll`.
