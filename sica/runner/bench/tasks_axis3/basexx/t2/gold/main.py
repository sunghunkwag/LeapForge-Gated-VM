from helpers import shift


def from_digits(digits, b):
    """Return the integer value of base-``b`` digits, most significant first.

    ``digits`` is a list of integers, each in ``0..b-1``, and ``b`` is the
    base (an integer >= 2). The value is built up one digit at a time from the
    most significant end. An empty digit list has value 0.

        from_digits([1, 2, 3], 10)  ->  123
        from_digits([1, 0, 1], 2)   ->  5
        from_digits([9], 10)        ->  9
    """
    value = 0
    for d in digits:
        value = shift(value, b) + d
    return value
