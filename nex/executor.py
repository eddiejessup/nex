from collections import deque

from .utils import ExecuteCommandError
from .reader import EndOfFile
from .registers import is_register_type
from .codes import CatCode, MathCode, GlyphCode, DelimiterCode, MathClass
from .constants.primitive_control_sequences import (Instructions,
                                                    h_add_glue_instructions)
from .tex_parameters import is_parameter_type
from .router import primitive_canon_tokens
from .state import Operation, Mode, Group, vertical_modes, horizontal_modes
from .box import (HBox, Rule, UnSetGlue, Character, FontDefinition,
                  FontSelection)
from .paragraphs import h_list_to_best_h_boxes
from . import evaluator as evaler


sub_executor_groups = (
    Group.h_box,
    Group.adjusted_h_box,
    Group.v_box,
    Group.v_top,
)


class EndOfSubExecutor(Exception):
    pass


shift_to_horizontal_instructions = (
    Instructions.char,
    Instructions.char_def_token,
    Instructions.un_h_box,
    Instructions.un_h_copy,
    # Instructions.v_align
    Instructions.v_rule,
    # Instructions.accent,
    # Instructions.discretionary,
    # Instructions.control_hyphen,
    # TODO: Add control-space primitive, parsing and control sequence.
    # Instructions.control_space,
)
shift_to_horizontal_instructions += tuple(h_add_glue_instructions)
shift_to_horizontal_types = tuple(i.value
                                  for i in shift_to_horizontal_instructions)
shift_to_horizontal_cat_codes = (CatCode.letter,
                                 CatCode.other,
                                 CatCode.math_shift)


def command_shifts_to_horizontal(command):
    if command.type in shift_to_horizontal_types:
        return True
    if (command.type == 'character' and
            command.value['cat'] in shift_to_horizontal_cat_codes):
        return True
    return False


def execute_command(command, state, banisher, reader):
    type_ = command.type
    v = command.value
    # Note: It would be nice to do this in the banisher, so we don't have
    # to mess about unpacking the command. But one cannot know at banisher-
    # time how a terminal token in isolation will be used. For example, a
    # char-cat pair might end up as part of a filename or something.
    if (state.mode in vertical_modes and
            command_shifts_to_horizontal(command)):
        # "If any of these tokens occurs as a command in vertical mode or
        # internal vertical mode, TeX automatically performs an \indent
        # command as explained above. This leads into horizontal mode with
        # the \everypar tokens in the input, after which TeX will see the
        # horizontal command again."
        # Put the terminal tokens that led to this command back on the input
        # queue.
        terminal_tokens = command._terminal_tokens
        # Get a primitive token for the indent command.
        indent_token = primitive_canon_tokens['indent']
        # And add it before the tokens we just read.
        banisher.instructions.replace_tokens_on_input([indent_token] +
                                                      terminal_tokens)
    elif type_ == 'SPACE':
        if state.mode in vertical_modes:
            # "Spaces have no effects in vertical modes".
            pass
        elif state.mode in horizontal_modes:
            # Spaces append glue to the current list; the exact amount of glue
            # depends on \spacefactor, the current font, and the \spaceskip and
            # \xspaceskip parameters, as described in Chapter 12.
            font = state.current_font
            # import pdb; pdb.set_trace()
            space_glue_item = UnSetGlue(dimen=font.spacing,
                                        stretch=font.space_stretch,
                                        shrink=font.space_shrink)
            state.append_to_list(space_glue_item)
        else:
            import pdb; pdb.set_trace()
    elif type_ == 'PAR':
        if state.mode in vertical_modes:
            # The primitive \par command has no effect when TeX is in vertical
            # mode, except that the page builder is exercised in case something
            # is present on the contribution list, and the paragraph shape
            # parameters are cleared.
            pass
        elif state.mode == Mode.restricted_horizontal:
            # The primitive \par command, also called \endgraf in plain \TeX,
            # does nothing in restricted horizontal mode.
            pass
        elif state.mode == Mode.horizontal:
            # "But it terminates horizontal mode: The current list is finished
            # off by doing,
            #   '\unskip \penalty10000 \hskip\parfillskip'
            # then it is broken into lines as explained in Chapter 14, and TeX
            # returns to the enclosing vertical or internal vertical mode. The
            # lines of the paragraph are appended to the enclosing vertical
            # list, interspersed with interline glue and interline penalties,
            # and with the migration of vertical material that was in the
            # horizontal list. Then TeX exercises the page builder."

            # TODO: Not sure whether to do the above things as internal calls,
            # or whether the tokens should be inserted.
            # TODO: Do these commands before we pop, using a proper interface
            # to state.
            # Get the horizontal list
            horizontal_list = deque(state.pop_mode())
            # Do \unskip.
            if isinstance(horizontal_list[-1], UnSetGlue):
                horizontal_list.pop()
            # Do \hskip\parfillskip.
            par_fill_glue = state.get_parameter_value('parfillskip')
            horizontal_list.append(UnSetGlue(**par_fill_glue))
            h_size = state.get_parameter_value('hsize')
            h_boxes = h_list_to_best_h_boxes(horizontal_list, h_size)
            # all_routes = get_all_routes(root_node, h_box_tree, h_size, outer=True)

            # for best_route in all_routes:
            for h_box in h_boxes:
                # Add it to the enclosing vertical list.
                state.append_to_list(h_box)
                line_glue_item = UnSetGlue(**state.get_parameter_value('baselineskip'))
                state.append_to_list(line_glue_item)

            # par_glue_item = UnSetGlue(dimen=200000)
            # state.append_to_list(par_glue_item)
        else:
            import pdb; pdb.set_trace()
    elif type_ == 'character':
        character_item = Character(command.value['char'],
                                   state.current_font)
        state.append_to_list(character_item)
    elif type_ == 'V_RULE':
        e_spec = {k: (None if d is None else evaler.evaluate_dimen(state, d))
                  for k, d in v.items()}
        rule_item = Rule(**e_spec)
        state.append_to_list(rule_item)
    # The box already has its contents in the correct way, built using this
    # very method. Recursion still amazes me sometimes.
    elif type_ == 'h_box':
        conts = v['contents'].value
        spec = v['specification']
        to = None
        spread = None
        if spec is not None:
            d = evaler.evaluate_dimen(state, spec.value)
            if spec.type == 'to':
                to = d
            elif spec.type == 'spread':
                spread = d
            else:
                import pdb; pdb.set_trace()
        h_box_item = HBox(contents=conts, to=to, spread=spread)
        state.append_to_list(h_box_item)
    # Commands like font commands aren't exactly boxes, but they go through
    # as DVI commands. Just put them in the box for now to deal with later.
    elif type_ == 'font_selection':
        state.set_current_font(v['global'], v['font_id'])
        font_select_item = FontSelection(font_nr=v['font_id'])
        state.append_to_list(font_select_item)
    elif type_ == 'font_definition':
        new_font_id = state.define_new_font(v['global'],
                                            v['control_sequence_name'],
                                            v['file_name'].value,
                                            v['at_clause'])
        font_info = state.global_font_state.fonts[new_font_id]
        font_define_item = FontDefinition(font_nr=new_font_id,
                                          font_name=font_info.font_name,
                                          file_name=font_info.file_name,
                                          at_clause=font_info.at_clause)
        state.append_to_list(font_define_item)
    elif type_ == 'family_assignment':
        family_nr = v['family_nr']
        family_nr_eval = evaler.evaluate_number(state, family_nr)
        state.set_font_family(v['global'], family_nr_eval,
                              v['font_range'], v['font_id'])
    elif type_ == 'input':
        reader.insert_file(command.value['file_name'])
    # I think technically only this should cause the program to end, not
    # EndOfFile anywhere. But for now, whatever.
    elif type_ == 'END':
        raise EndOfFile
    elif type_ == 'short_hand_definition':
        code_eval = evaler.evaluate_number(state, v['code'])
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
            'number': evaler.evaluate_number,
            'dimen': evaler.evaluate_dimen,
            'glue': evaler.evaluate_glue,
            'mu_glue': evaler.evaluate_glue,
            'token_list': evaler.evaluate_token_list,
        }
        value_evaluate_func = value_evaluate_map[value.type]
        evaled_value = value_evaluate_func(state, value)
        evaled_i = evaler.evaluate_size(state, variable.value)
        if is_register_type(variable.type):
            state.set_register_value(is_global=v['global'],
                                     type_=variable.type,
                                     i=evaled_i,
                                     value=evaled_value)
        elif is_parameter_type(variable.type):
            param_name = variable.value['canonical_name']
            state.set_parameter(is_global=v['global'],
                                name=param_name, value=evaled_value)
    elif type_ == 'set_box_assignment':
        # TODO: Implement.
        pass
    elif type_ == 'PATTERNS':
        # TODO: Implement.
        pass
    elif type_ == 'HYPHENATION':
        # TODO: Implement.
        pass
    elif type_ == 'code_assignment':
        code_type = v['code_type']
        char_size = evaler.evaluate_number(state, v['char'])
        code_size = evaler.evaluate_number(state, v['code'])
        char = chr(char_size)
        # TODO: Move inside state? What exactly is the benefit?
        # I guess separation of routing logic from execution logic.
        if code_type == 'CAT_CODE':
            code = CatCode(code_size)
        elif code_type == 'MATH_CODE':
            parts = evaler.split_hex_code(code_size, hex_length=4, inds=(1, 2))
            math_class_i, family, position = parts
            math_class = MathClass(math_class_i)
            glyph_code = GlyphCode(family, position)
            code = MathCode(math_class, glyph_code)
        elif code_type in ('UPPER_CASE_CODE', 'LOWER_CASE_CODE'):
            code = chr(code_size)
        elif code_type == 'SPACE_FACTOR_CODE':
            code = code_size
        elif code_type == 'DELIMITER_CODE':
            parts = evaler.split_hex_code(code_size, hex_length=6, inds=(1, 3, 4))
            small_family, small_position, large_family, large_position = parts
            small_glyph_code = GlyphCode(small_family, small_position)
            large_glyph_code = GlyphCode(large_family, large_position)
            code = DelimiterCode(small_glyph_code, large_glyph_code)
        state.set_code(v['global'], code_type, char, code)
    elif type_ == 'advance':
        value_eval = evaler.evaluate_number(state, v['value'])
        variable = v['variable']
        kwargs = {'is_global': v['global'],
                  'by_operand': value_eval,
                  'operation': Operation.advance}
        if is_register_type(variable.type):
            evaled_i = evaler.evaluate_size(state, variable.value)
            state.modify_register_value(type_=variable.type, i=evaled_i,
                                        **kwargs)
        elif is_parameter_type(variable.type):
            state.modify_parameter_value(name=variable.value['canonical_name'],
                                         **kwargs)
        else:
            import pdb; pdb.set_trace()
    elif type_ == 'let_assignment':
        state.do_let_assignment(v['global'], new_name=v['name'],
                                target_token=v['target_token'])
    elif type_ == 'skew_char_assignment':
        # TODO: can we make this nicer by storing the char instead of the
        # number?
        code_eval = evaler.evaluate_number(state, v['code'])
        state.global_font_state.set_hyphen_char(v['font_id'], code_eval)
    elif type_ == 'hyphen_char_assignment':
        # TODO: can we make this nicer by storing the char instead of the
        #         number?
        code_eval = evaler.evaluate_number(state, v['code'])
        state.global_font_state.set_hyphen_char(v['font_id'], code_eval)
    elif type_ == 'message':
        # print(command.value)
        pass
    elif type_ == 'write':
        # print(command.value)
        pass
    elif type_ == 'RELAX':
        pass
    elif type_ == 'INDENT':
        if state.mode in vertical_modes:
            # "The \parskip glue is appended to the current list, unless TeX is
            # in internal vertical mode and the current list is empty. Then TeX
            # enters unrestricted horizontal mode, starting the horizontal list
            # with an empty hbox whose width is \parindent. The \everypar
            # tokens are inserted into TeX's input. The page builder is
            # exercised."
            if not (state.mode == Mode.internal_vertical):
                par_skip_glue = state.get_parameter_value('parskip')
                par_skip_glue_item = UnSetGlue(**par_skip_glue)
                state.append_to_list(par_skip_glue_item)
            state.push_mode(Mode.horizontal)
            # An empty box of width \parindent is appended to the current list, and
            # the space factor is set to 1000.
            par_indent_width = state.get_parameter_value('parindent')
            par_indent_hbox_item = HBox(contents=[], to=par_indent_width)
            state.append_to_list(par_indent_hbox_item)
        elif state.mode in horizontal_modes:
            import pdb; pdb.set_trace()
    elif type_ == 'LEFT_BRACE':
        # A character token of category 1, or a control sequence like \bgroup
        # that has been \let equal to such a character token, causes TeX to
        # start a new level of grouping.
        state.push_group(Group.local)
        state.push_new_scope()
    elif type_ == 'RIGHT_BRACE':
        # I think roughly same comments as for LEFT_BRACE above apply.
        if state.group == Group.local:
            state.pop_group()
            state.pop_scope()
        # Groups where we started a sub-executor to get the box.
        # We need to tell the banisher to finish up so the resulting
        # box can be made into the container token.
        elif state.group in sub_executor_groups:
            # "
            # Eventually, when the matching '}' appears, TeX restores
            # values that were changed by assignments in the group just
            # ended.
            # "
            state.pop_group()
            state.pop_scope()
            raise EndOfSubExecutor
        else:
            import pdb; pdb.set_trace()
    else:
        # print(type_)
        # pass
        import pdb; pdb.set_trace()


def execute_commands(chunk_grabber, state, banisher, reader):
    _cs = []
    while True:
        try:
            command = chunk_grabber.get_chunk()
        except EndOfFile:
            break
        _cs.append(command)
        try:
            execute_command(command, state, banisher, reader)
        except EndOfFile:
            break
        except EndOfSubExecutor:
            break
        except Exception as e:
            raise ExecuteCommandError(command, e)
