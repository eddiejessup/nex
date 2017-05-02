from ..rply import ParserGenerator

from ..tokens import BuiltToken

from .utils import (ExpectedParsingError, ExhaustedTokensError,
                    is_end_token)

term_types = ['SPACE', 'RELAX', 'LEFT_BRACE', 'BALANCED_TEXT_AND_RIGHT_BRACE']
gen_txt_pg = ParserGenerator(term_types, cache_id="general_text")


@gen_txt_pg.production('general_text : filler LEFT_BRACE BALANCED_TEXT_AND_RIGHT_BRACE')
def general_text(p):
    return BuiltToken(type_='general_text', value=p[2].value,
                      position_like=p)


@gen_txt_pg.production('filler : optional_spaces')
@gen_txt_pg.production('filler : filler RELAX optional_spaces')
def filler(p):
    return None


@gen_txt_pg.production('optional_spaces : SPACE optional_spaces')
@gen_txt_pg.production('optional_spaces : empty')
def optional_spaces(p):
    return None


@gen_txt_pg.production('empty :')
def empty(p):
    return None


@gen_txt_pg.error
def error(look_ahead):
    # TODO: remove duplication of this function with command parser.
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
        raise Exception


general_text_parser = gen_txt_pg.build()
