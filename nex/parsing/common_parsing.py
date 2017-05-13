from string import ascii_lowercase

from ..rply import ParserGenerator

from ..tokens import BuiltToken, instructions_to_types
from ..registers import short_hand_reg_def_token_type_to_reg_type
from ..instructions import Instructions as I, register_instructions

from . import number_parsing
from . import dimen_parsing
from . import character_parsing

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


dimen_parsing.add_glue_literals(pg)


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
# Box dimension.
@pg.production('internal_dimen : box_dimension number')
def internal_scalar_quantity(p):
    return BuiltToken(type_='size',
                      value=p[0],
                      position_like=p)


@pg.production('box_dimension : BOX_DIMEN_HEIGHT')
@pg.production('box_dimension : BOX_DIMEN_WIDTH')
@pg.production('box_dimension : BOX_DIMEN_DEPTH')
def box_dimension(p):
    # TODO: Implement this.
    raise NotImplementedError
    box_dimen_type = p[0].type
    return BuiltToken(type_='box_dimen', value=1,
                      position_like=p)


dimen_parsing.add_dimen_literals(pg)
number_parsing.add_nr_literals(pg)
character_parsing.add_character_literals(pg)
