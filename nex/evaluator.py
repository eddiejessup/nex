from .tokens import BuiltToken, InstructionToken
from .instructions import Instructions
from .codes import CatCode
from .units import PhysicalUnit, MuUnit, InternalUnit, units_in_scaled_points
from .tex_parameters import Parameters


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
    # This is the true route, that eventually all should take.
    if isinstance(size_token, BuiltToken) and size_token.type == 'size':
        v = size_token.value
        # If the size is the contents of an integer or dimen parameter.
        if isinstance(v, InstructionToken) and v.type in (Instructions.integer_parameter.value,
                                                          Instructions.dimen_parameter.value):
            return state.parameters.get(v.value['parameter'])
        # If the size is the contents of a count or dimen register.
        elif isinstance(v, BuiltToken) and v.type in (Instructions.count.value,
                                                      Instructions.dimen.value):
            # The register number is a generic 'number' token, so evaluate this
            # first.
            evaled_i = evaluate_number(state, v.value)
            v = state.registers.get(v.type, i=evaled_i)
            return v
        # If the size is the short-hand character token. This is different to,
        # for example, a count_def_token, because that represents a register
        # containing a variable. A char_def_token represents a constant value.
        elif isinstance(v, InstructionToken) and v.type in ('CHAR_DEF_TOKEN', 'MATH_CHAR_DEF_TOKEN'):
            return v.value
        # If the size is the code of the target of a backtick instruction.
        elif isinstance(v, BuiltToken) and v.type == 'backtick':
            unexpanded_token = v.value
            if unexpanded_token.type == 'UNEXPANDED_CONTROL_SYMBOL':
                # If we have a single character control sequence in this context,
                # it is just a way of specifying a character in a way that
                # won't invoke its special effects.
                char = unexpanded_token.value['name']
            elif unexpanded_token.type == 'character':
                char = unexpanded_token.value['char']
            else:
                import pdb; pdb.set_trace()
            return ord(char)
        # If the size is the integer represented by an integer literal.
        elif isinstance(v, BuiltToken) and v.type == 'integer_constant':
            collection = v.value
            return get_integer_constant(collection)
        # If the size is the real number represented by a decimal number
        # literal.
        elif isinstance(v, BuiltToken) and v.type == 'decimal_constant':
            collection = v.value
            return get_real_decimal_constant(collection)
        # If the size is the value represented by a short-hand def token.
        elif isinstance(v, BuiltToken) and v.type == 'internal':
            return v.value
        # If the size is a specification of a dimension (this is different to a
        # call to retrieve the contents of a dimen register).
        elif isinstance(v, BuiltToken) and v.type == 'dimen':
            d_v = v.value
            nr_units_token, unit_token = d_v['factor'], d_v['unit']
            nr_units = evaluate_size(state, nr_units_token)

            unit = unit_token['unit']

            if unit == PhysicalUnit.fil:
                return BuiltToken(
                    type_='fil_dimension',
                    value={'factor': nr_units,
                           'number_of_fils': unit_token['number_of_fils']}
                )
            # Only one unit in mu units, a mu. I don't know what a mu is
            # though...
            elif unit == MuUnit.mu:
                unit_scale = 1
            elif unit == InternalUnit.em:
                unit_scale = state.current_font.em_size
            elif unit == InternalUnit.ex:
                unit_scale = state.current_font.ex_size
            else:
                unit_scale = units_in_scaled_points[unit]
                is_true_unit = unit_token['true']
                if is_true_unit:
                    magnification = state.parameters.get(Parameters.mag)
                    # ['true'] unmagnifies the units, so that the subsequent
                    # magnification will cancel out. For example, `\vskip 0.5 true
                    # cm' is equivalent to `\vskip 0.25 cm' if you have previously
                    # said `\magnification=2000'.
                    unit_scale *= 1000.0 / magnification
            size = int(round(nr_units * unit_scale))
            return size
        else:
            import pdb; pdb.set_trace()
    else:
        import pdb; pdb.set_trace()


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


def evaluate_number(state, number_token):
    number_value = number_token.value
    # Occurs if the number is a register-def-token.
    if isinstance(number_value, BuiltToken) and number_value.type == 'internal_number':
        return number_value.value
    elif isinstance(number_value, dict):
        size_token = number_value['size']
        size = evaluate_size(state, size_token)
        if 'signs' not in number_value:
            import pdb; pdb.set_trace()
        sign = evaluate_signs(number_value['signs'])
        if isinstance(size, BuiltToken) and size.type == 'fil_dimension':
            size.value['factor'] *= -1
        else:
            size *= sign
        return size
    else:
        raise ValueError


def evaluate_dimen(state, dimen_token):
    return evaluate_number(state, dimen_token)


def evaluate_glue(state, glue_token):
    v = glue_token.value
    if isinstance(v, BuiltToken) and v.type == 'explicit':
        # Should contain a dict specifying three dimens (in the general sense
        # of 'physical length'), a 'dimen' (in the narrow sense), 'shrink' and
        # 'stretch'.
        dimens = v.value
        evaluated_glue = {}
        for dimen_name, dimen_tok in dimens.items():
            if dimen_tok is None:
                evaluated_dimen = None
            else:
                evaluated_dimen = evaluate_dimen(state, dimen_tok)
            evaluated_glue[dimen_name] = evaluated_dimen
    # If the size is the contents of a glue or mu glue register.
    elif isinstance(v, BuiltToken) and v.type in (Instructions.skip.value,
                                                  Instructions.mu_skip.value):
        # The register number is a generic 'number' token, so evaluate this
        # first.
        evaled_i = evaluate_number(state, v.value)
        v = state.registers.get(v.type, i=evaled_i)
        return v
    # If the size is the contents of a parameter.
    elif isinstance(v, InstructionToken) and v.type in (Instructions.glue_parameter.value,
                                                        Instructions.mu_glue_parameter.value):
        return state.parameters.get(v.value['parameter'])
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
