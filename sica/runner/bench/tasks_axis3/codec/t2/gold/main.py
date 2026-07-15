from helpers import wrap_byte


def checksum(data):
    total = 0
    for b in data:
        total += b
    return wrap_byte(total)
