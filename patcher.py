'''
Common patcher framework stuff
'''

import struct

class FreeSpaceArea():
    def __init__(self, start_address: int, end_address: int):
        self._start_address = start_address
        self._end_address = end_address
        self._head = start_address

        # function_name -> address
        self._function_map = {}
    
    def head(self):
        return self._head
    
    def func(self, name: str):
        return self._function_map[name]

    def create_func_and_set_head(self, name: str, end_head: int):
        '''
        Assigns a function name at the current head position, then
        sets the head position to `end_head`.
        '''
        if end_head > self._end_address:
            raise RuntimeError("end_head went out of bounds")

        self._function_map[name] = self._head

        print(f"create_func_and_set_head: {name} 0x{self._head:04x} -> 0x{end_head:04x}")
        self._head = end_head

    def create_func_at_address(self, name: str, address: int):
        self._function_map[name] = address

def assert_address_32bit_aligned(address: int):
    if (address & 3) != 0:
        raise RuntimeError(f"address not 32-bit aligned: {address:08x}")

def assemble_post_function(cbb_image: bytes, address: int) -> tuple:
    '''
    Common POST function. Takes POST code in r4. r3 will be destroyed.
    '''
    assert_address_32bit_aligned(address)

    post_fcn = bytes([
        # set r3 = 0x8000020000061010 (POST output)
        0x38, 0x60, 0x02, 0x00,  # li r3,0x200
        0x64, 0x63, 0x80, 0x00,  # oris r3,r3,0x8000
        0x78, 0x63, 0x07, 0xc6,  # rldicr r3,r3,0x20,0x1f
        0x64, 0x63, 0x00, 0x06,  # oris r3,r3,0x6

        # write (postcode << 56) (in r4) to r3
        0x78, 0x84, 0xc1, 0xc6, # rldicr r4,r4,0x38,0x7
        0xf8, 0x83, 0x10, 0x10, # std r4,(r3)

        # return
        0x4e, 0x80, 0x00, 0x20  # blr
    ])

    end_addr = address + len(post_fcn)
    cbb_image[address:end_addr] = post_fcn

    return cbb_image, end_addr

def assemble_nop(cbb_image: bytes, address: int) -> tuple:
    '''
    `nop` (=`ori r0,r0,0`)
    '''
    assert_address_32bit_aligned(address)

    nopcode = bytes([
        0x60, 0x00, 0x00, 0x00 # ori r0,r0,0 - does nothing
    ])
    cbb_image[address:address+4] = nopcode
    return (cbb_image, address + 4)

def assemble_li_r3(cbb_image: bytes, address: int, imm8: int) -> tuple:
    '''
    `li r3,imm8`
    '''
    assert_address_32bit_aligned(address)

    if (0 <= imm8 <= 0xFF) is False:
        raise RuntimeError("li r3 takes imm8 argument (sorry, 16-bit likers)")
    cbb_image[address:address+4] = struct.pack(">BBBB", 0x38, 0x60, 0x00, imm8)
    return (cbb_image, address + 4)

def assemble_li_r4(cbb_image: bytes, address: int, imm8: int) -> tuple:
    '''
    `li r4,imm8`
    '''
    assert_address_32bit_aligned(address)

    if (0 <= imm8 <= 0xFF) is False:
        raise RuntimeError("li r4 takes imm8 argument (sorry, 16-bit likers)")
    cbb_image[address:address+4] = struct.pack(">BBBB", 0x38, 0x80, 0x00, imm8)
    return (cbb_image, address + 4)

def assemble_branch_to_link_register(cbb_image: bytes, address: int) -> tuple:
    assert_address_32bit_aligned(address)
    
    opcode = bytes([
        0x4E, 0x80, 0x00, 0x20
    ])
    cbb_image[address:address+4] = opcode
    return (cbb_image, address + 4)

def assemble_branch_generic(cbb_image: bytes, address: int, destination_address: int, with_link: False) -> tuple:
    assert_address_32bit_aligned(address)
    assert_address_32bit_aligned(destination_address)
    
    address_diff = destination_address - address
    if (-0x1FFFFFFF <= address_diff <= 0x1FFFFFFF) is False:
        raise RuntimeError("branch imm26 out of range")
    
    address_encoded = struct.unpack(">I", struct.pack(">i", address_diff))[0]
    address_encoded &= 0x03FFFFFC
    address_encoded |= 0x48000000
    if with_link is True:
        address_encoded |= 1

    cbb_image[address:address+4] = struct.pack(">I", address_encoded)
    return (cbb_image, address+4)

def assemble_branch_with_link(cbb_image: bytes, address: int, destination_address: int) -> tuple:
    '''
    Assemble `bl` opcode.

    DANGER: Remember that this is RISC! If you use `bl`, it WILL overwrite the contents of `lr`.
    If you don't preserve `lr` correctly your code will crash!
    '''
    return assemble_branch_generic(cbb_image, address, destination_address, True)

def assemble_branch(cbb_image: bytes, address: int, destination_address: int) -> tuple:
    return assemble_branch_generic(cbb_image, address, destination_address, False)

def assemble_panic(cbb_image: bytes, address: int, post_code: int, panic_fcn_address: int) -> tuple:
    assert_address_32bit_aligned(address)

    next_ptr = address
    cbb_image, next_ptr = assemble_li_r4(cbb_image, next_ptr, post_code)
    cbb_image, next_ptr = assemble_branch(cbb_image, next_ptr, panic_fcn_address)
    return cbb_image, next_ptr

def assemble_panic_function(cbb_image: bytes, address: int, post_fcn_address: int) -> tuple:
    assert_address_32bit_aligned(address)

    cur_address = address

    cbb_image, cur_address = assemble_branch_with_link(cbb_image, address, post_fcn_address)

    infinite_death_spiral = bytes([
        0x38, 0x00, 0x00, 0x00,  # li r0,0x00
        0x7c, 0x18, 0x23, 0xa6,  # mtspr CMPE,r0
        0x4b, 0xff, 0xff, 0xf8,  # b -8 - loop forever
    ])

    end_address = cur_address+len(infinite_death_spiral)
    cbb_image[cur_address:end_address] = infinite_death_spiral

    return cbb_image, end_address

def assemble_post_call(cbb_image: bytes, address: int, post_fcn_address: int, post_code: int):
    assert_address_32bit_aligned(address)

    cur_address = address
    cbb_image, cur_address = assemble_li_r4(cbb_image, cur_address, post_code)
    cbb_image, cur_address = assemble_branch_with_link(cbb_image, cur_address, post_fcn_address)

    return cbb_image, cur_address

def fill_nops_between(cbb_image: bytes, address: int, until_address: int):
    assert_address_32bit_aligned(address)
    assert_address_32bit_aligned(until_address)

    if address > until_address:
        raise RuntimeError("address already past until_address")
    
    pos = address
    while pos < until_address:
        cbb_image, pos = assemble_nop(cbb_image, pos)

    return cbb_image, pos

def make_post_codecave(cbb_image: bytes,
                       free_space_area: FreeSpaceArea,
                       insert_address: int,
                       post_code: int) -> bytes:
    assert_address_32bit_aligned(insert_address)
    post_fcn_address = free_space_area.func("post")

    # read instruction we're about to overwrite
    old_instruction = cbb_image[insert_address:insert_address+4]

    # assemble codecave in free space area
    pos = free_space_area.head()
    codecave_pos = pos
    cbb_image, pos = assemble_post_call(cbb_image, pos, post_fcn_address, post_code)
    cbb_image[pos:pos+4] = old_instruction
    pos += 4
    cbb_image, pos = assemble_branch(cbb_image, pos, insert_address + 4)
    free_space_area.create_func_and_set_head(f"post_{post_code:02x}_codecave", pos)
    cbb_image, _ = assemble_branch(cbb_image, insert_address, codecave_pos)

    return cbb_image
