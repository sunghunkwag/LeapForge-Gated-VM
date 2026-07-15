def from_roman(s):
    m = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}
    total = 0
    for i, ch in enumerate(s):
        if i+1 < len(s) and m[ch] < m[s[i+1]]:
            total -= m[ch]
        else:
            total += m[ch]
    return total
