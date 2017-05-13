from string import ascii_lowercase

from ..rply import ParserGenerator

from ..tokens import BuiltToken, instructions_to_types
from ..registers import short_hand_reg_def_token_type_to_reg_type
from ..instructions import Instructions as I, register_instructions

from . import number_rules
from . import dimen_rules
from . import glue_rules
from . import character_rules

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


def get_common_pg():
    pg = ParserGenerator(common_terminal_types, cache_id="changeme")
    return pg


def add_variable_rules(pg):
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


def add_common_rules(pg):
    add_variable_rules(pg)
    glue_rules.add_glue_rules(pg)
    dimen_rules.add_dimen_rules(pg)
    number_rules.add_number_rules(pg)
    character_rules.add_character_rules(pg)

    @pg.production('empty :')
    def empty(p):
        return None
