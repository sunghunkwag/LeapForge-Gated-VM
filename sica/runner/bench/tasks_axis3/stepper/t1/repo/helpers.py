"""Stepper helper. Do not edit -- this module is correct.

It defines the single forward step the stepper is built on: how a position is
nudged forward into its stepped form. Any code that needs to step a value back
has to reverse exactly the step written in the body of ``fwd`` below -- there
is no other description of it anywhere.
"""


def fwd(x):
    """Step a position forward into its stepped form.

    ``x`` is an integer position in the documented domain ``0..49``. The
    position is nudged forward by a small amount that depends on the position
    itself, so the step is not the same for every input:

        fwd(0)  ->  1
        fwd(1)  ->  3
        fwd(2)  ->  5
        fwd(3)  ->  4

    Because the amount added depends on the input, two neighbouring positions
    can move forward by different amounts (note how ``3`` lands *below* ``2``
    above), and the mapping is one-to-one over the domain: no two positions in
    ``0..49`` step to the same value. Any code that needs to step a value back
    therefore has to recover the unique position whose forward step produced a
    given value -- subtracting a single fixed amount does not do that.
    """
    return x + (x % 3) + 1
