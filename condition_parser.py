import operator

from typer import if_map
from common import Token
from common_parsing import pg as common_pg, evaluate_number
from parse_utils import ExpectedParsingError, ExhaustedTokensError, is_end_token


pg = common_pg.copy_to_extend()

pg.tokens += tuple(if_map.values())


@pg.production('outcome_wrap : outcome')
def outcome_wrap(parser_state, p):
    return Token(type_='outcome', value=p[0])


@pg.production('outcome : IF_TRUE')
def outcome_if_true(parser_state, p):
    return True


@pg.production('outcome : IF_FALSE')
def outcome_if_false(parser_state, p):
    return False


@pg.production('outcome : IF_NUM number relation number')
def outcome_if_num(parser_state, p):
    nr_1 = evaluate_number(parser_state.state, p[1])
    nr_2 = evaluate_number(parser_state.state, p[3])

    relation = p[2].value['char']
    operator_map = {
        '<': operator.lt,
        '=': operator.eq,
        '>': operator.gt,
    }
    op = operator_map[relation]
    outcome = op(nr_1, nr_2)
    return outcome


@pg.production('outcome : IF_CASE number')
def outcome_if_case(parser_state, p):
    return evaluate_number(parser_state.state, p[1])


@pg.production('relation : LESS_THAN')
@pg.production('relation : EQUALS')
@pg.production('relation : GREATER_THAN')
def relation(parser_state, p):
    return p[0]


@pg.error
def error(parser_state, look_ahead):
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
    # if parser_state.in_recovery_mode:
    #     print("Syntax error in input!")
    #     post_mortem(parser_state, parser)
    #     raise ValueError

condition_parser = pg.build()
