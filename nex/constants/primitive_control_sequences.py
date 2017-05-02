from string import ascii_lowercase
from enum import Enum


instructions = (
    'CAT_CODE',
    'MATH_CODE',
    'UPPER_CASE_CODE',
    'LOWER_CASE_CODE',
    'SPACE_FACTOR_CODE',
    'DELIMITER_CODE',

    'LET',

    'ADVANCE',

    'PAR',
    'RELAX',
    'IMMEDIATE',

    'FONT',

    # Font assignment things.
    'SKEW_CHAR',
    'HYPHEN_CHAR',
    'FONT_DIMEN',

    # Font ranges.
    'TEXT_FONT',
    'SCRIPT_FONT',
    'SCRIPT_SCRIPT_FONT',

    'UNDEFINED',

    # Macro modifiers.
    'GLOBAL_MOD',
    'LONG_MOD',
    'OUTER_MOD',

    # Box register assignment.
    'SET_BOX',
    # Box register calls.
    # This one deletes the register contents when called.
    'BOX',
    # This one does not.
    'COPY',

    'UN_H_BOX',
    'UN_H_COPY',
    'UN_V_BOX',
    'UN_V_COPY',

    # Remove and return (pop) the most recent h- or v-box, if any.
    'LAST_BOX',
    # Make a vbox by splitting off a certain amount of material from a box
    # register.
    'V_SPLIT',

    'BOX_DIMEN_HEIGHT',
    'BOX_DIMEN_WIDTH',
    'BOX_DIMEN_DEPTH',

    'KERN',
    'MATH_KERN',

    'V_RULE',
    'H_RULE',

    'INPUT',

    'END',

    'CHAR',
    'INDENT',

    # Messages.
    'MESSAGE',
    'ERROR_MESSAGE',
    'WRITE',

    # Hyphenation.
    'HYPHENATION',
    'PATTERNS',

    'H_SKIP',
    'H_FIL',
    'H_FILL',
    'H_STRETCH_OR_SHRINK',
    'H_FIL_NEG',
    'V_SKIP',
    'V_FIL',
    'V_FILL',
    'V_STRETCH_OR_SHRINK',
    'V_FIL_NEG',

    # Explicit boxes.
    'H_BOX',
    'V_BOX',
    # Like 'vbox', but its baseline is that of the top box inside,
    # rather than the bottom box inside.
    'V_TOP',

    # Registers.
    'COUNT',
    'DIMEN',
    'SKIP',
    'MU_SKIP',
    'TOKS',

    # Short-hand definitions.
    # Short-hand character definitions.
    'CHAR_DEF',
    'MATH_CHAR_DEF',
    # Short-hand register definitions.
    'COUNT_DEF',
    'DIMEN_DEF',
    'SKIP_DEF',
    'MU_SKIP_DEF',
    'TOKS_DEF',

    # Definitions.
    'DEF_',
    'G_DEF',
    'E_DEF',
    'X_DEF',

    # Conditions
    'IF_NUM',
    'IF_TRUE',
    'IF_FALSE',
    'IF_CASE',

    # Condition sub-instructions
    # Can't call it 'else' for Python syntax reasons when I make the enum.
    'ELSE_',
    'END_IF',
    'OR_',

    # Instructions that are handled before parsing, in the banisher.
    'MACRO',
    'STRING',
    'CS_NAME',
    'END_CS_NAME',
    'EXPAND_AFTER',
    'UPPER_CASE',
    'LOWER_CASE',
    'CR',

    # Short-hand definition tokens (produced internally).
    'CHAR_DEF_TOKEN',
    'MATH_CHAR_DEF_TOKEN',
    'COUNT_DEF_TOKEN',
    'DIMEN_DEF_TOKEN',
    'SKIP_DEF_TOKEN',
    'MU_SKIP_DEF_TOKEN',
    'TOKS_DEF_TOKEN',
    # Not defined by a short-hand def, but acts similarly.
    'FONT_DEF_TOKEN',

    # Strange internal instructions that are produced by the banisher.
    'LET_TARGET',
    # Control sequence names produced as part of a definition and such.
    'UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE',
    'UNEXPANDED_MANY_CHAR_CONTROL_SEQUENCE',
    # Parameter placeholder in macro definitions.
    'DELIMITED_PARAM',
    'UNDELIMITED_PARAM',
    'PARAM_NUMBER',
    'PARAMETER_TEXT',
    'BALANCED_TEXT_AND_RIGHT_BRACE',
    'HORIZONTAL_MODE_MATERIAL_AND_RIGHT_BRACE',
    'VERTICAL_MODE_MATERIAL_AND_RIGHT_BRACE',

    # Instructions usually created by char-cat pairs.

    'LESS_THAN',
    'GREATER_THAN',
    'EQUALS',
    'PLUS_SIGN',
    'MINUS_SIGN',
    'SINGLE_QUOTE',
    'DOUBLE_QUOTE',
    'BACKTICK',
    'POINT',
    'COMMA',

    'ZERO',
    'ONE',
    'TWO',
    'THREE',
    'FOUR',
    'FIVE',
    'SIX',
    'SEVEN',
    'EIGHT',
    'NINE',

    # Hex letters.
    'A',
    'B',
    'C',
    'D',
    'E',
    'F',

    'SPACE',
    'LEFT_BRACE',
    'RIGHT_BRACE',
    'ACTIVE_CHARACTER',
    'PARAMETER',
    'MATH_SHIFT',
    'ALIGN_TAB',
    'SUPERSCRIPT',
    'SUBSCRIPT',
    'MISC_CHAR_CAT_PAIR',

    'INTEGER_PARAMETER',
    'DIMEN_PARAMETER',
    'GLUE_PARAMETER',
    'MU_GLUE_PARAMETER',
    'TOKEN_PARAMETER',

    'SPECIAL_INTEGER',
    'SPECIAL_DIMEN',
)
# Add instructions representing ordinary character literal char-cats.
# TODO: Check if all these are really needed.
instructions += tuple('NON_ACTIVE_UNCASED_{}'.format(c)
                      for c in ascii_lowercase)


Instructions = Enum('Instructions', {s.lower(): s for s in instructions})
I = Instructions

terminal_primitive_instructions = (
    I.cat_code,
    I.math_code,
    I.upper_case_code,
    I.lower_case_code,
    I.space_factor_code,
    I.delimiter_code,
    I.let,
    I.advance,
    I.par,
    I.relax,
    I.immediate,
    I.font,
    I.skew_char,
    I.hyphen_char,
    I.font_dimen,
    I.text_font,
    I.script_font,
    I.script_script_font,
    I.undefined,
    I.global_mod,
    I.long_mod,
    I.outer_mod,
    I.set_box,
    I.box,
    I.copy,
    I.un_h_box,
    I.un_h_copy,
    I.un_v_box,
    I.un_v_copy,
    I.last_box,
    I.v_split,
    I.box_dimen_height,
    I.box_dimen_width,
    I.box_dimen_depth,
    I.kern,
    I.math_kern,
    I.v_rule,
    I.h_rule,
    I.input,
    I.end,
    I.char,
    I.indent,

    I.less_than,
    I.greater_than,
    I.equals,
    I.plus_sign,
    I.minus_sign,
    I.zero,
    I.one,
    I.two,
    I.three,
    I.four,
    I.five,
    I.six,
    I.seven,
    I.eight,
    I.nine,
    I.single_quote,
    I.double_quote,
    I.backtick,
    I.point,
    I.comma,
    I.a,
    I.b,
    I.c,
    I.d,
    I.e,
    I.f,
    I.space,
    I.left_brace,
    I.right_brace,
    I.active_character,
    # I don't think these are terminal.
    # I.parameter,
    # I.math_shift,
    # I.align_tab,
    # I.superscript,
    # I.subscript,
    I.misc_char_cat_pair,
    I.integer_parameter,
    I.dimen_parameter,
    I.glue_parameter,
    I.mu_glue_parameter,
    I.token_parameter,
    I.special_integer,
    I.special_dimen,

    I.char_def_token,
    I.math_char_def_token,
    I.count_def_token,
    I.dimen_def_token,
    I.skip_def_token,
    I.mu_skip_def_token,
    I.toks_def_token,
    I.font_def_token,
)
# Add ordinary character literals.
t = tuple(Instructions['non_active_uncased_{}'.format(c.lower())]
          for c in ascii_lowercase)
terminal_primitive_instructions += t


unexpanded_cs_instructions = (
    I.unexpanded_one_char_control_sequence,
    I.unexpanded_many_char_control_sequence,
)
terminal_primitive_instructions += unexpanded_cs_instructions

message_instructions = (
    I.message,
    I.error_message,
    I.write,
)
terminal_primitive_instructions += message_instructions

hyphenation_instructions = (
    I.hyphenation,
    I.patterns,
)
terminal_primitive_instructions += hyphenation_instructions

h_add_glue_instructions = (
    I.h_skip,
    I.h_fil,
    I.h_fill,
    I.h_stretch_or_shrink,
    I.h_fil_neg,
)
terminal_primitive_instructions += h_add_glue_instructions


v_add_glue_instructions = (
    I.v_skip,
    I.v_fil,
    I.v_fill,
    I.v_stretch_or_shrink,
    I.v_fil_neg,
)
terminal_primitive_instructions += v_add_glue_instructions

explicit_box_instructions = (
    I.h_box,
    I.v_box,
    I.v_top,
)
terminal_primitive_instructions += explicit_box_instructions

register_instructions = (
    I.count,
    I.dimen,
    I.skip,
    I.mu_skip,
    I.toks,
)
terminal_primitive_instructions += register_instructions

short_hand_def_instructions = (
    I.char_def,
    I.math_char_def,
    # Short-hand register definitions.
    I.count_def,
    I.dimen_def,
    I.skip_def,
    I.mu_skip_def,
    I.toks_def,
)
terminal_primitive_instructions += short_hand_def_instructions

def_instructions = (
    I.def_,
    I.g_def,
    I.e_def,
    I.x_def,
)
terminal_primitive_instructions += def_instructions

terminal_internal_instructions = (
    I.let_target,
    I.parameter_text,
    I.balanced_text_and_right_brace,
    I.horizontal_mode_material_and_right_brace,
    I.vertical_mode_material_and_right_brace,
)

terminal_instructions = (terminal_internal_instructions +
                         terminal_primitive_instructions)

# Note: These are only terminal for the condition parser, so not added to that
# list.
if_instructions = (
    I.if_num,
    I.if_true,
    I.if_false,
    I.if_case,
)
