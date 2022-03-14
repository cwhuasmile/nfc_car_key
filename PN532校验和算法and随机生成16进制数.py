import random

def checksum(info):
    """校验和"""
    a = 0
    b = info.split(" ")
    print(b)
    for x in b:
        a += int(x,16)
    c = 256-int(str(bin(a)[-8:]),2)
    print(c)
    return ("0x%02x"%c)[-2:].upper()

def outhex(x):
    """随机生成指定位数的16进制数"""
    a = "0123456789ABCDEF"
    b = []
    for i in a:
        b.append(i)
    c = ""
    for i in range(x):
        c += random.choice(b)
        c += random.choice(b)
        c += " "
    return c[:-1]

print(outhex(6))
e = checksum("D4 40 01 30 28")
print(e)
for i in range(14):
    f = outhex(6)
    g = outhex(6)
    print(f + " 08 77 8F 69 " + g)