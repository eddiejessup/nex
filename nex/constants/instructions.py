"""
Define the list of possible internal instructions that TeX might handle. These
might constitute full commands by themselves (such as 'end' to end the
document), or they might need to be composed with other pieces to form
commands, such as 'input', which requires a file-name as an argument.
"""
from enum import Enum


class Instructions(Enum):
    # Mode-independent commands.
    relax = 'RELAX'
    right_brace = 'RIGHT_BRACE'
    begin_group = 'BEGIN_GROUP'
    end_group = 'END_GROUP'
    show_token = 'SHOW_TOKEN'
    show_box = 'SHOW_BOX'
    show_lists = 'SHOW_LISTS'
    show_the = 'SHOW_THE'
    ship_out = 'SHIP_OUT'
    ignore_spaces = 'IGNORE_SPACES'
    after_assignment = 'AFTER_ASSIGNMENT'
    after_group = 'AFTER_GROUP'
    upper_case = 'UPPER_CASE'
    lower_case = 'LOWER_CASE'
    message = 'MESSAGE'
    error_message = 'ERROR_MESSAGE'
    immediate = 'IMMEDIATE'
    open_input = 'OPEN_INPUT'
    close_input = 'CLOSE_INPUT'
    open_output = 'OPEN_OUTPUT'
    close_output = 'CLOSE_OUTPUT'
    # 'read' doesn't strictly appear in the list, but it conceptually belongs
    # here.
    read = 'READ'
    write = 'WRITE'

    # Almost mode-independent commands, that just deal with different types of
    # lists.
    special = 'SPECIAL'
    add_penalty = 'ADD_PENALTY'
    kern = 'KERN'
    math_kern = 'MATH_KERN'
    un_penalty = 'UN_PENALTY'
    un_kern = 'UN_KERN'
    un_glue = 'UN_GLUE'
    mark = 'MARK'
    insert = 'INSERT'
    v_adjust = 'V_ADJUST'

    # These are a bit cheaty to put in mode-independent section.
    # They are described separately in each mode in the TeXBook.
    leaders = 'LEADERS'
    centered_leaders = 'CENTERED_LEADERS'
    expanded_leaders = 'EXPANDED_LEADERS'
    space = 'SPACE'
    #   Box invocations.
    #     Box register calls.
    #       This one deletes the register contents when called.
    box = 'BOX'
    #       This one does not.
    copy = 'COPY'
    #     Remove and return (pop) the most recent h- or v-box, if any.
    last_box = 'LAST_BOX'
    #     Make a vbox by splitting off a certain amount of material from a box
    #     register.
    v_split = 'V_SPLIT'
    #     Explicit boxes.
    h_box = 'H_BOX'
    v_box = 'V_BOX'
    #       Like 'vbox' but its baseline is that of the top box inside,
    #       rather than the bottom box inside.
    v_top = 'V_TOP'
    #   End box invocations.
    indent = 'INDENT'
    no_indent = 'NO_INDENT'
    par = 'PAR'
    left_brace = 'LEFT_BRACE'

    # Vertical commands.
    #   Glue.
    v_skip = 'V_SKIP'
    v_fil = 'V_FIL'
    v_fill = 'V_FILL'
    v_stretch_or_shrink = 'V_STRETCH_OR_SHRINK'
    v_fil_neg = 'V_FIL_NEG'
    #   End glue.
    move_left = 'MOVE_LEFT'
    move_right = 'MOVE_RIGHT'
    un_v_box = 'UN_V_BOX'
    un_v_copy = 'UN_V_COPY'
    h_rule = 'H_RULE'
    h_align = 'H_ALIGN'
    end = 'END'
    dump = 'DUMP'

    # Horizontal commands.
    #   Glue.
    h_skip = 'H_SKIP'
    h_fil = 'H_FIL'
    h_fill = 'H_FILL'
    h_stretch_or_shrink = 'H_STRETCH_OR_SHRINK'
    h_fil_neg = 'H_FIL_NEG'
    #   End glue.
    control_space = 'CONTROL_SPACE'
    raise_box = 'RAISE_BOX'
    lower_box = 'LOWER_BOX'
    un_h_box = 'UN_H_BOX'
    un_h_copy = 'UN_H_COPY'
    v_rule = 'V_RULE'
    v_align = 'V_ALIGN'
    char = 'CHAR'
    accent = 'ACCENT'
    italic_correction = 'ITALIC_CORRECTION'
    discretionary = 'DISCRETIONARY'
    discretionary_hyphen = 'DISCRETIONARY_HYPHEN'
    math_shift = 'MATH_SHIFT'

    # Assignments.
    #   Variables.
    #     Registers.
    #       Set box is usually slightly different to the rest.
    set_box = 'SET_BOX'
    count = 'COUNT'
    dimen = 'DIMEN'
    skip = 'SKIP'
    mu_skip = 'MU_SKIP'
    toks = 'TOKS'
    #     Short-hand definition tokens (produced internally).
    char_def_token = 'CHAR_DEF_TOKEN'
    math_char_def_token = 'MATH_CHAR_DEF_TOKEN'
    count_def_token = 'COUNT_DEF_TOKEN'
    dimen_def_token = 'DIMEN_DEF_TOKEN'
    skip_def_token = 'SKIP_DEF_TOKEN'
    mu_skip_def_token = 'MU_SKIP_DEF_TOKEN'
    toks_def_token = 'TOKS_DEF_TOKEN'
    #       Not defined by a short-hand def, but acts similarly.
    font_def_token = 'FONT_DEF_TOKEN'
    #     Box register dimensions.
    box_dimen_height = 'BOX_DIMEN_HEIGHT'
    box_dimen_width = 'BOX_DIMEN_WIDTH'
    box_dimen_depth = 'BOX_DIMEN_DEPTH'
    #     Parameters.
    integer_parameter = 'INTEGER_PARAMETER'
    dimen_parameter = 'DIMEN_PARAMETER'
    glue_parameter = 'GLUE_PARAMETER'
    mu_glue_parameter = 'MU_GLUE_PARAMETER'
    token_parameter = 'TOKEN_PARAMETER'
    #     Specials.
    special_integer = 'SPECIAL_INTEGER'
    special_dimen = 'SPECIAL_DIMEN'
    #   Arithmetic.
    advance = 'ADVANCE'
    multiply = 'MULTIPLY'
    divide = 'DIVIDE'
    #   Codes.
    cat_code = 'CAT_CODE'
    math_code = 'MATH_CODE'
    upper_case_code = 'UPPER_CASE_CODE'
    lower_case_code = 'LOWER_CASE_CODE'
    space_factor_code = 'SPACE_FACTOR_CODE'
    delimiter_code = 'DELIMITER_CODE'
    # Let assignments.
    let = 'LET'
    future_let = 'FUTURE_LET'
    #   Font ranges.
    text_font = 'TEXT_FONT'
    script_font = 'SCRIPT_FONT'
    script_script_font = 'SCRIPT_SCRIPT_FONT'
    # Shape.
    par_shape = 'PAR_SHAPE'
    #   Font property assignments.
    font_dimen = 'FONT_DIMEN'
    hyphen_char = 'HYPHEN_CHAR'
    skew_char = 'SKEW_CHAR'
    #   Hyphenation.
    hyphenation = 'HYPHENATION'
    patterns = 'PATTERNS'
    #   Interaction mode.
    error_stop_mode = 'ERROR_STOP_MODE'
    scroll_mode = 'SCROLL_MODE'
    non_stop_mode = 'NON_STOP_MODE'
    batch_mode = 'BATCH_MODE'
    #   Macro definitions.
    def_ = 'DEF'
    g_def = 'G_DEF'
    e_def = 'E_DEF'
    x_def = 'X_DEF'
    #   Short-hand macro definitions.
    #     Short-hand character definitions.
    char_def = 'CHAR_DEF'
    math_char_def = 'MATH_CHAR_DEF'
    #     Short-hand register definitions.
    count_def = 'COUNT_DEF'
    dimen_def = 'DIMEN_DEF'
    skip_def = 'SKIP_DEF'
    mu_skip_def = 'MU_SKIP_DEF'
    toks_def = 'TOKS_DEF'
    #   Macro modifiers.
    global_mod = 'GLOBAL_MOD'
    long_mod = 'LONG_MOD'
    outer_mod = 'OUTER_MOD'
    #   Font assignment.
    font = 'FONT'

    # Conditions
    # \ifnum <number_1> <relation> <number_2>
    # Compare two integers. The <relation> must be "<_12", "=_12" or ">_12".
    if_num = 'IF_NUM'
    # \ifdim <dimen_1> <relation> <dimen_2>
    # Compare two dimensions. Otherwise, same as above.
    if_dimen = 'IF_DIMEN'
    if_odd = 'IF_ODD'
    if_v_mode = 'IF_V_MODE'
    if_h_mode = 'IF_H_MODE'
    if_m_mode = 'IF_M_MODE'
    if_inner_mode = 'IF_INNER_MODE'
    if_char = 'IF_CHAR'
    if_cat = 'IF_CAT'
    if_token = 'IF_TOKEN'
    if_void = 'IF_VOID'
    if_h_box = 'IF_H_BOX'
    if_v_box = 'IF_V_BOX'
    if_end_of_file = 'IF_END_OF_FILE'
    if_true = 'IF_TRUE'
    if_false = 'IF_FALSE'
    if_case = 'IF_CASE'
    # Condition sub-instructions
    # Can't call it 'else' for Python syntax reasons when I make the enum.
    else_ = 'ELSE'
    end_if = 'END_IF'
    or_ = 'OR'

    # Instructions that are handled before parsing, in the banisher.
    number = 'NUMBER'
    roman_numeral = 'ROMAN_NUMERAL'
    string = 'STRING'
    job_name = 'JOB_NAME'
    font_name = 'FONT_NAME'
    meaning = 'MEANING'
    cs_name = 'CS_NAME'
    end_cs_name = 'END_CS_NAME'
    expand_after = 'EXPAND_AFTER'
    no_expand = 'NO_EXPAND'
    top_mark = 'TOP_MARK'
    first_mark = 'FIRST_MARK'
    bottom_mark = 'BOTTOM_MARK'
    split_first_mark = 'SPLIT_FIRST_MARK'
    split_bottom_mark = 'SPLIT_BOTTOM_MARK'
    input = 'INPUT'
    end_input = 'END_INPUT'
    the = 'THE'

    cr = 'CR'
    undefined = 'UNDEFINED'

    # Types of certain char-cat pairs.
    #   Number-related.
    less_than = 'LESS_THAN'
    greater_than = 'GREATER_THAN'
    equals = 'EQUALS'
    plus_sign = 'PLUS_SIGN'
    minus_sign = 'MINUS_SIGN'
    single_quote = 'SINGLE_QUOTE'
    double_quote = 'DOUBLE_QUOTE'
    backtick = 'BACKTICK'
    point = 'POINT'
    comma = 'COMMA'
    #   Digits.
    zero = 'ZERO'
    one = 'ONE'
    two = 'TWO'
    three = 'THREE'
    four = 'FOUR'
    five = 'FIVE'
    six = 'SIX'
    seven = 'SEVEN'
    eight = 'EIGHT'
    nine = 'NINE'
    #   Hex letters.
    a = 'A'
    b = 'B'
    c = 'C'
    d = 'D'
    e = 'E'
    f = 'F'
    #   Letters.
    non_active_uncased_a = 'NON_ACTIVE_UNCASED_A'
    non_active_uncased_b = 'NON_ACTIVE_UNCASED_B'
    non_active_uncased_c = 'NON_ACTIVE_UNCASED_C'
    non_active_uncased_d = 'NON_ACTIVE_UNCASED_D'
    non_active_uncased_e = 'NON_ACTIVE_UNCASED_E'
    non_active_uncased_f = 'NON_ACTIVE_UNCASED_F'
    non_active_uncased_g = 'NON_ACTIVE_UNCASED_G'
    non_active_uncased_h = 'NON_ACTIVE_UNCASED_H'
    non_active_uncased_i = 'NON_ACTIVE_UNCASED_I'
    non_active_uncased_j = 'NON_ACTIVE_UNCASED_J'
    non_active_uncased_k = 'NON_ACTIVE_UNCASED_K'
    non_active_uncased_l = 'NON_ACTIVE_UNCASED_L'
    non_active_uncased_m = 'NON_ACTIVE_UNCASED_M'
    non_active_uncased_n = 'NON_ACTIVE_UNCASED_N'
    non_active_uncased_o = 'NON_ACTIVE_UNCASED_O'
    non_active_uncased_p = 'NON_ACTIVE_UNCASED_P'
    non_active_uncased_q = 'NON_ACTIVE_UNCASED_Q'
    non_active_uncased_r = 'NON_ACTIVE_UNCASED_R'
    non_active_uncased_s = 'NON_ACTIVE_UNCASED_S'
    non_active_uncased_t = 'NON_ACTIVE_UNCASED_T'
    non_active_uncased_u = 'NON_ACTIVE_UNCASED_U'
    non_active_uncased_v = 'NON_ACTIVE_UNCASED_V'
    non_active_uncased_w = 'NON_ACTIVE_UNCASED_W'
    non_active_uncased_x = 'NON_ACTIVE_UNCASED_X'
    non_active_uncased_y = 'NON_ACTIVE_UNCASED_Y'
    non_active_uncased_z = 'NON_ACTIVE_UNCASED_Z'
    #   Weird categories.
    active_character = 'ACTIVE_CHARACTER'
    parameter = 'PARAMETER'
    align_tab = 'ALIGN_TAB'
    superscript = 'SUPERSCRIPT'
    subscript = 'SUBSCRIPT'

    # Strange internal instructions that are produced by the banisher.
    macro = 'MACRO'
    arbitrary_token = 'ARBITRARY_TOKEN'
    #   Control sequence names produced as part of a definition and such.
    unexpanded_control_symbol = 'UNEXPANDED_CONTROL_SYMBOL'
    unexpanded_control_word = 'UNEXPANDED_CONTROL_WORD'
    #   Parameter placeholder in macro definitions.
    delimited_param = 'DELIMITED_PARAM'
    undelimited_param = 'UNDELIMITED_PARAM'
    param_number = 'PARAM_NUMBER'
    parameter_text = 'PARAMETER_TEXT'
    balanced_text_and_right_brace = 'BALANCED_TEXT_AND_RIGHT_BRACE'
    horizontal_mode_material_and_right_brace = 'HORIZONTAL_MODE_MATERIAL_AND_RIGHT_BRACE'
    vertical_mode_material_and_right_brace = 'VERTICAL_MODE_MATERIAL_AND_RIGHT_BRACE'
    misc_char_cat_pair = 'MISC_CHAR_CAT_PAIR'


unexpanded_cs_instructions = (
    Instructions.unexpanded_control_symbol,
    Instructions.unexpanded_control_word,
)

message_instructions = (
    Instructions.message,
    Instructions.error_message,
    Instructions.write,
)

hyphenation_instructions = (
    Instructions.hyphenation,
    Instructions.patterns,
)

h_add_glue_instructions = (
    Instructions.h_skip,
    Instructions.h_fil,
    Instructions.h_fill,
    Instructions.h_stretch_or_shrink,
    Instructions.h_fil_neg,
)


v_add_glue_instructions = (
    Instructions.v_skip,
    Instructions.v_fil,
    Instructions.v_fill,
    Instructions.v_stretch_or_shrink,
    Instructions.v_fil_neg,
)

explicit_box_instructions = (
    Instructions.h_box,
    Instructions.v_box,
    Instructions.v_top,
)

register_instructions = (
    Instructions.count,
    Instructions.dimen,
    Instructions.skip,
    Instructions.mu_skip,
    Instructions.toks,
)

short_hand_def_instructions = (
    Instructions.char_def,
    Instructions.math_char_def,
    # Short-hand register definitions.
    Instructions.count_def,
    Instructions.dimen_def,
    Instructions.skip_def,
    Instructions.mu_skip_def,
    Instructions.toks_def,
)

def_instructions = (
    Instructions.def_,
    Instructions.g_def,
    Instructions.e_def,
    Instructions.x_def,
)

if_instructions = (
    Instructions.if_num,
    Instructions.if_dimen,
    Instructions.if_odd,
    Instructions.if_v_mode,
    Instructions.if_h_mode,
    Instructions.if_m_mode,
    Instructions.if_inner_mode,
    Instructions.if_char,
    Instructions.if_cat,
    Instructions.if_token,
    Instructions.if_void,
    Instructions.if_h_box,
    Instructions.if_v_box,
    Instructions.if_end_of_file,
    Instructions.if_true,
    Instructions.if_false,
    Instructions.if_case,
)

mark_instructions = (
    Instructions.top_mark,
    Instructions.first_mark,
    Instructions.bottom_mark,
    Instructions.split_first_mark,
    Instructions.split_bottom_mark,
)
