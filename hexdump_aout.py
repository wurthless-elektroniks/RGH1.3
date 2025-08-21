
with open("ppc/a.out", "rb") as f:
    data = f.read()

    if data[0x2C0:0x2C4] != bytes([0x48, 0x00, 0x00, 0x10]):
        print("something's wrong with the ELF")
        exit(1)
    
    formatted = []
    for b in data[0x2C0:0x3C0]:
        formatted.append(f"0x{b:02x}, ")
        
        if (len(formatted) & 0x0F) == 0:
            formatted.append("\n")
    
    print(u"".join(formatted))
