from collections import deque
import operator

from common import Token
from utils import NoSuchControlSequence
from parse_utils import ExpectedParsingError, ExhaustedTokensError
from reader import EndOfFile
from registers import is_register_type
from typer import (CatCode, MathCode, GlyphCode, DelimiterCode, MathClass,
                   PhysicalUnit, MuUnit, InternalUnit, units_in_scaled_points,
                   h_add_glue_tokens,
                   )
from tex_parameters import glue_keys
from expander import is_parameter_type, primitive_canon_tokens
from interpreter import Mode, Group, vertical_modes, horizontal_modes
from box import HBox, Rule, Glue, Character, FontDefinition, FontSelection, GlueNotSet


sub_executor_groups = (
    Group.h_box,
    Group.adjusted_h_box,
    Group.v_box,
    Group.v_top,
)


def h_list_to_h_boxes(horizontal_list, h_size):
    h_boxes = []
    # Loop making a paragraph.
    while horizontal_list:
        tentative_h_box = HBox(specification=None,
                               contents=[])
        tent_contents = tentative_h_box.contents
        # Loop making a line.
        while horizontal_list:
            word_list = []
            # Loop making a word.
            while True:
                word_list.append(horizontal_list.popleft())
                if isinstance(word_list[-1], Glue):
                    break_glue = word_list.pop()
                    break
            tent_contents.extend(word_list)
            badness = tentative_h_box.badness(h_size)
            if badness < 200:
                break
            # If we are not breaking, put the break glue on the list.
            tent_contents.append(break_glue)
        h_boxes.append(tentative_h_box)
    return h_boxes


class EndOfSubExecutor(Exception):
    pass


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
        magnification = state.get_parameter_value('mag')
        # ['true'] unmagnifies the units, so that the subsequent magnification
        # will cancel out. For example, `\vskip 0.5 true cm' is equivalent to
        # `\vskip 0.25 cm' if you have previously said `\magnification=2000'.
        if is_true_unit:
            number_of_scaled_points *= 1000.0 / magnification
            number_of_scaled_points = int(number_of_scaled_points)
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


shift_to_horizontal_control_sequence_types = (
    'char',
    'CHAR_DEF_TOKEN',
    'UN_H_BOX',
    'UN_H_COPY',
    # 'V_ALIGN',
    'V_RULE',
    # 'ACCENT',
    # 'DISCRETIONARY',
    # 'CONTROL_HYPHEN',
    # TODO: Add control-space primitive, parsing and control sequence.
    # 'CONTROL_SPACE',
)
shift_to_horizontal_control_sequence_types += tuple(h_add_glue_tokens.values())
shift_to_horizontal_cat_codes = (CatCode.letter,
                                 CatCode.other,
                                 CatCode.math_shift)


def command_shifts_to_horizontal(command):
    if command.type in shift_to_horizontal_control_sequence_types:
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
        banisher.input_tokens_queue.extendleft(reversed(terminal_tokens))
        # Get a primitive token for the indent command.
        indent_token = primitive_canon_tokens['indent']
        # And add it before the tokens we just read.
        banisher.input_tokens_queue.appendleft(indent_token)
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
            space_glue_item = Glue(dimen=font.spacing,
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

            # Get the horizontal list
            horizontal_list = deque(state.pop_mode())
            # Do \unskip.
            if isinstance(horizontal_list[-1], Glue):
                horizontal_list.pop()
            # Do \hskip\parfillskip.
            par_fill_glue = state.get_parameter_value('parfillskip')
            horizontal_list.append(Glue(**par_fill_glue))

            h_size = state.get_parameter_value('hsize')
            h_box_items = h_list_to_h_boxes(horizontal_list, h_size)

            for h_box_item in h_box_items:
                h_box_item.scale_and_set(h_size)
                # Add it to the enclosing vertical list.
                state.append_to_list(h_box_item)
                line_glue_item = Glue(**state.get_parameter_value('baselineskip'))
                state.append_to_list(line_glue_item)
            par_glue_item = Glue(dimen=1600000)
            state.append_to_list(par_glue_item)
        else:
            import pdb; pdb.set_trace()
    elif type_ == 'character':
        character_item = Character(command.value['char'],
                                   state.current_font)
        state.append_to_list(character_item)
    elif type_ == 'V_RULE':
        e_spec = {k: (None if d is None else evaluate_dimen(state, d))
                  for k, d in v.items()}
        rule_item = Rule(**e_spec)
        state.append_to_list(rule_item)
    # The box already has its contents in the correct way, built using this
    # very method. Recursion still amazes me sometimes.
    elif type_ == 'h_box':
        conts = v['contents'].value
        h_box_item = HBox(specification=v['specification'],
                          contents=conts)
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
                                            v['file_name'],
                                            v['at_clause'])
        font_define_item = FontDefinition(font_nr=new_font_id,
                                          font_name=v['file_name'],
                                          file_name=v['file_name'] + '.tfm',
                                          at_clause=v['at_clause'])
        state.append_to_list(font_define_item)
    elif type_ == 'family_assignment':
        family_nr = v['family_nr']
        family_nr_eval = evaluate_number(state, family_nr)
        state.set_font_family(v['global'], family_nr_eval,
                              v['font_range'], v['font_id'])
    elif type_ == 'input':
        reader.insert_file(command.value['file_name'])
    # I think technically only this should cause the program to end, not
    # EndOfFile anywhere. But for now, whatever.
    elif type_ == 'END':
        raise EndOfFile
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
                par_skip_glue_item = Glue(**par_skip_glue)
                state.append_to_list(par_skip_glue_item)
            state.push_mode(Mode.horizontal)
            par_indent_width = state.get_parameter_value('parindent')
            par_indent_hbox_item = HBox(specification=par_indent_width,
                                        contents=[])
            state.append_to_list(par_indent_hbox_item)
        # An empty box of width \parindent is appended to the current list, and
        # the space factor is set to 1000.
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


def execute_commands(command_grabber, state, banisher, reader):
    _cs = []
    while True:
        try:
            command = command_grabber.get_command()
        except EndOfFile:
            break
        _cs.append(command)
        try:
            execute_command(command, state, banisher, reader)
        except EndOfFile:
            break
        except EndOfSubExecutor:
            break


def write_box_to_doc(doc, layout_list, horizontal=False):
    for item in layout_list:
        if isinstance(item, FontDefinition):
            doc.define_font(item.font_nr, item.font_name,
                            font_path=item.file_name)
        elif isinstance(item, FontSelection):
            doc.select_font(item.font_nr)
        elif isinstance(item, HBox):
            doc.push()
            write_box_to_doc(doc, item.contents, horizontal=True)
            doc.pop()
        elif isinstance(item, Character):
            doc.set_char(item.code)
        elif isinstance(item, Glue):
            if not horizontal:
                item.set(item.natural_dimen)
            try:
                amount = item.dimen
            except GlueNotSet:
                import pdb; pdb.set_trace()
            if horizontal:
                # doc.put_rule(height=1000, width=amount)
                doc.right(amount)
            else:
                doc.down(amount)
        else:
            import pdb; pdb.set_trace()


class CommandGrabber(object):

    def __init__(self, banisher, parser):
        self.banisher = banisher
        self.parser = parser

        # Processing input tokens might return many tokens, so
        # we store them in a buffer.
        self.buffer_queue = deque()

    def get_command(self):
        # Want to extend the queue-to-be-parsed one token at a time,
        # so we can break as soon as we have all we need.
        parse_queue = deque()
        # Get enough tokens to evaluate command. We know to stop adding tokens
        # when we see a switch from failing because we run out of tokens
        # (ExhaustedTokensError) to an actual syntax error
        # (ExpectedParsingError).
        # We keep track of if we have parsed, just for checking for weird
        # situations.
        have_parsed = False
        while True:
            try:
                t = self.banisher.pop_or_fill_and_pop(self.buffer_queue)
            except EndOfFile:
                # If we get an EndOfFile, and we have just started trying to
                # get a command, we are done, so just return.
                if not parse_queue:
                    raise
                # If we get to the end of the file in the middle of a command,
                # something is wrong.
                else:
                    import pdb; pdb.set_trace()
                    pass
            # If we get an expansion error, it might be because we need to
            # execute this command first.
            except NoSuchControlSequence:
                if have_parsed:
                    break
                else:
                    import pdb; pdb.set_trace()
                    pass
            except Exception as e:
                import pdb; pdb.set_trace()
                raise
            parse_queue.append(t)
            try:
                result = self.parser.parse(iter(parse_queue))
            except ExpectedParsingError:
                if have_parsed:
                    # We got so many tokens of fluff due to extra reads,
                    # to make the parse queue not-parse.
                    # Put them back on the buffer.
                    self.buffer_queue.appendleft(parse_queue.pop())
                    break
                else:
                    import pdb; pdb.set_trace()
                    pass
            except ExhaustedTokensError:
                # Carry on getting more tokens, because it seems we can.
                pass
            else:
                # Implemented in a modified version of rply, we annotate the
                # output token to indicate whether the only action from the
                # current parse state could be to end. In this case, we do not
                # bother adding another token, and just finish the command.
                # This is important to limit the number of cases where we
                # expand too far, and must handle bad expansion of the post-
                # command tokens.
                if result._could_only_end:
                    break
                have_parsed = True
        result._terminal_tokens = parse_queue
        return result
