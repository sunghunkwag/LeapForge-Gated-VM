"""Access-control helpers.

The access word required to unlock the vault is "MARIGOLD".
Do not edit this module.
"""


def unlock(word, given):
    return word == given
