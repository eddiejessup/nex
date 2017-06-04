"""
Define the list of possible internal instructions that TeX might handle. These
might constitute full commands by themselves (such as 'end' to end the
document), or they might need to be composed with other pieces to form
commands, such as 'input', which requires a file-name as an argument.
"""
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

    'ACCENT',

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
    # Also remember SET_BOX, although it's slightly different.
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
    # \ifnum <number_1> <relation> <number_2>
    # Compare two integers. The <relation> must be "<_12", "=_12" or ">_12".
    'IF_NUM',
    # \ifdim <dimen_1> <relation> <dimen_2>
    # Compare two dimensions. Otherwise, same as above.
    'IF_DIMEN',
    'IF_ODD',
    'IF_V_MODE',
    'IF_H_MODE',
    'IF_M_MODE',
    'IF_INNER',
    'IF_CHAR',
    'IF_CAT',
    'IF_TOKEN',
    'IF_VOID',
    'IF_H_BOX',
    'IF_V_BOX',
    'IF_END_OF_FILE',
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
    'AFTER_ASSIGNMENT',
    'AFTER_GROUP',

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
    'ARBITRARY_TOKEN',
    # Control sequence names produced as part of a definition and such.
    'UNEXPANDED_CONTROL_SYMBOL',
    'UNEXPANDED_CONTROL_WORD',
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

unexpanded_cs_instructions = (
    I.unexpanded_control_symbol,
    I.unexpanded_control_word,
)

message_instructions = (
    I.message,
    I.error_message,
    I.write,
)

hyphenation_instructions = (
    I.hyphenation,
    I.patterns,
)

h_add_glue_instructions = (
    I.h_skip,
    I.h_fil,
    I.h_fill,
    I.h_stretch_or_shrink,
    I.h_fil_neg,
)


v_add_glue_instructions = (
    I.v_skip,
    I.v_fil,
    I.v_fill,
    I.v_stretch_or_shrink,
    I.v_fil_neg,
)

explicit_box_instructions = (
    I.h_box,
    I.v_box,
    I.v_top,
)

register_instructions = (
    I.count,
    I.dimen,
    I.skip,
    I.mu_skip,
    I.toks,
)

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

def_instructions = (
    I.def_,
    I.g_def,
    I.e_def,
    I.x_def,
)


if_instructions = (
    I.if_num,
    I.if_dimen,
    I.if_odd,
    I.if_v_mode,
    I.if_h_mode,
    I.if_m_mode,
    I.if_inner,
    I.if_char,
    I.if_cat,
    I.if_token,
    I.if_void,
    I.if_h_box,
    I.if_v_box,
    I.if_end_of_file,
    I.if_true,
    I.if_false,
    I.if_case,
)
