from .typer import if_map
from .common import Token
from .common_parsing import pg as common_pg
from .parse_utils import (ExpectedParsingError, ExhaustedTokensError,
                          is_end_token)


pg = common_pg.copy_to_extend()

pg.tokens += tuple(if_map.values())


@pg.production('condition_wrap : condition')
def condition_wrap(p):
    return Token(type_='condition', value=p[0])


@pg.production('condition : IF_TRUE')
def condition_if_true(p):
    return Token(type_='if_true', value=None)


@pg.production('condition : IF_FALSE')
def condition_if_false(p):
    return Token(type_='if_false', value=None)


@pg.production('condition : IF_NUM number relation number')
def condition_if_num(p):
    return Token(type_='if_num',
                 value={'left_number': p[1],
                        'right_number': p[3],
                        'relation': p[2]})


@pg.production('condition : IF_CASE number')
def condition_if_case(p):
    return Token(type_='if_case',
                 value={'number': p[1]})


@pg.production('relation : LESS_THAN')
@pg.production('relation : EQUALS')
@pg.production('relation : GREATER_THAN')
def relation(p):
    return p[0].value['char']


@pg.error
def error(look_ahead):
    # TODO: remove duplication of this function with main parser.
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

condition_parser = pg.build()
