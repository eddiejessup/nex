import operator
import logging
from enum import Enum
from collections import deque

from .utils import ExecuteCommandError, TidyEnd, UserError
from .reader import EndOfFile
from .codes import CatCode, MathCode, GlyphCode, DelimiterCode, MathClass
from .instructions import Instructions, h_add_glue_instructions
from .instructioner import make_primitive_control_sequence_instruction
from .parameters import Parameters, is_parameter_type
from .accessors import is_register_type, SpecialsAccessor
from .box import (HBox, VBox, Rule, Glue, Character, FontDefinition,
                  FontSelection, Kern)
from .paragraphs import h_list_to_best_h_boxes
from . import evaluator as evaler
from .fonts import GlobalFontState
from .scopes import (ScopedCodes, ScopedRegisters, ScopedRouter,
                     ScopedParameters, ScopedFontState, Operation)
from .units import PhysicalUnit, MuUnit, InternalUnit, units_in_scaled_points
from .tokens import BuiltToken, InstructionToken

logger = logging.getLogger(__name__)


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
math_modes = (Mode.math, Mode.display_math)
# Defined for \ifinner, TeXBook page 209.
inner_modes = (Mode.internal_vertical, Mode.restricted_horizontal, Mode.math)


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
    Instructions.accent,
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
                 specials,
                 codes, registers, scoped_font_state, router, parameters):
        self.global_font_state = global_font_state
        self.specials = specials

        self.codes = codes
        self.registers = registers
        self.scoped_font_state = scoped_font_state
        self.router = router
        self.parameters = parameters

        # At the beginning, TeX is in vertical mode, ready to construct pages.
        self.modes = [(Mode.vertical, [])]
        self.groups = [Group.outside]

    @classmethod
    def from_defaults(cls, font_search_paths=None, global_font_state=None):
        # We allow passing this in for testing purposes, because it touches the
        # outside world (the file system, to search for fonts).
        if global_font_state is None:
            global_font_state = GlobalFontState(font_search_paths)
        specials = SpecialsAccessor.from_defaults()
        codes = ScopedCodes.from_defaults()
        registers = ScopedRegisters.from_defaults()
        scoped_font_state = ScopedFontState.from_defaults()
        router = ScopedRouter.from_defaults()
        parameters = ScopedParameters.from_defaults()
        return cls(global_font_state, specials,
                   codes, registers, scoped_font_state, router, parameters)

    # Mode.

    @property
    def mode(self):
        return self.modes[-1][0]

    @property
    def _layout_list(self):
        return self.modes[-1][1]

    def push_mode(self, mode):
        logger.info(f'Entering {mode}')
        self.modes.append((mode, []))

    def pop_mode(self):
        mode, layout_list = self.modes.pop()
        logger.info(f'Exited {mode}')
        return layout_list

    def append_to_list(self, item):
        self._layout_list.append(item)

    def extend_list(self, items):
        self._layout_list.extend(items)

    # Group.

    @property
    def group(self):
        return self.groups[-1]

    def push_group(self, group):
        self.groups.append(group)

    def pop_group(self):
        return self.groups.pop()

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
        if self.current_font_id != GlobalFontState.null_font_id:
            self.select_font(is_global=False, font_id=self.current_font_id)

    # Fonts.

    def define_new_font(self, file_name, at_clause):
        # Affects both global and scoped state: fonts are stored in the global
        # state, but the current font and control sequences to access them are
        # scoped.
        # Load the font.
        new_font_id = self.global_font_state.define_new_font(file_name,
                                                             at_clause)
        # Add an instruction in the layout list to define a font.
        font_info = self.global_font_state.get_font(new_font_id)
        font_define_item = FontDefinition(font_nr=new_font_id,
                                          font_name=font_info.font_name,
                                          file_name=font_info.file_name,
                                          at_clause=font_info.at_clause)
        self.append_to_list(font_define_item)
        return new_font_id

    @property
    def current_font_id(self):
        return self.scoped_font_state.current_font_id

    @property
    def current_font(self):
        return self.global_font_state.get_font(self.current_font_id)

    def select_font(self, is_global, font_id):
        self.scoped_font_state.set_current_font(is_global, font_id)
        font_select_item = FontSelection(font_nr=font_id)
        self.append_to_list(font_select_item)

    # Evaluate quantities.

    def get_box_dimen(self, i, type_):
        box_item = self.registers.get(Instructions.set_box.value, i=i)
        if type_ == Instructions.box_dimen_height.value:
            return box_item.height
        elif type_ == Instructions.box_dimen_width.value:
            return box_item.width
        elif type_ == Instructions.box_dimen_depth.value:
            return box_item.depth
        else:
            raise ValueError(f'Unknown box dimension requested: {v.type}')

    def get_infinite_dimen(self, nr_fils, nr_units):
        return BuiltToken(
            type_='fil_dimension',
            value={'factor': nr_units,
                   'number_of_fils': nr_fils}
        )

    def get_finite_dimen(self, unit, nr_units, is_true_unit):
        # Only one unit in mu units, a mu. I don't know what a mu is
        # though...
        if unit == MuUnit.mu:
            unit_scale = 1
        elif unit == InternalUnit.em:
            unit_scale = self.current_font.quad
        elif unit == InternalUnit.ex:
            unit_scale = self.current_font.x_height
        else:
            unit_scale = units_in_scaled_points[unit]
            if is_true_unit:
                magnification = self.parameters.get(Parameters.mag)
                # ['true'] unmagnifies the units, so that the subsequent
                # magnification will cancel out. For example, `\vskip 0.5
                # true cm' is equivalent to `\vskip 0.25 cm' if you have
                # previously said `\magnification=2000'.
                unit_scale *= 1000.0 / magnification
        size = int(round(nr_units * unit_scale))
        return size

    # Evaluate conditions.

    def evaluate_if_num(self, left_number, right_number, relation):
        left_number_eval = self.eval_number_token(left_number)
        right_number_eval = self.eval_number_token(right_number)
        operator_map = {
            '<': operator.lt,
            '=': operator.eq,
            '>': operator.gt,
        }
        op = operator_map[relation]
        outcome = op(left_number_eval, right_number_eval)
        return outcome

    evaluate_if_dim = evaluate_if_num

    def evaluate_if_odd(self, number):
        number_eval = self.eval_number_token(number)
        return number_eval % 2

    def evaluate_if_v_mode(self):
        return self.mode in vertical_modes

    def evaluate_if_h_mode(self):
        return self.mode in horizontal_modes

    def evaluate_if_m_mode(self):
        return self.mode in math_modes

    def evaluate_if_inner_mode(self):
        return self.mode in inner_modes

    def evaluate_if_chars_equal(self, tok_1, tok_2):
        # TODO: we will assume tokens are not expandable. Maybe check for this?
        # Instructions in TeXBook page 209.
        raise NotImplementedError

    def evaluate_if_cats_equal(self, tok_1, tok_2):
        # Instructions in TeXBook page 209.
        raise NotImplementedError

    def evaluate_if_tokens_equal(self, tok_1, tok_2):
        # Instructions in TeXBook page 210.
        raise NotImplementedError

    def evaluate_if_box_register_void(self, reg_nr):
        # Instructions in TeXBook page 210.
        raise NotImplementedError

    def evaluate_if_box_register_h_box(self, reg_nr):
        # Instructions in TeXBook page 210.
        raise NotImplementedError

    def evaluate_if_box_register_v_box(self, reg_nr):
        # Instructions in TeXBook page 210.
        raise NotImplementedError

    def evaluate_if_end_of_file(self, input_stream_nr):
        # Instructions in TeXBook page 210.
        raise NotImplementedError

    def evaluate_if_case(self, number):
        number_eval = self.eval_number_token(number)
        if number_eval < 0:
            raise ValueError(f'if-case should not return negative number: '
                             f'{number_eval}')
        return number_eval

    # Do chunky commands.

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
            logger.info(f'Adding paragraph')

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
            if isinstance(horizontal_list[-1], Glue):
                horizontal_list.pop()
            # Do \hskip\parfillskip.
            par_fill_glue = self.parameters.get(Parameters.par_fill_skip)
            horizontal_list.append(Glue(**par_fill_glue))
            h_size = self.parameters.get(Parameters.h_size)
            h_boxes = h_list_to_best_h_boxes(horizontal_list, h_size)
            # all_routes = get_all_routes(root_node, h_box_tree, h_size, outer=True)

            # for best_route in all_routes:
            for h_box in h_boxes:
                # Add it to the enclosing vertical list.
                self.append_to_list(h_box)
                bl_skip = self.parameters.get(Parameters.base_line_skip)
                line_glue_item = Glue(**bl_skip)
                self.append_to_list(line_glue_item)

            # par_glue_item = Glue(dimen=200000)
            # self.append_to_list(par_glue_item)
        else:
            import pdb; pdb.set_trace()

    def get_character_item(self, *args, **kwargs):
        return Character(font=self.current_font, *args, **kwargs)

    def add_character_code(self, code):
        self.append_to_list(self.get_character_item(code))

    def add_character_char(self, char):
        return self.add_character_code(ord(char))

    def add_accented_character(self, accent_code, char_code):
        char_item = self.get_character_item(char_code)
        char_w = self.current_font.width(char_code)
        acc_w = self.current_font.width(accent_code)
        # Go back to the middle of the character, than go back half the accent
        # width, so that the middle of the accent will be the same as that of
        # the character.
        kern_item = Kern(int(round(-char_w / 2 - acc_w / 2)))
        # TeXbook page 54: The accent is assumed to be properly positioned for
        # a character whose height equals the x-height of the current font;
        # taller or shorter characters cause the accent to be raised or
        # lowered, taking due account of the slantedness of the fonts of
        # accenter and accentee.
        # TODO: Slantedness.
        char_h = self.current_font.height(char_code)
        height_to_raise = char_h - self.current_font.x_height
        acc_char_item = self.get_character_item(accent_code)
        acc_item = HBox(contents=[acc_char_item], offset=height_to_raise)
        # TeXbook page 54: The width of the final construction is the width of
        # the character being accented, regardless of the width of the accent.
        item = HBox(contents=[char_item, kern_item, acc_item],
                    to=char_item.width)
        self.append_to_list(item)

    def do_accent(self, accent_code, target_code=None):
        logger.info(f"Adding accent \"{accent_code}\"")
        # TeXbook page 54: If it turns out that no suitable character is
        # present, the accent will appear by itself as if you had said
        # \char\<number> instead of
        # \accent\<number>. For example, \'{} produces '.
        if target_code is None:
            self.add_character_code(accent_code)
        else:
            self.add_accented_character(accent_code, target_code)
        # TODO: Set space factor to 1000.

    def add_kern(self, length):
        return self.append_to_list(Kern(length))

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
            space_glue_item = Glue(dimen=font.spacing,
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
            width = self.eval_number_token(width)
        if height is None:
            if self.mode == Mode.vertical:
                height = self.parameters.get(Parameters.v_size)
            else:
                raise NotImplementedError
        else:
            height = self.eval_number_token(height)
        if depth is None:
            if self.mode == Mode.vertical:
                depth = self.parameters.get(Parameters.v_size)
            else:
                raise NotImplementedError
        else:
            depth = self.eval_number_token(depth)
        self.add_rule(width, height, depth)

    def add_h_rule(self, width, height, depth):
        from .pydvi.TeXUnit import pt2sp
        if width is None:
            if self.mode in (Mode.horizontal, Mode.vertical):
                width = self.parameters.get(Parameters.h_size)
            else:
                raise NotImplementedError
        else:
            width = self.eval_number_token(width)
        if height is None:
            height = int(pt2sp(0.4))
        else:
            height = self.eval_number_token(height)
        if depth is None:
            depth = 0
        else:
            depth = self.eval_number_token(depth)
        self.add_rule(width, height, depth)

    def do_indent(self):
        if self.mode in vertical_modes:
            # "The \parskip glue is appended to the current list, unless
            # TeX is in internal vertical mode and the current list is
            # empty. Then TeX enters unrestricted horizontal mode, starting
            # the horizontal list with an empty hbox whose width is
            # \parindent. The \everypar tokens are inserted into TeX's
            # input. The page builder is exercised."
            if self.mode != Mode.internal_vertical:
                par_skip_glue = self.parameters.get(Parameters.par_skip)
                par_skip_glue_item = Glue(**par_skip_glue)
                self.append_to_list(par_skip_glue_item)
            self.push_mode(Mode.horizontal)
            # An empty box of width \parindent is appended to the current
            # list, and the space factor is set to 1000.
            par_indent_width = self.parameters.get(Parameters.par_indent)
            par_indent_hbox_item = HBox(contents=[], to=par_indent_width)
            self.append_to_list(par_indent_hbox_item)
        elif self.mode in horizontal_modes:
            raise NotImplementedError
        else:
            raise ValueError(f"Unknown mode '{self.mode}'")

    def set_box_register(self, i, item, is_global):
        self.registers.set(type_=Instructions.set_box.value, i=i,
                           value=item, is_global=is_global)

    def get_register_box(self, i, copy):
        if copy:
            get_func = self.registers.get
        else:
            get_func = self.registers.pop
        return get_func(Instructions.set_box.value, i)

    def append_register_box(self, i, copy):
        box_item = self.get_register_box(i, copy)
        # If void box, do nothing.
        if box_item is not None:
            self.append_to_list(box_item)

    def append_unboxed_register_box(self, i, copy, horizontal):
        # See TeXbook page 120.
        # TODO: implement global voiding:
        # 'If you say `\global\setbox3=<box>`, register \box3 will become
        # "globally void" when it is subsequently used or unboxed.'
        # TODO: Unset glue:
        # An unboxing operation 'unsets' any glue that was set at the box's
        # outer level. For example, consider the sequence of commands:
        #
        # \setbox5=\hbox{A \hbox{B C}} \setbox6=\hbox to 1.05\wd5{\unhcopy5}
        #
        # This makes \box6 five percent wider than \box5; the glue between A
        # and \hbox{B C} stretches to make the difference, but the glue inside
        # the inner hbox does not change.
        box_item = self.get_register_box(i, copy)
        if isinstance(box_item, HBox):
            if horizontal:
                unwrapped_box_contents = box_item.contents
            else:
                raise UserError('Asked to unbox horizontal box, '
                                'but found vertical box')
        elif isinstance(box_item, VBox):
            if horizontal:
                raise UserError('Asked to unbox vertical box, '
                                'but found horizontal box')
            else:
                unwrapped_box_contents = box_item.contents
        # Void box.
        elif box_item is None:
            unwrapped_box_contents = []
        else:
            raise ValueError(f'Box Register contains non-box: {box_item}')
        self.extend_list(unwrapped_box_contents)

    # Driving with tokens.

    def execute_command_tokens(self, commands, banisher, reader):
        while True:
            try:
                self.execute_next_command_token(commands, banisher, reader)
            except EndOfFile:
                return
            except EndOfSubExecutor:
                return

    def execute_next_command_token(self, commands, banisher, reader):
        command = next(commands)
        try:
            self.execute_command_token(command, banisher, reader)
        except (EndOfFile, EndOfSubExecutor, TidyEnd):
            raise
        except Exception as e:
            raise ExecuteCommandError(command, e)

    def _parse_h_box_token(self, v):
        conts = v['contents']
        spec = v['specification']
        to = None
        spread = None
        if spec is not None:
            d = self.eval_number_token(spec.value)
            if spec.type == 'to':
                to = d
            elif spec.type == 'spread':
                spread = d
            else:
                raise ValueError(f'Unknown specification type {spec.type}')
        h_box_item = HBox(contents=conts, to=to, spread=spread)
        return h_box_item

    def eval_size_token(self, size_token):
        v = size_token.value
        # If the size is the contents of an integer or dimen parameter.
        if isinstance(v, InstructionToken) and v.type in (Instructions.integer_parameter.value,
                                                          Instructions.dimen_parameter.value):
            return self.parameters.get(v.value['parameter'])
        # If the size is the contents of a count or dimen register.
        elif isinstance(v, BuiltToken) and v.type in (Instructions.count.value,
                                                      Instructions.dimen.value):
            # The register number is a generic 'number' token, so evaluate
            # this.
            evaled_i = self.eval_number_token(v.value)
            return self.registers.get(v.type, i=evaled_i)
        elif isinstance(v, BuiltToken) and v.type in (Instructions.box_dimen_height.value,
                                                      Instructions.box_dimen_width.value,
                                                      Instructions.box_dimen_depth.value):
            # The box register number is a generic 'number' token, so evaluate
            # this.
            evaled_i = self.eval_number_token(v.value)
            return self.get_box_dimen(evaled_i, v.type)
        # If the size is the short-hand character token.
        # This is different to, for example, a count_def_token. A character
        # token has an integer that represents a character code, and is itself
        # the value. A count-def token has an integer that represents the
        # *location* of the actual value.
        elif isinstance(v, InstructionToken) and v.type in ('CHAR_DEF_TOKEN', 'MATH_CHAR_DEF_TOKEN'):
            return v.value
        # If the size is the code of the target of a backtick instruction.
        elif isinstance(v, BuiltToken) and v.type == 'backtick':
            return evaler.get_backtick_target_code(target=v.value)
        # If the size is the integer represented by an integer literal.
        elif isinstance(v, BuiltToken) and v.type == 'integer_constant':
            return evaler.get_integer_constant(v.value)
        # If the size is the real number represented by a decimal number
        # literal.
        elif isinstance(v, BuiltToken) and v.type == 'decimal_constant':
            return evaler.get_real_decimal_constant(v.value)
        # If the size is the value represented by a short-hand def token.
        elif isinstance(v, BuiltToken) and v.type == 'internal':
            return v.value
        # If the size is a specification of a dimension (this is different to a
        # call to retrieve the contents of a dimen register).
        elif isinstance(v, BuiltToken) and v.type == 'dimen':
            nr_units = self.eval_size_token(v.value['factor'])
            unit_attrs = v.value['unit']
            unit = unit_attrs['unit']
            if unit == PhysicalUnit.fil:
                nr_fils = unit_attrs['number_of_fils']
                return self.get_infinite_dimen(nr_fils, nr_units)
            else:
                is_true_unit = unit_attrs.get('true', False)
                return self.get_finite_dimen(unit, nr_units, is_true_unit)
        else:
            raise ValueError

    def eval_number_token(self, number_token):
        number_value = number_token.value
        # Occurs if the number is a register-def-token.
        if isinstance(number_value, BuiltToken) and number_value.type == 'internal_number':
            return number_value.value
        elif isinstance(number_value, dict):
            size_token = number_value['size']
            size = self.eval_size_token(size_token)
            sign = evaler.evaluate_signs(number_value['signs'])
            if isinstance(size, BuiltToken) and size.type == 'fil_dimension':
                size.value['factor'] *= sign
            else:
                size *= sign
            return size
        else:
            raise ValueError

    def eval_glue_token(self, glue_token):
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
                    evaluated_dimen = self.eval_number_token(dimen_tok)
                evaluated_glue[dimen_name] = evaluated_dimen
        # If the size is the contents of a glue or mu glue register.
        elif isinstance(v, BuiltToken) and v.type in (Instructions.skip.value,
                                                      Instructions.mu_skip.value):
            # The register number is a generic 'number' token, so evaluate this
            # first.
            evaled_i = self.eval_number_token(v.value)
            v = self.registers.get(v.type, i=evaled_i)
            return v
        # If the size is the contents of a parameter.
        elif isinstance(v, InstructionToken) and v.type in (Instructions.glue_parameter.value,
                                                            Instructions.mu_glue_parameter.value):
            return self.parameters.get(v.value['parameter'])
        return evaluated_glue

    def eval_token_list_token(self, token_list_token):
        token_list_value = token_list_token.value
        if token_list_value.type == 'general_text':
            evaluated_token_list = token_list_value.value
        # Also could be token_register, or token parameter.
        else:
            raise NotImplementedError
        return evaluated_token_list

    def execute_command_token(self, command, banisher, reader):
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
            logger.info(f'"{type_}" causing shift to horizontal mode')
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
        elif type_ == Instructions.space.value:
            self.do_space()
        elif type_ == Instructions.par.value:
            self.do_paragraph()
        elif type_ == 'character':
            logger.info(f"Adding character \"{v['char']}\"")
            self.add_character_char(v['char'])
        elif type_ == Instructions.accent.value:
            assignments = v['assignments'].value
            accent_code_eval = self.eval_number_token(v['accent_code'])
            char_tok = v['target_char']
            if char_tok is None:
                target_char_code = None
            elif char_tok.type == 'character':
                target_char_code = ord(char_tok.value['char'])
            else:
                raise NotImplementedError
            # TeXbook page 54: Mode-independent commands like font changes may
            # appear between the accent number and the character to be
            # accented, but grouping operations must not intervene.
            for assignment in assignments:
                self.execute_command_token(assignment, banisher, reader)
            self.do_accent(accent_code_eval, target_char_code)
        elif type_ == Instructions.v_rule.value:
            logger.info(f"Adding vertical rule")
            self.add_v_rule(**v)
        elif type_ == Instructions.h_rule.value:
            logger.info(f"Adding horizontal rule")
            self.add_h_rule(**v)
        # The box already has its contents in the correct way, built using this
        # very method. Recursion still amazes me sometimes.
        elif type_ == 'h_box':
            logger.info(f'Adding horizontal box')
            h_box_item = self._parse_h_box_token(v)
            self.append_to_list(h_box_item)
        elif type_ in (Instructions.box.value, Instructions.copy.value):
            evaled_i = self.eval_number_token(v)
            # \box empties the register; \copy doesn't
            is_copy = type_ == Instructions.copy.value
            self.append_register_box(i=evaled_i, copy=is_copy)
        elif type_ == 'un_box':
            reg_nr = self.eval_number_token(v['nr'])
            is_copy = v['cmd_type'] in (Instructions.un_h_copy,
                                        Instructions.un_v_copy)
            is_h = v['cmd_type'] in (Instructions.un_h_copy,
                                     Instructions.un_h_box)
            self.append_unboxed_register_box(i=reg_nr, copy=is_copy,
                                             horizontal=is_h)
        # Commands like font commands aren't exactly boxes, but they go through
        # as DVI commands. Just put them in the box for now to deal with later.
        elif type_ == 'font_selection':
            logger.info(f"Selecting font {v['font_id']}")
            self.select_font(v['global'], v['font_id'])
        elif type_ == 'font_definition':
            file_name = v['file_name'].value
            logger.info(f"Defining font at \"{file_name}\" as \"{v['control_sequence_name']}\"")
            new_font_id = self.define_new_font(
                file_name, v['at_clause'],
            )
            # Make a control sequence pointing to it.
            self.router.define_new_font_control_sequence(
                v['global'], v['control_sequence_name'], new_font_id)
        elif type_ == 'family_assignment':
            family_nr_uneval = v['family_nr']
            family_nr_eval = self.eval_number_token(family_nr_uneval)
            logger.info(f"Setting font family {family_nr_eval}")
            self.scoped_font_state.set_font_family(v['global'],
                                                   family_nr_eval,
                                                   v['font_range'],
                                                   v['font_id'])
        elif type_ == 'input':
            file_name = command.value['file_name']
            logger.info(f"Inserting new file '{file_name}'")
            reader.insert_file(file_name)
        # I think technically only this should cause the program to end, not
        # EndOfFile anywhere. But for now, whatever.
        elif type_ == 'END':
            logger.info(f"Doing paragraph if needed, then ending")
            self.do_paragraph()
            raise TidyEnd
        elif type_ == 'short_hand_definition':
            code_uneval = v['code']
            code_eval = self.eval_number_token(code_uneval)
            cs_name = v['control_sequence_name']
            # TODO: Log symbolic argument too.
            logger.info(f'Defining short macro "{cs_name}" as {code_eval}')
            self.router.do_short_hand_definition(
                v['global'], cs_name, v['def_type'],
                code_eval
            )
        elif type_ == 'macro_assignment':
            name = v['name']
            logger.info(f'Defining macro "{name}"')
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
            value_evaluate_map = {
                'number': self.eval_number_token,
                'dimen': self.eval_number_token,
                'glue': self.eval_glue_token,
                'token_list': self.eval_token_list_token,
            }
            value_evaluate_func = value_evaluate_map[value.type]
            evaled_value = value_evaluate_func(value)
            if is_register_type(variable.type):
                evaled_i = self.eval_number_token(variable.value)
                self.registers.set(
                    type_=variable.type, i=evaled_i, value=evaled_value,
                    is_global=v['global'],
                )
            elif is_parameter_type(variable.type):
                parameter = variable.value['parameter']
                self.parameters.set_parameter(
                    name=parameter, value=evaled_value,
                    is_global=v['global'],
                )
        elif type_ == 'advance':
            variable, value = v['variable'], v['value']
            # See 'variable_assignment' case.
            evaled_value = self.eval_number_token(value)
            kwargs = {'is_global': v['global'],
                      'by_operand': evaled_value,
                      'operation': Operation.advance}
            if is_register_type(variable.type):
                evaled_i = self.eval_number_token(variable.value)
                self.registers.modify_register_value(
                    type_=variable.type, i=evaled_i, **kwargs
                )
            elif is_parameter_type(variable.type):
                self.parameters.modify_parameter_value(
                    name=variable.value['parameter'], **kwargs
                )
            else:
                raise ValueError(f"Unknown unknown variable type: "
                                 f"'{variable.type}'")
        elif type_ == Instructions.set_box.value:
            evaled_i = self.eval_number_token(v['nr'])
            box_type = v['box'].type
            if box_type == 'h_box':
                box_item = self._parse_h_box_token(v['box'].value)
            else:
                raise NotImplementedError
            self.set_box_register(evaled_i, box_item, v['global'])
        elif type_ == 'PATTERNS':
            raise NotImplementedError
        elif type_ == 'HYPHENATION':
            raise NotImplementedError
        elif type_ == 'code_assignment':
            code_type = v['code_type']
            char_size = self.eval_number_token(v['char'])
            code_size = self.eval_number_token(v['code'])
            char = chr(char_size)
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
        elif type_ == 'let_assignment':
            self.router.do_let_assignment(v['global'], new_name=v['name'],
                                          target_token=v['target_token'])
        elif type_ == 'skew_char_assignment':
            code_eval = self.eval_number_token(v['code'])
            self.global_font_state.set_hyphen_char(v['font_id'], code_eval)
        elif type_ == 'hyphen_char_assignment':
            code_eval = self.eval_number_token(v['code'])
            self.global_font_state.set_hyphen_char(v['font_id'], code_eval)
        elif type_ == 'message':
            conts = v['content'].value
            s = ''.join(t.value['char'] for t in conts)
            print(f'MESSAGE: {s}')
        elif type_ == 'write':
            conts = v['content'].value
            # s = ''.join(t.value['char'] for t in conts)
            print(f'LOG: <TODO>')
            # TODO: This should be read with expansion, but at the moment we
            # read it unexpanded, so what we get here is not printable.
            pass
        elif type_ == 'RELAX':
            pass
        elif type_ == 'INDENT':
            self.do_indent()
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
            glue = self.eval_glue_token(v)
            item = Glue(**glue)
            logger.info(f'Adding vertical glue {item}')
            self.append_to_list(item)
        elif type_ == 'H_STRETCH_OR_SHRINK':
            unit = {'unit': PhysicalUnit.fil,
                    'true': True,
                    'number_of_fils': 1,
                    'factor': 1}
            fil = BuiltToken(type_='fil_unit', value=unit)
            item = Glue(dimen=0, stretch=fil, shrink=fil)
            logger.info(f'Adding horizontal super-elastic glue {item}')
            self.append_to_list(item)
        else:
            raise ValueError(f"Command type '{type_}' not recognised.")

    # This method has a long name to emphasize that it will return the index of
    # the token block to pick, not the result of the condition.
    def evaluate_if_token_to_block(self, if_token):
        v = if_token.value
        t = if_token.type
        if t == 'IF_NUM':
            relation_str = v['relation'].value['char']
            outcome = self.evaluate_if_num(v['left_number'], v['right_number'],
                                           relation_str)
        elif t == 'IF_DIMEN':
            relation_str = v['relation'].value['char']
            outcome = self.evaluate_if_dim(v['left_dimen'], v['right_dimen'],
                                           relation_str)
        elif t == 'IF_CASE':
            outcome = self.evaluate_if_case(v['number'])
        elif t == 'IF_TRUE':
            outcome = True
        elif t == 'IF_FALSE':
            outcome = False
        else:
            raise NotImplementedError
        if t == 'IF_CASE':
            i_block_to_pick = outcome
        else:
            i_block_to_pick = 0 if outcome else 1
        return i_block_to_pick
