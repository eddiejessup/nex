from ..tokens import BuiltToken


def add_condition_rules(pg):
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
