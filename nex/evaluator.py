from .tokens import BuiltToken, InstructionToken
from .registers import is_register_type
from .constants.units import (PhysicalUnit, MuUnit, InternalUnit,
                              units_in_scaled_points)
from .tex_parameters import glue_keys, is_parameter_type


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


def evaluate_size(state, size_token):
    if isinstance(size_token, InstructionToken):
        if is_parameter_type(size_token.type):
            return state.get_parameter_value(size_token.value['name'])
        elif size_token.type in ('CHAR_DEF_TOKEN', 'MATH_CHAR_DEF_TOKEN'):
            return size_token.value
        else:
            import pdb; pdb.set_trace()
    elif isinstance(size_token, BuiltToken):
        if size_token.type == 'backtick_integer':
            unexpanded_token = size_token.value
            if unexpanded_token.type == 'UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE':
                # If we have a single character control sequence in this context,
                # it is just a way of specifying a character in a way that
                # won't invoke its special effects.
                char = unexpanded_token.value['name']
            elif unexpanded_token.type == 'character':
                char = unexpanded_token.value['char']
            else:
                import pdb; pdb.set_trace()
            return ord(char)
        elif size_token.type == 'control_sequence':
            raise NotImplementedError
        elif is_register_type(size_token.type):
            evaled_i = evaluate_size(state, size_token.value)
            v = state.get_register_value(size_token.type, i=evaled_i)
            if size_token.type == 'SKIP':
                import pdb; pdb.set_trace()
            return v
        elif size_token.type == 'integer_constant':
            collection = size_token.value
            return get_integer_constant(collection)
        elif size_token.type == 'decimal_constant':
            collection = size_token.value
            return get_real_decimal_constant(collection)
        else:
            import pdb; pdb.set_trace()
    else:
        return size_token


def evaluate_number(state, number_token):
    number_value = number_token.value
    size_token = number_value['size']
    number = evaluate_size(state, size_token)
    sign = number_value['sign'].value
    if sign == '-':
        number *= -1
    return number


def evaluate_dimen(state, dimen_token):
    # TODO: Check if the sign is stored and retrieved in numbers, dimens, glues
    # and so on.
    dimen_value = dimen_token.value
    size_token, sign = dimen_value['size'], dimen_value['sign']
    if isinstance(size_token.value, int):
        return size_token.value
    number_of_units_token = size_token.value['factor']
    unit_token = size_token.value['unit']
    number_of_units = evaluate_size(state, number_of_units_token)
    unit = unit_token['unit']
    if unit == PhysicalUnit.fil:
        if 'number_of_fils' not in unit_token:
            import pdb; pdb.set_trace()
        return BuiltToken(
            type_='fil_dimension',
            value={'factor': number_of_units,
                   'number_of_fils': unit_token['number_of_fils']}
        )
    # Only one unit in mu units, a mu. I don't know what a mu is though...
    elif unit in MuUnit:
        number_of_scaled_points = number_of_units
    elif unit in InternalUnit:
        if unit == InternalUnit.em:
            number_of_scaled_points = state.current_font.em_size
        elif unit == InternalUnit.ex:
            number_of_scaled_points = state.current_font.ex_size
    else:
        is_true_unit = unit_token['true']
        number_of_scaled_points = units_in_scaled_points[unit] * number_of_units
        magnification = state.get_parameter_value('mag')
        # ['true'] unmagnifies the units, so that the subsequent magnification
        # will cancel out. For example, `\vskip 0.5 true cm' is equivalent to
        # `\vskip 0.25 cm' if you have previously said `\magnification=2000'.
        if is_true_unit:
            number_of_scaled_points *= 1000.0 / magnification
    if sign == '-':
        number_of_scaled_points *= -1
    return int(round(number_of_scaled_points))


def evaluate_glue(state, glue_token):
    glue_value = glue_token.value
    evaluated_glue = {}
    for k in glue_keys:
        dimen_token = glue_value[k]
        if dimen_token is None:
            evaluated_dimen = None
        else:
            evaluated_dimen = evaluate_dimen(state, dimen_token)
        evaluated_glue[k] = evaluated_dimen
    return evaluated_glue


def evaluate_token_list(state, token_list_token):
    token_list_value = token_list_token.value
    if token_list_value.type == 'general_text':
        evaluated_token_list = token_list_value.value
    # Also could be token_register, or token parameter.
    else:
        raise NotImplementedError
    return evaluated_token_list


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
