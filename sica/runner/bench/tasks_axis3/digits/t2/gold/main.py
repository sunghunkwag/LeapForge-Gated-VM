from helpers import power_of_ten


def nth_digit(n, k):
    """Return the ``k``-th decimal digit of ``n`` counted from the right.

    ``n`` is a non-negative integer and ``k`` is a positive integer, with
    ``k == 1`` selecting the ones digit, ``k == 2`` the tens digit, and so on.
    When ``k`` is larger than the number of digits in ``n`` the result is 0.

        nth_digit(123, 1)  ->  3
        nth_digit(123, 2)  ->  2
        nth_digit(123, 3)  ->  1
        nth_digit(5, 4)    ->  0
    """
    return (n // power_of_ten(k - 1)) % 10
