from reader import EndOfFile
from registers import is_register_type
from expander import is_parameter_type
from interpreter import vertical_modes, horizontal_modes
from common_parsing import (evaluate_number, evaluate_dimen, evaluate_glue,
                            evaluate_token_list)


def execute_commands(command_grabber, state, reader):
    box = []
    _cs = []
    while True:
        try:
            command = command_grabber.get_command()
        except EndOfFile:
            break
        _cs.append(command)
        type_ = command.type
        v = command.value
        if type_ == 'SPACE':
            if state.mode in vertical_modes:
                pass
            elif state.mode in horizontal_modes:
                box.append(command)
        elif type_ == 'input':
            reader.insert_file(command.value['file_name'])
        # I think technically only this should cause a break, not EndOfFile.
        # But for now, whatever.
        elif type_ == 'END':
            break
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
            state.set_code(v['global'], v['code_type'], v['char'], v['code'])
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
