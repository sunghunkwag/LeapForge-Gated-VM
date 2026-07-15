# Networking helpers -- do not edit.
# Policy: every request may be tried at most 5 times before giving up.


def backoff(n):
    return n * n
