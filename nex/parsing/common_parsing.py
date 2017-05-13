from string import ascii_lowercase

from ..rply import ParserGenerator

from ..tokens import BuiltToken, instructions_to_types
from ..units import PhysicalUnit
from ..tex_parameters import glue_keys
from ..registers import short_hand_reg_def_token_type_to_reg_type
from ..instructions import (Instructions as I,
                            unexpanded_cs_instructions,
                            register_instructions)

from . import number_parsing
from . import dimen_parsing
from . import utils as pu

common_terminal_instructions = (
    I.box_dimen_height,
    I.box_dimen_width,
    I.box_dimen_depth,
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
    I.unexpanded_control_symbol,
)
# Add ordinary character literals.
char_instructions = tuple(I['non_active_uncased_{}'.format(c.lower())]
                          for c in ascii_lowercase)
common_terminal_instructions += char_instructions
common_terminal_instructions += register_instructions

common_terminal_types = instructions_to_types(common_terminal_instructions)

pg = ParserGenerator(common_terminal_types, cache_id="changeme")


@pg.production('token_variable : token_register')
@pg.production('mu_glue_variable : mu_skip_register')
@pg.production('glue_variable : skip_register')
@pg.production('dimen_variable : dimen_register')
@pg.production('integer_variable : count_register')
def quantity_variable_register(p):
    return p[0]


@pg.production('token_variable : TOKEN_PARAMETER')
@pg.production('mu_glue_variable : MU_GLUE_PARAMETER')
@pg.production('glue_variable : GLUE_PARAMETER')
@pg.production('dimen_variable : DIMEN_PARAMETER')
@pg.production('integer_variable : INTEGER_PARAMETER')
def quantity_variable_parameter(p):
    return p[0]


@pg.production('token_register : TOKS number')
@pg.production('mu_skip_register : MU_SKIP number')
@pg.production('skip_register : SKIP number')
@pg.production('dimen_register : DIMEN number')
@pg.production('count_register : COUNT number')
def quantity_register_explicit(p):
    return BuiltToken(type_=p[0].type, value=p[1], position_like=p)


@pg.production('token_register : TOKS_DEF_TOKEN')
@pg.production('mu_skip_register : MU_SKIP_DEF_TOKEN')
@pg.production('skip_register : SKIP_DEF_TOKEN')
@pg.production('dimen_register : DIMEN_DEF_TOKEN')
@pg.production('count_register : COUNT_DEF_TOKEN')
def register_token(p):
    reg_type = short_hand_reg_def_token_type_to_reg_type[p[0].type]
    number = p[0].value

    # A bit of token wrangling to make the result look the same as, for
    # example, `SKIP number`.

    sign = '+' if number >= 0 else '-'
    sign_tok = BuiltToken(type_='sign', value=sign)

    size_value_tok = BuiltToken(type_='internal', value=abs(number))
    size_tok = BuiltToken(type_='size', value=size_value_tok)
    nr_tok = BuiltToken(type_='number', value={'sign': sign_tok,
                                               'size': size_tok})
    return BuiltToken(type_=reg_type, value=nr_tok, position_like=p)


@pg.production('mu_glue : internal_mu_glue')
@pg.production('glue : internal_glue')
def glue_internal(p):
    return BuiltToken(type_='glue', value=p[0], position_like=p)


@pg.production('mu_glue : mu_dimen mu_stretch mu_shrink')
@pg.production('glue : dimen stretch shrink')
def glue_explicit(p):
    # Wrap up arguments in a dict.
    dimens = dict(zip(glue_keys, tuple(p)))
    glue_spec = BuiltToken(type_='explicit', value=dimens, position_like=p)
    return BuiltToken(type_='glue', value=glue_spec, position_like=p)


@pg.production('shrink : minus dimen')
@pg.production('shrink : minus fil_dimen')
@pg.production('stretch : plus dimen')
@pg.production('stretch : plus fil_dimen')
@pg.production('mu_shrink : minus mu_dimen')
@pg.production('mu_shrink : minus fil_dimen')
@pg.production('mu_stretch : plus mu_dimen')
@pg.production('mu_stretch : plus fil_dimen')
def stretch_or_shrink(p):
    return p[1]


@pg.production('stretch : optional_spaces')
@pg.production('shrink : optional_spaces')
@pg.production('mu_stretch : optional_spaces')
@pg.production('mu_shrink : optional_spaces')
def stretch_or_shrink_omitted(p):
    dimen_size_token = BuiltToken(type_='internal',
                                  value=0,
                                  position_like=p)
    size_token = BuiltToken(type_='size',
                            value=dimen_size_token,
                            position_like=p)
    sign_token = BuiltToken(type_='sign', value='+', position_like=p)
    return BuiltToken(type_='dimen', value={'sign': sign_token,
                                            'size': size_token},
                      position_like=p)


@pg.production('fil_dimen : optional_signs factor fil_unit optional_spaces')
def fil_dimen(p):
    dimen_size_token = BuiltToken(type_='dimen',
                                  value={'factor': p[1], 'unit': p[2].value},
                                  position_like=p)
    size_token = BuiltToken(type_='size',
                            value=dimen_size_token,
                            position_like=p)
    return BuiltToken(type_='dimen', value={'sign': p[0], 'size': size_token},
                      position_like=p)


@pg.production('fil_unit : fil_unit NON_ACTIVE_UNCASED_l')
def fil_unit_append(p):
    # Add one infinity for every letter 'l'.
    unit = p[0]
    unit.value['number_of_fils'] += 1
    return unit


@pg.production('fil_unit : fil')
def fil_unit(p):
    unit = {'unit': PhysicalUnit.fil, 'number_of_fils': 1}
    return BuiltToken(type_='fil_unit',
                      value=unit,
                      position_like=p)


def _make_scalar_quantity_token(type_, p):
    '''Small helper to avoid repetition.'''
    return BuiltToken(type_=type_, value={'sign': p[0], 'size': p[1]},
                      position_like=p)


@pg.production('mu_dimen : optional_signs unsigned_mu_dimen')
@pg.production('dimen : optional_signs unsigned_dimen')
def maybe_mu_dimen(p):
    return _make_scalar_quantity_token('dimen', p)


@pg.production('number : optional_signs unsigned_number')
def number(p):
    return _make_scalar_quantity_token('number', p)


@pg.production('unsigned_mu_dimen : normal_mu_dimen')
@pg.production('unsigned_mu_dimen : coerced_mu_dimen')
@pg.production('unsigned_dimen : normal_dimen')
@pg.production('unsigned_dimen : coerced_dimen')
def maybe_mu_unsigned_dimen(p):
    return p[0]


@pg.production('coerced_dimen : internal_glue')
@pg.production('coerced_mu_dimen : internal_mu_glue')
def maybe_mu_coerced_dimen(p):
    raise NotImplementedError


@pg.production('unsigned_number : normal_integer')
@pg.production('unsigned_number : coerced_integer')
def unsigned_number(p):
    return p[0]


@pg.production('coerced_integer : internal_dimen')
def coerced_integer_dimen(p):
    return p[0]


@pg.production('coerced_integer : internal_glue')
def coerced_integer_glue(p):
    raise NotImplementedError


@pg.production('normal_integer : internal_integer')
def normal_integer_internal_integer(p):
    return p[0]


@pg.production('normal_dimen : internal_dimen')
def normal_dimen_internal_dimen(p):
    return p[0]


# Registers.
@pg.production('internal_mu_glue : mu_skip_register')
@pg.production('internal_glue : skip_register')
# Parameters.
@pg.production('internal_mu_glue : MU_GLUE_PARAMETER')
@pg.production('internal_glue : GLUE_PARAMETER')
def internal_glue(p):
    return p[0]


# Special quantities.
@pg.production('internal_integer : SPECIAL_INTEGER')
@pg.production('internal_dimen : SPECIAL_DIMEN')
# Registers.
@pg.production('internal_dimen : dimen_register')
@pg.production('internal_integer : count_register')
# Character codes.
@pg.production('internal_integer : CHAR_DEF_TOKEN')
@pg.production('internal_integer : MATH_CHAR_DEF_TOKEN')
# Parameters.
@pg.production('internal_dimen : DIMEN_PARAMETER')
@pg.production('internal_integer : INTEGER_PARAMETER')
def internal_scalar_quantity(p):
    return BuiltToken(type_='size',
                      value=p[0],
                      position_like=p)


@pg.production('internal_dimen : box_dimension number')
def internal_dimen_box_dimension(p):
    # TODO: Implement this.
    raise NotImplementedError
    box_dimen_type = p[0].type
    return BuiltToken(type_='box_dimen', value=1,
                      position_like=p)


@pg.production('box_dimension : BOX_DIMEN_HEIGHT')
@pg.production('box_dimension : BOX_DIMEN_WIDTH')
@pg.production('box_dimension : BOX_DIMEN_DEPTH')
def box_dimension(p):
    return p[0]


dimen_parsing.add_dimen_literals(pg)
number_parsing.add_nr_literals(pg)


@pg.production('one_optional_space : SPACE')
@pg.production('one_optional_space : empty')
def one_optional_space(p):
    return None


@pg.production(pu.get_literal_production_rule('minus'))
@pg.production(pu.get_literal_production_rule('plus'))
@pg.production(pu.get_literal_production_rule('fil'))
def literal(p):
    return pu.make_literal_token(p)


@pg.production('character : MISC_CHAR_CAT_PAIR')
@pg.production('character : EQUALS')
@pg.production('character : GREATER_THAN')
@pg.production('character : LESS_THAN')
@pg.production('character : PLUS_SIGN')
@pg.production('character : MINUS_SIGN')
@pg.production('character : ZERO')
@pg.production('character : ONE')
@pg.production('character : TWO')
@pg.production('character : THREE')
@pg.production('character : FOUR')
@pg.production('character : FIVE')
@pg.production('character : SIX')
@pg.production('character : SEVEN')
@pg.production('character : EIGHT')
@pg.production('character : NINE')
@pg.production('character : SINGLE_QUOTE')
@pg.production('character : DOUBLE_QUOTE')
@pg.production('character : BACKTICK')
@pg.production('character : COMMA')
@pg.production('character : POINT')
def character(p):
    return BuiltToken(type_='character', value=p[0].value,
                      position_like=p)


# Add character productions for letters.
for letter_type in pu.letter_to_non_active_uncased_type_map.values():
    rule = 'character : {}'.format(letter_type)
    character = pu.wrap(pg, character, rule)


# We split out some types of these letters for parsing into hexadecimal
# constants. Here we allow them to be considered as normal characters.
@pg.production('non_active_uncased_a : A')
@pg.production('non_active_uncased_a : NON_ACTIVE_UNCASED_a')
@pg.production('non_active_uncased_b : B')
@pg.production('non_active_uncased_b : NON_ACTIVE_UNCASED_b')
@pg.production('non_active_uncased_c : C')
@pg.production('non_active_uncased_c : NON_ACTIVE_UNCASED_c')
@pg.production('non_active_uncased_d : D')
@pg.production('non_active_uncased_d : NON_ACTIVE_UNCASED_d')
@pg.production('non_active_uncased_e : E')
@pg.production('non_active_uncased_e : NON_ACTIVE_UNCASED_e')
@pg.production('non_active_uncased_f : F')
@pg.production('non_active_uncased_f : NON_ACTIVE_UNCASED_f')
def non_active_uncased_hex_letter(p):
    return p[0]


@pg.production('optional_spaces : SPACE optional_spaces')
@pg.production('optional_spaces : empty')
def optional_spaces(p):
    return None


@pg.production('empty :')
def empty(p):
    return None
