from ..constants.instructions import (Instructions,
                                      message_instructions,
                                      hyphenation_instructions,
                                      register_instructions,
                                      h_add_glue_instructions,
                                      v_add_glue_instructions,
                                      short_hand_def_instructions,
                                      def_instructions,
                                      if_instructions
                                      )
from ..tokens import instructions_to_types

base_terminal_instructions = (
    Instructions.relax,
    Instructions.begin_group,
    Instructions.end_group,
    Instructions.show_lists,
    Instructions.ship_out,
    Instructions.un_penalty,
    Instructions.un_kern,
    Instructions.un_glue,
    Instructions.space,
    Instructions.indent,
    Instructions.no_indent,
    Instructions.par,
    Instructions.left_brace,
    Instructions.end,
    Instructions.dump,
    Instructions.control_space,
    Instructions.italic_correction,
    Instructions.discretionary_hyphen,
    Instructions.math_shift,

    Instructions.box_dimen_height,
    Instructions.box_dimen_width,
    Instructions.box_dimen_depth,
    Instructions.less_than,
    Instructions.greater_than,
    Instructions.equals,
    Instructions.plus_sign,
    Instructions.minus_sign,
    Instructions.zero,
    Instructions.one,
    Instructions.two,
    Instructions.three,
    Instructions.four,
    Instructions.five,
    Instructions.six,
    Instructions.seven,
    Instructions.eight,
    Instructions.nine,
    Instructions.single_quote,
    Instructions.double_quote,
    Instructions.backtick,
    Instructions.point,
    Instructions.comma,
    Instructions.a,
    Instructions.b,
    Instructions.c,
    Instructions.d,
    Instructions.e,
    Instructions.f,
    Instructions.misc_char_cat_pair,
    Instructions.integer_parameter,
    Instructions.dimen_parameter,
    Instructions.glue_parameter,
    Instructions.mu_glue_parameter,
    Instructions.token_parameter,
    Instructions.special_integer,
    Instructions.special_dimen,

    Instructions.char_def_token,
    Instructions.math_char_def_token,
    Instructions.count_def_token,
    Instructions.dimen_def_token,
    Instructions.skip_def_token,
    Instructions.mu_skip_def_token,
    Instructions.toks_def_token,
    Instructions.unexpanded_control_symbol,
    Instructions.accent,

    Instructions.cat_code,
    Instructions.math_code,
    Instructions.upper_case_code,
    Instructions.lower_case_code,
    Instructions.space_factor_code,
    Instructions.delimiter_code,
    Instructions.let,
    Instructions.advance,
    Instructions.immediate,
    Instructions.font,
    Instructions.skew_char,
    Instructions.hyphen_char,
    # Instructions.font_dimen,
    Instructions.text_font,
    Instructions.script_font,
    Instructions.script_script_font,
    # Instructions.undefined,
    Instructions.global_mod,
    Instructions.long_mod,
    Instructions.outer_mod,
    Instructions.set_box,
    Instructions.box,
    Instructions.copy,
    Instructions.un_h_box,
    Instructions.un_h_copy,
    Instructions.un_v_box,
    Instructions.un_v_copy,
    # Instructions.last_box,
    # Instructions.v_split,
    # Instructions.box_dimen_height,
    # Instructions.box_dimen_width,
    # Instructions.box_dimen_depth,
    Instructions.kern,
    Instructions.math_kern,
    Instructions.v_rule,
    Instructions.h_rule,
    Instructions.char,
    Instructions.right_brace,
    Instructions.font_def_token,
    Instructions.arbitrary_token,
    Instructions.parameter_text,
    Instructions.balanced_text_and_right_brace,
    Instructions.horizontal_mode_material_and_right_brace,
    Instructions.vertical_mode_material_and_right_brace,
    Instructions.h_box,
    Instructions.v_box,
    Instructions.v_top,
    Instructions.active_character,
    Instructions.unexpanded_control_word,
    Instructions.after_assignment,
    Instructions.after_group,
    Instructions.open_input,
    Instructions.non_active_uncased_a,
    Instructions.non_active_uncased_b,
    Instructions.non_active_uncased_c,
    Instructions.non_active_uncased_d,
    Instructions.non_active_uncased_e,
    Instructions.non_active_uncased_f,
    Instructions.non_active_uncased_g,
    Instructions.non_active_uncased_h,
    Instructions.non_active_uncased_i,
    Instructions.non_active_uncased_j,
    Instructions.non_active_uncased_k,
    Instructions.non_active_uncased_l,
    Instructions.non_active_uncased_m,
    Instructions.non_active_uncased_n,
    Instructions.non_active_uncased_o,
    Instructions.non_active_uncased_p,
    Instructions.non_active_uncased_q,
    Instructions.non_active_uncased_r,
    Instructions.non_active_uncased_s,
    Instructions.non_active_uncased_t,
    Instructions.non_active_uncased_u,
    Instructions.non_active_uncased_v,
    Instructions.non_active_uncased_w,
    Instructions.non_active_uncased_x,
    Instructions.non_active_uncased_y,
    Instructions.non_active_uncased_z,
)
terminal_instructions = (
    base_terminal_instructions
    + register_instructions
    + message_instructions
    + hyphenation_instructions
    + h_add_glue_instructions
    + v_add_glue_instructions
    + short_hand_def_instructions
    + def_instructions
    + if_instructions
)
terminal_types = instructions_to_types(terminal_instructions)
