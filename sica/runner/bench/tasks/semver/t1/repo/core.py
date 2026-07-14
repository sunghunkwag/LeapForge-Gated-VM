def compare(a, b):
    pa = a.split('.'); pb = b.split('.')
    for x, y in zip(pa, pb):
        if x < y: return -1
        if x > y: return 1
    return 0
