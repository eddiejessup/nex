import operator

from expander import if_map
from common_parsing import pg as common_pg, evaluate_number


pg = common_pg.copy_to_extend()

pg.tokens += tuple(if_map.values())


@pg.production('condition : IF_NUM number relation number')
def condition_if_num(parser_state, p):
    nr_1 = evaluate_number(p[1])
    nr_2 = evaluate_number(p[3])
    relation = p[2].value['char']
    operator_map = {
        '<': operator.lt,
        '=': operator.eq,
        '>': operator.gt,
    }
    op = operator_map[relation]
    outcome = op(nr_1, nr_2)
    return outcome


@pg.production('relation : LESS_THAN')
@pg.production('relation : EQUALS')
@pg.production('relation : GREATER_THAN')
def relation(parser_state, p):
    return p[0]

condition_parser = pg.build()
