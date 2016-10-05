import pytest

from ..utils import get_bytes_needed, is_signed_nr_expressible_in_n_bits


max_bits_we_can_use = 4 * 8

# Integers to test on.
# All numbers from 0 to 255.
test_ints = list(range(2 ** 8))
# Powers of two up to just over our capacity (we test for this failure).
test_ints += [2 ** i for i in range(max_bits_we_can_use + 2)]
# Include powers of two plus and minus 1.
test_ints += [n + 1 for n in test_ints] + [n - 1 for n in test_ints]
# And the negative equivalents of all these.
test_ints += [-n for n in test_ints]
# Remove duplicates.
test_ints = set(test_ints)


def _test(signed, n):
    # Can't encode a number.
    if not is_signed_nr_expressible_in_n_bits(n, max_bits_we_can_use):
        with pytest.raises(ValueError):
            get_bytes_needed(n, signed)
    # Meaningless arguments.
    elif not signed and n < 0:
        with pytest.raises(ValueError):
            get_bytes_needed(n, signed)
    # Should work.
    else:
        nr_bytes = get_bytes_needed(n, signed)
        n.to_bytes(length=nr_bytes, byteorder='big', signed=signed)

        if nr_bytes > 1:
            nr_bytes_one_smaller = nr_bytes - 1
            with pytest.raises(OverflowError):
                n.to_bytes(length=nr_bytes_one_smaller,
                           byteorder='big', signed=signed)


def test_bytes_needed():
    for signed in (True, False):
        for n in test_ints:
            _test(signed, n)
