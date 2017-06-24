"""
Define the list of internal parameters that TeX requires to run. For example,
'par_indent' controls the size of a paragraph's indentation. There are several
types, roughly: integers, dimensions (physical lengths), 'glue' (a physical
length that can vary to some extent), and lists of tokens.
"""
from typing import Dict, Tuple, Iterable

from enum import Enum

from .instructions import Instructions
from ..tokens import instructions_to_types


class Parameters(Enum):
    pre_tolerance = 'PRE_TOLERANCE'
    tolerance = 'TOLERANCE'
    h_badness = 'H_BADNESS'
    v_badness = 'V_BADNESS'
    line_penalty = 'LINE_PENALTY'
    hyphen_penalty = 'HYPHEN_PENALTY'
    ex_hyphen_penalty = 'EX_HYPHEN_PENALTY'
    bin_op_penalty = 'BIN_OP_PENALTY'
    rel_penalty = 'REL_PENALTY'
    club_penalty = 'CLUB_PENALTY'
    widow_penalty = 'WIDOW_PENALTY'
    display_widow_penalty = 'DISPLAY_WIDOW_PENALTY'
    broken_penalty = 'BROKEN_PENALTY'
    pre_display_penalty = 'PRE_DISPLAY_PENALTY'
    post_display_penalty = 'POST_DISPLAY_PENALTY'
    inter_line_penalty = 'INTER_LINE_PENALTY'
    floating_penalty = 'FLOATING_PENALTY'
    output_penalty = 'OUTPUT_PENALTY'
    double_hyphen_demerits = 'DOUBLE_HYPHEN_DEMERITS'
    final_hyphen_demerits = 'FINAL_HYPHEN_DEMERITS'
    adj_demerits = 'ADJ_DEMERITS'
    looseness = 'LOOSENESS'
    pausing = 'PAUSING'
    holding_inserts = 'HOLDING_INSERTS'
    tracing_on_line = 'TRACING_ON_LINE'
    tracing_macros = 'TRACING_MACROS'
    tracing_stats = 'TRACING_STATS'
    tracing_paragraphs = 'TRACING_PARAGRAPHS'
    tracing_pages = 'TRACING_PAGES'
    tracing_output = 'TRACING_OUTPUT'
    tracing_lostchars = 'TRACING_LOSTCHARS'
    tracing_commands = 'TRACING_COMMANDS'
    tracing_restores = 'TRACING_RESTORES'
    language = 'LANGUAGE'
    uc_hyph = 'UC_HYPH'
    left_hyphen_min = 'LEFT_HYPHEN_MIN'
    right_hyphen_min = 'RIGHT_HYPHEN_MIN'
    global_defs = 'GLOBAL_DEFS'
    max_dead_cycles = 'MAX_DEAD_CYCLES'
    hang_after = 'HANG_AFTER'
    fam = 'FAM'
    mag = 'MAG'
    escape_char = 'ESCAPE_CHAR'
    default_hyphen_char = 'DEFAULT_HYPHEN_CHAR'
    default_skew_char = 'DEFAULT_SKEW_CHAR'
    end_line_char = 'END_LINE_CHAR'
    new_line_char = 'NEW_LINE_CHAR'
    delimiter_factor = 'DELIMITER_FACTOR'
    # THESE TIME ONES WILL BE SET IN GET_INITIAL_PARAMETERS.
    time = 'TIME'
    day = 'DAY'
    month = 'MONTH'
    year = 'YEAR'
    show_box_breadth = 'SHOW_BOX_BREADTH'
    show_box_depth = 'SHOW_BOX_DEPTH'
    error_context_lines = 'ERROR_CONTEXT_LINES'
    h_fuzz = 'H_FUZZ'
    v_fuzz = 'V_FUZZ'
    over_full_rule = 'OVER_FULL_RULE'
    h_size = 'H_SIZE'
    v_size = 'V_SIZE'
    max_depth = 'MAX_DEPTH'
    split_max_depth = 'SPLIT_MAX_DEPTH'
    box_max_depth = 'BOX_MAX_DEPTH'
    line_skip_limit = 'LINE_SKIP_LIMIT'
    delimiter_short_fall = 'DELIMITER_SHORT_FALL'
    null_delimiter_space = 'NULL_DELIMITER_SPACE'
    script_space = 'SCRIPT_SPACE'
    math_surround = 'MATH_SURROUND'
    pre_display_size = 'PRE_DISPLAY_SIZE'
    display_width = 'DISPLAY_WIDTH'
    display_indent = 'DISPLAY_INDENT'
    par_indent = 'PAR_INDENT'
    hang_indent = 'HANG_INDENT'
    h_offset = 'H_OFFSET'
    v_offset = 'V_OFFSET'
    base_line_skip = 'BASE_LINE_SKIP'
    line_skip = 'LINE_SKIP'
    par_skip = 'PAR_SKIP'
    above_display_skip = 'ABOVE_DISPLAY_SKIP'
    above_display_short_skip = 'ABOVE_DISPLAY_SHORT_SKIP'
    below_display_skip = 'BELOW_DISPLAY_SKIP'
    below_display_short_skip = 'BELOW_DISPLAY_SHORT_SKIP'
    left_skip = 'LEFT_SKIP'
    right_skip = 'RIGHT_SKIP'
    top_skip = 'TOP_SKIP'
    split_top_skip = 'SPLIT_TOP_SKIP'
    tab_skip = 'TAB_SKIP'
    space_skip = 'SPACE_SKIP'
    x_space_skip = 'X_SPACE_SKIP'
    par_fill_skip = 'PAR_FILL_SKIP'
    thin_mu_skip = 'THIN_MU_SKIP'
    med_mu_skip = 'MED_MU_SKIP'
    thick_mu_skip = 'THICK_MU_SKIP'
    output = 'OUTPUT'
    every_par = 'EVERY_PAR'
    every_math = 'EVERY_MATH'
    every_display = 'EVERY_DISPLAY'
    every_h_box = 'EVERY_H_BOX'
    every_v_box = 'EVERY_V_BOX'
    every_job = 'EVERY_JOB'
    every_cr = 'EVERY_CR'
    err_help = 'ERR_HELP'


param_to_instr: Dict[Parameters, Instructions] = {
    Parameters.pre_tolerance: Instructions.integer_parameter,
    Parameters.tolerance: Instructions.integer_parameter,
    Parameters.h_badness: Instructions.integer_parameter,
    Parameters.v_badness: Instructions.integer_parameter,
    Parameters.line_penalty: Instructions.integer_parameter,
    Parameters.hyphen_penalty: Instructions.integer_parameter,
    Parameters.ex_hyphen_penalty: Instructions.integer_parameter,
    Parameters.bin_op_penalty: Instructions.integer_parameter,
    Parameters.rel_penalty: Instructions.integer_parameter,
    Parameters.club_penalty: Instructions.integer_parameter,
    Parameters.widow_penalty: Instructions.integer_parameter,
    Parameters.display_widow_penalty: Instructions.integer_parameter,
    Parameters.broken_penalty: Instructions.integer_parameter,
    Parameters.pre_display_penalty: Instructions.integer_parameter,
    Parameters.post_display_penalty: Instructions.integer_parameter,
    Parameters.inter_line_penalty: Instructions.integer_parameter,
    Parameters.floating_penalty: Instructions.integer_parameter,
    Parameters.output_penalty: Instructions.integer_parameter,
    Parameters.double_hyphen_demerits: Instructions.integer_parameter,
    Parameters.final_hyphen_demerits: Instructions.integer_parameter,
    Parameters.adj_demerits: Instructions.integer_parameter,
    Parameters.looseness: Instructions.integer_parameter,
    Parameters.pausing: Instructions.integer_parameter,
    Parameters.holding_inserts: Instructions.integer_parameter,
    Parameters.tracing_on_line: Instructions.integer_parameter,
    Parameters.tracing_macros: Instructions.integer_parameter,
    Parameters.tracing_stats: Instructions.integer_parameter,
    Parameters.tracing_paragraphs: Instructions.integer_parameter,
    Parameters.tracing_pages: Instructions.integer_parameter,
    Parameters.tracing_output: Instructions.integer_parameter,
    Parameters.tracing_lostchars: Instructions.integer_parameter,
    Parameters.tracing_commands: Instructions.integer_parameter,
    Parameters.tracing_restores: Instructions.integer_parameter,
    Parameters.language: Instructions.integer_parameter,
    Parameters.uc_hyph: Instructions.integer_parameter,
    Parameters.left_hyphen_min: Instructions.integer_parameter,
    Parameters.right_hyphen_min: Instructions.integer_parameter,
    Parameters.global_defs: Instructions.integer_parameter,
    Parameters.max_dead_cycles: Instructions.integer_parameter,
    Parameters.hang_after: Instructions.integer_parameter,
    Parameters.fam: Instructions.integer_parameter,
    Parameters.mag: Instructions.integer_parameter,
    Parameters.escape_char: Instructions.integer_parameter,
    Parameters.default_hyphen_char: Instructions.integer_parameter,
    Parameters.default_skew_char: Instructions.integer_parameter,
    Parameters.end_line_char: Instructions.integer_parameter,
    Parameters.new_line_char: Instructions.integer_parameter,
    Parameters.delimiter_factor: Instructions.integer_parameter,
    # THESE TIME ONES WILL BE SET IN GET_INITIAL_PARAMETERS.
    Parameters.time: Instructions.integer_parameter,
    Parameters.day: Instructions.integer_parameter,
    Parameters.month: Instructions.integer_parameter,
    Parameters.year: Instructions.integer_parameter,
    Parameters.show_box_breadth: Instructions.integer_parameter,
    Parameters.show_box_depth: Instructions.integer_parameter,
    Parameters.error_context_lines: Instructions.integer_parameter,
    Parameters.h_fuzz: Instructions.dimen_parameter,
    Parameters.v_fuzz: Instructions.dimen_parameter,
    Parameters.over_full_rule: Instructions.dimen_parameter,
    Parameters.h_size: Instructions.dimen_parameter,
    Parameters.v_size: Instructions.dimen_parameter,
    Parameters.max_depth: Instructions.dimen_parameter,
    Parameters.split_max_depth: Instructions.dimen_parameter,
    Parameters.box_max_depth: Instructions.dimen_parameter,
    Parameters.line_skip_limit: Instructions.dimen_parameter,
    Parameters.delimiter_short_fall: Instructions.dimen_parameter,
    Parameters.null_delimiter_space: Instructions.dimen_parameter,
    Parameters.script_space: Instructions.dimen_parameter,
    Parameters.math_surround: Instructions.dimen_parameter,
    Parameters.pre_display_size: Instructions.dimen_parameter,
    Parameters.display_width: Instructions.dimen_parameter,
    Parameters.display_indent: Instructions.dimen_parameter,
    Parameters.par_indent: Instructions.dimen_parameter,
    Parameters.hang_indent: Instructions.dimen_parameter,
    Parameters.h_offset: Instructions.dimen_parameter,
    Parameters.v_offset: Instructions.dimen_parameter,
    Parameters.base_line_skip: Instructions.glue_parameter,
    Parameters.line_skip: Instructions.glue_parameter,
    Parameters.par_skip: Instructions.glue_parameter,
    Parameters.above_display_skip: Instructions.glue_parameter,
    Parameters.above_display_short_skip: Instructions.glue_parameter,
    Parameters.below_display_skip: Instructions.glue_parameter,
    Parameters.below_display_short_skip: Instructions.glue_parameter,
    Parameters.left_skip: Instructions.glue_parameter,
    Parameters.right_skip: Instructions.glue_parameter,
    Parameters.top_skip: Instructions.glue_parameter,
    Parameters.split_top_skip: Instructions.glue_parameter,
    Parameters.tab_skip: Instructions.glue_parameter,
    Parameters.space_skip: Instructions.glue_parameter,
    Parameters.x_space_skip: Instructions.glue_parameter,
    Parameters.par_fill_skip: Instructions.glue_parameter,
    Parameters.thin_mu_skip: Instructions.mu_glue_parameter,
    Parameters.med_mu_skip: Instructions.mu_glue_parameter,
    Parameters.thick_mu_skip: Instructions.mu_glue_parameter,
    Parameters.output: Instructions.token_parameter,
    Parameters.every_par: Instructions.token_parameter,
    Parameters.every_math: Instructions.token_parameter,
    Parameters.every_display: Instructions.token_parameter,
    Parameters.every_h_box: Instructions.token_parameter,
    Parameters.every_v_box: Instructions.token_parameter,
    Parameters.every_job: Instructions.token_parameter,
    Parameters.every_cr: Instructions.token_parameter,
    Parameters.err_help: Instructions.token_parameter,
}

param_to_type: Dict[Parameters, str] = {
    p: instr.value
    for p, instr in param_to_instr.items()
}

param_instrs: Tuple[Instructions, ...] = (
    Instructions.integer_parameter,
    Instructions.dimen_parameter,
    Instructions.glue_parameter,
    Instructions.mu_glue_parameter,
    Instructions.token_parameter,
)

parameter_instr_types: Tuple[str, ...] = instructions_to_types(param_instrs)


def param_instr_subset(instr: Instructions) -> Iterable[Parameters]:
    return (p for p in Parameters if param_to_instr[p] == instr)


def is_parameter_type(type_: str) -> bool:
    return type_ in parameter_instr_types
