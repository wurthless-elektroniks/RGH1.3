#
# "CB_Y" intermediate stage for RGH1.3 postless methods
#
# Also backwards compatible with RGH3 and RGH1.3 1-wire/2-wire methods
# and contains built-in g3fix so older kernels can run
#
# Heavily based on CB_X by 15432
# hwinit reverse engineering done by Mate Kukri
#
    .org 0x0000

    .word 0x4342     # "CB"
    .word 42069
    .long 0x00000800 # ????
    .long 0x000003D0 # entry point
    .long 0x00000400 # size

    .org 0x0260
_start_after_reloc:
    b _pci_init_start

    # the big PCI initialization table of values.
    # this is for fat systems ONLY. slims initialize the PCI BARs slightly differently.
    #
    # initializing the PCI BARs is mandatory if you want to talk to the SMC, which we do in this case...
    
    # init PCI host bridges
    .long 0xD0008010, 0xE0000000 # store_word 0xe0000000 -> 0xd0008010
    .long 0x50008004, 0x00000002 # store_half 2 -> 0xD0008004
    .long 0xE0020000, 0x00000000 # store_word 0 -> 0xE0020000
    .long 0xE0020004, 0xC0000000
    .long 0xE1020004, 0x00000018
    .long 0xE1010000, 0x5F076009
    .long 0xE1018020, 0x00004000

    # initialize GPU/Northbridge/SDRAM controllers
    .long 0xD0010010, 0xE4000000
    .long 0x50010004, 0x00000002
    .long 0xE4000284, 0x20000000
    .long 0xE4000200, 0x00000000
    .long 0xE4000210, 0x20000000
    .long 0xE4000244, 0x20000000
    .long 0xE4002000, 0x00000000
    .long 0xE4002100, 0x00000000
    .long 0xE40002A4, 0x00000000

    # initialize PCI bridge to southbridge (and SMC)
    .long 0xD0000018, 0x00020100
    .long 0xD0150010, 0xEA001000
    .long 0x50150004, 0x00000002
    .long 0xEA00101C, 0x000001E6

    # this is what actually sends our "CB_Y has started" message to the SMC
    .long 0xEA001084, 0x00000004  # claim FIFO
    .long 0xEA001080, 0x000000A0  # write command 0xA0 (SMC will not reply)
    .long 0xEA001084, 0x00000000  # release FIFO
    
    .long 0xFFFFFFFF # end of list

_pci_init_start:
    # POST 0x54 (for compatibility with CB_X and debugging)
    oris   %r4,%r3,0x6         # 0x8000020000060000, I/O
    li     %r2,0x54            # bit #1 must be ‘0’ here
    rldicr %r2,%r2,0x38,0x7
    std    %r2,0x1010(%r4)     # POST 0x54 to tell SMC we're done

    oris %r2,%r3,0x1
    ori  %r2,%r2,0xC260        # point r2 to SRAM 0xC260 (table start - 4)
    
    oris %r7,%r3,0x8000        # base address = 0x8000020080000000

_pci_init_loop:
    lwzu %r4,0x0004(%r2)      # read dest address from table above
    cmpwi %r4,-1              # if word was 0xFFFFFFFF, we're done
    beq _load_cbb
    cmpwi %cr7,%r4,0          # also check if bit 31 was set - we'll come back to this soon
    lwzu %r6,0x0004(%r2)      # read word to be written
    or %r4,%r4,%r7            # OR address with base value
    blt %cr7,_pci_st32        # if dest address bit 31 was set, it's a 32-bit word
    sthbrx %r6,0,%r4          # otherwise, it's a 16-bit half - store it in little endian form
    b _pci_sync_and_go_next
_pci_st32:
    stwbrx %r6,0,%r4          # 32-bit words have to be stored in little endian form too
_pci_sync_and_go_next:
    sync 0x00
    b _pci_init_loop

    # back to normal CB_X code
_load_cbb:
    oris       %r6,%r3,0xc800      # 0x8000020000C80000, mapped NAND
    subi       %r6,%r6,0x4
    rldicl     %r2,%r31,0x0,0x20
    or         %r7,%r3,%r3
    add        %r6,%r6,%r2         # + provided r31 offset
    lwz        %r4,0x10(%r6)       # CB_B size
    lwz        %r3,0xc(%r6)        # CB_B entry point
    add        %r31,%r31,%r4       # update r31 offset
    rldicl     %r4,%r4,0x3e,0x2
    mtspr      %CTR,%r4
_load_cbb_loop:
    lwzu       %r2,0x4(%r6)
    stwu       %r2,0x4(%r5)
    bdnz       _load_cbb_loop

    # let SMC know that CB_B is about to run
    oris       %r7,%r7,0xEA00     # point r3 at southbridge
    lis        %r2,0x4000
    stw        %r2,0x1084(%r7)    # grab FIFO
    lis        %r2,0xA100
    stw        %r2,0x1080(%r7)    # send IPC command 0xA1
    li         %r2,0
    stw        %r2,0x1084(%r7)    # release FIFO

    # jump to remnants of CB_A 9188 MFG to load/start CB_B
    # (fixes older dashboards crashing, but we need to recalc/disable SMC checksums)
    or         %r4,%r31,%r31
    b          cba_jump_to_cbb    # should also work for retail CB_As 5772, 6572, 9188.
                                  # remember: this code is actually executing at 0xCxxx

    # lowest possible entry point
    .org 0x03D0
_entry:
    li   %r3,0x200                # r3 = 0x8000020000000000
    oris %r3,%r3,0x8000
    rldicr %r3,%r3,0x20,0x1f
    oris %r4,%r3,0x1              # 0x8000020000010000, SRAM address
    subi %r5,%r4,0x4
    ori %r6,%r4,0xc000             
    li %r2,0x7f                   # copy 0x400 bytes
    mtspr %CTR,%r2
_payload_reloc_loop:
    ldu  %r2,0x08(%r4)
    stdu %r2,0x08(%r6)
    bdnz _payload_reloc_loop

    b run_relocated_stub

    # the following stubs exist because gnu assembler cannot into relative jumps with absolute addresses

    .org 0x0478
cba_jump_to_cbb:
    # (this actually jumps to 0xC478 where the remnants of CB_A live)

    .org 0xC260
run_relocated_stub:
    # (remember that the code at 0x0260 has been relocated here)
