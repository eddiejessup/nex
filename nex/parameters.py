from enum import Enum

from .instructions import Instructions
from .tokens import instructions_to_types

params = {
    'PRE_TOLERANCE': Instructions.integer_parameter,
    'TOLERANCE': Instructions.integer_parameter,
    'H_BADNESS': Instructions.integer_parameter,
    'V_BADNESS': Instructions.integer_parameter,
    'LINE_PENALTY': Instructions.integer_parameter,
    'HYPHEN_PENALTY': Instructions.integer_parameter,
    'EX_HYPHEN_PENALTY': Instructions.integer_parameter,
    'BIN_OP_PENALTY': Instructions.integer_parameter,
    'REL_PENALTY': Instructions.integer_parameter,
    'CLUB_PENALTY': Instructions.integer_parameter,
    'WIDOW_PENALTY': Instructions.integer_parameter,
    'DISPLAY_WIDOW_PENALTY': Instructions.integer_parameter,
    'BROKEN_PENALTY': Instructions.integer_parameter,
    'PRE_DISPLAY_PENALTY': Instructions.integer_parameter,
    'POST_DISPLAY_PENALTY': Instructions.integer_parameter,
    'INTER_LINE_PENALTY': Instructions.integer_parameter,
    'FLOATING_PENALTY': Instructions.integer_parameter,
    'OUTPUT_PENALTY': Instructions.integer_parameter,
    'DOUBLE_HYPHEN_DEMERITS': Instructions.integer_parameter,
    'FINAL_HYPHEN_DEMERITS': Instructions.integer_parameter,
    'ADJ_DEMERITS': Instructions.integer_parameter,
    'LOOSENESS': Instructions.integer_parameter,
    'PAUSING': Instructions.integer_parameter,
    'HOLDING_INSERTS': Instructions.integer_parameter,
    'TRACING_ON_LINE': Instructions.integer_parameter,
    'TRACING_MACROS': Instructions.integer_parameter,
    'TRACING_STATS': Instructions.integer_parameter,
    'TRACING_PARAGRAPHS': Instructions.integer_parameter,
    'TRACING_PAGES': Instructions.integer_parameter,
    'TRACING_OUTPUT': Instructions.integer_parameter,
    'TRACING_LOSTCHARS': Instructions.integer_parameter,
    'TRACING_COMMANDS': Instructions.integer_parameter,
    'TRACING_RESTORES': Instructions.integer_parameter,
    'LANGUAGE': Instructions.integer_parameter,
    'UC_HYPH': Instructions.integer_parameter,
    'LEFT_HYPHEN_MIN': Instructions.integer_parameter,
    'RIGHT_HYPHEN_MIN': Instructions.integer_parameter,
    'GLOBAL_DEFS': Instructions.integer_parameter,
    'MAX_DEAD_CYCLES': Instructions.integer_parameter,
    'HANG_AFTER': Instructions.integer_parameter,
    'FAM': Instructions.integer_parameter,
    'MAG': Instructions.integer_parameter,
    'ESCAPE_CHAR': Instructions.integer_parameter,
    'DEFAULT_HYPHEN_CHAR': Instructions.integer_parameter,
    'DEFAULT_SKEW_CHAR': Instructions.integer_parameter,
    'END_LINE_CHAR': Instructions.integer_parameter,
    'NEW_LINE_CHAR': Instructions.integer_parameter,
    'DELIMITER_FACTOR': Instructions.integer_parameter,
    # THESE TIME ONES WILL BE SET IN GET_INITIAL_PARAMETERS.
    'TIME': Instructions.integer_parameter,
    'DAY': Instructions.integer_parameter,
    'MONTH': Instructions.integer_parameter,
    'YEAR': Instructions.integer_parameter,
    'SHOW_BOX_BREADTH': Instructions.integer_parameter,
    'SHOW_BOX_DEPTH': Instructions.integer_parameter,
    'ERROR_CONTEXT_LINES': Instructions.integer_parameter,
    'H_FUZZ': Instructions.dimen_parameter,
    'V_FUZZ': Instructions.dimen_parameter,
    'OVER_FULL_RULE': Instructions.dimen_parameter,
    'H_SIZE': Instructions.dimen_parameter,
    'V_SIZE': Instructions.dimen_parameter,
    'MAX_DEPTH': Instructions.dimen_parameter,
    'SPLIT_MAX_DEPTH': Instructions.dimen_parameter,
    'BOX_MAX_DEPTH': Instructions.dimen_parameter,
    'LINE_SKIP_LIMIT': Instructions.dimen_parameter,
    'DELIMITER_SHORT_FALL': Instructions.dimen_parameter,
    'NULL_DELIMITER_SPACE': Instructions.dimen_parameter,
    'SCRIPT_SPACE': Instructions.dimen_parameter,
    'MATH_SURROUND': Instructions.dimen_parameter,
    'PRE_DISPLAY_SIZE': Instructions.dimen_parameter,
    'DISPLAY_WIDTH': Instructions.dimen_parameter,
    'DISPLAY_INDENT': Instructions.dimen_parameter,
    'PAR_INDENT': Instructions.dimen_parameter,
    'HANG_INDENT': Instructions.dimen_parameter,
    'H_OFFSET': Instructions.dimen_parameter,
    'V_OFFSET': Instructions.dimen_parameter,
    'BASE_LINE_SKIP': Instructions.glue_parameter,
    'LINE_SKIP': Instructions.glue_parameter,
    'PAR_SKIP': Instructions.glue_parameter,
    'ABOVE_DISPLAY_SKIP': Instructions.glue_parameter,
    'ABOVE_DISPLAY_SHORT_SKIP': Instructions.glue_parameter,
    'BELOW_DISPLAY_SKIP': Instructions.glue_parameter,
    'BELOW_DISPLAY_SHORT_SKIP': Instructions.glue_parameter,
    'LEFT_SKIP': Instructions.glue_parameter,
    'RIGHT_SKIP': Instructions.glue_parameter,
    'TOP_SKIP': Instructions.glue_parameter,
    'SPLIT_TOP_SKIP': Instructions.glue_parameter,
    'TAB_SKIP': Instructions.glue_parameter,
    'SPACE_SKIP': Instructions.glue_parameter,
    'X_SPACE_SKIP': Instructions.glue_parameter,
    'PAR_FILL_SKIP': Instructions.glue_parameter,
    'THIN_MU_SKIP': Instructions.mu_glue_parameter,
    'MED_MU_SKIP': Instructions.mu_glue_parameter,
    'THICK_MU_SKIP': Instructions.mu_glue_parameter,
    'OUTPUT': Instructions.token_parameter,
    'EVERY_PAR': Instructions.token_parameter,
    'EVERY_MATH': Instructions.token_parameter,
    'EVERY_DISPLAY': Instructions.token_parameter,
    'EVERY_H_BOX': Instructions.token_parameter,
    'EVERY_V_BOX': Instructions.token_parameter,
    'EVERY_JOB': Instructions.token_parameter,
    'EVERY_CR': Instructions.token_parameter,
    'ERR_HELP': Instructions.token_parameter,
}
Parameters = Enum('Parameters', {s.lower(): s for s in params})
param_to_instr = {p: params[p.value] for p in Parameters}
param_to_type = {p: instr.value for p, instr in param_to_instr.items()}

param_instrs = (
    Instructions.integer_parameter,
    Instructions.dimen_parameter,
    Instructions.glue_parameter,
    Instructions.mu_glue_parameter,
    Instructions.token_parameter,
)
parameter_instr_types = instructions_to_types(param_instrs)


def param_instr_subset(instr):
    return filter(lambda p: param_to_instr[p] == instr, Parameters)


def is_parameter_type(type_):
    return type_ in parameter_instr_types


# Specials.

specials = {
    'SPACE_FACTOR': Instructions.special_integer,
    # The number of lines in the paragraph most recently completed or partially
    # completed.
    'PREV_GRAF': Instructions.special_integer,
    # The number of times \output was called since the last \shipout.
    'DEAD_CYCLES': Instructions.special_integer,
    # Means different things:
    # 1. In the ouput routine, the total number of held-over insertions. For
    #    each class of insertions this includes the unused part of a split
    #    insertion and all other insertions which don't appear on the current
    #    page.
    # 2. In the page-making routine, the total of the \floatingpenalty for each
    #    unsplit insertion which is carried over to the next page.
    'INSERT_PENALTIES': Instructions.special_integer,

    # The depth of the last box added to the current vertical list.
    'PREV_DEPTH': Instructions.special_dimen,
    # The actual depth of the last box on the main page.
    'PAGE_DEPTH': Instructions.special_dimen,
    # The desired height of the current page.
    'PAGE_GOAL': Instructions.special_dimen,
    # The accumulated height of the current page.
    'PAGE_TOTAL': Instructions.special_dimen,
    # The amount of finite stretchability in the current page.
    'PAGE_STRETCH': Instructions.special_dimen,
    # The amount of first-order infinite stretchability in the current page.
    'PAGE_FIL_STRETCH': Instructions.special_dimen,
    # The amount of second-order infinite stretchability in the current page.
    'PAGE_FILL_STRETCH': Instructions.special_dimen,
    # The amount of third-order infinite stretchability in the current page.
    'PAGE_FILLL_STRETCH': Instructions.special_dimen,
    # The amount of finite shrinkability in the current page.
    'PAGE_SHRINK': Instructions.special_dimen,
}
Specials = Enum('Specials', {s.lower(): s for s in specials})
special_to_instr = {p: specials[p.value] for p in Specials}
special_to_type = {p: instr.value for p, instr in special_to_instr.items()}

special_instrs = (
    Instructions.special_integer,
    Instructions.special_dimen,
)
special_instr_types = instructions_to_types(special_instrs)


def is_special_type(type_):
    return type_ in special_instr_types
