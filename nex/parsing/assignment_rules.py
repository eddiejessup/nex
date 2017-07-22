from ..tokens import BuiltToken
from ..fonts import FontRange

from .utils import make_literal_token, get_literal_production_rule


def add_assignment_rules(pg):
    @pg.production('assignment : macro_assignment')
    @pg.production('assignment : non_macro_assignment')
    def assignment(p):
        return BuiltToken(type_='assignment',
                          value=p[0],
                          position_like=p)
        return p[0]

    # Start of 'macro assignment', an assignment.

    @pg.production('macro_assignment : prefix macro_assignment')
    def macro_assignment_prefix(p):
        p[1].value['prefixes'].add(p[0])
        return p[1]

    @pg.production('prefix : GLOBAL_MOD')
    @pg.production('prefix : LONG_MOD')
    @pg.production('prefix : OUTER_MOD')
    def prefix(p):
        return p[0].type

    @pg.production('macro_assignment : definition')
    def macro_assignment(p):
        macro_token = BuiltToken(type_='macro_assignment',
                                 value=dict(prefixes=set(), **p[0].value),
                                 position_like=p)
        return macro_token

    @pg.production('definition : def control_sequence definition_text')
    def definition(p):
        return BuiltToken(type_='definition',
                          value=dict(def_type=p[0],
                                     name=p[1].value['name'],
                                     **p[2].value),
                          position_like=p)

    @pg.production('def : DEF')
    @pg.production('def : G_DEF')
    @pg.production('def : E_DEF')
    @pg.production('def : X_DEF')
    def def_(p):
        return p[0]

    @pg.production('definition_text : PARAMETER_TEXT LEFT_BRACE BALANCED_TEXT_AND_RIGHT_BRACE')
    def definition_text(p):
        def_text_token = BuiltToken(type_='definition_text',
                                    value={'parameter_text': p[0].value,
                                           'replacement_text': p[2].value},
                                    position_like=p)
        return def_text_token

    # End of 'macro assignment', an assignment.

    # Start of 'non-macro assignment', an assignment.
    # (This is basically just 'simple assignment's, with an optional \global
    # prefix.)

    @pg.production('non_macro_assignment : GLOBAL_MOD non_macro_assignment')
    def non_macro_assignment_global(p):
        tok = p[1]
        tok.value['global'] = True
        return tok

    @pg.production('non_macro_assignment : simple_assignment')
    def non_macro_assignment(p):
        tok = p[0]
        # A simple assignment is local (non-global) unless indicated otherwise.
        # The only way to be already global is if the simple assigment is of
        # type 'global assignment'. In this case, we should not touch the
        # value.
        if 'global' not in tok.value:
            tok.value['global'] = False
        return tok

    @pg.production('simple_assignment : variable_assignment')
    @pg.production('simple_assignment : arithmetic')
    @pg.production('simple_assignment : code_assignment')
    @pg.production('simple_assignment : let_assignment')
    @pg.production('simple_assignment : short_hand_definition')
    @pg.production('simple_assignment : font_selection')
    @pg.production('simple_assignment : family_assignment')
    @pg.production('simple_assignment : set_box_assignment')
    @pg.production('simple_assignment : font_definition')
    @pg.production('simple_assignment : global_assignment')
    def simple_assignment(p):
        return p[0]

    # 'font selection', a simple assignment.

    @pg.production('font_selection : FONT_DEF_TOKEN')
    def simple_assignment_font_selection(p):
        return BuiltToken(type_='font_selection',
                          value={'font_id': p[0].value},
                          position_like=p)

    @pg.production('variable_assignment : partial_variable_assignment')
    def variable_assignment(p):
        variable, value = p[0]
        return BuiltToken(type_='variable_assignment',
                          value={'variable': variable, 'value': value},
                          position_like=p[0])

    @pg.production('partial_variable_assignment : token_variable equals general_text')
    @pg.production('partial_variable_assignment : token_variable equals filler token_variable')
    def partial_variable_assignment_token_variable(p):
        value = BuiltToken(type_='token_list', value=p[-1],
                           position_like=p)
        return [p[0], value]

    @pg.production('partial_variable_assignment : mu_glue_variable equals mu_glue')
    @pg.production('partial_variable_assignment : glue_variable equals glue')
    @pg.production('partial_variable_assignment : dimen_variable equals dimen')
    @pg.production('partial_variable_assignment : integer_variable equals number')
    def partial_variable_assignment_quantity(p):
        return [p[0], p[2]]

    # End of 'variable assignment', a simple assignment.

    # Start of 'arithmetic', a simple assignment.

    @pg.production('arithmetic : ADVANCE integer_variable optional_by number')
    def arithmetic_integer_variable(p):
        # TODO: Allow arithmetic on parameters.
        # TODO: Allow multiply and divide operations.
        # TODO: Allow arithmetic on dimen, glue and muglue.
        return BuiltToken(type_='advance',
                          value={'variable': p[1], 'value': p[3]},
                          position_like=p)

    @pg.production('optional_by : by')
    @pg.production('optional_by : optional_spaces')
    def optional_by(p):
        return None

    @pg.production(get_literal_production_rule('by'))
    def literal_by(p):
        return make_literal_token(p)

    # End of 'arithmetic', a simple assignment.

    # Start of 'code assignment', a simple assignment.

    @pg.production('code_assignment : code_variable equals number')
    def code_assignment(p):
        return BuiltToken(type_='code_assignment',
                          value={
                            'variable': p[0],
                            'code': p[2],
                          },
                          position_like=p)

    @pg.production('code_variable : code_name number')
    def code_variable(p):
        return BuiltToken(type_=p[0].type,
                          value=p[1],
                          position_like=p)

    @pg.production('code_name : CAT_CODE')
    @pg.production('code_name : MATH_CODE')
    @pg.production('code_name : UPPER_CASE_CODE')
    @pg.production('code_name : LOWER_CASE_CODE')
    @pg.production('code_name : SPACE_FACTOR_CODE')
    @pg.production('code_name : DELIMITER_CODE')
    def code_name(p):
        return p[0]

    # End of 'code assignment', a simple assignment.

    # Start of 'let assignment', a simple assignment.

    @pg.production('let_assignment : LET control_sequence equals one_optional_space ARBITRARY_TOKEN')
    def let_assignment_control_sequence(p):
        target_token = p[4].value
        new_name = p[1].value['name']
        return BuiltToken(type_='let_assignment',
                          value={
                            'name': new_name,
                            'target_token': target_token
                          },
                          position_like=p)

    # End of 'let assignment', a simple assignment.

    # Start of 'short-hand definition', a simple assignment.

    @pg.production('short_hand_definition : short_hand_def control_sequence equals number')
    def short_hand_definition(p):
        code = p[3]
        def_type = p[0].type
        control_sequence_name = p[1].value['name']
        return BuiltToken(type_='short_hand_definition',
                          value={
                            'code': code,
                            'def_type': def_type,
                            'control_sequence_name': control_sequence_name
                          },
                          position_like=p)

    @pg.production('short_hand_def : CHAR_DEF')
    @pg.production('short_hand_def : MATH_CHAR_DEF')
    @pg.production('short_hand_def : COUNT_DEF')
    @pg.production('short_hand_def : DIMEN_DEF')
    @pg.production('short_hand_def : SKIP_DEF')
    @pg.production('short_hand_def : MU_SKIP_DEF')
    @pg.production('short_hand_def : TOKS_DEF')
    def short_hand_def(p):
        return p[0]

    # End of 'short-hand definition', a simple assignment.

    # Start of 'family assignment', a simple assignment.

    @pg.production('family_assignment : family_member equals font')
    def family_assignment(p):
        # TODO: will this work for productions of font other than
        # FONT_DEF_TOKEN?
        font_id = p[2].value
        font_range = p[0].type
        family_nr = p[0].value
        return BuiltToken(type_='family_assignment',
                          value={'family_nr': family_nr,
                                 'font_range': font_range,
                                 'font_id': font_id},
                          position_like=p)

    @pg.production('family_member : font_range number')
    def family_member(p):
        return BuiltToken(type_=p[0].value, value=p[1],
                          position_like=p)

    @pg.production('font_range : TEXT_FONT')
    @pg.production('font_range : SCRIPT_FONT')
    @pg.production('font_range : SCRIPT_SCRIPT_FONT')
    def font_range(p):
        # TODO: Doing too much in the parser.
        return BuiltToken(type_='font_range',
                          value=FontRange(p[0].type),
                          position_like=p)

    # End of 'family assignment', a simple assignment.

    # Start of 'set box assignment', a simple assignment.

    @pg.production('set_box_assignment : SET_BOX number equals filler box')
    def set_box_assignment(p):
        return BuiltToken(type_=p[0].type,
                          value={'nr': p[1], 'box': p[4]},
                          position_like=p)

    @pg.production('box : box_explicit')
    @pg.production('box : box_register')
    @pg.production('box : box_v_split')
    @pg.production('box : LAST_BOX')
    def box(p):
        return BuiltToken(type_='box',
                          value=p[0],
                          position_like=p)

    @pg.production('box_explicit : H_BOX box_specification LEFT_BRACE HORIZONTAL_MODE_MATERIAL_AND_RIGHT_BRACE')
    @pg.production('box_explicit : V_BOX box_specification LEFT_BRACE VERTICAL_MODE_MATERIAL_AND_RIGHT_BRACE')
    @pg.production('box_explicit : V_TOP box_specification LEFT_BRACE VERTICAL_MODE_MATERIAL_AND_RIGHT_BRACE')
    def box_explicit(p):
        return BuiltToken(type_='explicit_box',
                          value={
                            'box_type': p[0].type,
                            'specification': p[1],
                            'contents': p[3].value,
                          },
                          position_like=p)

    @pg.production('box_register : BOX number')
    @pg.production('box_register : COPY number')
    def box_from_register(p):
        return BuiltToken(type_='box_register',
                          value={
                            'retrieve_type': p[0].type,
                            'number': p[1],
                          },
                          position_like=p)

    @pg.production('box_v_split : V_SPLIT number to dimen')
    def box_v_split(p):
        return BuiltToken(type_=p[0].type,
                          value={
                            'number': p[1],
                            'dimen': p[3]
                          },
                          position_like=p)

    @pg.production('box_specification : to dimen filler')
    def box_specification_to(p):
        return BuiltToken(type_='to', value=p[1],
                          position_like=p)

    @pg.production('box_specification : spread dimen filler')
    def box_specification_spread(p):
        return BuiltToken(type_='spread', value=p[1],
                          position_like=p)

    @pg.production(get_literal_production_rule('to'))
    @pg.production(get_literal_production_rule('spread'))
    def literal_box_spec(p):
        return make_literal_token(p)

    @pg.production('box_specification : filler')
    def box_specification_empty(p):
        return None

    # End of 'set box assignment', a simple assignment.

    # Start of 'font definition', a simple assignment.

    @pg.production('font_definition : FONT control_sequence equals optional_spaces file_name filler at_clause')
    def font_definition(p):
        control_sequence_name = p[1].value['name']
        return BuiltToken(type_='font_definition',
                          value={
                            'file_name': p[4], 'at_clause': p[6],
                            'control_sequence_name': control_sequence_name
                          },
                          position_like=p)

    @pg.production('control_sequence : UNEXPANDED_CONTROL_WORD')
    @pg.production('control_sequence : UNEXPANDED_CONTROL_SYMBOL')
    def control_sequence(p):
        return p[0]

    @pg.production('control_sequence : ACTIVE_CHARACTER')
    def control_sequence_active(p):
        # We will prefix active characters with @.
        # This really needs changing, but will do for now.
        v = p[0]
        v.value['name'] = v.value['char']
        return v

    @pg.production('at_clause : at dimen')
    def at_clause_dimen(p):
        return BuiltToken(type_='at_dimen', value=p[1],
                          position_like=p)

    @pg.production('at_clause : scaled number')
    def at_clause_scaled(p):
        return BuiltToken(type_='scaled_number', value=p[1],
                          position_like=p)

    @pg.production(get_literal_production_rule('at'))
    @pg.production(get_literal_production_rule('scaled'))
    def literal_at_clause(p):
        return make_literal_token(p)

    @pg.production('at_clause : optional_spaces')
    def at_clause_empty(p):
        return None

    # End of 'font definition', a simple assignment.

    # Start of 'global assignment', a simple assignment.

    @pg.production('global_assignment : font_assignment')
    @pg.production('global_assignment : hyphenation_assignment')
    # @pg.production('global_assignment : box_size_assignment')
    # @pg.production('global_assignment : interaction_mode_assignment')
    @pg.production('global_assignment : intimate_assignment')
    def global_assignment(p):
        return p[0]

    @pg.production('font_assignment : dimen_font_variable equals dimen')
    @pg.production('font_assignment : integer_font_variable equals number')
    def font_assignment(p):
        return BuiltToken(type_=p[0].type,
                          value={
                            'variable': p[0],
                            'value': p[2],
                          },
                          position_like=p)

    @pg.production('intimate_assignment : SPECIAL_INTEGER equals number')
    @pg.production('intimate_assignment : SPECIAL_DIMEN equals dimen')
    def intimate_assignment(p):
        return BuiltToken(type_='intimate_assignment',
                          value={
                            'variable': p[0],
                            'value': p[2],
                          },
                          position_like=p)

    @pg.production('integer_font_variable : SKEW_CHAR font')
    @pg.production('integer_font_variable : HYPHEN_CHAR font')
    def integer_font_variable(p):
        return BuiltToken(type_=p[0].type,
                          value={
                            'font': p[1],
                          },
                          position_like=p)

    @pg.production('dimen_font_variable : FONT_DIMEN number font')
    def dimen_font_variable(p):
        return BuiltToken(type_=p[0].type,
                          value={
                            'dimen_number': p[1],
                            'font': p[2],
                          },
                          position_like=p)

    @pg.production('font : FONT_DEF_TOKEN')
    @pg.production('font : family_member')
    @pg.production('font : FONT')
    def font(p):
        return BuiltToken(type_='font', value=p[0])

    @pg.production('hyphenation_assignment : HYPHENATION general_text')
    @pg.production('hyphenation_assignment : PATTERNS general_text')
    def hyphenation_assignment(p):
        return BuiltToken(type_=p[0].type, value={'content': p[1]},
                          position_like=p)

    @pg.production('general_text : filler LEFT_BRACE BALANCED_TEXT_AND_RIGHT_BRACE')
    def general_text(p):
        return BuiltToken(type_='general_text', value=p[2].value,
                          position_like=p)

    @pg.production('filler : optional_spaces')
    @pg.production('filler : filler RELAX optional_spaces')
    def filler(p):
        return None

    # End of 'global assignment', a simple assignment.

    # End of 'simple assignment', an assignment.
