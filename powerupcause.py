'''
GetPowerUpCause() codes

Simplified from the amazingly terrible code in xeBuild (Ghidra decompiled).
Additional powerup causes found in SMC disassemblies.
'''

from enum import Enum

class PowerUpCause(Enum):
    POWER           = 0x11
    EJECT           = 0x12
    UNDOCUMENTED_15 = 0x15
    UNDOCUMENTED_16 = 0x16
    REMOPOWER       = 0x20
    UNDOCUMENTED_21 = 0x21
    REMOX           = 0x22
    WINBUTTON       = 0x24
    UNDOCUMENTED_30 = 0x30
    UNDOCUMENTED_31 = 0x31
    KIOSK           = 0x41
    WIRELESSX       = 0x55
    WIREDXF1        = 0x56
    WIREDXF2        = 0x57
    WIREDXB2        = 0x58
    WIREDXB1        = 0x59
    WIREDXB3        = 0x5A

POWERUP_CAUSE_DICT = {
    PowerUpCause.POWER: "console power button",
    PowerUpCause.EJECT: "console DVD eject button",
    PowerUpCause.REMOPOWER: "IR remote power button",
    PowerUpCause.REMOX: "IR remote guide/X button",
    PowerUpCause.WINBUTTON: "IR remote Windows button",
    PowerUpCause.KIOSK: "KIOSK debug pin",
    PowerUpCause.WIRELESSX: "wireless controller",
    PowerUpCause.WIREDXF1: "wired controller (front left/front top USB port)",
    PowerUpCause.WIREDXF2: "wired controller (front right/bottom top USB port)",
    PowerUpCause.WIREDXB2: "wired controller (rear middle USB port, slims only)",
    PowerUpCause.WIREDXB1: "wired controller (rear top USB port)",
    PowerUpCause.WIREDXB3: "wired controller (rear USB port/rear bottom USB port)",
    PowerUpCause.UNDOCUMENTED_15: "undocumented (0x15)",
    PowerUpCause.UNDOCUMENTED_16: "undocumented (0x16)",
    PowerUpCause.UNDOCUMENTED_21: "undocumented (0x21)",
    PowerUpCause.UNDOCUMENTED_30: "undocumented (0x30)",
    PowerUpCause.UNDOCUMENTED_31: "undocumented (0x31)"
}
