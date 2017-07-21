from .constants.codes import CatCode


def get_real_decimal_constant(collection):
    # Our function assumes the digits are in base 10.
    assert collection.base == 10
    chars = [t.value['char'] for t in collection.digits]
    s = ''.join(chars)
    return float(s)


def get_integer_constant(collection):
    chars = [t.value['char'] for t in collection.digits]
    s = ''.join(chars)
    return int(s, base=collection.base)


def get_backtick_target_code(target):
    if target.type == 'UNEXPANDED_CONTROL_SYMBOL':
        # If we have a single character control sequence in this context,
        # it is just a way of specifying a character in a way that
        # won't invoke its special effects.
        return ord(target.value['name'])
    elif target.type == 'character':
        return ord(target.value['char'])
    else:
        raise ValueError(f'Unknown backtick target type: {target.type}')


def split_at(s, inds):
    inds = [0] + list(inds) + [len(s)]
    return [s[inds[i]:inds[i + 1]] for i in range(0, len(inds) - 1)]


def split_hex_code(n, hex_length, inds):
    # Get the zero-padded string representation of the number in base 16.
    n_hex = format(n, '0{}x'.format(hex_length))
    # Check the number is of the correct magnitude.
    assert len(n_hex) == hex_length
    # Split the hex string into pieces, at the given indices.
    parts_hex = split_at(n_hex, inds)
    # Convert each part from hex to decimal.
    parts = [int(part, base=16) for part in parts_hex]
    return parts


def evaluate_signs(signs_token):
    sign = 1
    for t in signs_token.value:
        if t.value['char'] == '-' and t.value['cat'] == CatCode.other:
            sign *= -1
        elif t.value['char'] == '+' and t.value['cat'] == CatCode.other:
            pass
        else:
            raise ValueError
    return sign
