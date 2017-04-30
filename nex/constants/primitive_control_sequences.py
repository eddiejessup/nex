terminal_primitive_control_sequences_map = {
    'catcode': 'CAT_CODE',
    'mathcode': 'MATH_CODE',
    'uccode': 'UPPER_CASE_CODE',
    'lccode': 'LOWER_CASE_CODE',
    'sfcode': 'SPACE_FACTOR_CODE',
    'delcode': 'DELIMITER_CODE',

    'let': 'LET',

    'advance': 'ADVANCE',

    'par': 'PAR',
    'relax': 'RELAX',
    'immediate': 'IMMEDIATE',

    'font': 'FONT',

    # Font assignment things.
    'skewchar': 'SKEW_CHAR',
    'hyphenchar': 'HYPHEN_CHAR',
    'fontdimen': 'FONT_DIMEN',

    # Font ranges.
    'textfont': 'TEXT_FONT',
    'scriptfont': 'SCRIPT_FONT',
    'scriptscriptfont': 'SCRIPT_SCRIPT_FONT',

    'undefined': 'UNDEFINED',

    # Macro modifiers.
    'global': 'GLOBAL',
    'long': 'LONG',
    'outer': 'OUTER',

    # Box related things.

    # Box register assignment.
    'setbox': 'SET_BOX',
    # Box register calls.
    # This one deletes the register contents when called.
    'box': 'BOX',
    # This one does not.
    'copy': 'COPY',

    'unhbox': 'UN_H_BOX',
    'unhcopy': 'UN_H_COPY',
    'unvbox': 'UN_V_BOX',
    'unvcopy': 'UN_V_COPY',

    # Remove and return (pop) the most recent h- or v-box, if any.
    'lastbox': 'LAST_BOX',
    # Make a vbox by splitting off a certain amount of material from a box
    # register.
    'vsplit': 'V_SPLIT',

    'ht': 'BOX_DIMEN_HEIGHT',
    'wd': 'BOX_DIMEN_WIDTH',
    'dp': 'BOX_DIMEN_DEPTH',

    'kern': 'KERN',
    'mkern': 'MATH_KERN',

    'vrule': 'V_RULE',
    'hrule': 'H_RULE',

    'input': 'INPUT',

    'end': 'END',

    'char': 'CHAR',
    'indent': 'INDENT',
}

message_map = {
    'message': 'MESSAGE',
    'errmessage': 'ERROR_MESSAGE',
    'write': 'WRITE',
}
terminal_primitive_control_sequences_map.update(message_map)

hyphenation_map = {
    'hyphenation': 'HYPHENATION',
    'patterns': 'PATTERNS',
}
terminal_primitive_control_sequences_map.update(hyphenation_map)

_add_glue_stems = {
    'skip': 'SKIP',
    'fil': 'FIL',
    'fill': 'FILL',
    'ss': 'STRETCH_OR_SHRINK',
    'filneg': 'FIL_NEG',
}


def get_add_glue_map_for_direction(d):
    return {'{}{}'.format(d, cs_stem): '{}_{}'.format(d.upper(), type_stem)
            for cs_stem, type_stem in _add_glue_stems.items()}


h_add_glue_tokens = get_add_glue_map_for_direction('h')
v_add_glue_tokens = get_add_glue_map_for_direction('v')
add_glue_tokens = dict(**h_add_glue_tokens, **v_add_glue_tokens)
terminal_primitive_control_sequences_map.update(add_glue_tokens)

explicit_box_map = {
    'hbox': 'H_BOX',
    'vbox': 'V_BOX',
    # Like 'vbox', but its baseline is that of the top box inside,
    # rather than the bottom box inside.
    'vtop': 'V_TOP',
}
terminal_primitive_control_sequences_map.update(explicit_box_map)


register_map = {
    'count': 'COUNT',
    'dimen': 'DIMEN',
    'skip': 'SKIP',
    'muskip': 'MU_SKIP',
    'toks': 'TOKS',
}
terminal_primitive_control_sequences_map.update(register_map)

short_hand_def_map = {
    'chardef': 'CHAR_DEF',
    'mathchardef': 'MATH_CHAR_DEF',
}
short_hand_def_register_map = {
    '{}def'.format(k): '{}_DEF'.format(v) for k, v in register_map.items()
}
short_hand_def_map.update(short_hand_def_register_map)
terminal_primitive_control_sequences_map.update(short_hand_def_map)

def_map = {
    'def': 'DEF',
    'gdef': 'G_DEF',
    'edef': 'E_DEF',
    'xdef': 'X_DEF',
}
terminal_primitive_control_sequences_map.update(def_map)

# Handy map from the type representing a token definition, to the type of the
# token it creates.
short_hand_def_to_def_token_map = {
    v: '{}_TOKEN'.format(v)
    for v in short_hand_def_map.values()
}
font_def_token_type = 'FONT_DEF_TOKEN'


if_map = {
    'ifnum': 'IF_NUM',
    'iftrue': 'IF_TRUE',
    'iffalse': 'IF_FALSE',
    'ifcase': 'IF_CASE',
}
# Complicated, because to a condition_parser they are terminal, but not to any
# other.
terminal_primitive_control_sequences_map.update(if_map)

# Primitive control sequences that call functions that are handled before
# parsing, in the banisher.
non_terminal_primitive_control_sequences_map = {
    'string': 'STRING',
    'csname': 'CS_NAME',
    'endcsname': 'END_CS_NAME',

    'expandafter': 'EXPAND_AFTER',

    'uppercase': 'UPPER_CASE',
    'lowercase': 'LOWER_CASE',

    'cr': 'CR',
}

# Primitive control sequences used in condition parsing.
condition_tokens_map = {
    'else': 'ELSE',
    'fi': 'END_IF',
    'or': 'OR',
}
non_terminal_primitive_control_sequences_map.update(condition_tokens_map)

primitive_control_sequences_map = dict(
    **terminal_primitive_control_sequences_map,
    **non_terminal_primitive_control_sequences_map
)
