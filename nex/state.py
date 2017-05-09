from enum import Enum
from collections import deque

from .utils import ExecuteCommandError, TidyEnd
from .reader import EndOfFile
from .registers import is_register_type
from .codes import CatCode, MathCode, GlyphCode, DelimiterCode, MathClass
from .instructions import Instructions, h_add_glue_instructions
from .instructioner import make_primitive_control_sequence_instruction
from .tex_parameters import is_parameter_type, Parameters
from .box import (HBox, Rule, UnSetGlue, Character, FontDefinition,
                  FontSelection)
from .paragraphs import h_list_to_best_h_boxes
from . import evaluator as evaler
from .fonts import GlobalFontState
from .scopes import (ScopedCodes, ScopedRegisters, ScopedRouter,
                     ScopedParameters, ScopedFontState, Operation)


class Mode(Enum):
    # Building the main vertical list.
    vertical = 'V'
    # Building a vertical list for a vbox.
    internal_vertical = 'IV'
    # Building a horizontal list for a paragraph.
    horizontal = 'H'
    # Building a horizontal list for an hbox.
    restricted_horizontal = 'RH'
    # Building a formula to be placed in a horizontal list.
    math = 'M'
    # Building a formula to be placed on a line by itself,
    # interrupting the current paragraph.
    display_math = 'DM'


vertical_modes = (Mode.vertical, Mode.internal_vertical)
horizontal_modes = (Mode.horizontal, Mode.restricted_horizontal)


class Group(Enum):

    # Note, this is *not* the same as 'global scope'. We could enter
    # sub-groups that do not start a new scope, such as a math group.
    outside = 0
    # For 'local structure'.
    local = 1
    # \hbox{...}.
    h_box = 2
    # \hbox{...} in vertical mode.
    adjusted_h_box = 3
    # \vbox{...}.
    v_box = 4
    # \vtop{...}.
    v_top = 5
    # \halign{...} and \valign{...}.
    align = 6
    # \noalign{...}.
    no_align = 7
    # Output routine.
    output = 8
    # For things such as '^{...}'
    math = 9
    # \discretionary{...}{...}{...}.
    discretionary = 10
    # \insert{...} and \vadjust{...}
    insert = 11
    # \vcenter{...}
    v_center = 12
    # \mathchoice{...}{...}{...}{...}
    math_choice = 13
    # \begingroup...\endgroup
    local_verbose = 14
    # $...$
    math_shift = 15
    # \left...\right
    math_left_right = 16


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


class GlobalState:

    def __init__(self, global_font_state,
                 codes, registers, scoped_font_state, router, parameters):
        self.global_font_state = global_font_state
        self.codes = codes
        self.registers = registers
        self.scoped_font_state = scoped_font_state
        self.router = router
        self.parameters = parameters

        # At the beginning, TeX is in vertical mode, ready to construct pages.
        self.modes = [(Mode.vertical, [])]
        self.groups = [Group.outside]

    @classmethod
    def from_defaults(cls, font_search_paths):
        global_font_state = GlobalFontState(font_search_paths)
        codes = ScopedCodes.from_defaults()
        registers = ScopedRegisters.from_defaults()
        scoped_font_state = ScopedFontState.from_defaults()
        router = ScopedRouter.from_defaults()
        parameters = ScopedParameters.from_defaults()
        return cls(global_font_state,
                   codes, registers, scoped_font_state, router, parameters)

    # Mode.

    @property
    def mode(self):
        return self.modes[-1][0]

    @property
    def _layout_list(self):
        return self.modes[-1][1]

    def push_mode(self, mode):
        self.modes.append((mode, []))

    def pop_mode(self):
        mode, layout_list = self.modes.pop()
        return layout_list

    def append_to_list(self, item):
        self._layout_list.append(item)

    # Group.

    @property
    def group(self):
        return self.groups[-1]

    def push_group(self, group):
        self.groups.append(group)

    def pop_group(self):
        return self.groups.pop()

    # Affects both global and scoped state: fonts are stored in the global
    # state, but the current font and control sequences to access them are
    # scoped.

    def define_new_font(self, file_name, at_clause):
        # Load the font
        new_font_id = self.global_font_state.define_new_font(file_name, at_clause)
        # Add an instruction in the layout list to define a font.
        font_info = self.global_font_state.get_font(new_font_id)
        font_define_item = FontDefinition(font_nr=new_font_id,
                                          font_name=font_info.font_name,
                                          file_name=font_info.file_name,
                                          at_clause=font_info.at_clause)
        self.append_to_list(font_define_item)
        return new_font_id

    @property
    def current_font(self):
        current_font_id = self.scoped_font_state.current_font_id
        return self.global_font_state.get_font(current_font_id)

    # Scope

    @property
    def _scoped_accessors(self):
        return [self.codes, self.registers, self.scoped_font_state,
                self.router, self.parameters]

    def push_new_scope(self):
        for acc in self._scoped_accessors:
            acc.push_new_scope()

    def pop_scope(self):
        for acc in self._scoped_accessors:
            acc.pop_scope()

    def execute_commands(self, commands, banisher, reader):
        while True:
            try:
                self.execute_next_command(commands, banisher, reader)
            except EndOfFile:
                return
            except EndOfSubExecutor:
                return

    def execute_next_command(self, commands, banisher, reader):
        command = next(commands)
        try:
            self.execute_command(command, banisher, reader)
        except (EndOfFile, EndOfSubExecutor, TidyEnd):
            raise
        except Exception as e:
            raise ExecuteCommandError(command, e)

    def select_font(self, is_global, font_id):
        self.scoped_font_state.set_current_font(is_global, font_id)
        font_select_item = FontSelection(font_nr=font_id)
        self.append_to_list(font_select_item)

    def do_paragraph(self):
        if self.mode in vertical_modes:
            # The primitive \par command has no effect when TeX is in
            # vertical mode, except that the page builder is exercised in
            # case something is present on the contribution list, and the
            # paragraph shape parameters are cleared.
            return
        elif self.mode == Mode.restricted_horizontal:
            # The primitive \par command, also called \endgraf in plain
            # \TeX, does nothing in restricted horizontal mode.
            return
        elif self.mode == Mode.horizontal:
            # "But it terminates horizontal mode: The current list is
            # finished off by doing, '\unskip \penalty10000
            # \hskip\parfillskip' then it is broken into lines as explained
            # in Chapter 14, and TeX returns to the enclosing vertical or
            # internal vertical mode. The lines of the paragraph are
            # appended to the enclosing vertical list, interspersed with
            # interline glue and interline penalties, and with the
            # migration of vertical material that was in the horizontal
            # list. Then TeX exercises the page builder."

            # TODO: Not sure whether to do the above things as internal
            # calls, or whether the tokens should be inserted.
            # TODO: Do these commands before we pop.
            # Get the horizontal list
            horizontal_list = deque(self.pop_mode())
            # Do \unskip.
            if isinstance(horizontal_list[-1], UnSetGlue):
                horizontal_list.pop()
            # Do \hskip\parfillskip.
            par_fill_glue = self.parameters.get(Parameters.par_fill_skip)
            horizontal_list.append(UnSetGlue(**par_fill_glue))
            h_size = self.parameters.get(Parameters.h_size)
            h_boxes = h_list_to_best_h_boxes(horizontal_list, h_size)
            # all_routes = get_all_routes(root_node, h_box_tree, h_size, outer=True)

            # for best_route in all_routes:
            for h_box in h_boxes:
                # Add it to the enclosing vertical list.
                self.append_to_list(h_box)
                bl_skip = self.parameters.get(Parameters.base_line_skip)
                line_glue_item = UnSetGlue(**bl_skip)
                self.append_to_list(line_glue_item)

            # par_glue_item = UnSetGlue(dimen=200000)
            # self.append_to_list(par_glue_item)
        else:
            import pdb; pdb.set_trace()

    def add_character(self, char):
        character_item = Character(char, self.current_font)
        self.append_to_list(character_item)

    def do_space(self):
        if self.mode in vertical_modes:
            # "Spaces have no effects in vertical modes".
            pass
        elif self.mode in horizontal_modes:
            # Spaces append glue to the current list; the exact amount of
            # glue depends on \spacefactor, the current font, and the
            # \spaceskip and
            # \xspaceskip parameters, as described in Chapter 12.
            font = self.current_font
            space_glue_item = UnSetGlue(dimen=font.spacing,
                                        stretch=font.space_stretch,
                                        shrink=font.space_shrink)
            self.append_to_list(space_glue_item)
        else:
            import pdb; pdb.set_trace()

    def add_rule(self, width, height, depth):
        self.append_to_list(Rule(width, height, depth))

    def add_v_rule(self, width, height, depth):
        from .pydvi.TeXUnit import pt2sp
        if width is None:
            width = pt2sp(0.4)
        else:
            width = evaler.evaluate_dimen(self, width)
        if height is None:
            if self.mode == Mode.vertical:
                height = self.parameters.get(Parameters.v_size)
            else:
                raise NotImplementedError
        else:
            height = evaler.evaluate_dimen(self, height)
        if depth is None:
            if self.mode == Mode.vertical:
                depth = self.parameters.get(Parameters.v_size)
            else:
                raise NotImplementedError
        else:
            depth = evaler.evaluate_dimen(self, depth)
        self.add_rule(width, height, depth)

    def add_h_rule(self, width, height, depth):
        from .pydvi.TeXUnit import pt2sp
        if width is None:
            if self.mode in (Mode.horizontal, Mode.vertical):
                width = self.parameters.get(Parameters.h_size)
            else:
                raise NotImplementedError
        else:
            width = evaler.evaluate_dimen(self, width)
        if height is None:
            height = int(pt2sp(0.4))
        else:
            height = evaler.evaluate_dimen(self, height)
        if depth is None:
            depth = 0
        else:
            depth = evaler.evaluate_dimen(self, depth)
        self.add_rule(width, height, depth)

    def execute_command(self, command, banisher, reader):
        # Reader needed to allow us to insert new input in response to
        # commands.
        # Banisher needed to allow us to put output back on the queue in
        # response to commands.
        type_ = command.type
        v = command.value
        # Note: It would be nice to do this in the banisher, so we don't have
        # to mess about unpacking the command. But one cannot know at banisher-
        # time how a terminal token in isolation will be used. For example, a
        # char-cat pair might end up as part of a filename or something.
        if (self.mode in vertical_modes and
                command_shifts_to_horizontal(command)):
            # "If any of these tokens occurs as a command in vertical mode or
            # internal vertical mode, TeX automatically performs an \indent
            # command as explained above. This leads into horizontal mode with
            # the \everypar tokens in the input, after which TeX will see the
            # horizontal command again."
            # Put the terminal tokens that led to this command back on the
            # input queue.
            terminal_tokens = command._terminal_tokens
            # Get a primitive token for the indent command.
            indent_token = make_primitive_control_sequence_instruction(
                name='indent', instruction=Instructions.indent)
            # And add it before the tokens we just read.
            banisher.instructions.replace_tokens_on_input([indent_token] +
                                                          terminal_tokens)
        elif type_ == 'SPACE':
            self.do_space()
        elif type_ == 'PAR':
            self.do_paragraph()
        elif type_ == 'character':
            self.add_character(v['char'])
        elif type_ == 'V_RULE':
            self.add_v_rule(**v)
        elif type_ == 'H_RULE':
            self.add_h_rule(**v)
        # The box already has its contents in the correct way, built using this
        # very method. Recursion still amazes me sometimes.
        elif type_ == 'h_box':
            conts = v['contents'].value
            spec = v['specification']
            to = None
            spread = None
            if spec is not None:
                d = evaler.evaluate_dimen(self, spec.value)
                if spec.type == 'to':
                    to = d
                elif spec.type == 'spread':
                    spread = d
                else:
                    import pdb; pdb.set_trace()
            h_box_item = HBox(contents=conts, to=to, spread=spread)
            self.append_to_list(h_box_item)
        # Commands like font commands aren't exactly boxes, but they go through
        # as DVI commands. Just put them in the box for now to deal with later.
        elif type_ == 'font_selection':
            self.select_font(v['global'], v['font_id'])
        elif type_ == 'font_definition':
            new_font_id = self.define_new_font(
                v['file_name'].value, v['at_clause'],
            )
            # Make a control sequence pointing to it.
            self.router.define_new_font_control_sequence(
                v['global'], v['control_sequence_name'], new_font_id)
        elif type_ == 'family_assignment':
            family_nr = v['family_nr']
            family_nr_eval = evaler.evaluate_number(self, family_nr)
            self.scoped_font_state.set_font_family(v['global'],
                                                   family_nr_eval,
                                                   v['font_range'],
                                                   v['font_id'])
        elif type_ == 'input':
            reader.insert_file(command.value['file_name'])
        # I think technically only this should cause the program to end, not
        # EndOfFile anywhere. But for now, whatever.
        elif type_ == 'END':
            self.do_paragraph()
            raise TidyEnd
        elif type_ == 'short_hand_definition':
            code_eval = evaler.evaluate_number(self, v['code'])
            self.router.do_short_hand_definition(
                v['global'], v['control_sequence_name'], v['def_type'],
                code_eval
            )
        elif type_ == 'macro_assignment':
            name = v['name']
            self.router.set_macro(
                name, parameter_text=v['parameter_text'],
                replacement_text=v['replacement_text'],
                def_type=v['def_type'], prefixes=v['prefixes']
            )
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
            evaled_value = value_evaluate_func(self, value)
            evaled_i = evaler.evaluate_size(self, variable.value)
            if is_register_type(variable.type):
                self.registers.set(
                    is_global=v['global'], type_=variable.type,
                    i=evaled_i, value=evaled_value
                )
            elif is_parameter_type(variable.type):
                parameter = variable.value['parameter']
                self.parameters.set_parameter(
                    is_global=v['global'], parameter=parameter,
                    value=evaled_value
                )
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
            char_size = evaler.evaluate_number(self, v['char'])
            code_size = evaler.evaluate_number(self, v['code'])
            char = chr(char_size)
            # TODO: Move inside state? What exactly is the benefit?
            # I guess separation of routing logic from execution logic.
            if code_type == 'CAT_CODE':
                code = CatCode(code_size)
            elif code_type == 'MATH_CODE':
                parts = evaler.split_hex_code(code_size,
                                              hex_length=4, inds=(1, 2))
                math_class_i, family, position = parts
                math_class = MathClass(math_class_i)
                glyph_code = GlyphCode(family, position)
                code = MathCode(math_class, glyph_code)
            elif code_type in ('UPPER_CASE_CODE', 'LOWER_CASE_CODE'):
                code = chr(code_size)
            elif code_type == 'SPACE_FACTOR_CODE':
                code = code_size
            elif code_type == 'DELIMITER_CODE':
                parts = evaler.split_hex_code(code_size,
                                              hex_length=6, inds=(1, 3, 4))
                small_family, small_position, large_family, large_position = parts
                small_glyph_code = GlyphCode(small_family, small_position)
                large_glyph_code = GlyphCode(large_family, large_position)
                code = DelimiterCode(small_glyph_code, large_glyph_code)
            self.codes.set(v['global'], code_type, char, code)
        elif type_ == 'advance':
            value_eval = evaler.evaluate_number(self, v['value'])
            variable = v['variable']
            kwargs = {'is_global': v['global'],
                      'by_operand': value_eval,
                      'operation': Operation.advance}
            if is_register_type(variable.type):
                evaled_i = evaler.evaluate_size(self, variable.value)
                self.registers.modify_register_value(type_=variable.type,
                                                           i=evaled_i, **kwargs)
            elif is_parameter_type(variable.type):
                self.registers.modify_parameter_value(parameter=variable.value['parameter'],
                                                            **kwargs)
            else:
                import pdb; pdb.set_trace()
        elif type_ == 'let_assignment':
            self.router.do_let_assignment(v['global'], new_name=v['name'],
                                                target_token=v['target_token'])
        elif type_ == 'skew_char_assignment':
            # TODO: can we make this nicer by storing the char instead of the
            # number?
            code_eval = evaler.evaluate_number(self, v['code'])
            self.global_font_state.set_hyphen_char(v['font_id'],
                                                         code_eval)
        elif type_ == 'hyphen_char_assignment':
            # TODO: can we make this nicer by storing the char instead of the
            #         number?
            code_eval = evaler.evaluate_number(self, v['code'])
            self.global_font_state.set_hyphen_char(v['font_id'],
                                                         code_eval)
        elif type_ == 'message':
            # print(command.value)
            pass
        elif type_ == 'write':
            # print(command.value)
            pass
        elif type_ == 'RELAX':
            pass
        elif type_ == 'INDENT':
            if self.mode in vertical_modes:
                # "The \parskip glue is appended to the current list, unless
                # TeX is in internal vertical mode and the current list is
                # empty. Then TeX enters unrestricted horizontal mode, starting
                # the horizontal list with an empty hbox whose width is
                # \parindent. The \everypar tokens are inserted into TeX's
                # input. The page builder is exercised."
                if self.mode != Mode.internal_vertical:
                    par_skip_glue = self.parameters.get(Parameters.par_skip)
                    par_skip_glue_item = UnSetGlue(**par_skip_glue)
                    self.append_to_list(par_skip_glue_item)
                self.push_mode(Mode.horizontal)
                # An empty box of width \parindent is appended to the current
                # list, and the space factor is set to 1000.
                par_indent_width = self.parameters.get(Parameters.par_indent)
                par_indent_hbox_item = HBox(contents=[], to=par_indent_width)
                self.append_to_list(par_indent_hbox_item)
            elif self.mode in horizontal_modes:
                import pdb; pdb.set_trace()
        elif type_ == 'LEFT_BRACE':
            # A character token of category 1, or a control sequence like \bgroup
            # that has been \let equal to such a character token, causes TeX to
            # start a new level of grouping.
            self.push_group(Group.local)
            self.push_new_scope()
        elif type_ == 'RIGHT_BRACE':
            # I think roughly same comments as for LEFT_BRACE above apply.
            if self.group == Group.local:
                self.pop_group()
                self.pop_scope()
            # Groups where we started a sub-executor to get the box.
            # We need to tell the banisher to finish up so the resulting
            # box can be made into the container token.
            elif self.group in sub_executor_groups:
                # "
                # Eventually, when the matching '}' appears, TeX restores
                # values that were changed by assignments in the group just
                # ended.
                # "
                self.pop_group()
                self.pop_scope()
                raise EndOfSubExecutor
            else:
                import pdb; pdb.set_trace()
        elif type_ == 'V_SKIP':
            glue = evaler.evaluate_glue(self, v)
            item = UnSetGlue(**glue)
            self.append_to_list(item)
        elif type_ == 'H_STRETCH_OR_SHRINK':
            from .units import PhysicalUnit
            from .tokens import BuiltToken
            unit = {'unit': PhysicalUnit.fil,
                    'true': True,
                    'number_of_fils': 1,
                    'factor': 1}
            fil = BuiltToken(type_='fil_unit', value=unit)
            item = UnSetGlue(dimen=0, stretch=fil, shrink=fil)
            self.append_to_list(item)
        else:
            # print(type_)
            # pass
            import pdb; pdb.set_trace()
