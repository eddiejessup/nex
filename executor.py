import operator

from common import Token
from reader import EndOfFile
from registers import is_register_type
from typer import (CatCode, MathCode, GlyphCode, DelimiterCode, MathClass,
                   PhysicalUnit, MuUnit, InternalUnit, units_in_scaled_points,
                   )
from tex_parameters import glue_keys
from expander import is_parameter_type
from interpreter import vertical_modes, horizontal_modes


def evaluate_size(state, size_token):
    if isinstance(size_token, Token):
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
            v = state.get_register_value(size_token.type, i=size_token.value)
            if size_token.type == 'SKIP':
                import pdb; pdb.set_trace()
            return v
        elif is_parameter_type(size_token.type):
            state.get_parameter_value(size_token.value['name'])
        else:
            import pdb; pdb.set_trace()
    else:
        return size_token


def evaluate_number(state, number_token):
    number_value = number_token.value
    size_token = number_value['size']
    number = evaluate_size(state, size_token)
    sign = number_value['sign']
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
        return Token(type_='fil_dimension',
                     value={'factor': number_of_units,
                            'number_of_fils': unit_token['number_of_fils']})
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
        # TODO: deal with 'true' and 'not-true' scales properly
        mag_parameter = 1000.0
        if is_true_unit:
            number_of_scaled_points *= 1000.0 / mag_parameter
    if sign == '-':
        number_of_scaled_points *= -1
    return number_of_scaled_points


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


def execute_if_num(if_token, state):
    v = if_token.value
    left_number = evaluate_number(state, v['left_number'])
    right_number = evaluate_number(state, v['right_number'])
    operator_map = {
        '<': operator.lt,
        '=': operator.eq,
        '>': operator.gt,
    }
    op = operator_map[v['relation']]
    outcome = op(left_number, right_number)
    return outcome


def execute_if_case(if_token, state):
    v = if_token.value
    return evaluate_number(state, v['number'])


def execute_condition(condition_token, state):
    if_token = condition_token.value
    exec_func_map = {
        'if_num': execute_if_num,
        'if_case': execute_if_case,
        'if_true': lambda *args: True,
        'if_false': lambda *args: False,
    }
    exec_func = exec_func_map[if_token.type]
    outcome = exec_func(if_token, state)
    return outcome


def execute_command(command, state, reader):
    box = []
    type_ = command.type
    v = command.value
    if type_ == 'SPACE':
        if state.mode in vertical_modes:
            pass
        elif state.mode in horizontal_modes:
            box.append(command)
    elif type_ == 'input':
        reader.insert_file(command.value['file_name'])
    # I think technically only this should cause the program to end, not
    # EndOfFile anywhere. But for now, whatever.
    elif type_ == 'END':
        raise EndOfFile
    # Commands like font commands aren't exactly boxes, but they go through
    # as DVI commands. Just put them in the box for now to deal with later.
    elif type_ == 'font_selection':
        state.set_current_font(v['global'], v['font_id'])
        box.append(command)
    elif type_ == 'family_assignment':
        family_nr = v['family_nr']
        family_nr_eval = evaluate_number(state, family_nr)
        state.set_font_family(v['global'], family_nr_eval,
                              v['font_range'], v['font_id'])
    elif type_ == 'short_hand_definition':
        code_eval = evaluate_number(state, v['code'])
        state.do_short_hand_definition(v['global'],
                                       v['control_sequence_name'],
                                       v['def_type'],
                                       code_eval)
    elif type_ == 'macro_assignment':
        name = v['definition'].value['name']
        state.set_macro(name, v['definition'],
                        prefixes=v['prefixes'])
    elif type_ == 'variable_assignment':
        variable, value = v['variable'], v['value']
        # The value might be a variable reference or something, so we must
        # evaluate it to its contents first before assigning a variable to
        # it.
        # TODO: Could we evaluate the value inside the state call?
        # Might reduce duplication?
        # TODO: We could actually have a 'set_variable' function in state.
        value_evaluate_map = {
            'number': evaluate_number,
            'dimen': evaluate_dimen,
            'glue': evaluate_glue,
            'mu_glue': evaluate_glue,
            'token_list': evaluate_token_list,
        }
        value_evaluate_func = value_evaluate_map[value.type]
        evaled_value = value_evaluate_func(state, value)
        if is_register_type(variable.type):
            state.set_register_value(is_global=v['global'],
                                     type_=variable.type,
                                     i=variable.value,
                                     value=evaled_value)
        elif is_parameter_type(variable.type):
            param_name = variable.value['canonical_name']
            state.set_parameter(is_global=v['global'],
                                name=param_name, value=evaled_value)
    elif type_ == 'font_definition':
        state.define_new_font(v['global'],
                              v['control_sequence_name'],
                              v['file_name'],
                              v['at_clause'])
        box.append(command)
    elif type_ == 'code_assignment':
        code_type = v['code_type']
        char_size = evaluate_number(state, v['char'])
        code_size = evaluate_number(state, v['code'])
        char = chr(char_size)
        # TODO: Move inside state? What exactly is the benefit?
        # I guess separation of routing logic from execution logic.
        if code_type == 'CAT_CODE':
            code = CatCode(code_size)
        elif code_type == 'MATH_CODE':
            parts = split_hex_code(code_size, hex_length=4, inds=(1, 2))
            math_class_i, family, position = parts
            math_class = MathClass(math_class_i)
            glyph_code = GlyphCode(family, position)
            code = MathCode(math_class, glyph_code)
        elif code_type in ('UPPER_CASE_CODE', 'LOWER_CASE_CODE'):
            code = chr(code_size)
        elif code_type == 'SPACE_FACTOR_CODE':
            code = code_size
        elif code_type == 'DELIMITER_CODE':
            parts = split_hex_code(code_size, hex_length=6, inds=(1, 3, 4))
            small_family, small_position, large_family, large_position = parts
            small_glyph_code = GlyphCode(small_family, small_position)
            large_glyph_code = GlyphCode(large_family, large_position)
            code = DelimiterCode(small_glyph_code, large_glyph_code)
        state.set_code(v['global'], code_type, char, code)
    elif type_ == 'advance':
        value_eval = evaluate_number(state, v['value'])
        variable = v['variable']
        if is_register_type(variable.type):
            state.advance_register_value(is_global=v['global'],
                                         type_=variable.type,
                                         i=variable.value,
                                         value=value_eval)
    elif type_ == 'let_assignment':
        state.do_let_assignment(v['global'], new_name=v['name'],
                                target_token=v['target_token'])
    elif type_ == 'skew_char_assignment':
        # TODO: can we make this nicer by storing the char instead of the
        # number?
        code_eval = evaluate_number(state, v['code'])
        state.global_font_state.set_hyphen_char(v['font_id'], code_eval)
    elif type_ == 'hyphen_char_assignment':
        # TODO: can we make this nicer by storing the char instead of the
        #         number?
        code_eval = evaluate_number(state, v['code'])
        state.global_font_state.set_hyphen_char(v['font_id'], code_eval)
    elif type_ == 'character':
        box.append(command)
    # The box already has its contents in the correct way, built using this
    # very method. Recursion still amazes me sometimes.
    elif type_ == 'h_box':
        box.append(command)
    else:
        # print(type_)
        pass
        # import pdb; pdb.set_trace()
    return box


def execute_commands(command_grabber, state, reader):
    box = []
    _cs = []
    while True:
        try:
            command = command_grabber.get_command()
        except EndOfFile:
            break
        _cs.append(command)
        try:
            box_contents = execute_command(command, state, reader)
        except EndOfFile:
            break
        box.extend(box_contents)
        if command_grabber.finish_up_grabbing:
            break
        # print(command)
    return box


def write_box_to_doc(doc, box):
    font_nr = 0
    for tok in box:
        type_ = tok.type
        v = tok.value
        if type_ == 'h_box':
            contents = tok.value['contents'].value
            write_box_to_doc(doc, contents)
        elif type_ == 'font_definition':
            doc.define_font(font_nr, v['file_name'],
                            font_path=v['file_name'] + '.tfm')
            font_nr += 1
        elif type_ == 'font_selection':
            # TODO: Fix font number getting.
            doc.select_font(0)
        elif type_ == 'character':
            doc.set_char(ord(v['char']))
        elif type_ == 'SPACE':
            doc.right(200000)
        else:
            print(type_)
            import pdb; pdb.set_trace()
