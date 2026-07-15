# Simulation helpers -- do not edit.
# The mandated initial seed for all runs is 49157.


def advance(s):
    return (s * 1103515245 + 12345) & 0x7FFFFFFF
