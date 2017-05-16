from string import ascii_lowercase
import warnings
import logging

from ..rply import ParserGenerator
from ..tokens import BuiltToken, instructions_to_types
from ..accessors import short_hand_reg_def_token_type_to_reg_type
from ..instructions import (Instructions as I,
                            message_instructions,
                            hyphenation_instructions,
                            register_instructions,
                            h_add_glue_instructions,
                            v_add_glue_instructions,
                            short_hand_def_instructions,
                            def_instructions,
                            if_instructions
                            )

from . import (number_rules, dimen_rules, glue_rules, character_rules,
               command_rules)
from .utils import (ExpectedParsingError, ExhaustedTokensError,
                    is_end_token,
                    make_literal_token,
                    get_literal_production_rule)

logger = logging.getLogger(__name__)


terminal_instructions = (
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
    I.accent,

    I.cat_code,
    I.math_code,
    I.upper_case_code,
    I.lower_case_code,
    I.space_factor_code,
    I.delimiter_code,
    I.let,
    I.advance,
    I.par,
    I.relax,
    I.immediate,
    I.font,
    I.skew_char,
    I.hyphen_char,
    # I.font_dimen,
    I.text_font,
    I.script_font,
    I.script_script_font,
    # I.undefined,
    I.global_mod,
    I.long_mod,
    I.outer_mod,
    I.set_box,
    # I.box,
    # I.copy,
    I.un_h_box,
    I.un_h_copy,
    I.un_v_box,
    I.un_v_copy,
    # I.last_box,
    # I.v_split,
    # I.box_dimen_height,
    # I.box_dimen_width,
    # I.box_dimen_depth,
    I.kern,
    I.math_kern,
    I.v_rule,
    I.h_rule,
    I.input,
    I.end,
    I.char,
    I.indent,
    I.left_brace,
    I.right_brace,
    I.font_def_token,
    I.let_target,
    I.parameter_text,
    I.balanced_text_and_right_brace,
    I.horizontal_mode_material_and_right_brace,
    # I.vertical_mode_material_and_right_brace,
    I.h_box,
    # I.v_box,
    # I.v_top,
    I.active_character,
    I.unexpanded_control_word,
)
# Add ordinary character literals.
char_instructions = tuple(I['non_active_uncased_{}'.format(c.lower())]
                          for c in ascii_lowercase)
terminal_instructions += char_instructions
terminal_instructions += register_instructions
terminal_instructions += message_instructions
terminal_instructions += hyphenation_instructions
terminal_instructions += h_add_glue_instructions
terminal_instructions += v_add_glue_instructions
terminal_instructions += short_hand_def_instructions
terminal_instructions += def_instructions
terminal_instructions += if_instructions
terminal_types = instructions_to_types(terminal_instructions)


def add_condition_rules(pg):
    @pg.production('condition_wrap : condition')
    def condition_wrap(p):
        return p[0]

    @pg.production('condition : IF_TRUE')
    def condition_if_true(p):
        return BuiltToken(type_=p[0].type, value=None)

    @pg.production('condition : IF_FALSE')
    def condition_if_false(p):
        return BuiltToken(type_=p[0].type, value=None)

    @pg.production('condition : IF_NUM number relation number')
    def condition_if_num(p):
        return BuiltToken(type_=p[0].type,
                          value={'left_number': p[1],
                                 'right_number': p[3],
                                 'relation': p[2]})

    @pg.production('condition : IF_DIMEN dimen relation dimen')
    def condition_if_dimen(p):
        return BuiltToken(type_=p[0].type,
                          value={'left_dimen': p[1],
                                 'right_dimen': p[3],
                                 'relation': p[2]})

    @pg.production('condition : IF_ODD number')
    def condition_if_odd(p):
        return BuiltToken(type_=p[0].type, value={'number': p[1]})

    @pg.production('condition : IF_V_MODE')
    def condition_if_v_mode(p):
        return BuiltToken(type_=p[0].type, value=None)

    @pg.production('condition : IF_H_MODE')
    def condition_if_h_mode(p):
        return BuiltToken(type_=p[0].type, value=None)

    @pg.production('relation : LESS_THAN')
    @pg.production('relation : EQUALS')
    @pg.production('relation : GREATER_THAN')
    def relation(p):
        return p[0]

    @pg.production('condition : IF_CASE number')
    def condition_if_case(p):
        return BuiltToken(type_=p[0].type, value={'number': p[1]})


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
        internal_nr_tok = BuiltToken(type_='internal_number',
                                     value=p[0].value)
        nr_tok = BuiltToken(type_='number', value=internal_nr_tok)
        return BuiltToken(type_=reg_type, value=nr_tok, position_like=p)


pg = ParserGenerator(terminal_types, cache_id="changeme")
command_rules.add_command_rules(pg)
add_condition_rules(pg)
add_variable_rules(pg)
glue_rules.add_glue_rules(pg)
dimen_rules.add_dimen_rules(pg)
number_rules.add_number_rules(pg)
character_rules.add_character_rules(pg)


@pg.production('empty :')
def empty(p):
    return None


def chunker_error(look_ahead):
    # If we have exhausted the list of tokens while still
    # having a valid command, we should read more tokens until we get a syntax
    # error.
    if is_end_token(look_ahead):
        raise ExhaustedTokensError
    # Assume we have an actual syntax error, which we interpret to mean the
    # current command has finished being parsed and we are looking at tokens
    # for the next command.
    elif look_ahead is not None:
        raise ExpectedParsingError
    else:
        import pdb; pdb.set_trace()


def batch_error(look_ahead):
    raise Exception


def get_parser(start='command', chunking=True):
    """Build and return a parser that tries to construct the `start` token. By
    default this is `command`, the usual target of the program. Other values
    can be passed to get smaller semantic units, for detailed parsing and
    testing."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        parser = pg.build(start=start)
    if chunking:
        error_handler = chunker_error
    else:
        error_handler = batch_error
    parser.error_handler = error_handler
    return parser


command_parser = get_parser()
