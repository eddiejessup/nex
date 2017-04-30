from .primitive_control_sequences import (short_hand_def_to_def_token_map,
                                          font_def_token_type)


unexpanded_many_char_cs_type = 'UNEXPANDED_MANY_CHAR_CONTROL_SEQUENCE'
unexpanded_one_char_cs_type = 'UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE'
unexpanded_cs_types = (unexpanded_many_char_cs_type,
                       unexpanded_one_char_cs_type)
let_target_type = 'LET_TARGET'


composite_terminal_token_types = (
    'BALANCED_TEXT_AND_RIGHT_BRACE',
    'PARAMETER_TEXT',
    'HORIZONTAL_MODE_MATERIAL_AND_RIGHT_BRACE',
    'VERTICAL_MODE_MATERIAL_AND_RIGHT_BRACE',
)


def_token_types = (tuple(short_hand_def_to_def_token_map.values()) +
                   (font_def_token_type,))
