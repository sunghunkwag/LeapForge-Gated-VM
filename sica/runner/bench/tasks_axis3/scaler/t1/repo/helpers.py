"""Scaler helper. Do not edit -- this module is correct.

It defines the single fixed-point transform the scaler is built on: how a
value is *packed* into its stored integer representation. Any code that needs
to reverse the transform has to undo exactly the step written in the body of
``pack`` below -- there is no other description of it anywhere.
"""


def pack(v):
    """Pack a value into its fixed-point stored form.

    The value is scaled up and a small fixed bias is added, so the stored
    form carries both pieces of information. Unpacking must remove the bias
    and then undo the scaling in order to recover the original value exactly.

        pack(0)  ->  7
        pack(1)  ->  107
        pack(10) ->  1007

    Two different values never pack to the same stored form, and the same
    bias is applied to every value, so a correct inverse has to account for
    it rather than assume the stored form is just the scaled value.
    """
    return v * 100 + 7
