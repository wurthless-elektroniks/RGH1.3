import struct

def encrypt_smc(data: bytes,
                skip_swap_firstfour: bool = False) -> bytes:

    # the SMC image is scrambled somewhat, with the real first 4 bytes
    # being placed at the very end of the SMC ( len(smc)-8 ).
    # this bit of code scrambles the SMC prior to injection.
    # if your SMC image is already scrambled, set skip_swap_firstfour=True.
    if skip_swap_firstfour is False:
        
        # if we randomize the first four bytes like 15432's code does it
        # then we'll have to commit new ECCs every time we build
        # so let's set the fake first four to something suitably juvenile

        rnd = bytes([0x04, 0x20, 0x69, 0x69])
        # rnd = bytes([0xE1, 0x75, 0x39, 0x76]) # falcon

        data = rnd + data[4:-8] + data[0:4] + b"\x00"*4
    
    key = [0x42, 0x75, 0x4e, 0x79]
    res = bytearray()
    for i in range(len(data)):
        j = data[i] ^ (key[i&3] & 0xFF)
        mod = j * 0xFB
        res += struct.pack("B", j)
        key[(i+1)&3] += mod
        key[(i+2)&3] += mod >> 8

    return bytes(res)

def decrypt_smc(data: bytes) -> bytes:
    key = [0x42, 0x75, 0x4e, 0x79]
    res = bytearray()

    # this was copied from a from script with credit
    # "modified by GliGli and Tiros for the reset glitch hack"
    # most likely based on tmbinc's work for JTAG?
    for i in range(len(data)):
        j = data[i]
        mod = j * 0xFB
        res.append((j ^ key[i&3] & 0xFF))
        key[(i+1)&3] += mod
        key[(i+2)&3] += mod >> 8

    # unscramble final plaintext
    res = res[-8:-4] + res[4:-8] + b"\x00"*8

    return res

def _rol64(val: int, count: int) -> int:
    for _ in range(0,count):
        carry = (val & 0x8000000000000000) != 0
        val <<= 1
        val &= 0xFFFFFFFFFFFFFFFF
        if carry is True:
            val |= 1
    return val

def calc_smc_checksum(cyphertext: bytes, seed: list = None) -> list:
    '''
    Recalc SMC checksum from encrypted SMC image.
    Based on CB_B 6752 function @ 0x7DB0.
    '''
    if (len(cyphertext) & 3) != 0:
        raise RuntimeError("cyphertext must be a multiple of 4 bytes")

    pos = 0

    sumval = 0
    diffval = 0
    if seed is not None:
        sumval  = seed[0]
        diffval = seed[1]

    while pos < len(cyphertext):
        dat = struct.unpack(">I", cyphertext[pos:pos+4])[0]

        sumval += dat
        sumval &= 0xFFFFFFFFFFFFFFFF

        diffval -= dat
        
        # convert to 2s complement on underflow
        if diffval < 0:
            diffval += 2**64

        diffval &= 0xFFFFFFFFFFFFFFFF

        sumval = _rol64(sumval, 0x1D)
        diffval = _rol64(diffval, 0x1F)

        pos += 4
    
    return [sumval, diffval]
