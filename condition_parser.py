import operator

from typer import if_map
from common_parsing import pg as common_pg, evaluate_number


pg = common_pg.copy_to_extend()

pg.tokens += tuple(if_map.values())


class ExpectedParsingError(Exception):
    pass


@pg.production('condition : IF_TRUE')
def condition_if_true(parser_state, p):
    return True


@pg.production('condition : IF_FALSE')
def condition_if_false(parser_state, p):
    return False


@pg.production('condition : IF_NUM number relation number')
def condition_if_num(parser_state, p):
    nr_1 = evaluate_number(parser_state, p[1])
    nr_2 = evaluate_number(parser_state, p[3])

    relation = p[2].value['char']
    operator_map = {
        '<': operator.lt,
        '=': operator.eq,
        '>': operator.gt,
    }
    op = operator_map[relation]
    outcome = op(nr_1, nr_2)
    return outcome


@pg.production('condition : IF_CASE number')
def condition_if_case(parser_state, p):
    return evaluate_number(parser_state, p[1])


@pg.production('relation : LESS_THAN')
@pg.production('relation : EQUALS')
@pg.production('relation : GREATER_THAN')
def relation(parser_state, p):
    return p[0]


@pg.error
def error(parser_state, p):
    raise ExpectedParsingError

condition_parser = pg.build()
