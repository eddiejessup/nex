import math
import sys

IS_PYTHON_3 = sys.version_info[0] == 3


def is_signed_nr_expressible_in_n_bits(n, nr_bits):
    min_signed_val = -(2 ** (nr_bits - 1))
    max_signed_val = 2 ** (nr_bits - 1) - 1
    return min_signed_val <= n <= max_signed_val


def get_bytes_needed(n, signed, is_check_sum=False):
    if n < 0 and not signed:
        raise ValueError
    if n == 0:
        return 1
    nr_bytes = int(math.log(abs(n), 256)) + 1
    # 4 byte arguments are always signed.
    if nr_bytes == 4:
        signed = True
    if signed:
        nr_bits = 8 * nr_bytes
        if not is_signed_nr_expressible_in_n_bits(n, nr_bits):
            nr_bytes += 1
    # We can never use more than 4 bytes in a command.
    if not 0 < nr_bytes <= 4:
        raise ValueError
    return nr_bytes
